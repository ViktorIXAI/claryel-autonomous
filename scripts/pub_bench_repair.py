#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validator-driven repair arm, contract `pub-repair-v1`.

Why this exists: the frozen contour `0.0.2.56` produced ZERO repair events on every public parity
workspace (IFEval 541 rows -> 541 model calls, 0 fixes, 0 blocks, 0 ladder steps; BFCL 1244 -> 1244;
HumanEval 164 -> 164; MMLU-Pro 500 -> 500), while the same runtime fires 30-46 fixes over 77 rows on
the hard bank. The reason is structural: its gates watch request/response *shape*, and on public sets
the first response is already well-formed. The one place where a public set does have a real verifier
(the vendored IFEval checker) is wired into scoring only, never into a repair path.

This arm measures the missing loop, at arm level and without touching the frozen line:
  1. read the pinned first-arm answer bytes (no paid re-run of the first pass),
  2. run the pinned validator on them,
  3. for a task the validator rejects, re-ask ONCE, naming the violated check ids and their pinned
     kwargs, and showing the rejected attempt,
  4. re-check the retry with the same validator,
  5. keep the first answer whenever the retry does not strictly pass (a repair must never hurt).

Two percents are published, never one, because the keep-best rule is a lower bound and a naive
harness would take the second answer unconditionally:
  keep-best  : max(first, retry) per asked task,
  retry-only : the retry replaces the first answer for every asked task.

Nothing here registers a contour stamp and nothing edits a stored arm: `0.0.2.56` rows stay byte for
byte. The arm is resumable by task id and refuses to score when the first arm is partial.

Usage: pub_bench_repair.py <tasks.jsonl> <first-answers.jsonl> [--limit N] [--out DIR]
       --validator ifeval|lcb-public [--hidden F.gz]     (livecodebench: validator = the question's
       PUBLIC sample tests, scorer = the hidden battery; the loop never sees a hidden byte)
