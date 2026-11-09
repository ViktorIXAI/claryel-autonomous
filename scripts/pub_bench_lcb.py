#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LiveCodeBench `test6` slice: pin it, decode its hidden tests, score code by execution.

Contract `lcb-exec-v2` (this file is the contract; any change means a new contract id).
`lcb-exec-v1` scored only the `stdin` regime and named the 63 functional questions unscored;
v2 adds the functional driver below and leaves the stdin path byte-identical, so every
published stdin cell must re-score to the same verdict under v2 (a rescore check ships with
the release in MANIFEST.json `checker_history`).

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
`functional` (LeetCode, 63 questions) — the v2 driver, all of it derived from the question's
own pinned bytes, never from the prompt prose:
  signature     method name + parameter count parsed from the question's own `starter_code`
                stub (the empty stub body gets a `pass` for parsing only)
  case decoding one input string -> exactly that many JSON values, parsed sequentially with
                raw_decode (newline-separated or pretty-printed); a leftover token or a short
                count is MALFORMED -> UNSCORED, never guessed. Measured on the shipped
                payload: 2367/2367 hidden functional cases decode clean.
  expected      one JSON value per case; numbers compared with absolute/relative 1e-6
                tolerance (float-return questions exist; 1 of 63), bool never equals int,
                lists compared element-wise with the same rule, everything else exact
  execution     ONE child per question: the extracted code is exec'd; `Solution` is
                instantiated, or a bare function of the stub's name is used (completion style
                varies); per-case SIGALRM at the 20 s test budget, child rlimits identical to
                the stdin regime (1 GiB AS, question-total CPU cap), recursion limit raised
                because the LC environment is not CPython's default. A typing-name NameError
                at exec (the stub itself writes `List[int]` unimported) re-runs the question
                ONCE with a `typing` prelude, adopted only if it strictly reduces failures.
  verdict       every hidden case must pass, same rule as stdin. A driver crash is a loss,
                never a pass, and the anatomy names the first failing cases.

usage:
  pub_bench_lcb.py selftest                       # contract tests on synthetic tasks
  pub_bench_lcb.py build <test6.jsonl> <out.tasks.jsonl> [--hidden-out F.gz]
  pub_bench_lcb.py score <tasks.jsonl> <answers.jsonl> --hidden F.gz [--verdicts OUT]
"""
import argparse
import ast
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

LCB_CONTRACT = "lcb-exec-v2"
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


# ------------------------------------------------- functional driver (v2)

FUNC_PRELUDE = "from typing import List, Optional, Tuple, Dict, Set, Union, Deque, DefaultDict, Any\n"

_DRIVER_SRC = r'''import json, signal, sys, importlib.util
sys.setrecursionlimit(10 ** 6)

def close(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= 1e-6 + 1e-6 * max(abs(a), abs(b))
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    return type(a) == type(b) and a == b

class _TLE(Exception):
    pass

def _alrm(s, f):
    raise _TLE()

signal.signal(signal.SIGALRM, _alrm)
spec = importlib.util.spec_from_file_location("_answer", "_answer.py")
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except BaseException as exc:
    print("case0:exec_error:%s" % type(exc).__name__)
    sys.exit(0)
meth = sys.argv[1]
fn = None
if hasattr(mod, "Solution"):
    try:
        fn = getattr(mod.Solution(), meth)
    except BaseException:
        fn = None
if fn is None:
    fn = getattr(mod, meth, None)
if fn is None:
    print("case0:no_solution_method")
    sys.exit(0)
for i, c in enumerate(json.load(open("fcases.json"))):
    signal.alarm(20)
    try:
        res = fn(*c["a"])
        print("case%d:%s" % (i, "ok" if close(res, c["e"]) else "wrong_answer"), flush=True)
    except _TLE:
        print("case%d:tle" % i, flush=True)
    except BaseException as exc:
        print("case%d:exception:%s" % (i, type(exc).__name__), flush=True)
    signal.alarm(0)
'''


def _preexec_func():
    res = _limits()
    res.setrlimit(res.RLIMIT_AS, (MEM_LIMIT, MEM_LIMIT))
    res.setrlimit(res.RLIMIT_CPU, (int(QUESTION_TIMEOUT) + 4, int(QUESTION_TIMEOUT) + 6))
    res.setrlimit(res.RLIMIT_FSIZE, (16 * 1024 * 1024, 16 * 1024 * 1024))


def _stub_patch(src):
    """Give every body-less stub method a `pass` so the starter parses."""
    lines = src.split("\n")
    out = []
    for i, l in enumerate(lines):
        out.append(l)
        if l.rstrip().endswith(":"):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            ind = len(l) - len(l.lstrip())
            if j >= len(lines) or (len(lines[j]) - len(lines[j].lstrip())) <= ind:
                out.append(" " * (ind + 4) + "pass")
    return "\n".join(out)


def stub_signature(starter):
    """(method_name, n_params) from the question's own stub; None if not one method."""
    try:
        tree = ast.parse(_stub_patch(starter))
    except SyntaxError:
        return None
    defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if len(defs) != 1:
        return None
    return defs[0].name, len([a for a in defs[0].args.args if a.arg != "self"])


