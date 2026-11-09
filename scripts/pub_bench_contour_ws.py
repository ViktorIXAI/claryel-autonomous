#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Item P0 (contour parity): stage a PUBLIC-benchmark workspace for the frozen runtime.

What this is. The owner asked for a with-harness row on every published public set, produced by
the FROZEN contour runtime `0.0.2.56` (tag `stable-hard-0.0.2.56`) over the SAME pinned task
ids, and scored by the SAME public checker contract. This script stages that workspace the way
`scripts/build_hard_v6_ws.py` stages a hard-bank one: the harness modules are copied verbatim,
including the frozen deciding bytes the runner's contract guard hashes (`parb_check_v6.py`,
`parb_loop.py`, `e_sandbox.py`). No new contour stamp and no new contour feature is registered
here — the stamp is pinned to the frozen line and the runner itself refuses any unregistered
stamp before the endpoint is reserved.

The one deliberate difference: a public task gets category "P". `gate_run`'s contour routing is
keyed to the hard-bank families A..K, so a "P" task reaches only the generic ladder path and no
hard-bank family grammar (Russian invoice fields, coverage-choice nudges, plan gates) is grafted
onto a public prompt. Scoring goes through the public checker module (`scripts/pub_bench_score.py`,
loaded by path), i.e. the same bytes that decided the bare row. If the frozen runtime cannot
serve a public class at all, that refusal is the published finding — no contour row is faked.

Usage: pub_bench_contour_ws.py <bench> <limit> [shape=frozen|bare] [out-dir]
                               [validator=score|exec|ifeval|bfcl|lcb]

`validator=exec` puts the pytest-v1 execution checker (scripts/pub_bench_exec.py) in the validator
slot, which is what HumanEval's bare row was scored with; the builder runs that checker's self-test
and refuses to stage if it fails. `validator=ifeval` puts the IFEval contract `pub-ifeval-v1`
(scripts/pub_bench_ifeval.py + the vendored upstream checker) in the slot, which is what IFEval's
bare row is scored with: the builder runs that checker's own two gates (41-test upstream unit suite
+ the recorded reference band) through the pinned venv interpreter and refuses to stage if they
fail. `validator=bfcl` puts the BFCL contract `bfcl-ast-v1` (scripts/pub_bench_bfcl.py) in the slot,
which is what BFCL's bare row is scored with; its self-test is re-run at staging time and the
task's own `functions` docs and `gold` calls are carried into every bank row, because the AST
matcher scores against them. Default `score` keeps `pub-checkers-v2`.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARN = os.path.join(REPO, "harness")
STAMP = "0.0.2.56"                      # the frozen line; a newer stamp is not allowed here
# The runner fail-closes unless these deciding bytes are present unmodified; the builder
# checks them first so a launch is never burned on a staging mistake.
PINS = {"parb_check_v6.py": "89437d8cfe1fc6c8",
        "parb_loop.py": "f5f5b78ab46a0f0c",
        "e_sandbox.py": "424c04126e9b6c1e"}
MODULES = ("gate_run.py", "gate_versioning.py", "gate_engine_guard.py", "gate_j_rerank.py",
           "gate_c_ground.py", "gate_fixers.py", "gate_scorer_contract.py",
           "gate_bank_versions.py", "os_record.py", "parb_check.py", "parb_check_v6.py",
           "parb_check_v6_2.py", "parb_loop.py", "e_sandbox.py")

# Task-file fields the validator shim needs but the generic bank row does not carry by default.
# Kept as a table so a new contract adds fields without touching the row builder.
EXTRA_FIELDS = {"lcb": ("testtype", "hidden_count", "hidden_sha16", "platform", "difficulty")}

# The token ceiling the BARE arm of this set used, so a `bare`-shape ws states the ladder it must
# be launched with. The parity rule pins the contour leg's FIRST RUNG to the bare arm's
# max_tokens; that number is per-set (1200 on the classic sets, 2400 on LiveCodeBench), so it is
# read from the environment instead of being hardcoded here.
BARE_MAX_TOKENS = int(os.environ.get("PUB_BARE_MAX_TOKENS", "1200"))