Env:   PARB_API, PARB_KEY_FILE, PARB_MODEL  (same pinned endpoint as the first arm)
"""
import argparse
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import time
import urllib.request

CONTRACT = "pub-repair-v1"
HERE = pathlib.Path(__file__).resolve().parent
MAX_PREV_CHARS = 1500          # the rejected attempt is shown, truncated; the flag is recorded
MAX_PREV_CHARS_CODE = 4000     # code answers need the rejected program itself to be reviewable
MAX_FAIL_CHARS = 700           # per sample-test field shown in an lcb re-ask
TEMP = 0.7
AUTH_PREFIX = "Bearer"


def sha16(p):
    return hashlib.sha1(pathlib.Path(p).read_bytes()).hexdigest()[:16]


def check_text(task, idx):
    """Human-usable description of a violated pinned check: id + its pinned kwargs."""
    cid = task["instruction_id_list"][idx]
    kw = (task.get("kwargs") or [{}])[idx] if idx < len(task.get("kwargs") or []) else {}
    return cid, json.dumps(kw, ensure_ascii=False, sort_keys=True)


def build_prompt(task, prev):
    fails = task["_failed_checks"]
    lines = ["Your previous answer was rejected by a mechanical checker. It violated these checks:"]
    for cid, kw in fails:
        lines.append("- %s%s" % (cid, "" if kw == "{}" else " (parameters: %s)" % kw))
    prev_cut = prev if len(prev) <= MAX_PREV_CHARS else prev[:MAX_PREV_CHARS] + "\n[truncated]"
    task["_prev_truncated"] = len(prev) > MAX_PREV_CHARS
    return ("%s\n\n%s\n\nRejected attempt:\n%s\n\n"
            "Rewrite the answer so that every check above is satisfied exactly. "
            "Output only the corrected answer."
            % (task["prompt"], "\n".join(lines), prev_cut))


def api_call(url, key, model, prompt, max_tokens):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": TEMP, "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": AUTH_PREFIX + " " + key})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)


# ------------------------------------------------------------- lcb-public validator
# Contract `lcb-public-v1`: the repair loop's validator is the question's OWN PUBLIC sample tests
# (tracked bytes of the pinned tasks file), executed through the same pinned contract that scores
# (`lcb-exec-v2`: `run_stdin` for stdin tasks, the functional driver for functional tasks). The
# hidden battery only scores, offline, after the arm: the loop names public inputs/expected
# outputs it already ships in the prompt, never a hidden byte. Blind spots are published
# honestly: a hidden failure whose PUBLIC tests pass is invisible to the loop by construction.

def public_verdict(lcb, task, answer):
    """Run the question's public sample tests over the extracted code.
    -> (passed, fails) with fails = [(idx, verdict, test)] up to the first three.
    stdin regime: one `run_stdin` child per public test. functional regime (lcb-exec-v2):
    the same driver over the question's PUBLIC functional cases — stub gives the signature,
    the case gives the args — so the validator sees public sample bytes only in both regimes;
    the hidden battery never enters this function."""
    code = lcb.extract_code(answer)
    if not code.strip():
        return False, [(None, "empty_code", None)]
    fails = []
    tests = task.get("public_tests") or []
    if task.get("testtype") == "functional":
        sig = lcb.stub_signature(task.get("starter_code") or "")
        seen, cases = [], []
        if sig is None:
            return True, []                                # validator blind: no fake fail, no ask
        meth, npar = sig
        for i, test in enumerate(tests):
            args = lcb.func_args(test["input"], npar)
            exp = None
            try:
                exp = json.loads(test["output"])
            except ValueError:
                args = None
            if args is None:
                return True, []                            # malformed public bytes: blind, not fail
            cases.append((args, exp))
            seen.append(test)
        if not cases:
            return True, []
        with tempfile.TemporaryDirectory(prefix="lcbpubf-") as wd:
            with open(os.path.join(wd, "_driver.py"), "w", encoding="utf-8") as fh:
                fh.write(lcb._DRIVER_SRC)
            for f in lcb.run_functional(code, cases, meth, wd)[:3]:
                i = int(f.partition(":")[0][4:])
                fails.append((i, f.partition(":")[2], seen[i]))
        return not fails, fails
    with tempfile.TemporaryDirectory(prefix="lcbpub-") as wd:
        for i, test in enumerate(tests):
            v = lcb.run_stdin(code, test, wd)
            if v != "ok":
                fails.append((i, v, test))
                if len(fails) >= 3:
                    break
    return not fails, fails


def build_prompt_lcb(task, prev):
    lines = ["Your previous program failed the sample tests of the task above:"]
    for idx, v, test in task["_fails"]:
        if test is None:
            lines.append("- no runnable program was found in your answer.")
            continue
        lines.append("- sample test %d: verdict %s\n  input:\n%s\n  expected output:\n%s"
                     % (idx, v, (test["input"] or "")[:MAX_FAIL_CHARS],
                        (test["output"] or "")[:MAX_FAIL_CHARS]))
    cut = prev if len(prev) <= MAX_PREV_CHARS_CODE \
        else prev[:MAX_PREV_CHARS_CODE] + "\n[truncated]"
    task["_prev_truncated"] = len(prev) > MAX_PREV_CHARS_CODE
    if task.get("testtype") == "functional":
        body = ("%s\n\nStarter signature:\n```python\n%s```\n\n%s\n\nRejected attempt:\n%s\n\n"
                "Write the complete corrected solution for the task above: one Python class "
                "`Solution` implementing the method from the starter signature. The tests call "
                "the method directly with the arguments shown in the sample tests; do not read "
                "from standard input. Output only the class, in one Python code block."
                % (task["prompt"], task.get("starter_code") or "", "\n".join(lines), cut))
        return body
    return ("%s\n\n%s\n\nRejected attempt:\n%s\n\n"
            "Write the complete corrected program for the task above. It must read from standard "
            "input and print to standard output in exactly the format the sample tests show. "
            "Output only the program, in one Python code block."
            % (task["prompt"], "\n".join(lines), cut))


def run_lcb(a, tasks, first, first_rows):
    """pub-repair-lcb-v1: public-test validator, hidden-battery scorer. Kept separate from the
    ifeval flow so published v1/v2 re-scores keep byte-identical code paths."""
    global CONTRACT
    CONTRACT = "pub-repair-lcb-v1"
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import pub_bench_lcb as lcb                            # noqa: E402
    import gzip as _gzip
    if not lcb.selftest():
        sys.exit("REFUSING TO RUN: %s checker gate failed" % lcb.LCB_CONTRACT)
    if not a.hidden:
        sys.exit("REFUSING TO RUN: --hidden <sidecar.gz> is required for --validator lcb-public")
    hidden = {}
    with _gzip.open(a.hidden, "rt", encoding="utf-8") as gz:
        for l in gz:
            if l.strip():
                h = json.loads(l)
                hidden[h["id"]] = h["tests"]

    budgets = {r.get("max_tokens") for r in first_rows if r.get("max_tokens")}
    if len(budgets) != 1:
        sys.exit("REFUSING TO RUN: first arm mixes call budgets %s" % sorted(map(str, budgets)))
    max_tokens = int(budgets.pop())
    first_budget = max_tokens
    env_budget = os.environ.get("PARB_MAX_TOKENS")
    if env_budget and int(env_budget) != max_tokens:
        CONTRACT = "pub-repair-lcb-v2"
        print("note: PARB_MAX_TOKENS overrides the first arm budget %d -> %d; this arm runs "
              "under contract %s" % (max_tokens, int(env_budget), CONTRACT), flush=True)
        max_tokens = int(env_budget)
    temps = {r.get("temp") for r in first_rows if r.get("temp") is not None}
    if temps and temps != {TEMP}:
        sys.exit("REFUSING TO RUN: first arm temperature %s != this arm's %s" % (temps, TEMP))

    # Validate the first arm with the PUBLIC tests only, and pin the hidden scorer wiring: the
    # first-arm hidden verdicts must equal the published bare arm's shipped verdict rows cell for
    # cell, or this script is mis-wired and nothing may run.
    hv_first, asked = {}, []
    for t in tasks:
        if t["id"] not in hidden:
            sys.exit("REFUSING TO RUN: no hidden payload row for %s" % t["id"])
        v, _why = lcb.score_question(t, hidden[t["id"]], first[t["id"]])
        if v == "unscored":
            sys.exit("REFUSING TO RUN: hidden scorer unscored %s" % t["id"])
        hv_first[t["id"]] = (v == "ok")
        passed, fails = public_verdict(lcb, t, first[t["id"]])
        t["_fails"] = fails
        if not passed:
            asked.append(t)
    n_first = sum(1 for ok in hv_first.values() if ok)
    print("first arm hidden %d/%d (all %d regimes scored by %s) | public validator rejects %d "
          "tasks (%d stdin, %d functional) -> %d re-asks"
          % (n_first, len(hv_first), len(tasks), lcb.LCB_CONTRACT, len(asked),
             sum(1 for t in asked if t["testtype"] == "stdin"),
             sum(1 for t in asked if t["testtype"] == "functional"), len(asked)), flush=True)
    if a.verdicts_ref:
        ref = {}
        for line in pathlib.Path(a.verdicts_ref).read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                ref.setdefault(r["id"], bool(r["ok"]))
        diff = [i for i in hv_first if ref.get(i) != hv_first[i]]
        if diff or set(ref) != set(hv_first):
            sys.exit("REFUSING TO RUN: first-arm hidden verdicts differ from the published "
                     "reference on %d cells %s" % (len(diff), diff[:5]))
        print("first-arm hidden verdicts match the published reference cell for cell (%d ids)"
              % len(ref), flush=True)
    if a.dry_run:
        return 0

    if a.merge:
        url = key_file = key = model = None
    else:
        url = os.environ.get("PARB_API")
        key_file = os.environ.get("PARB_KEY_FILE")
        model = os.environ.get("PARB_MODEL")
        if not (url and key_file and model):
            raise SystemExit("PARB_API, PARB_KEY_FILE and PARB_MODEL are required")
        key = json.load(open(key_file, encoding="utf-8"))["api_key"]

    out = pathlib.Path(a.out or str(pathlib.Path(a.first_answers).parent))
    out.mkdir(parents=True, exist_ok=True)   # --out may name a directory that does not exist yet
    dst = out / ("pub-repair-%s.jsonl" % CONTRACT)
    done = {}
    if dst.exists():
        for line in dst.read_text().splitlines():
            r = json.loads(line)
            if r.get("finish") == "ok":
                done[r["id"]] = r
    queue = [t for t in asked if t["id"] not in done]
    if a.limit:
        queue = queue[:a.limit]
    if a.merge:
        queue = []
    print("asked=%d already stored=%d to run=%d" % (len(asked), len(done), len(queue)), flush=True)

    t0, n_bad = time.time(), 0
    with dst.open("a", encoding="utf-8") as fh:
        for i, t in enumerate(queue):
            rec = {"id": t["id"], "bench": t["bench"], "arm": CONTRACT, "model": model,
                   "temp": TEMP, "max_tokens": max_tokens,
                   "task_sha16": sha16(a.tasks), "first_answer_sha16":
                   hashlib.sha1(first[t["id"]].encode()).hexdigest()[:16],
                   "failed_samples": ["test%d:%s" % (ix, v) for ix, v, _ in t["_fails"]],
                   "validator": "lcb-public-v1", "prev_truncated": False}
            st = time.time()
            try:
                r = api_call(url, key, model, build_prompt_lcb(t, first[t["id"]]), max_tokens)
                ch = (r.get("choices") or [{}])[0]
                rec["answer"] = (ch.get("message") or {}).get("content") or ""
                rec["finish"] = "ok" if rec["answer"].strip() else "empty"
                rec["api_finish"] = ch.get("finish_reason")
                u = r.get("usage") or {}
                rec["ptok"], rec["ctok"] = u.get("prompt_tokens"), u.get("completion_tokens")
            except Exception as exc:                      # noqa: BLE001 - store, do not hide
                rec["answer"], rec["finish"] = "", "error"
                rec["engine_error"] = "%s: %s" % (type(exc).__name__, str(exc)[:160])
                n_bad += 1
            rec["seconds"] = round(time.time() - st, 2)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if (i + 1) % 10 == 0:
                rate = (i + 1) / max(time.time() - t0, 0.01)
                print("repair %d/%d %.1f s/task eta %.0f s"
                      % (i + 1, len(queue), (time.time() - t0) / (i + 1),
                         (len(queue) - i - 1) / rate), flush=True)

    stored = dict(done)
    for line in dst.read_text().splitlines():
        r = json.loads(line)
        if r.get("finish") == "ok":
            stored[r["id"]] = r

    # Retry validation is PUBLIC-only, exactly like the first pass; keep-best is validator-driven,
    # never hidden-driven. The hidden battery then scores the merged arm (that is the measurement).
    pub_ok = {}
    for t in asked:
        if t["id"] in stored:
            pub_ok[t["id"]] = public_verdict(lcb, t, stored[t["id"]]["answer"])[0]
    hv_merged, hv_retry_only = {}, {}
    for t in tasks:
        keep = "retry" if pub_ok.get(t["id"]) is True else "first"
        ans_m = stored[t["id"]]["answer"] if (t["id"] in stored and keep == "retry") \
            else first[t["id"]]
        ans_r = stored[t["id"]]["answer"] if (t["id"] in stored and t in asked) \
            else first[t["id"]]
        hv_merged[t["id"]] = lcb.score_question(t, hidden[t["id"]], ans_m)[0] == "ok"
        hv_retry_only[t["id"]] = lcb.score_question(t, hidden[t["id"]], ans_r)[0] == "ok"
        t["_keep"] = keep
    n = len(hv_merged)
    kb = sum(1 for ok in hv_merged.values() if ok)
    ro = sum(1 for ok in hv_retry_only.values() if ok)
    fixed = [i for i in hv_merged if hv_merged[i] and not hv_first[i]]
    worse = [i for i in hv_merged if hv_first[i] and not hv_merged[i]]
    p_kb, p_ro = 0, 0
    try:
        from pub_bench_compare import sign_test          # one sign test for the whole line
        p_kb = sign_test(len(fixed), len(worse))
    except Exception:                                    # noqa: BLE001
        pass
    first_model = first_rows[0].get("model")
    merged, verdict_rows = [], []
    for t in tasks:
        keep = t.get("_keep", "first")
        merged.append({"id": t["id"], "bench": t["bench"], "arm": "%s-merged" % CONTRACT,
                       "model": first_model, "temp": TEMP, "max_tokens": max_tokens,
                       "finish": "ok", "kept": keep,
                       "answer": stored[t["id"]]["answer"]
                       if (t["id"] in stored and keep == "retry") else first[t["id"]]})
        hid = t["id"] in hv_first
        verdict_rows.append({"id": t["id"],
                             "hidden_first": hv_first.get(t["id"]),
                             "retry_public_ok": pub_ok.get(t["id"]),
                             "hidden_kept": hv_merged.get(t["id"]),
                             "kept": keep,
                             "strict": hv_merged.get(t["id"]) if hid else None})
    for name, rows in (("%s-merged-answers.jsonl" % CONTRACT, merged),
                       ("%s-verdicts.jsonl" % CONTRACT, verdict_rows)):
        (out / name).write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True)
                                          for r in rows) + "\n")
        (out / (name + ".sha16")).write_text(
            hashlib.sha1((out / name).read_bytes()).hexdigest()[:16] + "\n")
    ptok = sum(r.get("ptok") or 0 for r in stored.values())
    ctok = sum(r.get("ctok") or 0 for r in stored.values())
    cen = {"contract": CONTRACT, "tasks": n, "task_sha16": sha16(a.tasks),
           "functional_tasks": sum(1 for t in tasks if t["testtype"] != "stdin"),
           "first_arm_hidden": n_first, "asked_stored": len(pub_ok),
           "asked_unrun": len(asked) - len(pub_ok),
           "retry_passes_public": sum(1 for ok in pub_ok.values() if ok),
           "retry_fails_public": sum(1 for ok in pub_ok.values() if not ok),
           "hidden_fixed": len(fixed), "hidden_fixed_ids": sorted(fixed),
           "hidden_worse": len(worse), "hidden_worse_ids": sorted(worse),
           "sign_test_keepbest_vs_first_p": p_kb,
           "keep_best_hidden": kb, "retry_only_hidden": ro,
           "validator": "lcb-public-v1 (public sample tests only)",
           "checker": lcb.LCB_CONTRACT,
           "hidden_sidecar_sha16": sha16(a.hidden),
           "call": {"temp": TEMP, "max_tokens": max_tokens,
                    "first_arm_max_tokens": first_budget},
           "retry_calls": len(stored), "retry_prompt_tokens": ptok,
           "retry_completion_tokens": ctok,
           "wall_s": round(time.time() - t0, 1), "transport_errors": n_bad,
           "first_answers_sha16": sha16(a.first_answers)}
    (out / ("pub-repair-%s-census.json" % CONTRACT)).write_text(json.dumps(cen, indent=2) + "\n")
    print("census: asked %d/%d | retry passes public %d | hidden fixed %d | hidden worse %d | "
          "unrun %d" % (len(pub_ok), len(asked), cen["retry_passes_public"], len(fixed),
                        len(worse), len(asked) - len(pub_ok)))
    print("%s keep-best hidden %d/%d = %.1f %% | retry-only %d/%d = %.1f %% | first arm was "
          "%d/%d = %.1f %%" % (CONTRACT, kb, n, 100.0 * kb / n, ro, n, 100.0 * ro / n,
                               n_first, n, 100.0 * n_first / n))
    if len(pub_ok) != len(asked):
        print("PARTIAL: %d re-asks still missing - no digest row written"
              % (len(asked) - len(pub_ok)))
        return 1

    if a.merge or a.no_digest:
        print("--merge / --no-digest: artifacts written, no digest row")
        return 0
    dig = HERE.parent / "benchmarks" / "public" / "PUB-DIGEST.md"
    import pub_bench_score as pbs                          # noqa: E402
    bench = tasks[0]["bench"]
    # the tasks cell must name the SAME sha the scorer rows for this set use (SHA-256/16), or
    # digest rows for one set would not be comparable; the census names SHA-1/16 beside it
    tasks_cell = hashlib.sha256(open(a.tasks, "rb").read()).hexdigest()[:16]
    model_label = "%s+%s(keep-best)" % (model or first_model, CONTRACT)
    key_cell = "\n| %s | %s | %d | %s |" % (bench, model_label, n, tasks_cell)
    body = dig.read_text() if dig.exists() else ""
    if key_cell in body:
        print("digest row already present - not duplicated")
    else:
        line = ("| %s | %s | %d | %s | validator = the question's PUBLIC sample tests "
                "(lcb-public-v1), scorer = hidden battery %s over the full set (%d functional "
                "questions driver-scored): %d re-asks, %d pass public after repair, hidden "
                "fixed %d, hidden worse %d (sign test p=%.2g); same %s, temp %.1f, "
                "retry max_tokens %d (first arm %d); retry-only variant "
                "%d/%d = %.1f%% | %d/%d = **%.1f%%** |"
                % (bench, model_label, n, tasks_cell, lcb.LCB_CONTRACT,
                   cen["functional_tasks"], len(pub_ok),
                   cen["retry_passes_public"], len(fixed), len(worse), p_kb, lcb.LCB_CONTRACT,
                   TEMP, max_tokens, first_budget, ro, n,
                   100.0 * ro / n, kb, n, 100.0 * kb / n))
        pbs.write_digest(line, str(dig))
        print("digest row appended")
    return 0


# ------------------------------------------------------------------ bfcl validator
# Contract `pub-repair-bfcl-v1`, the line's PRE-REGISTERED NEGATIVE CONTROL. On this set the pinned
# AST verifier (`bfcl-ast-v1`) IS the scorer: there is no held-out signal the loop could be accused
# of reading, but there is also no proxy, so two rails keep the row honest.
#   (1) The re-ask names only the failure CLASS — never a gold call name, never an expected call
#       count, never a parameter value. A gold call name would be a grading byte the bare prompt
#       never ships, and the arm would measure hint-reading instead of repair.
#   (2) The redraw control published beside the row is computed from PUBLISHED bytes of the same
#       brain at the same shape (`--control-verdicts`, the contour-0.0.2.56 matched arm): the cells
#       where a plain second draw under the same keep rule turned a first-arm failure into a pass.
#       A repair pass is only worth claiming above that count.
# Because every asked cell is a first-arm failure, keep-best and retry-only coincide by
# construction here (a failed retry replaces an already-failing answer); the census says so.

BFCL_CLASS_TEXT = {
    "calls": "the answer did not contain exactly the number of function calls the request implies "
             "(a call is missing or an extra call was emitted)",
    "unmatched": "at least one function call in the answer does not match the request — re-check "
                 "the function name, every parameter name and every parameter value and type "
                 "against the function docs given above",
}


def bfcl_class(why):
    """Verifier verdict -> failure class, with every gold token stripped."""
    stem = (why.split("=")[0] if "=" in why else why.split(" ")[0]).strip()
    return stem, BFCL_CLASS_TEXT.get(stem, "the pinned verifier rejected the answer")


def build_prompt_bfcl(B, task, prev):
    """The retry request PREFIX is the pinned first-arm prompt bytes verbatim (`task["prompt"]` is
    exactly what `pub_bench_run.py` sent), so the retry differs from the bare call only by the
    feedback block appended after it."""
    stem, text = bfcl_class(task["_why"])
    truncated = len(prev or "") > MAX_PREV_CHARS_CODE
    return ("%s\n\n### Verifier feedback on your previous answer\n"
            "The pinned verifier rejected your previous answer for this exact request. The request "
            "and the function docs above are unchanged; nothing has been added to them.\n"
            "What the verifier reports: %s\n"
            "Re-answer the request above in the required format (only the calls, one per line, no "
            "explanation) and fix exactly what the verdict names.\n\n"
            "### Your previous answer%s\n%s\n"
            % (task["prompt"], text,
               " (truncated)" if truncated else "", (prev or "")[:MAX_PREV_CHARS_CODE]))


def run_bfcl(a, tasks, first, first_rows):
    """pub-repair-bfcl-v1: verdict-only re-ask over the AST-checker failures, keep-best."""
    global CONTRACT
    CONTRACT = "pub-repair-bfcl-v1"
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import pub_bench_bfcl as B                            # noqa: E402
    if not B.selftest():
        sys.exit("REFUSING TO RUN: %s checker gate failed" % B.BFCL_CHECKER)

    budgets = {r.get("max_tokens") for r in first_rows if r.get("max_tokens")}
    if len(budgets) != 1:
        sys.exit("REFUSING TO RUN: first arm mixes call budgets %s" % sorted(map(str, budgets)))
    max_tokens = int(budgets.pop())
    first_budget = max_tokens
    env_budget = os.environ.get("PARB_MAX_TOKENS")
    if env_budget and int(env_budget) != max_tokens:
        CONTRACT = "pub-repair-bfcl-v2"
        print("note: PARB_MAX_TOKENS overrides the first arm budget %d -> %d; this arm runs "
              "under contract %s" % (max_tokens, int(env_budget), CONTRACT), flush=True)
        max_tokens = int(env_budget)
    temps = {r.get("temp") for r in first_rows if r.get("temp") is not None}
    temps.discard(None)
    if temps and temps != {TEMP}:
        sys.exit("REFUSING TO RUN: first arm temperature %s != this arm's %s" % (temps, TEMP))

    # Wiring guard: the first arm must reproduce the PUBLISHED verdict rows cell for cell, or this
    # script is mis-wired and no model call may happen.
    ok_first, asked = {}, []
    for t in tasks:
        if t["id"] not in first:
            sys.exit("REFUSING TO RUN: no first-arm answer for %s" % t["id"])
        ok, why = B.score_entry(t, first[t["id"]])
        ok_first[t["id"]] = ok
        t["_why"] = why
        t["_class"] = bfcl_class(why)[0]
        if not ok:
            asked.append(t)
    n_first = sum(1 for v in ok_first.values() if v)
    by_class = {}
    for t in asked:
        by_class[t["_class"]] = by_class.get(t["_class"], 0) + 1
    print("first arm %d/%d = %.1f %% | verifier rejects %d tasks (%s) -> %d re-asks"
          % (n_first, len(ok_first), 100.0 * n_first / len(ok_first), len(asked),
             ", ".join("%s %d" % kv for kv in sorted(by_class.items())), len(asked)), flush=True)

    if a.verdicts_ref:
        ref = {}
        for line in pathlib.Path(a.verdicts_ref).read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                ref.setdefault(r["id"], bool(r["ok"]))
        diff = [i for i in ok_first if ref.get(i) != ok_first[i]]
        if diff or set(ref) != set(ok_first):
            sys.exit("REFUSING TO RUN: first-arm verdicts differ from the published reference on "
                     "%d cells %s" % (len(diff), diff[:5]))
        print("first-arm verdicts match the published reference cell for cell (%d ids)"
              % len(ref), flush=True)

    # Redraw control, computed from published bytes BEFORE any call: how many first-arm failures a
    # plain second draw of this brain at the same shape turned into passes.
    control = {"file": None, "control_arms": 0, "redraw_keep_conversions": None}
    if a.control_verdicts:
        cv = {}
        for line in pathlib.Path(a.control_verdicts).read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                cv.setdefault(r["id"], bool(r["ok"]))
        if set(cv) != set(ok_first):
            sys.exit("REFUSING TO RUN: control verdicts cover %d ids, first arm covers %d"
                     % (len(cv), len(ok_first)))
        conv = [i for i in ok_first if not ok_first[i] and cv[i]]
        control = {"file": str(pathlib.Path(a.control_verdicts).name),
                   "file_sha16": sha16(a.control_verdicts),
                   "control_arm_pass": sum(1 for v in cv.values() if v),
                   "redraw_keep_conversions": len(conv),
                   "redraw_keep_pp": round(100.0 * len(conv) / len(ok_first), 2)}
        print("redraw control (%s): a plain second draw converts %d first-arm failures (%.2f pp)"
              % (control["file"], control["redraw_keep_conversions"],
                 control["redraw_keep_pp"]), flush=True)

    if a.dry_run:
        return 0

    if a.merge:
        url = key_file = key = model = None
    else:
        url = os.environ.get("PARB_API")
        key_file = os.environ.get("PARB_KEY_FILE")
        model = os.environ.get("PARB_MODEL")
        if not (url and key_file and model):
            raise SystemExit("PARB_API, PARB_KEY_FILE and PARB_MODEL are required")
        key = json.load(open(key_file, encoding="utf-8"))["api_key"]

    out = pathlib.Path(a.out or str(pathlib.Path(a.first_answers).parent))
    out.mkdir(parents=True, exist_ok=True)   # --out may name a directory that does not exist yet
    dst = out / ("pub-repair-%s.jsonl" % CONTRACT)
    done = {}
    if dst.exists():
        for line in dst.read_text().splitlines():
            r = json.loads(line)
            if r.get("finish") == "ok":
                done[r["id"]] = r
    queue = [t for t in asked if t["id"] not in done]
    if a.limit:
        queue = queue[:a.limit]
    if a.merge:
        queue = []
    print("asked=%d already stored=%d to run=%d" % (len(asked), len(done), len(queue)), flush=True)

    t0, n_bad = time.time(), 0
    with dst.open("a", encoding="utf-8") as fh:
        for i, t in enumerate(queue):
            rec = {"id": t["id"], "bench": t["bench"], "arm": CONTRACT, "model": model,
                   "temp": TEMP, "max_tokens": max_tokens,
                   "task_sha16": sha16(a.tasks),
                   "first_answer_sha16": hashlib.sha1(first[t["id"]].encode()).hexdigest()[:16],
                   "verifier_class": t["_class"], "validator": "bfcl-ast-v1 (verdict only)",
                   "prev_truncated": len(first[t["id"]] or "") > MAX_PREV_CHARS_CODE}
            st = time.time()
            try:
                r = api_call(url, key, model, build_prompt_bfcl(B, t, first[t["id"]]), max_tokens)
                ch = (r.get("choices") or [{}])[0]
                rec["answer"] = (ch.get("message") or {}).get("content") or ""
                rec["finish"] = "ok" if rec["answer"].strip() else "empty"
                rec["api_finish"] = ch.get("finish_reason")
                u = r.get("usage") or {}
                rec["ptok"], rec["ctok"] = u.get("prompt_tokens"), u.get("completion_tokens")
            except Exception as exc:                      # noqa: BLE001 - store, do not hide
                rec["answer"], rec["finish"] = "", "error"
                rec["engine_error"] = "%s: %s" % (type(exc).__name__, str(exc)[:160])
                n_bad += 1
            rec["seconds"] = round(time.time() - st, 2)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if (i + 1) % 10 == 0:
                rate = (i + 1) / max(time.time() - t0, 0.01)
                print("repair %d/%d %.1f s/task eta %.0f s"
                      % (i + 1, len(queue), (time.time() - t0) / (i + 1),
                         (len(queue) - i - 1) / rate), flush=True)

    stored = dict(done)
    for line in dst.read_text().splitlines():
        r = json.loads(line)
        if r.get("finish") == "ok":
            stored[r["id"]] = r

    # The same pinned verifier re-checks every retry. It is the scorer for this set, which is why
    # the re-ask names only the class: the census below publishes what the loop could have learned.
    chk_retry = {}
    for t in asked:
        if t["id"] in stored:
            chk_retry[t["id"]] = B.score_entry(t, stored[t["id"]]["answer"])[0]
    kb_ok, ro_ok, keep = {}, {}, {}
    for t in tasks:
        asked_here = t["id"] in chk_retry
        use_retry = asked_here and chk_retry[t["id"]]
        kb_ok[t["id"]] = True if use_retry else ok_first[t["id"]]
        ro_ok[t["id"]] = chk_retry[t["id"]] if asked_here else ok_first[t["id"]]
        keep[t["id"]] = "retry" if use_retry else "first"
    n = len(kb_ok)
    kb = sum(1 for v in kb_ok.values() if v)
    ro = sum(1 for v in ro_ok.values() if v)
    fixed = [i for i in kb_ok if kb_ok[i] and not ok_first[i]]
    worse = [i for i in kb_ok if ok_first[i] and not kb_ok[i]]
    fixed_by_class = {}
    for t in asked:
        if t["id"] in fixed or kb_ok[t["id"]] and not ok_first[t["id"]]:
            fixed_by_class[t["_class"]] = fixed_by_class.get(t["_class"], 0) + 1
    p_kb, p_ro = 0, 0
    try:
        from pub_bench_compare import sign_test          # one sign test for the whole line
        p_kb = sign_test(len(fixed), len(worse))
        p_ro = sign_test(len([i for i in ro_ok if ro_ok[i] and not ok_first[i]]),
                         len([i for i in ro_ok if ok_first[i] and not ro_ok[i]]))
    except Exception:                                    # noqa: BLE001
        pass
    first_model = first_rows[0].get("model")
    merged, verdict_rows = [], []
    for t in tasks:
        merged.append({"id": t["id"], "bench": t["bench"], "arm": "%s-merged" % CONTRACT,
                       "model": first_model, "temp": TEMP, "max_tokens": max_tokens,
                       "finish": "ok", "kept": keep[t["id"]],
                       "answer": stored[t["id"]]["answer"]
                       if (t["id"] in stored and keep[t["id"]] == "retry") else first[t["id"]]})
        verdict_rows.append({"id": t["id"],
                             "first_ok": ok_first[t["id"]],
                             "verifier_class": t.get("_class"),
                             "retry_verifier_ok": chk_retry.get(t["id"]),
                             "kept": keep[t["id"]],
                             "strict": kb_ok[t["id"]]})
    for name, rows in (("%s-merged-answers.jsonl" % CONTRACT, merged),
                       ("%s-verdicts.jsonl" % CONTRACT, verdict_rows)):
        (out / name).write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True)
                                          for r in rows) + "\n")
        (out / (name + ".sha16")).write_text(
            hashlib.sha1((out / name).read_bytes()).hexdigest()[:16] + "\n")
    ptok = sum(r.get("ptok") or 0 for r in stored.values())
    ctok = sum(r.get("ctok") or 0 for r in stored.values())
    cen = {"contract": CONTRACT, "tasks": n, "task_sha16": sha16(a.tasks),
           "first_arm_pass": n_first,
           "asked_stored": len(chk_retry), "asked_unrun": len(asked) - len(chk_retry),
           "asked_by_class": dict(sorted(by_class.items())),
           "retry_passes_verifier": sum(1 for v in chk_retry.values() if v),
           "retry_fails_verifier": sum(1 for v in chk_retry.values() if not v),
           "converted": len(fixed), "converted_ids": sorted(fixed),
           "converted_by_class": dict(sorted(fixed_by_class.items())),
           "worse": len(worse), "worse_ids": sorted(worse),
           "keep_best_equals_retry_only_by_construction": bool(ro == kb),
           "sign_test_keepbest_vs_first_p": p_kb, "sign_test_retryonly_vs_first_p": p_ro,
           "keep_best": kb, "retry_only": ro,
           "redraw_control": control,
           "validator": "bfcl-ast-v1 (verdict only: class named, no gold name, no gold count)",
           "checker": B.BFCL_CHECKER,
           "call": {"temp": TEMP, "max_tokens": max_tokens,
                    "first_arm_max_tokens": first_budget},
           "retry_calls": len(stored),
           "retry_ceiling_hits": sum(1 for r in stored.values()
                                     if r.get("api_finish") == "length"),
           "retry_prompt_tokens": ptok, "retry_completion_tokens": ctok,
           "wall_s": round(time.time() - t0, 1), "transport_errors": n_bad,
           "first_answers_sha16": sha16(a.first_answers)}
    (out / ("pub-repair-%s-census.json" % CONTRACT)).write_text(json.dumps(cen, indent=2) + "\n")
    print("census: asked %d/%d | retry passes verifier %d | converted %d (%s) | worse %d | "
          "unrun %d | redraw control converts %s"
          % (len(chk_retry), len(asked), cen["retry_passes_verifier"], len(fixed),
             ", ".join("%s %d" % kv for kv in sorted(fixed_by_class.items())), len(worse),
             len(asked) - len(chk_retry), control["redraw_keep_conversions"]))
    print("%s keep-best %d/%d = %.1f %% | retry-only %d/%d = %.1f %% | first arm was "
          "%d/%d = %.1f %%" % (CONTRACT, kb, n, 100.0 * kb / n, ro, n, 100.0 * ro / n,
                               n_first, n, 100.0 * n_first / n))
    if len(chk_retry) != len(asked):
        print("PARTIAL: %d re-asks still missing - no digest row written"
              % (len(asked) - len(chk_retry)))
        return 1

    if a.merge or a.no_digest:
        print("--merge / --no-digest: artifacts written, no digest row")
        return 0
    dig = HERE.parent / "benchmarks" / "public" / "PUB-DIGEST.md"
    import pub_bench_score as pbs                          # noqa: E402
    bench = tasks[0]["bench"]
    tasks_cell = hashlib.sha256(open(a.tasks, "rb").read()).hexdigest()[:16]
    model_label = "%s+%s(keep-best)" % (model or first_model, CONTRACT)
    key_cell = "\n| %s | %s | %d | %s |" % (bench, model_label, n, tasks_cell)
    body = dig.read_text() if dig.exists() else ""
    if key_cell in body:
        print("digest row already present - not duplicated")
    else:
        line = ("| %s | %s | %d | %s | validator = the pinned %s verdict, CLASS ONLY "
                "(no gold call name, no expected count), scorer = the same %s (this set has no "
                "held-out verifier - pre-registered negative control): %d re-asks (%s), "
                "%d pass the verifier after repair, converted %d, worse %d (sign test p=%.2g); "
                "redraw control from published bytes converts %s; same %s, temp %.1f, "
                "retry max_tokens %d (first arm %d); keep-best = retry-only here by construction "
                "| %d/%d = **%.1f%%** |"
                % (bench, model_label, n, tasks_cell, B.BFCL_CHECKER, B.BFCL_CHECKER,
                   len(chk_retry),
                   ", ".join("%s %d" % kv for kv in sorted(by_class.items())),
                   cen["retry_passes_verifier"], len(fixed), len(worse), p_kb,
                   control["redraw_keep_conversions"], B.BFCL_CHECKER, TEMP, max_tokens,
                   first_budget, kb, n, 100.0 * kb / n))
        pbs.write_digest(line, str(dig))
        print("digest row appended")
    return 0


# pub-repair-humaneval-v1 — verdict-only repair over the execution checker's failures.
# PRE-REGISTERED BEFORE THIS CODE EXISTED (benchmarks/public/HUMANEVAL-RESULT.md, "Repair arm
# pub-repair-humaneval-v1 — pre-registration", 2026-11-09 23:58 CET, and the PUB-PLAN item-5 block):
# the bare arm fails 5/164 cells, all of them wrong-value assertion failures, so the ceiling is
# 3.05 pp; the redraw control (published contour-0.0.2.56 bare-matched arm, no feedback) converts 2
# of those 5; with 5 discordant cells the best possible exact sign test is 5/0 at p = 0.0625, so the
# arm is published as a wiring and cost measurement whatever it returns. The re-ask wording is fixed
# there in advance: COARSE CLASS ONLY — "wrong value" / "crashed" / "did not compile" — never a test
# body, a gold value or an example pair, because this set ships no public tests and the verifier here
# IS the scorer. The exception class name is deliberately NOT echoed either: it goes past the
# pre-registered class boundary and is information the bare prompt never carried.
# The flow mirrors run_bfcl rather than refactoring it: the BFCL branch already backs published arm
# bytes and a midnight refactor of published tooling buys nothing (a follow-up can unify the two).

HE_CLASS_TEXT = {
    "wrong_value": "the program compiled and ran, but a hidden test reported a wrong return value",
    "crash": "the program raised an exception while the hidden tests were running",
    "syntax": "the submitted code did not compile — the answer must contain a complete definition "
              "of the function named in the task",
    "no_code": "no definition of the function named in the task could be found in the answer, so "
               "nothing was executed",
    "timeout": "the program did not finish within the checker's time limit",
}

_TIMEOUT_MARK, _SYNTAX_MARKS = "timeout", ("SyntaxError", "IndentationError")


def he_class(err):
    """Checker stderr tail -> the pre-registered COARSE class. Never the message body: HumanEval
    assertion tails can carry expected values, which are grading bytes."""
    s = str(err or "").strip()
    if s == _TIMEOUT_MARK:
        stem = "timeout"
    else:
        stem = s.split(":")[0].strip()
        if stem in _SYNTAX_MARKS:
            stem = "syntax"
        elif stem == "AssertionError":
            stem = "wrong_value"
        elif stem and stem.endswith("Error"):
            stem = "crash"
        else:
            stem = "no_code"
    return stem, HE_CLASS_TEXT[stem]


def build_prompt_humaneval(task, prev):
    """Retry PREFIX = `task["prompt"]` verbatim (exactly the bytes `pub_bench_run.py` sends for a
    code set), so the retry differs from the bare call only by the appended verdict block."""
    stem, text = he_class(task["_why"])
    truncated = len(prev or "") > MAX_PREV_CHARS_CODE
    return ("%s\n\n### Verifier feedback on your previous answer\n"
            "The pinned execution checker ran its test battery against your previous answer for this "
            "exact task. The task text above is unchanged and nothing has been added to it.\n"
            "What the checker reports, as a class: %s\n"
            "Re-answer the task above with the complete function and fix exactly what the verdict "
            "names. No test body, no example value and no expected output is given, and none is "
            "implied by the wording above.\n\n"
            "### Your previous answer%s\n%s\n"
            % (task["prompt"], text,
               " (truncated)" if truncated else "", (prev or "")[:MAX_PREV_CHARS_CODE]))


def run_humaneval(a, tasks, first, first_rows):
    """pub-repair-humaneval-v1: verdict-only re-ask over the pytest-v2 execution failures."""
    global CONTRACT
    CONTRACT = "pub-repair-humaneval-v1"
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import pub_bench_exec as E                            # noqa: E402
    if E.selftest() != 0:
        sys.exit("REFUSING TO RUN: %s checker gate failed" % E.EXEC_CHECKER)

    budgets = {r.get("max_tokens") for r in first_rows if r.get("max_tokens")}
    if len(budgets) != 1:
        sys.exit("REFUSING TO RUN: first arm mixes call budgets %s" % sorted(map(str, budgets)))
    max_tokens = int(budgets.pop())
    first_budget = max_tokens
    env_budget = os.environ.get("PARB_MAX_TOKENS")
    if env_budget and int(env_budget) != max_tokens:
        CONTRACT = "pub-repair-humaneval-v2"
        print("note: PARB_MAX_TOKENS overrides the first arm budget %d -> %d; this arm runs "
              "under contract %s" % (max_tokens, int(env_budget), CONTRACT), flush=True)
        max_tokens = int(env_budget)
    temps = {r.get("temp") for r in first_rows if r.get("temp") is not None}
    temps.discard(None)
    if temps and temps != {TEMP}:
        sys.exit("REFUSING TO RUN: first arm temperature %s != this arm's %s" % (temps, TEMP))

    def score(t, answer):
        meta = t["meta"] if isinstance(t["meta"], dict) else json.loads(t["meta"])
        entry = meta.get("entry_point") or E.entry_point(t["prompt"])
        if not entry:
            return False, "no entry point in prompt"
        return E.run_case(t["prompt"], E.extract_code(answer, t["prompt"], entry),
                          meta["test"], entry)

    # Wiring guard against the PUBLISHED verdict rows before any model call.
    ok_first, asked = {}, []
    for t in tasks:
        if t["id"] not in first:
            sys.exit("REFUSING TO RUN: no first-arm answer for %s" % t["id"])
        ok, why = score(t, first[t["id"]])
        ok_first[t["id"]] = bool(ok)
        t["_why"] = why
        t["_class"] = he_class(why)[0]
        if not ok:
            asked.append(t)
    n_first = sum(1 for v in ok_first.values() if v)
    by_class = {}
    for t in asked:
        by_class[t["_class"]] = by_class.get(t["_class"], 0) + 1
    print("first arm %d/%d = %.1f %% | checker rejects %d tasks (%s) -> %d re-asks"
          % (n_first, len(ok_first), 100.0 * n_first / len(ok_first), len(asked),
             ", ".join("%s %d" % kv for kv in sorted(by_class.items())), len(asked)), flush=True)

    if a.verdicts_ref:
        ref = {}
        for line in pathlib.Path(a.verdicts_ref).read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                ref.setdefault(r["id"], bool(r["ok"]))
        diff = [i for i in ok_first if ref.get(i) != ok_first[i]]
        if diff or set(ref) != set(ok_first):
            sys.exit("REFUSING TO RUN: first-arm verdicts differ from the published reference on "
                     "%d cells %s" % (len(diff), diff[:5]))
        print("first-arm verdicts match the published reference cell for cell (%d ids)"
              % len(ref), flush=True)

    control = {"file": None, "control_arms": 0, "redraw_keep_conversions": None}
    if a.control_verdicts:
        cv = {}
        for line in pathlib.Path(a.control_verdicts).read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                cv.setdefault(r["id"], bool(r["ok"]))
        if set(cv) != set(ok_first):
            sys.exit("REFUSING TO RUN: control verdicts cover %d ids, first arm covers %d"
                     % (len(cv), len(ok_first)))
        conv = [i for i in ok_first if not ok_first[i] and cv[i]]
        control = {"file": str(pathlib.Path(a.control_verdicts).name),
                   "file_sha16": sha16(a.control_verdicts),
                   "control_arm_pass": sum(1 for v in cv.values() if v),
                   "redraw_keep_conversions": len(conv),
                   "converted_ids": sorted(conv),
                   "redraw_keep_pp": round(100.0 * len(conv) / len(ok_first), 2)}
        print("redraw control (%s): a plain second draw converts %d first-arm failures (%.2f pp)"
              % (control["file"], control["redraw_keep_conversions"],
                 control["redraw_keep_pp"]), flush=True)

    if a.dry_run:
        return 0

    if a.merge:
        url = key_file = key = model = None
    else:
        url = os.environ.get("PARB_API")
        key_file = os.environ.get("PARB_KEY_FILE")
        model = os.environ.get("PARB_MODEL")
        if not (url and key_file and model):
            raise SystemExit("PARB_API, PARB_KEY_FILE and PARB_MODEL are required")
        key = json.load(open(key_file, encoding="utf-8"))["api_key"]

    out = pathlib.Path(a.out or str(pathlib.Path(a.first_answers).parent))
    out.mkdir(parents=True, exist_ok=True)   # --out may name a directory that does not exist yet
    dst = out / ("pub-repair-%s.jsonl" % CONTRACT)
    done = {}
    if dst.exists():
        for line in dst.read_text().splitlines():
            r = json.loads(line)
            if r.get("finish") == "ok":
                done[r["id"]] = r
    queue = [t for t in asked if t["id"] not in done]
    if a.limit:
        queue = queue[:a.limit]
    if a.merge:
        queue = []
    print("asked=%d already stored=%d to run=%d" % (len(asked), len(done), len(queue)), flush=True)

    t0, n_bad = time.time(), 0
    with dst.open("a", encoding="utf-8") as fh:
        for i, t in enumerate(queue):
            rec = {"id": t["id"], "bench": t["bench"], "arm": CONTRACT, "model": model,
                   "temp": TEMP, "max_tokens": max_tokens,
                   "task_sha16": sha16(a.tasks),
                   "first_answer_sha16": hashlib.sha1(first[t["id"]].encode()).hexdigest()[:16],
                   "verifier_class": t["_class"], "validator": "%s (verdict only)" % E.EXEC_CHECKER,
                   "prev_truncated": len(first[t["id"]] or "") > MAX_PREV_CHARS_CODE}
            st = time.time()
            try:
                r = api_call(url, key, model, build_prompt_humaneval(t, first[t["id"]]), max_tokens)
                ch = (r.get("choices") or [{}])[0]
                rec["answer"] = (ch.get("message") or {}).get("content") or ""
                rec["finish"] = "ok" if rec["answer"].strip() else "empty"
                rec["api_finish"] = ch.get("finish_reason")
                u = r.get("usage") or {}
                rec["ptok"], rec["ctok"] = u.get("prompt_tokens"), u.get("completion_tokens")
            except Exception as exc:                      # noqa: BLE001 - store, do not hide
                rec["answer"], rec["finish"] = "", "error"
                rec["engine_error"] = "%s: %s" % (type(exc).__name__, str(exc)[:160])
                n_bad += 1
            rec["seconds"] = round(time.time() - st, 2)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if (i + 1) % 5 == 0:
                print("repair %d/%d %.1f s/task" % (i + 1, len(queue),
                                                    (time.time() - t0) / (i + 1)), flush=True)

    stored = dict(done)
    for line in dst.read_text().splitlines():
        r = json.loads(line)
        if r.get("finish") == "ok":
            stored[r["id"]] = r

    # The same pinned checker re-runs the battery on every retry. It is the scorer for this set,
    # which is exactly why the re-ask stays at the coarse class: the census publishes what the loop
    # could have learned and did not get.
    chk_retry = {}
    for t in asked:
        if t["id"] in stored:
            chk_retry[t["id"]] = bool(score(t, stored[t["id"]]["answer"])[0])
    kb_ok, ro_ok, keep = {}, {}, {}
    for t in tasks:
        asked_here = t["id"] in chk_retry
        use_retry = asked_here and chk_retry[t["id"]]
        kb_ok[t["id"]] = True if use_retry else ok_first[t["id"]]
        ro_ok[t["id"]] = chk_retry[t["id"]] if asked_here else ok_first[t["id"]]
        keep[t["id"]] = "retry" if use_retry else "first"
    n = len(kb_ok)
    kb = sum(1 for v in kb_ok.values() if v)
    ro = sum(1 for v in ro_ok.values() if v)
    fixed = [i for i in kb_ok if kb_ok[i] and not ok_first[i]]
    worse = [i for i in kb_ok if ok_first[i] and not kb_ok[i]]
    fixed_by_class = {}
    for t in asked:
        if t["id"] in fixed:
            fixed_by_class[t["_class"]] = fixed_by_class.get(t["_class"], 0) + 1
    p_kb = p_ro = 0
    try:
        from pub_bench_compare import sign_test
        p_kb = sign_test(len(fixed), len(worse))
        p_ro = sign_test(len([i for i in ro_ok if ro_ok[i] and not ok_first[i]]),
                         len([i for i in ro_ok if ok_first[i] and not ro_ok[i]]))
    except Exception:                                    # noqa: BLE001
        pass
    first_model = first_rows[0].get("model")
    merged, verdict_rows = [], []
    for t in tasks:
        merged.append({"id": t["id"], "bench": t["bench"], "arm": "%s-merged" % CONTRACT,
                       "model": first_model, "temp": TEMP, "max_tokens": max_tokens,
                       "finish": "ok", "kept": keep[t["id"]],
                       "answer": stored[t["id"]]["answer"]
                       if (t["id"] in stored and keep[t["id"]] == "retry") else first[t["id"]]})
        verdict_rows.append({"id": t["id"],
                             "first_ok": ok_first[t["id"]],
                             "verifier_class": t.get("_class"),
                             "retry_verifier_ok": chk_retry.get(t["id"]),
                             "kept": keep[t["id"]],
                             "strict": kb_ok[t["id"]]})
    for name, rows in (("%s-merged-answers.jsonl" % CONTRACT, merged),
                       ("%s-verdicts.jsonl" % CONTRACT, verdict_rows)):
        (out / name).write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True)
                                          for r in rows) + "\n")
        (out / (name + ".sha16")).write_text(
            hashlib.sha1((out / name).read_bytes()).hexdigest()[:16] + "\n")
    ptok = sum(r.get("ptok") or 0 for r in stored.values())
    ctok = sum(r.get("ctok") or 0 for r in stored.values())
    sec = sorted(r.get("seconds") or 0.0 for r in stored.values())
    cen = {"contract": CONTRACT, "tasks": n, "task_sha16": sha16(a.tasks),
           "first_arm_pass": n_first,
           "asked_stored": len(chk_retry), "asked_unrun": len(asked) - len(chk_retry),
           "asked_by_class": dict(sorted(by_class.items())),
           "retry_passes_checker": sum(1 for v in chk_retry.values() if v),
           "retry_fails_checker": sum(1 for v in chk_retry.values() if not v),
           "converted": len(fixed), "converted_ids": sorted(fixed),
           "converted_by_class": dict(sorted(fixed_by_class.items())),
           "worse": len(worse), "worse_ids": sorted(worse),
           "keep_best_equals_retry_only_by_construction": bool(ro == kb),
           "sign_test_keepbest_vs_first_p": p_kb, "sign_test_retryonly_vs_first_p": p_ro,
           "keep_best": kb, "retry_only": ro,
           "ceiling_pp": round(100.0 * len(asked) / n, 2),
           "pre_registered": {"headroom_cells": 5, "control_conversions": 2,
                              "best_possible_sign_test_p": 0.0625,
                              "status": "written 2026-11-09 23:58 CET, before this code existed"},
           "redraw_control": control,
           "validator": "%s (verdict only: coarse class, no test body, no gold value, no example "
                        "pair, no exception-class name)" % E.EXEC_CHECKER,
           "checker": E.EXEC_CHECKER,
           "call": {"temp": TEMP, "max_tokens": max_tokens,
                    "first_arm_max_tokens": first_budget},
           "retry_calls": len(stored),
           "retry_ceiling_hits": sum(1 for r in stored.values()
                                     if r.get("api_finish") == "length"),
           "retry_seconds_median": (sec[len(sec) // 2] if sec else None),
           "retry_prompt_tokens": ptok, "retry_completion_tokens": ctok,
           "wall_s": round(time.time() - t0, 1), "transport_errors": n_bad,
           "first_answers_sha16": sha16(a.first_answers)}
    (out / ("pub-repair-%s-census.json" % CONTRACT)).write_text(json.dumps(cen, indent=2) + "\n")
    print("census: asked %d/%d | retry passes checker %d | converted %d (%s) | worse %d | "
          "unrun %d | redraw control converts %s"
          % (len(chk_retry), len(asked), cen["retry_passes_checker"], len(fixed),
             ", ".join("%s %d" % kv for kv in sorted(fixed_by_class.items())), len(worse),
             len(asked) - len(chk_retry), control["redraw_keep_conversions"]))
    print("%s keep-best %d/%d = %.1f %% | retry-only %d/%d = %.1f %% | first arm was "
          "%d/%d = %.1f %%" % (CONTRACT, kb, n, 100.0 * kb / n, ro, n, 100.0 * ro / n,
                               n_first, n, 100.0 * n_first / n))
    if len(chk_retry) != len(asked):
        print("PARTIAL: %d re-asks still missing - no digest row written"
              % (len(asked) - len(chk_retry)))
        return 1

    if a.merge or a.no_digest:
        print("--merge / --no-digest: artifacts written, no digest row")
        return 0
    dig = HERE.parent / "benchmarks" / "public" / "PUB-DIGEST.md"
    import pub_bench_score as pbs                          # noqa: E402
    bench = tasks[0]["bench"]
    tasks_cell = hashlib.sha256(open(a.tasks, "rb").read()).hexdigest()[:16]
    model_label = "%s+%s(keep-best)" % (model or first_model, CONTRACT)
    key_cell = "\n| %s | %s | %d | %s |" % (bench, model_label, n, tasks_cell)
    body = dig.read_text() if dig.exists() else ""
    if key_cell in body:
        print("digest row already present - not duplicated")
    else:
        line = ("| %s | %s | %d | %s | validator = the pinned %s execution checker, verdict CLASS "
                "only (no test body, no gold value, no example pair, no exception-class name), "
                "scorer = the same %s (this set ships no public tests - pre-registered wiring/cost "
                "measurement): %d re-asks (%s), %d pass the checker after repair, converted %d, "
                "worse %d (sign test p=%.3g; the best this arm could reach on %d discordant cells "
                "is p=0.0625); redraw control from published bytes converts %s; same %s, temp %.1f, "
                "retry max_tokens %d (first arm %d); keep-best = retry-only here by construction "
                "| %d/%d = **%.1f%%** |"
                % (bench, model_label, n, tasks_cell, E.EXEC_CHECKER, E.EXEC_CHECKER,
                   len(chk_retry),
                   ", ".join("%s %d" % kv for kv in sorted(by_class.items())),
                   cen["retry_passes_checker"], len(fixed), len(worse), p_kb, len(asked),
                   control["redraw_keep_conversions"], E.EXEC_CHECKER, TEMP, max_tokens,
                   first_budget, kb, n, 100.0 * kb / n))
        pbs.write_digest(line, str(dig))
        print("digest row appended")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks")
    ap.add_argument("first_answers")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--merge", action="store_true",
                    help="no model call: re-score the stored retries and write the merged arm bytes")
    ap.add_argument("--validator", choices=("ifeval", "lcb-public", "bfcl", "humaneval"),
                    default="ifeval",
                    help="which validator drives the loop (lcb-public = the question's public "
                         "sample tests; the hidden battery only scores; bfcl = the pinned AST "
                         "checker itself, named as a failure CLASS only, pre-registered "
                         "negative control; humaneval = the pinned pytest-v2 execution checker, "
                         "named as a COARSE CLASS only, pre-registered wiring/cost measurement)")
    ap.add_argument("--hidden", default=None,
                    help="lcb: hidden-test sidecar used ONLY for scoring, never by the loop")
    ap.add_argument("--verdicts-ref", default=None,
                    help="lcb/bfcl: published verdict rows the first-arm pass must match "
                         "cell for cell before any model call")
    ap.add_argument("--control-verdicts", default=None,
                    help="bfcl: a published same-brain same-shape arm's verdict rows; the cells "
                         "where that plain second draw turned a first-arm failure into a pass are "
                         "the redraw control published beside the row (never read by the loop)")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate + count the headroom, no model call")
    ap.add_argument("--no-digest", action="store_true",
                    help="write the artifacts without appending a digest row")
    a = ap.parse_args()

    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))

    tasks = [json.loads(l) for l in pathlib.Path(a.tasks).read_text().splitlines()]
    first = {}
    for line in pathlib.Path(a.first_answers).read_text().splitlines():
        r = json.loads(line)
        first.setdefault(r["id"], r.get("answer", ""))
    missing = [t["id"] for t in tasks if t["id"] not in first]
    if missing:
        sys.exit("REFUSING TO RUN: first arm partial - %d/%d answers present"
                 % (len(tasks) - len(missing), len(tasks)))
    first_rows = [json.loads(l) for l in pathlib.Path(a.first_answers).read_text().splitlines()]

    if a.validator == "lcb-public":
        return run_lcb(a, tasks, first, first_rows)
    if a.validator == "bfcl":
        return run_bfcl(a, tasks, first, first_rows)
    if a.validator == "humaneval":
        return run_humaneval(a, tasks, first, first_rows)

    import pub_bench_ifeval as pifev                       # noqa: E402
    ev = pifev.load_vendor()
    ok, why = pifev.selftest(ev)
    if not ok:
        sys.exit("REFUSING TO RUN: checker gate failed - %s" % why)
    print("checker gate: %s" % why, flush=True)

    # The pinned call budget of the first arm is inherited, so a repair row can never wear a
    # different request shape from the row it repairs.
    budgets = {r.get("max_tokens") for r in first_rows if r.get("max_tokens")}
    if len(budgets) != 1:
        sys.exit("REFUSING TO RUN: first arm mixes call budgets %s" % sorted(map(str, budgets)))
    max_tokens = int(budgets.pop())
    first_budget = max_tokens
    env_budget = os.environ.get("PARB_MAX_TOKENS")
    if env_budget and int(env_budget) != max_tokens:
        global CONTRACT           # a different retry budget is a different contract,
        CONTRACT = "pub-repair-v2"  # never an edit of the v1 row or the v1 artifacts
        print("note: PARB_MAX_TOKENS overrides the first arm budget %d -> %d; "
              "this arm runs under contract %s"
              % (max_tokens, int(env_budget), CONTRACT), flush=True)
        max_tokens = int(env_budget)
    temps = {r.get("temp") for r in first_rows if r.get("temp") is not None}
    if temps and temps != {TEMP}:
        sys.exit("REFUSING TO RUN: first arm temperature %s != this arm's %s" % (temps, TEMP))

    # Score the first arm with the pinned validator, and collect the violated checks per task.
    scored, asked = [], []
    for t in tasks:
        inp = ev.InputExample(key=int(t["id"].rsplit("-", 1)[1]),
                              instruction_id_list=t["instruction_id_list"],
                              prompt=t["prompt"], kwargs=t["kwargs"])
        v = ev.test_instruction_following_strict(inp, {t["prompt"]: first[t["id"]]})
        t["_first_strict"] = bool(v.follow_all_instructions)
        t["_failed_checks"] = [check_text(t, i) for i, okc in enumerate(v.follow_instruction_list)
                               if not okc]
        scored.append(t)
        if not t["_first_strict"]:
            asked.append(t)
    n_first = sum(1 for t in scored if t["_first_strict"])
    print("first arm strict %d/%d = %.1f %% | validator rejects %d tasks -> %d re-asks"
          % (n_first, len(scored), 100.0 * n_first / len(scored), len(asked), len(asked)), flush=True)
    if a.dry_run:
        return 0

    if a.merge:
        url = key_file = key = model = None
    else:
        url = os.environ.get("PARB_API")
        key_file = os.environ.get("PARB_KEY_FILE")
        model = os.environ.get("PARB_MODEL")
        if not (url and key_file and model):
            raise SystemExit("PARB_API, PARB_KEY_FILE and PARB_MODEL are required")
        key = json.load(open(key_file, encoding="utf-8"))["api_key"]

    out = pathlib.Path(a.out or str(pathlib.Path(a.first_answers).parent))
    out.mkdir(parents=True, exist_ok=True)   # --out may name a directory that does not exist yet
    dst = out / ("pub-repair-%s.jsonl" % CONTRACT)
    done = {}
    if dst.exists():
        for line in dst.read_text().splitlines():
            r = json.loads(line)
            if r.get("finish") == "ok":
                done[r["id"]] = r
    queue = [t for t in asked if t["id"] not in done]
    if a.limit:
        queue = queue[:a.limit]
    if a.merge:
        queue = []
    print("asked=%d already stored=%d to run=%d" % (len(asked), len(done), len(queue)), flush=True)

    t0, n_bad = time.time(), 0
    with dst.open("a", encoding="utf-8") as fh:
        for i, t in enumerate(queue):
            rec = {"id": t["id"], "bench": t["bench"], "arm": CONTRACT, "model": model,
                   "temp": TEMP, "max_tokens": max_tokens,
                   "task_sha16": sha16(a.tasks), "first_answer_sha16":
                   hashlib.sha1(first[t["id"]].encode()).hexdigest()[:16],
                   "violated": [c for c, _ in t["_failed_checks"]],
                   "prev_truncated": False}
            st = time.time()
            try:
                r = api_call(url, key, model, build_prompt(t, first[t["id"]]), max_tokens)
                ch = (r.get("choices") or [{}])[0]
                rec["answer"] = (ch.get("message") or {}).get("content") or ""
                rec["finish"] = "ok" if rec["answer"].strip() else "empty"
                rec["api_finish"] = ch.get("finish_reason")
                u = r.get("usage") or {}
                rec["ptok"], rec["ctok"] = u.get("prompt_tokens"), u.get("completion_tokens")
            except Exception as exc:                      # noqa: BLE001 - store, do not hide
                rec["answer"], rec["finish"] = "", "error"
                rec["engine_error"] = "%s: %s" % (type(exc).__name__, str(exc)[:160])
                n_bad += 1
            rec["seconds"] = round(time.time() - st, 2)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if (i + 1) % 10 == 0:
                rate = (i + 1) / max(time.time() - t0, 0.01)
                print("repair %d/%d %.1f s/task eta %.0f s"
                      % (i + 1, len(queue), (time.time() - t0) / (i + 1),
                         (len(queue) - i - 1) / rate), flush=True)

    stored = dict(done)
    for line in dst.read_text().splitlines():
        r = json.loads(line)
        if r.get("finish") == "ok":
            stored[r["id"]] = r

    # Score the retries with the same pinned validator.
    fixed = still = 0
    for t in scored:
        t["_retry_strict"] = None
        if t["_first_strict"] or t["id"] not in stored:
            continue
        inp = ev.InputExample(key=int(t["id"].rsplit("-", 1)[1]),
                              instruction_id_list=t["instruction_id_list"],
                              prompt=t["prompt"], kwargs=t["kwargs"])
        rv = ev.test_instruction_following_strict(inp, {t["prompt"]: stored[t["id"]]["answer"]})
        t["_retry_strict"] = bool(rv.follow_all_instructions)
        if t["_retry_strict"]:
            fixed += 1
        else:
            still += 1
    n = len(scored)
    kb = n_first + fixed                    # keep-best: a retry only replaces the first answer if it passes
    asked_ran = fixed + still
    # retry-only: every asked task takes the retry answer, pass or fail (what a naive harness scores)
    retry_only = sum(1 for t in scored if (t["_retry_strict"] if t["_retry_strict"] is not None
                                           else t["_first_strict"]))
    # Merged arm bytes: the answer the repaired arm actually gives, plus the per-task keep/retry
    # decision, so the percent can be re-scored later with zero model calls.
    first_model = first_rows[0].get("model")
    merged, verdict_rows = [], []
    for t in scored:
        kept = "retry" if t["_retry_strict"] is True else "first"
        merged.append({"id": t["id"], "bench": t["bench"], "arm": "%s-merged" % CONTRACT,
                       "model": first_model, "temp": TEMP, "max_tokens": max_tokens,
                       "finish": "ok", "kept": kept,
                       "answer": stored[t["id"]]["answer"] if kept == "retry" else first[t["id"]]})
        verdict_rows.append({"id": t["id"], "first_strict": t["_first_strict"],
                             "retry_strict": t["_retry_strict"], "kept": kept,
                             "strict": bool(t["_first_strict"] or t["_retry_strict"] is True)})
    for name, rows in (("%s-merged-answers.jsonl" % CONTRACT, merged),
                       ("%s-verdicts.jsonl" % CONTRACT, verdict_rows)):
        (out / name).write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True)
                                          for r in rows) + "\n")
        (out / (name + ".sha16")).write_text(
            hashlib.sha1((out / name).read_bytes()).hexdigest()[:16] + "\n")
    print("merged arm bytes -> %s | verdicts -> %s"
          % (out / ("%s-merged-answers.jsonl" % CONTRACT), out / ("%s-verdicts.jsonl" % CONTRACT)))
    cen = {"contract": CONTRACT, "tasks": n, "task_sha16": sha16(a.tasks),
           "first_arm_strict": n_first, "asked_stored": asked_ran, "asked_unrun": len(asked) - asked_ran,
           "retry_fixed": fixed, "retry_still_failing": still,
           "keep_best_strict": kb, "retry_only_strict": retry_only,
           "checker": pifev.CHECKER, "call": {"temp": TEMP, "max_tokens": max_tokens,
                                             "first_arm_max_tokens": first_budget},
           "wall_s": round(time.time() - t0, 1), "transport_errors": n_bad,
           "first_answers_sha16": sha16(a.first_answers)}
    (out / ("pub-repair-%s-census.json" % CONTRACT)).write_text(json.dumps(cen, indent=2) + "\n")
    print("census: asked %d/%d | retry fixed %d | still failing %d | unrun %d"
          % (asked_ran, len(asked), fixed, still, len(asked) - asked_ran))
    print("%s keep-best %d/%d = %.1f %% | retry-only %d/%d = %.1f %% | first arm was %d/%d = %.1f %%"
          % (CONTRACT, kb, n, 100.0 * kb / n, retry_only, n, 100.0 * retry_only / n,
             n_first, n, 100.0 * n_first / n))
    if asked_ran != len(asked):
        print("PARTIAL: %d re-asks still missing - no digest row written" % (len(asked) - asked_ran))
        return 1

    if a.merge or a.no_digest:
        print("--merge / --no-digest: artifacts written, no digest row")
        return 0
    dig = HERE.parent / "benchmarks" / "public" / "PUB-DIGEST.md"
    import pub_bench_score as pbs                          # noqa: E402
    bench = tasks[0]["bench"]
    model_label = "%s+%s(keep-best)" % (model or first_model, CONTRACT)
    key = "\n| %s | %s | %d | %s |" % (bench, model_label, n, sha16(a.tasks))
    body = dig.read_text() if dig.exists() else ""
    if key in body:
        print("digest row already present - not duplicated")
    else:
        line = ("| %s | %s | %d | %s | validator-driven one-shot repair over the stored first-arm "
                "bytes: %d re-asks, %d fixed, %d still failing; same pinned checker %s, temp %.1f, "
                "retry max_tokens %d (first arm %d); retry-only variant %d/%d = %.1f%% | %d/%d = **%.1f%%** |"
                % (bench, model_label, n, sha16(a.tasks), asked_ran, fixed, still, pifev.CHECKER,
                   TEMP, max_tokens, first_budget, retry_only, n, 100.0 * retry_only / n, kb, n,
                   100.0 * kb / n))
        pbs.write_digest(line, str(dig))
        print("digest row appended")
    return 0


if __name__ == "__main__":
    sys.exit(main())
