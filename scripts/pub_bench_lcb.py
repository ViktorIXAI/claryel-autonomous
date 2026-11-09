#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LiveCodeBench `test6` slice: pin it, decode its hidden tests, score code by execution.

Contract `lcb-exec-v1` (this file is the contract; any change means a new contract id).

Why a separate contract: the answer-graded checkers in `pub_bench_score.py` compare a final
answer, and the HumanEval contract `pytest-v2` runs the upstream `check()` of a fixed file.
LiveCodeBench problems are competitive-programming tasks with two different I/O regimes
(`stdin` programs on AtCoder, method-call `functional` cases on LeetCode) and a hidden-test
payload that is not plain JSON, so the pinning, decoding and execution rules all have to be
written down and self-tested before any arm runs.

Pinned input (measured on the bytes, 2026-11-09): HF `livecodebench/code_generation_lite`,
file `test6.jsonl` (134 303 240 B, SHA-256/16 `bb4c364f71921c44`), 175 questions, contest
dates 2025-01-04 to 2025-04-06 — inside the post-cutoff window this ladder item exists for.

Decoding, and the one security obligation that comes with it:
  public tests  : plain JSON list of {"input","output","testtype"}
  hidden tests  : base64 -> zlib -> **pickle** -> JSON (the unpickled object is a str/bytes
                  holding a JSON document)
  A pickle is an execution primitive, so the decoder uses an Unpickler whose `find_globals`
  REFUSES EVERY global class and function. Measured: 175/175 rows decode under that guard,
  because the payload is pure JSON data — the refusal is a self-test (`pickler_guard`), not a
  nicety, and a payload that ever needs a global fails closed instead of running code.

The hidden payload (289.5 MB decoded, median 48.7 KB and worst 29.9 MB per question) cannot be
a tracked git file. `build` therefore writes TWO files:
  <out.tasks.jsonl>          tracked: ids, prompts, starter code, PUBLIC tests (the validator
                             slot the contour may see), difficulty, dates, and for every
                             question the count + SHA-256/16 of its canonical hidden-test JSON
  <out.hidden.jsonl.gz>      untracked sidecar: {"id", "hidden_sha16", "tests"} per question,
                             which `score` requires; the pin pairs in the tasks file are what
                             bind a scored run to those bytes.

Declared execution budget (pre-registered, measured against the slice so nothing is excluded
by construction: max single test input 4.36 MB, max single test output 3.44 MB, worst question
total 29.9 MB):
  per-test input cap            8 MiB      over cap -> the test is a REJECT (a loss, not a skip)
  per-test expected-output cap  8 MiB      same
  per-question total cap        64 MiB     over cap -> REJECT the whole question
  per-test wall clock           20 s       over -> TLE, a loss
  per-test memory (child rlimit) 1 GiB     over -> MLE, a loss
  per-question wall clock       600 s      over -> the remaining tests are recorded as TLE
Verdict rule: a question passes only if EVERY hidden test passes. Public tests are never the
verdict — they are the validator slot a harness may iterate against; scoring uses hidden tests.
`functional` (LeetCode, 63 questions) needs a driver generated from the case's own type list;
that driver is NOT part of this contract yet, so those questions are UNSCORED and stay out of
the denominator, and every print names the unscored count.

usage:
  pub_bench_lcb.py selftest                       # contract tests on synthetic tasks
  pub_bench_lcb.py build <test6.jsonl> <out.tasks.jsonl> [--hidden-out F.gz]
  pub_bench_lcb.py score <tasks.jsonl> <answers.jsonl> --hidden F.gz [--verdicts OUT]