SHIM = '''

# ---- public-benchmark validator shim (workspace-only, written by pub_bench_contour_ws.py) ----
# Category "P" is a public benchmark task: gate_run's contour routing is keyed to the hard-bank
# families A..K, so a "P" task reaches only the generic ladder path and no family grammar is
# grafted onto a public prompt. The verdict is decided by the PUBLIC checker contract (the same
# bytes that scored the bare arm), not by the hard-bank scorers. format_ok is fixed to 1 because
# the public contract has no separate format axis, so strict (content == 1.0 and format_ok) is
# exactly the public verdict.
import hashlib as _shim_hashlib
import importlib.util as _shim_ilu
_PUB_SCORE_PATH = @@PUBPATH@@
_spec = _shim_ilu.spec_from_file_location("pub_bench_score_shim", _PUB_SCORE_PATH)
PBS = _shim_ilu.module_from_spec(_spec)
_spec.loader.exec_module(PBS)
PUB_CHECKER_CONTRACT = PBS.CHECKER_CONTRACT
PUB_SCORER_SHA16 = _shim_hashlib.sha256(open(_PUB_SCORE_PATH, "rb").read()).hexdigest()[:16]


def check_public(t, text):
    """Public checker verdict mapped onto the harness score slots (documented above)."""
    ok = PBS.check(t.get("checker", ""), t.get("gold"), text or "")
    if ok is None:
        return None, None, ["pub_unscored_checker:%s" % t.get("checker", "")]
    if ok:
        return 1.0, 1, ["pub:ok"]
    return 0.0, 1, ["pub:mismatch"]


CHECK["P"] = check_public
'''

# Variant for execution-graded public sets (HumanEval). The validator slot must hold the SAME
# bytes that scored the bare arm, and for HumanEval that is the `pytest-v1` execution contract in
# scripts/pub_bench_exec.py, not the number/letter/exact contract. The staging builder refuses to
# build this variant unless that checker's own self-test passes first.
SHIM_EXEC = '''

# ---- public-benchmark validator shim, EXECUTION variant (workspace-only, written by
# ---- pub_bench_contour_ws.py). Contract: pytest-v1 (scripts/pub_bench_exec.py). ----
# Category "P" is a public benchmark task: gate_run's contour routing is keyed to the hard-bank
# families A..K, so a "P" task reaches only the generic ladder path and no family grammar is
# grafted onto a public prompt. The verdict is decided by RUNNING the task's own upstream
# check(candidate) tests in the rlimit'd child pub_bench_exec.py uses for the bare arm — the same
# bytes, the same isolation, so the contour row and the bare row are graded identically.
# format_ok is fixed to 1 because the public contract has no separate format axis.
import hashlib as _shim_hashlib
import importlib.util as _shim_ilu
_PUB_EXEC_PATH = @@PUBPATH@@
_spec = _shim_ilu.spec_from_file_location("pub_bench_exec_shim", _PUB_EXEC_PATH)
PBS = _shim_ilu.module_from_spec(_spec)
_spec.loader.exec_module(PBS)
PUB_CHECKER_CONTRACT = "pytest-v1"
PUB_SCORER_SHA16 = _shim_hashlib.sha256(open(_PUB_EXEC_PATH, "rb").read()).hexdigest()[:16]


def check_public(t, text):
    """Execution verdict mapped onto the harness score slots (documented above)."""
    meta = t.get("meta") or {}
    if isinstance(meta, str):
        import json as _shim_json
        meta = _shim_json.loads(meta)
    entry = PBS.entry_point(t.get("prompt", ""))
    if not entry or not meta.get("test"):
        return None, None, ["pub_unscored_checker:no_test_material"]
    ok, note = PBS.run_case(t.get("prompt", ""), PBS.strip_code(text or ""),
                            meta["test"], entry)
    if ok:
        return 1.0, 1, ["pub:exec_ok"]
    return 0.0, 1, ["pub:exec_fail:%s" % str(note)[:120]]


CHECK["P"] = check_public
'''