def func_args(input_str, n):
    """One input string -> exactly n sequential JSON values, or None (malformed)."""
    dec = json.JSONDecoder()
    vals, i = [], 0
    while len(vals) < n:
        while i < len(input_str) and input_str[i] in " \n\r\t":
            i += 1
        try:
            v, i = dec.raw_decode(input_str, i)
        except ValueError:
            return None
        vals.append(v)
    return None if input_str[i:].strip() else vals


def run_functional(code, cases, meth, workdir):
    """cases: [(args, expected)]. -> list of 'case<i>:<why>' failures ([] == all pass)."""
    def attempt(src):
        with open(os.path.join(workdir, "_answer.py"), "w", encoding="utf-8") as fh:
            fh.write(src)
        with open(os.path.join(workdir, "fcases.json"), "w", encoding="utf-8") as fh:
            json.dump([{"a": a, "e": e} for a, e in cases], fh)
        try:
            p = subprocess.run([sys.executable, os.path.join(workdir, "_driver.py"), meth],
                               capture_output=True, timeout=QUESTION_TIMEOUT + 10,
                               preexec_fn=_preexec_func, cwd=workdir)
        except subprocess.TimeoutExpired:
            return ["process_tle_budget"]
        except Exception as exc:                                            # noqa: BLE001
            return ["driver_spawn_error:%s" % type(exc).__name__]
        lines = [ln for ln in p.stdout.decode("utf-8", "replace").splitlines()
                 if ln.startswith("case")]
        if p.returncode != 0:
            # a killed child is a loss, never a pass: attribute the cases it did not answer
            got = {int(ln.partition(":")[0][4:]) for ln in lines}
            return (["case%d:killed_rc%s" % (i, p.returncode) for i in range(len(cases))
                     if i not in got] or ["driver_crashed:rc%s" % p.returncode])
        fails = []
        got = {}
        for ln in lines:
            head, _, why = ln.partition(":")
            got[int(head[4:])] = why
        for i in range(len(cases)):
            w = got.get(i)
            if w is None:
                fails.append("case%d:missing" % i)
            elif w != "ok":
                fails.append("case%d:%s" % (i, w))
        return fails

    fails = attempt(code)
    if fails and any("exception:NameError" in f or "exec_error:NameError" in f for f in fails) \
            and FUNC_PRELUDE not in code:
        # the stub itself writes `List[int]` unimported; retry with typing names only, and
        # adopt ONLY if it strictly reduces failures (a rescue, never a reroll)
        retry = attempt(FUNC_PRELUDE + code)
        if len(retry) < len(fails):
            fails = retry
    return fails


def _score_functional(task, hidden_tests, code):
    sig = stub_signature(task.get("starter_code") or "")
    if sig is None:
        return "unscored", "starter stub is not a single parseable method"
    meth, npar = sig
    cases = []
    for i, t in enumerate(hidden_tests):
        if t.get("testtype") != "functional":
            return "unscored", "case %d has testtype %r" % (i, t.get("testtype"))
        if len(t["input"]) > INPUT_CAP or len(t["output"]) > OUTPUT_CAP:
            return "fail", "test%d:over_byte_cap" % i
        args = func_args(t["input"], npar)
        if args is None:
            return "unscored", "case %d input does not decode to %d JSON arguments" % (i, npar)
        try:
            exp = json.loads(t["output"])
        except ValueError:
            return "unscored", "case %d output is not JSON" % i
        cases.append((args, exp))
    with tempfile.TemporaryDirectory(prefix="lcbf-") as wd:
        with open(os.path.join(wd, "_driver.py"), "w", encoding="utf-8") as fh:
            fh.write(_DRIVER_SRC)
        fails = run_functional(code, cases, meth, wd)
    if fails:
        return "fail", ",".join(fails[:6])
    return "ok", "functional hidden %d/%d" % (len(cases), len(cases))