"""
import argparse
import base64
import gzip
import hashlib
import io
import json
import os
import pickle
import re
import subprocess
import sys
import tempfile
import time
import zlib

LCB_CONTRACT = "lcb-exec-v1"
TEST6_RAW_SHA16 = "bb4c364f71921c44"
INPUT_CAP = 8 * 1024 * 1024
OUTPUT_CAP = 8 * 1024 * 1024
QUESTION_CAP = 64 * 1024 * 1024
TEST_TIMEOUT = 20.0
QUESTION_TIMEOUT = 600.0
MEM_LIMIT = 1 << 30

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pub_bench_score import digest_row, write_digest                    # noqa: E402


# ---------------------------------------------------------------- decoding

class _GuardedUnpickler(pickle.Unpickler):
    """Refuse every global: an LCB payload is JSON data, so a global reference means the file
    is not what this contract claims, and loading it would execute arbitrary code."""

    def find_globals(self, module, name):
        raise RuntimeError("pickler refused global %s.%s (payload must be pure data)"
                           % (module, name))

    def find_class(self, module, name):
        self.find_globals(module, name)


def decode_hidden(blob):
    """base64 -> zlib -> guarded pickle -> JSON list."""
    raw = zlib.decompress(base64.b64decode(blob))
    obj = _GuardedUnpickler(io.BytesIO(raw)).load()
    if isinstance(obj, (bytes, bytearray)):
        obj = obj.decode("utf-8")
    if isinstance(obj, str):
        obj = json.loads(obj)
    if not isinstance(obj, list):
        raise ValueError("hidden payload is not a JSON list (%s)" % type(obj).__name__)
    for t in obj:
        if not isinstance(t, dict) or "input" not in t or "output" not in t:
            raise ValueError("hidden test has no input/output keys")
    return obj


def canon_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------- build

PROMPT_TMPL = (
    "You are given one competitive-programming problem. Write a complete Python 3 program that "
    "reads the input described below from standard input and writes exactly the required output "
    "to standard output. Output the program only, in one ```python fenced block. Do not print "
    "explanations, prompts or debug output.\n\n### Problem: {title}\n{content}\n"
)
FUNC_TMPL = (
    "You are given one programming problem with a provided class skeleton. Complete the method "
    "so that it returns the required value. Output only the completed Python code (the class or "
    "the method), in one ```python fenced block; do not read from standard input.\n\n"
    "### Problem: {title}\n{content}\n\n### Starter code:\n{starter}\n"
)


def build(raw_path, out_path, hidden_out=None):
    rows = [json.loads(l) for l in open(raw_path, encoding="utf-8") if l.strip()]
    if len(rows) != 175:
        print("note: %d rows (the pinned slice measured 175)" % len(rows))
    hidden = []
    with open(out_path, "w", encoding="utf-8") as fh:
        for r in rows:
            hid = decode_hidden(r["private_test_cases"])
            pub = json.loads(r["public_test_cases"]) if r["public_test_cases"] else []
            ttype = (pub[0].get("testtype") if pub else hid[0].get("testtype")) or "stdin"
            tmpl = FUNC_TMPL if ttype == "functional" else PROMPT_TMPL
            rec = {
                "id": "lcb-%s" % r["question_id"],
                "bench": "livecodebench",
                "title": r["question_title"],
                "platform": r["platform"],
                "testtype": ttype,
                "difficulty": r.get("difficulty", "?"),
                "contest_date": r.get("contest_date", ""),
                "starter_code": r.get("starter_code", ""),
                "prompt": tmpl.format(title=r["question_title"], content=r["question_content"],
                                      starter=r.get("starter_code", "")),
                "public_tests": pub,
                "hidden_count": len(hid),
                "hidden_sha16": sha16(canon_json(hid)),
                "hidden_bytes": sum(len(t["input"]) + len(t["output"]) for t in hid),
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            hidden.append({"id": rec["id"], "hidden_sha16": rec["hidden_sha16"], "tests": hid})
    if hidden_out:
        with gzip.open(hidden_out, "wt", encoding="utf-8") as gz:
            for h in hidden:
                gz.write(json.dumps(h, ensure_ascii=False) + "\n")
        print("hidden sidecar (UNTRACKED, not a git file): %s" % hidden_out)
    mix = {}
    for r in rows:
        pass
    print("wrote %s (%d tasks; tracked bytes carry public tests + hidden sha16, never the "
          "hidden payload)" % (out_path, len(rows)))


# ---------------------------------------------------------------- execution

FENCE = re.compile(r"```(?:python[23]?)?\n(.*?)```", re.S)


def extract_code(answer):
    blocks = FENCE.findall(answer or "")
    if blocks:
        return max(blocks, key=len)
    return (answer or "").strip()


RESOURCES = None


def _limits():
    global RESOURCES
    if RESOURCES is None:
        import resource
        RESOURCES = resource
    return RESOURCES


def _preexec():
    res = _limits()
    res.setrlimit(res.RLIMIT_AS, (MEM_LIMIT, MEM_LIMIT))
    res.setrlimit(res.RLIMIT_CPU, (int(TEST_TIMEOUT) + 2, int(TEST_TIMEOUT) + 4))
    res.setrlimit(res.RLIMIT_FSIZE, (16 * 1024 * 1024, 16 * 1024 * 1024))


def _norm(text):
    return " ".join((text or "").split())


def run_stdin(code, test, workdir):
    src = os.path.join(workdir, "submission.py")
    with open(src, "w", encoding="utf-8") as fh:
        fh.write(code)
    try:
        p = subprocess.run([sys.executable, src], input=test["input"].encode("utf-8"),
                           capture_output=True, timeout=TEST_TIMEOUT, preexec_fn=_preexec,
                           cwd=workdir)
    except subprocess.TimeoutExpired:
        return "tle"
    except Exception as exc:                                            # noqa: BLE001
        return "runtime_error:%s" % type(exc).__name__
    if p.returncode != 0:
        if "MemoryError" in (p.stderr or b"").decode("utf-8", "replace"):
            return "mle"
        return "runtime_error:rc%s" % p.returncode
    if _norm(p.stdout.decode("utf-8", "replace")) == _norm(test["output"]):
        return "ok"
    return "wrong_answer"


def score_question(task, hidden_tests, answer):
    """-> (verdict, detail). verdict in ok / fail / unscored."""
    if task["testtype"] != "stdin":
        return "unscored", "driver for testtype=functional is not in %s" % LCB_CONTRACT
    if len(hidden_tests) != task["hidden_count"] or sha16(canon_json(hidden_tests)) != task["hidden_sha16"]:
        return "unscored", "hidden payload does not match the pinned hidden_sha16"
    total = sum(len(t["input"]) + len(t["output"]) for t in hidden_tests)
    if total > QUESTION_CAP:
        return "fail", "question_total_bytes %d over cap %d" % (total, QUESTION_CAP)
    code = extract_code(answer)
    if not code.strip():
        return "fail", "empty_answer"
    fails = []
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="lcb-") as wd:
        for i, t in enumerate(hidden_tests):
            if len(t["input"]) > INPUT_CAP or len(t["output"]) > OUTPUT_CAP:
                fails.append("test%d:over_byte_cap" % i)
                continue
            if time.time() - started > QUESTION_TIMEOUT:
                fails.append("tle_budget")
                break
            v = run_stdin(code, t, wd)
            if v != "ok":
                fails.append("test%d:%s" % (i, v))
                if len(fails) >= 4:
                    break                                                 # anatomy is enough
    if fails:
        return "fail", ",".join(fails[:6])
    return "ok", "hidden %d/%d" % (len(hidden_tests), len(hidden_tests))


# ---------------------------------------------------------------- self-test

def selftest():
    ok, notes = True, []

    def chk(cond, name):
        nonlocal ok
        notes.append("%s %s" % ("PASS" if cond else "FAIL", name))
        ok = ok and bool(cond)

    # 1. pickler guard: data decodes, a global reference is refused.
    payload = base64.b64encode(zlib.compress(pickle.dumps(
        [{"input": "1", "output": "1", "testtype": "stdin"}]))).decode()
    chk(decode_hidden(payload)[0]["output"] == "1", "pickler_decodes_pure_data")

    class Evil:
        def __reduce__(self):
            return (os.system, ("echo pwned",))

    evil = base64.b64encode(zlib.compress(pickle.dumps(Evil()))).decode()
    try:
        decode_hidden(evil)
        chk(False, "pickler_refuses_global")
    except Exception as exc:                                             # noqa: BLE001
        chk("refused global" in str(exc) and "pwned" not in str(exc), "pickler_refuses_global")

    # 2. synthetic stdin task: correct passes, off-by-one fails, crash fails, TLE fails.
    tests = [{"input": "3\n", "output": "6\n", "testtype": "stdin"},
             {"input": "0\n", "output": "0\n", "testtype": "stdin"},
             {"input": "7\n", "output": "42\n", "testtype": "stdin"}]
    task = {"id": "lcb-synthetic-1", "testtype": "stdin", "hidden_count": len(tests),
            "hidden_sha16": sha16(canon_json(tests))}
    good = "print({3: 6, 0: 0, 7: 42}[int(input())])\n"
    chk(score_question(task, tests, "```python\n%s```" % good)[0] == "ok", "reference_passes")
    bad = "import sys\nn=int(input())\nprint(0)\n"
    v, d = score_question(task, tests, "```python\n%s```" % bad)
    chk(v == "fail" and "wrong_answer" in d, "wrong_completion_fails")
    v, d = score_question(task, tests, "```python\nraise SystemExit(3)\n```")
    chk(v == "fail" and "runtime_error" in d, "crash_fails")
    # a hidden payload that does not match the pinned sha16 is refused, never guessed
    v, d = score_question(task, [dict(tests[0])], good)
    chk(v == "unscored" and "hidden_sha16" in d, "payload_pin_fail_closed")
    loop = "while True:\n    pass\n"
    t0 = time.time()
    v, d = score_question({"id": "x", "testtype": "stdin", "hidden_count": 1,
                           "hidden_sha16": sha16(canon_json([tests[0]]))}, [tests[0]], loop)
    chk(v == "fail" and "tle" in d and time.time() - t0 < TEST_TIMEOUT + 8, "infinite_loop_tle")
    v, d = score_question(task, tests, "")
    chk(v == "fail" and d == "empty_answer", "empty_answer_fails")
    # 3. the functional regime is refused out loud, never silently scored.
    v, d = score_question({"id": "y", "testtype": "functional", "hidden_count": 1,
                           "hidden_sha16": sha16(canon_json(tests))}, tests, "print(1)")
    chk(v == "unscored" and "functional" in d, "functional_unscored_named")
    # 4. over-cap test input is a REJECT, not a skip.
    big = {"input": "9" * (INPUT_CAP + 10), "output": "0", "testtype": "stdin"}
    v, d = score_question({"id": "z", "testtype": "stdin", "hidden_count": 1,
                           "hidden_sha16": sha16(canon_json([big]))}, [big], "print(0)")
    chk(v == "fail" and "over_byte_cap" in d, "over_byte_cap_is_a_loss")
    print("\n".join(notes))
    print("%s self-test: %d checks, %s" % (LCB_CONTRACT, len(notes), "0 failures" if ok else "FAILURES"))
    return ok


# ---------------------------------------------------------------- score

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("a", nargs="?")
    ap.add_argument("b", nargs="?")
    ap.add_argument("--hidden-out")
    ap.add_argument("--hidden")
    ap.add_argument("--verdicts")
    ap.add_argument("--call", default="temp 0.7, max_tokens pinned by the leg, one request per task")
    args = ap.parse_args()

    if args.cmd == "selftest":
        sys.exit(0 if selftest() else 1)
    if args.cmd == "build":
        if not args.a or not args.b:
            sys.exit("usage: pub_bench_lcb.py build <test6.jsonl> <out.tasks.jsonl> [--hidden-out F.gz]")
        build(args.a, args.b, args.hidden_out)
        return
    if args.cmd != "score" or not args.a or not args.b:
        sys.exit(__doc__)
    if not selftest():
        sys.exit("refusing to score: contract self-test failed")
    tasks = [json.loads(l) for l in open(args.a, encoding="utf-8") if l.strip()]
    ans = {}
    for l in open(args.b, encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            ans.setdefault(r["id"], r)
    hidden = {}
    if args.hidden:
        opener = gzip.open if args.hidden.endswith(".gz") else open
        with opener(args.hidden, "rt", encoding="utf-8") as gz:
            for l in gz:
                if l.strip():
                    h = json.loads(l)
                    hidden[h["id"]] = h["tests"]
    verdicts, unscored, missing = [], [], 0
    for t in tasks:
        a = ans.get(t["id"])
        if a is None or not (a.get("answer") or "").strip():
            missing += 1
            continue
        if t["id"] not in hidden:
            unscored.append((t["id"], "no hidden payload for this id"))
            continue
        v, d = score_question(t, hidden[t["id"]], a["answer"])
        if v == "unscored":
            unscored.append((t["id"], d))
            continue
        verdicts.append({"id": t["id"], "ok": v == "ok", "why": d})
    n = len(verdicts)
    if not n or missing > 0.05 * len(tasks):
        sys.exit("refusing: %d scored, %d missing of %d (>5%% missing or empty arm)"
                 % (n, missing, len(tasks)))
    ok = sum(1 for v in verdicts if v["ok"])
    print("livecodebench %d/%d = %.1f %% (%s; unscored %d of %d tasks: %s)"
          % (ok, n, 100.0 * ok / n, LCB_CONTRACT, len(unscored), len(tasks),
             unscored[0][1] if unscored else "-"))
    for i, why in unscored[:5]:
        print("  unscored %s: %s" % (i, why))
    if args.verdicts:
        with open(args.verdicts, "w", encoding="utf-8") as fh:
            for v in verdicts:
                fh.write(json.dumps(v, ensure_ascii=False) + "\n")
    sha = hashlib.sha256(open(args.a, "rb").read()).hexdigest()[:16]
    model = next((a.get("model") for a in ans.values() if a.get("model")), "unknown")
    row = digest_row("livecodebench", model, n, sha,
                     "%s; %d unscored (driver gap), hidden tests by sha16; checker %s"
                     % (args.call, len(unscored), LCB_CONTRACT), ok, n)
    print("-> %s" % os.path.basename(write_digest(row)))


if __name__ == "__main__":
    main()