# Variant for instruction-following sets (IFEval). The verdict here is not answer matching at all:
# it is the conjunction of the upstream per-instruction checks, so the slot must hold the vendor's
# own code — the same vendored modules, the same entry point and the same strict axis that decided
# the bare row. The shim imports the vendored evaluation_lib in-process, which means the leg must be
# launched with the pinned venv interpreter (absl, langdetect, immutabledict, NLTK words); the
# builder records that interpreter in WS-IDENTITY.json and the go-script uses it.
SHIM_IFEVAL = '''

# ---- public-benchmark validator shim, IFEval variant (workspace-only, written by
# ---- pub_bench_contour_ws.py). Contract: pub-ifeval-v1 (scripts/pub_bench_ifeval.py plus the
# ---- vendored upstream checker under benchmarks/public/vendor/instruction_following_eval/). ----
# Category "P" is a public benchmark task: gate_run's contour routing is keyed to the hard-bank
# families A..K, so a "P" task reaches only the generic ladder path and no family grammar is
# grafted onto a public prompt. The verdict is the upstream STRICT verdict on the contour's final
# answer text (follow_all_instructions), i.e. the same bytes and entry point that scored the bare
# arm. format_ok is fixed to 1 because the public contract has no separate format axis, so the
# harness strict rule (content == 1.0 and format_ok) is exactly the vendor strict verdict.
import hashlib as _shim_hashlib
import importlib.util as _shim_ilu
import sys as _shim_sys
_SHIM_VENDOR = @@VENDOR@@
_IFEVAL_PATH = @@PUBPATH@@
if _SHIM_VENDOR not in _shim_sys.path:
    _shim_sys.path.insert(0, _SHIM_VENDOR)
_spec = _shim_ilu.spec_from_file_location("pub_bench_ifeval_shim", _IFEVAL_PATH)
PBI = _shim_ilu.module_from_spec(_spec)
_spec.loader.exec_module(PBI)
EV = PBI.load_vendor()
PUB_CHECKER_CONTRACT = "pub-ifeval-v1"
PUB_SCORER_SHA16 = _shim_hashlib.sha256(open(_IFEVAL_PATH, "rb").read()).hexdigest()[:16]


def check_public(t, text):
    """Upstream strict IFEval verdict mapped onto the harness score slots (see above)."""
    ids = list(t.get("instruction_id_list") or [])
    kw = list(t.get("kwargs") or [])
    prompt = t.get("prompt", "")
    if not ids or not prompt:
        return None, None, ["pub_unscored_checker:no_instruction_ids"]
    try:
        key = int(str(t.get("id", "")).rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return None, None, ["pub_unscored_checker:bad_task_key"]
    inp = EV.InputExample(key=key, instruction_id_list=ids, prompt=prompt, kwargs=kw)
    res = EV.test_instruction_following_strict(inp, {prompt: text or ""})
    if res.follow_all_instructions:
        return 1.0, 1, ["pub:ifeval_strict_pass"]
    bad = [cid for cid, okc in zip(ids, res.follow_instruction_list) if not okc]
    return 0.0, 1, ["pub:ifeval_strict_fail:%s" % ",".join(bad)[:160]]


CHECK["P"] = check_public
'''


# Variant for function-calling sets (BFCL v4). The validator slot must hold the SAME bytes that
# scored the bare arm: the AST matcher over the task's own `functions` docs and `gold` call list.
# The task's docs and gold therefore have to reach the shim, which is why the staging builder
# carries `functions` and `category` through into every bank row for this contract.
SHIM_BFCL = '''

# ---- public-benchmark validator shim, BFCL variant (workspace-only, written by
# ---- pub_bench_contour_ws.py). Contract: bfcl-ast-v1 (scripts/pub_bench_bfcl.py). ----
# Category "P" is a public benchmark task: gate_run's contour routing is keyed to the hard-bank
# families A..K, so a "P" task reaches only the generic ladder path and no family grammar is
# grafted onto a public prompt. The verdict is the SAME AST match that scored the bare arm:
# `score_entry(task, answer)` over the task's own `functions` docs and `gold` call list.
# format_ok is fixed to 1 because the public contract has no separate format axis, so the harness
# strict rule (content == 1.0 and format_ok) is exactly the checker's verdict.
import hashlib as _shim_hashlib
import importlib.util as _shim_ilu
_BFCL_PATH = @@PUBPATH@@
_spec = _shim_ilu.spec_from_file_location("pub_bench_bfcl_shim", _BFCL_PATH)
PBFCL = _shim_ilu.module_from_spec(_spec)
_spec.loader.exec_module(PBFCL)
PUB_CHECKER_CONTRACT = PBFCL.BFCL_CHECKER
PUB_SCORER_SHA16 = _shim_hashlib.sha256(open(_BFCL_PATH, "rb").read()).hexdigest()[:16]


def check_public(t, text):
    """AST-match verdict mapped onto the harness score slots (documented above)."""
    if not t.get("functions"):
        return None, None, ["pub_unscored_checker:no_functions"]
    ok, why = PBFCL.score_entry(t, text or "")
    if ok:
        return 1.0, 1, ["pub:bfcl_ast_match"]
    return 0.0, 1, ["pub:bfcl_ast_fail:%s" % str(why)[:160]]


CHECK["P"] = check_public
'''