def score_question(task, hidden_tests, answer):
    """-> (verdict, detail). verdict in ok / fail / unscored."""
    if task["testtype"] not in ("stdin", "functional"):
        return "unscored", "unknown testtype %r" % task["testtype"]
    if len(hidden_tests) != task["hidden_count"] or sha16(canon_json(hidden_tests)) != task["hidden_sha16"]:
        return "unscored", "hidden payload does not match the pinned hidden_sha16"
    total = sum(len(t["input"]) + len(t["output"]) for t in hidden_tests)
    if total > QUESTION_CAP:
        return "fail", "question_total_bytes %d over cap %d" % (total, QUESTION_CAP)
    code = extract_code(answer)
    if not code.strip():
        return "fail", "empty_answer"
    if task["testtype"] == "functional":
        return _score_functional(task, hidden_tests, code)
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
    # 3. functional driver (lcb-exec-v2): the stub gives the signature, the case's single
    #    input string gives the arguments, and only the pinned bytes decide.
    ftests = [{"input": "2\n3", "output": "5", "testtype": "functional"},
              {"input": "[1, 2, 3]\n2", "output": "[2, 4, 6]", "testtype": "functional"},
              {"input": '"hi"\n3', "output": '"hihihi"', "testtype": "functional"}]
    ftask = {"id": "lcb-synthetic-f", "testtype": "functional",
             "starter_code": "class Solution:\n    def mix(self, a, b):\n         ",
             "hidden_count": len(ftests), "hidden_sha16": sha16(canon_json(ftests))}
    fgood = ("class Solution:\n    def mix(self, a, b):\n"
             "        if isinstance(a, int):\n            return a + b\n"
             "        if isinstance(a, list):\n            return [x * b for x in a]\n"
             "        return a * b\n")
    v, d = score_question(ftask, ftests, "```python\n%s```" % fgood)
    chk(v == "ok", "functional_reference_passes")
    v, d = score_question(ftask, ftests, "```python\nclass Solution:\n    def mix(self, a, b):\n        return 0\n```")
    chk(v == "fail" and "wrong_answer" in d, "functional_wrong_fails")
    v, d = score_question(ftask, ftests, "```python\nclass Solution:\n    def mix(self, a, b):\n        return a + b\n```")
    chk(v == "fail" and "exception" in d, "functional_exception_anatomy")
    shim = ("def mix(a, b):\n    if isinstance(a, int):\n        return a + b\n"
            "    if isinstance(a, list):\n        return [x * b for x in a]\n    return a * b\n")
    v, d = score_question(ftask, ftests, "```python\n%s```" % shim)
    chk(v == "ok", "functional_bare_method_shim")
    ft2 = [{"input": "1", "output": "0.5", "testtype": "functional"}]
    ftask2 = {"id": "lcb-synthetic-f2", "testtype": "functional",
              "starter_code": "class Solution:\n    def half(self, x: int) -> float:\n         ",
              "hidden_count": 1, "hidden_sha16": sha16(canon_json(ft2))}
    v, d = score_question(ftask2, ft2, "```python\nclass Solution:\n    def half(self, x):\n        return x / 2.0 - 1e-9\n```")
    chk(v == "ok", "functional_float_tolerance")
    v, d = score_question(ftask2, ft2, "```python\nclass Solution:\n    def half(self, x):\n        return 0.51\n```")
    chk(v == "fail" and "wrong_answer" in d, "functional_float_out_of_tol_fails")
    fbad = [{"input": "1\n", "output": "1", "testtype": "functional"}]  # mix takes 2 args
    ftask3 = dict(ftask, hidden_count=1, hidden_sha16=sha16(canon_json(fbad)))
    v, d = score_question(ftask3, fbad, "```python\n%s```" % fgood)
    chk(v == "unscored" and "decode" in d, "functional_malformed_input_unscored")
    ft4 = [{"input": "5\n2", "output": "7", "testtype": "functional"},
           {"input": "1\n1", "output": "2", "testtype": "functional"}]
    ftask4 = dict(ftask, hidden_count=2, hidden_sha16=sha16(canon_json(ft4)))
    t0 = time.time()
    v, d = score_question(ftask4, ft4, "```python\nclass Solution:\n    def mix(self, a, b):\n        if a == 5:\n            while True:\n                pass\n        return a + b\n```")
    chk(v == "fail" and "tle" in d and time.time() - t0 < TEST_TIMEOUT + 25, "functional_case_tle")
    # a completion using the stub's unimported List[int] is rescued by the typing prelude
    ft5 = [{"input": "[3, 1]", "output": "[1, 3]", "testtype": "functional"}]
    ftask5 = {"id": "lcb-synthetic-f5", "testtype": "functional",
              "starter_code": "class Solution:\n    def up(self, a: List[int]) -> List[int]:\n         ",
              "hidden_count": 1, "hidden_sha16": sha16(canon_json(ft5))}
    typed = "class Solution:\n    def up(self, a: List[int]) -> List[int]:\n        return sorted(a)\n"
    v, d = score_question(ftask5, ft5, "```python\n%s```" % typed)
    chk(v == "ok", "functional_typing_prelude_rescue")
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