# Variant for hidden-test code sets (LiveCodeBench). The verdict is not answer matching and not a
# public-test run: `lcb-exec-v1` (scripts/pub_bench_lcb.py) runs the question's HIDDEN battery and
# requires every test to pass, after verifying the battery against the pinned per-question
# hidden_sha16. The hidden payload is an untracked sidecar (the decoded battery is 289 MB, far too
# large for a tracked file), so the shim reads it from the path the builder stamps here and the
# checker re-derives the pin per question — a payload swap fails closed as UNSCORED, never as a
# guess. The same module, the same caps and the same rlimit'd child decide the bare row and the
# contour row, which is what makes the two rows comparable. `testtype`/`hidden_count`/
# `hidden_sha16` therefore have to reach the shim, so the builder carries them into the bank rows.
SHIM_LCB = '''

# ---- public-benchmark validator shim, LCB variant (workspace-only, written by
# ---- pub_bench_contour_ws.py). Contract: lcb-exec-v1 (scripts/pub_bench_lcb.py). ----
# Category "P" is a public benchmark task: gate_run's contour routing is keyed to the hard-bank
# families A..K, so a "P" task reaches only the generic ladder path and no family grammar is
# grafted onto a public prompt. format_ok is fixed to 1 because the public contract has no separate
# format axis, so the harness strict rule (content == 1.0 and format_ok) is exactly the checker's
# verdict. A `functional` question has no shipped driver in this contract and stays UNSCORED
# (content None), exactly as it does for the bare arm — never a zero.
import gzip as _shim_gzip
import hashlib as _shim_hashlib
import importlib.util as _shim_ilu
_LCB_PATH = @@PUBPATH@@
_LCB_HIDDEN_PATH = @@LCBHIDDEN@@
_spec = _shim_ilu.spec_from_file_location("pub_bench_lcb_shim", _LCB_PATH)
PLCB = _shim_ilu.module_from_spec(_spec)
_spec.loader.exec_module(PLCB)
PUB_CHECKER_CONTRACT = PLCB.LCB_CONTRACT
PUB_SCORER_SHA16 = _shim_hashlib.sha256(open(_LCB_PATH, "rb").read()).hexdigest()[:16]
_LCB_BATTERY = {}


def _lcb_battery():
    """Load the pinned hidden battery once; the per-question sha16 check is inside score_question."""
    if not _LCB_BATTERY:
        _opener = _shim_gzip.open if _LCB_HIDDEN_PATH.endswith(".gz") else open
        with _opener(_LCB_HIDDEN_PATH, "rt", encoding="utf-8") as _fh:
            for _l in _fh:
                if _l.strip():
                    _h = json.loads(_l)
                    _LCB_BATTERY[_h["id"]] = _h["tests"]
    return _LCB_BATTERY


def check_public(t, text):
    """Hidden-battery verdict mapped onto the harness score slots (documented above)."""
    _tests = _lcb_battery().get(t.get("id"))
    if _tests is None:
        return None, None, ["pub_unscored_checker:no_hidden_payload"]
    _v, _d = PLCB.score_question(t, _tests, text or "")
    if _v == "ok":
        return 1.0, 1, ["pub:lcb_exec_ok:%s" % str(_d)[:80]]
    if _v == "unscored":
        return None, None, ["pub_unscored_checker:%s" % str(_d)[:120]]
    return 0.0, 1, ["pub:lcb_exec_fail:%s" % str(_d)[:160]]


CHECK["P"] = check_public
'''


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    bench, limit = sys.argv[1], int(sys.argv[2])
    # Item P0 parity rule (2026-11-08): `bare` stages a workspace whose leg must be launched with
    # PARB_SHAPE=bare PARB_LADDER=<bare arm's max_tokens>, i.e. the request shape the bare row
    # used (first rung = 1200, serve-default thinking, no request seed). `frozen` (default) keeps
    # the published escalation shape.
    shape = (sys.argv[3] if len(sys.argv) > 3 else "frozen").strip().lower()
    if shape not in ("frozen", "bare"):
        sys.exit("shape must be 'frozen' or 'bare', got %r" % shape)
    # The validator slot must hold the bytes that decided the BARE row of this set. For the
    # answer-graded sets that is the number/letter/exact contract; for HumanEval it is the
    # pytest-v1 execution checker, which is a different module and a different contract id.
    validator = (sys.argv[5] if len(sys.argv) > 5 else "score").strip().lower()
    if validator not in ("score", "exec", "ifeval", "bfcl", "lcb"):
        sys.exit("validator must be 'score', 'exec', 'ifeval', 'bfcl' or 'lcb', got %r" % validator)
    pub_mod = {"exec": "pub_bench_exec.py",
               "ifeval": "pub_bench_ifeval.py",
               "bfcl": "pub_bench_bfcl.py",
               "lcb": "pub_bench_lcb.py"}.get(validator, "pub_bench_score.py")
    # The LCB verdict comes from the question's hidden battery, which is an untracked sidecar by
    # design (289 MB decoded). Staging without it would score every row UNSCORED, so the builder
    # resolves and verifies the sidecar before it reserves anything.
    lcb_hidden = None
    if validator == "lcb":
        lcb_hidden = os.environ.get("PUB_LCB_HIDDEN") or os.path.expanduser(
            "~/pub-bench/lcb/livecodebench.hidden.jsonl.gz")
        if not os.path.exists(lcb_hidden):
            sys.exit("LCB validator needs the pinned hidden sidecar, missing: %s" % lcb_hidden)
    if validator in ("exec", "lcb"):
        r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", pub_mod),
                            "selftest"], capture_output=True, text=True)
        print((r.stdout or "").strip() or (r.stderr or "").strip())
        if r.returncode != 0:
            sys.exit("EXEC CHECKER SELF-TEST FAILED - refusing to stage an execution-validated ws")
    if validator == "bfcl":
        r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "pub_bench_bfcl.py"),
                            "selftest"], capture_output=True, text=True)
        print((r.stdout or "").strip() or (r.stderr or "").strip())
        if r.returncode != 0:
            sys.exit("BFCL AST CHECKER SELF-TEST FAILED - refusing to stage a bfcl-validated ws")
    # IFEval's contract is the vendored upstream checker, whose runtime deps (absl, langdetect,
    # immutabledict, NLTK words) live in a pinned venv, never in the system interpreter. The gate
    # is the checker's own two self-tests (41 upstream unit tests + the recorded reference band),
    # run through that interpreter before any endpoint is reserved.
    ife_py = None
    if validator == "ifeval":
        ife_py = os.environ.get("PARB_IFEVAL_PY") or os.path.expanduser(
            "~/pub-bench/ifeval-venv/bin/python")
        if not os.path.exists(ife_py):
            sys.exit("IFEval validator needs the pinned venv python, missing: %s" % ife_py)
        r = subprocess.run(
            [ife_py, os.path.join(REPO, "scripts", "pub_bench_ifeval.py"), "/dev/null",
             os.path.join(REPO, "benchmarks", "public", "ifeval.tasks.jsonl"),
             "ifeval", "staging-selftest", "staging-selftest", "--selftest-only"],
            capture_output=True, text=True, timeout=1200)
        print((r.stdout or "").strip() or (r.stderr or "").strip())
        if r.returncode != 0:
            sys.exit("IFEVAL CHECKER SELF-TEST FAILED - refusing to stage an IFEval-validated ws")
    out = (sys.argv[4] if len(sys.argv) > 4
           else os.path.expanduser("~/parb-pub-contour/%s%s"
                                   % (bench, "-matched" if shape == "bare" else "")))
    os.makedirs(out, exist_ok=True)
    for m in MODULES:
        shutil.copy2(os.path.join(HARN, m), os.path.join(out, m))
    for name, want in PINS.items():
        got = sha16(os.path.join(out, name))
        if got != want:
            sys.exit("PIN DRIFT %s: contract wants %s, ws has %s" % (name, want, got))
    if shape == "bare":
        gr = open(os.path.join(out, "gate_run.py"), encoding="utf-8").read()
        if "SHAPE_BARE" not in gr:
            sys.exit("SHAPE SWITCH MISSING: this harness has no PARB_SHAPE switch; a 'bare' "
                     "parity workspace would silently re-measure the escalation shape")
    shim = {"exec": SHIM_EXEC, "ifeval": SHIM_IFEVAL,
            "bfcl": SHIM_BFCL, "lcb": SHIM_LCB}.get(validator, SHIM)
    shim = shim.replace("@@PUBPATH@@", json.dumps(os.path.join(REPO, "scripts", pub_mod)))
    shim = shim.replace("@@LCBHIDDEN@@", json.dumps(lcb_hidden or ""))
    shim = shim.replace("@@VENDOR@@",
                        json.dumps(os.path.join(REPO, "benchmarks", "public", "vendor")))
    with open(os.path.join(out, "parb_check.py"), "a", encoding="utf-8") as fh:
        fh.write(shim)

    tasks_f = os.path.join(REPO, "benchmarks", "public", "%s.tasks.jsonl" % bench)
    rows = [json.loads(l) for l in open(tasks_f, encoding="utf-8") if l.strip()][:limit]
    if len(rows) != limit:
        sys.exit("task file holds fewer than %d rows" % limit)
    # Public tasks carry no hard-bank family fields: no sys prompt, no ref, no assembled_doc.
    # Instruction-following sets carry no checker/gold fields at all (the verdict comes from the
    # instruction ids), and their ids/kwargs must reach the validator shim, so both are carried
    # through instead of assumed.
    bank = [{"id": t["id"], "cat": "P", "kind": "public", "level": "pub",
             "prompt": t["prompt"], "checker": t.get("checker", ""), "gold": t.get("gold", ""),
             "meta": t.get("meta", {}),
             "seed": int(hashlib.sha256(t["id"].encode()).hexdigest()[:6], 16)}
            for t in rows]
    for b, t in zip(bank, rows):
        # `functions`/`category` must reach the validator shim for function-calling sets: the AST
        # matcher scores against the task's own docs, and `category` is what the report splits by.
        # `testtype`/`hidden_count`/`hidden_sha16` must reach it for hidden-battery sets: the
        # checker refuses to run a battery whose bytes do not match the pinned hash, and the
        # difficulty/platform columns are what the result doc splits by.
        extra_fields = list(EXTRA_FIELDS.get(validator, ()))
        for extra in ("instruction_id_list", "kwargs", "functions", "category") + tuple(extra_fields):
            if extra in t:
                b[extra] = t[extra]
    json.dump(bank, open(os.path.join(out, "bank.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    # sp1 seed protocol, identical to the hard bank, so a public pair is cell-comparable
    # the same way: gseed = int(sha256(task|rep)[:8], 16) % 999983.
    plan = [{"task": b["id"], "rep": 0, "series": "main", "rep_group": "pub", "stage": 1,
             "gseed": int(hashlib.sha256(("%s|0" % b["id"]).encode()).hexdigest()[:8], 16) % 999983}
            for b in bank]
    json.dump(plan, open(os.path.join(out, "plan.json"), "w", encoding="utf-8"))

    bank_sha = sha16(os.path.join(out, "bank.json"))
    json.dump({"bank_version": "pub-%s-%d" % (bench, len(bank)),
               "ws_bank_sha16": bank_sha,
               "source": "benchmarks/public/%s.tasks.jsonl (first %d ids, file order)"
                         % (bench, len(bank)),
               "written": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(out, "bank-version.json"), "w", encoding="utf-8"), indent=2)
    sha = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    open(os.path.join(out, "HARNESS_GIT_SHA"), "w").write(sha + "\n")
    if validator == "exec":
        validator_identity = {"contract": "pytest-v1",
                              "module": "scripts/pub_bench_exec.py",
                              "sha16": sha16(os.path.join(REPO, "scripts",
                                                           "pub_bench_exec.py"))}
    elif validator == "ifeval":
        validator_identity = {"contract": "pub-ifeval-v1",
                              "module": "scripts/pub_bench_ifeval.py",
                              "sha16": sha16(os.path.join(REPO, "scripts",
                                                           "pub_bench_ifeval.py")),
                              "vendor_dir":
                                  "benchmarks/public/vendor/instruction_following_eval",
                              "gates": "41-test upstream unit suite + reference band "
                                       "(strict 416/540, loose 431/540) passed at staging "
                                       "time through the pinned venv interpreter"}
    elif validator == "bfcl":
        # Contract id is read from the checker module, never retyped here: a checker bump must not
        # be able to leave a stale label in a workspace identity file.
        _cid = subprocess.run(
            [sys.executable, "-c",
             "import importlib.util as u;s=u.spec_from_file_location('b',%r);"
             "m=u.module_from_spec(s);s.loader.exec_module(m);print(m.BFCL_CHECKER)"
             % os.path.join(REPO, "scripts", "pub_bench_bfcl.py")],
            capture_output=True, text=True)
        validator_identity = {"contract": (_cid.stdout or "").strip() or "bfcl-ast-v1",
                              "module": "scripts/pub_bench_bfcl.py",
                              "sha16": sha16(os.path.join(REPO, "scripts",
                                                           "pub_bench_bfcl.py")),
                              "gates": "22-case self-test re-run at staging time (refuses on "
                                       "failure); gold-as-answer 1240/1240 and perturbed-gold "
                                       "control 1000/1000 rejected were recorded when the checker "
                                       "shipped, and the pinned task bytes have not moved"}
    elif validator == "lcb":
        _cid = subprocess.run(
            [sys.executable, "-c",
             "import importlib.util as u;s=u.spec_from_file_location('l',%r);"
             "m=u.module_from_spec(s);s.loader.exec_module(m);print(m.LCB_CONTRACT)"
             % os.path.join(REPO, "scripts", "pub_bench_lcb.py")],
            capture_output=True, text=True)
        validator_identity = {"contract": (_cid.stdout or "").strip() or "lcb-exec-v1",
                              "module": "scripts/pub_bench_lcb.py",
                              "sha16": sha16(os.path.join(REPO, "scripts", "pub_bench_lcb.py")),
                              "hidden_sidecar": lcb_hidden,
                              "hidden_sidecar_sha16": sha16(lcb_hidden),
                              "gates": "10-case contract self-test re-run at staging time "
                                       "(refuses on failure); the checker verifies every "
                                       "question's hidden battery against the pinned "
                                       "hidden_sha16 before running it"}
    else:
        validator_identity = {"contract": "pub-checkers-v2",
                              "module": "scripts/pub_bench_score.py",
                              "sha16": sha16(os.path.join(REPO, "scripts",
                                                           "pub_bench_score.py"))}
    ident = {"contour_stamp": STAMP, "harness_git_sha": sha,
             "tasks_file": "benchmarks/public/%s.tasks.jsonl" % bench,
             "tasks_file_sha16": sha16(tasks_f), "tasks": len(bank),
             "bank_ws_sha16": bank_sha, "plan_sha16": sha16(os.path.join(out, "plan.json")),
             "seed_protocol": ("sp1 (gseed = int(sha256(task|rep)[:8],16) % 999983); in 'bare' "
                               "shape the gseed stays in the plan for cell identity but is NOT "
                               "sent as a request seed, matching the bare arm's seed policy"
                               if shape == "bare" else
                               "sp1 (gseed = int(sha256(task|rep)[:8],16) % 999983)"),
             "request_shape": ({"mode": "bare-matched",
                                "bare_max_tokens": BARE_MAX_TOKENS,
                                "launch_env_required": "PARB_SHAPE=bare PARB_LADDER=%d"
                                                       % BARE_MAX_TOKENS,
                                "why": ("parity with the bare arm: first rung = the bare "
                                        "arm's max_tokens (%d), serve-default thinking (no "
                                        "chat_template_kwargs), temperature 0.7, no request "
                                        "seed" % BARE_MAX_TOKENS)
                                } if shape == "bare" else
                               {"mode": "frozen-contour",
                                "why": ("published shape: first rung 512 escalating to the "
                                        "ladder ceiling, sp1 request seed, enable_thinking off")}),
             "validator": validator_identity,
             "frozen_scorer_bytes_present": PINS,
             "ws_modules": {m: sha16(os.path.join(out, m)) for m in MODULES}}
    json.dump(ident, open(os.path.join(out, "WS-IDENTITY.json"), "w", encoding="utf-8"), indent=2)
    print("ws ready:", out)
    print("stamp", STAMP, "shape", shape, "validator", ident["validator"]["contract"],
          "tasks", len(bank), "bank", bank_sha,
          "tasks-file", ident["tasks_file_sha16"], "harness", sha[:12])
    if shape == "bare":
        print("launch this ws with: PARB_SHAPE=bare PARB_LADDER=%d (the bare arm's shape)"
              % BARE_MAX_TOKENS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
