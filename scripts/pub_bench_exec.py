#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HumanEval execution checker (contract `pytest` v1) for the public benchmark line.

Scoring is by running the model's code against the upstream `check(candidate)` tests inside a
resource-limited child process (address, CPU, file-size and process-count rlimits, wall timeout,
empty environment, private temp cwd). No network isolation is claimed — that is stated in the
result doc, not hidden. A task passes only if the child exits 0.

The file refuses to score anything until its own self-test passes: the reference solution for
HumanEval/0 must pass and a deliberately wrong completion must fail. A checker that cannot
discriminate right from wrong is not allowed to publish a percent.

Usage:
  pub_bench_exec.py selftest
  pub_bench_exec.py <tasks.jsonl> <answers.jsonl>
"""
import hashlib
import json
import os
import re
import resource
import subprocess
import sys
import tempfile

TIMEOUT = 25
EXEC_CHECKER = "pytest-v1"      # named in the digest row: this percent is not `number`/`letter`

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pub_bench_score import call_label, digest_row, write_digest  # noqa: E402  (one digest format)


def strip_code(ans):
    """Take code out of a chat answer: prefer a fenced block, else the whole text."""
    blocks = re.findall(r"```(?:python)?\n(.*?)```", ans or "", re.S)
    return ("\n\n".join(blocks) if blocks else (ans or "")).strip()


def entry_point(prompt):
    names = re.findall(r"(?m)^def\s+([A-Za-z_]\w*)\s*\(", prompt or "")
    return names[-1] if names else None


def compose(prompt, completion, entry):
    """Two answer shapes are accepted and told apart explicitly: a full function (the normal chat
    answer, which redefines the prompt's stub) or a body-only completion, which gets the prompt's
    indentation back. The earlier version stripped the body's leading indent and produced an
    IndentationError - caught only because the checker has a self-test."""
    if re.search(r"(?m)^def\s+%s\b" % re.escape(entry or ""), completion or ""):
        return "%s\n%s" % (prompt, completion)
    lines = (completion or "").splitlines()
    first = next((l for l in lines if l.strip()), "")
    if first[:1] in (" ", "\t"):                    # body already carries the prompt indent
        body = "\n".join(lines)
    else:
        body = "\n".join(("    " + l if l.strip() else l) for l in lines)
    return "%s\n%s\n" % (prompt, body)


def run_case(prompt, completion, test, entry):
    # program = stub + answer + upstream test block + the call into the candidate
    src = "%s\n%s\ncheck(%s)\n" % (compose(prompt, completion, entry), test, entry)
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "t.py")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(src)

        def limit():
            resource.setrlimit(resource.RLIMIT_AS, (768 << 20, 768 << 20))
            resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
            resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
            resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
        try:
            r = subprocess.run([sys.executable, "-I", "-B", p], cwd=td, timeout=TIMEOUT,
                               capture_output=True, text=True, preexec_fn=limit,
                               env={"PYTHONIOENCODING": "utf-8"})
        except subprocess.TimeoutExpired:
            return False, "timeout"
        ok = r.returncode == 0
        return ok, ((r.stderr or r.stdout or "").strip().splitlines() or [""])[-1][:200]


def selftest():
    """The checker must separate a correct from a wrong completion on HumanEval/0."""
    tasks = {}
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "benchmarks", "public", "humaneval.tasks.jsonl")
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        tasks[d["id"]] = d
    t = tasks["humaneval-0000"]
    meta = t["meta"] if isinstance(t["meta"], dict) else json.loads(t["meta"])
    entry = entry_point(t["prompt"])
    gold = t["gold"]
    good, e1 = run_case(t["prompt"], gold, meta["test"], entry)
    bad, e2 = run_case(t["prompt"], "def has_close_elements(numbers, threshold):\n    return False",
                       meta["test"], entry)
    print("selftest entry=%s reference_passes=%s wrong_passes=%s" % (entry, good, bad))
    if good and not bad:
        print("checker self-test OK")
        return 0
    print("checker self-test FAILED: ref_err=%r wrong_err=%r" % (e1, e2))
    return 1


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "selftest":
        return selftest()
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    tasks_f, ans_f = sys.argv[1], sys.argv[2]
    if selftest() != 0:
        print("refusing to score: checker self-test failed")
        return 1
    tasks = {}
    for line in open(tasks_f, encoding="utf-8"):
        d = json.loads(line)
        tasks[d["id"]] = d
    ans = {}
    for line in open(ans_f, encoding="utf-8"):
        d = json.loads(line)
        if d["id"] not in ans:
            ans[d["id"]] = d
    ok = n = missing = 0
    fails = []
    for tid, t in sorted(tasks.items()):
        a = ans.get(tid)
        if not a or not (a.get("answer") or "").strip():
            missing += 1
            continue
        meta = t["meta"] if isinstance(t["meta"], dict) else json.loads(t["meta"])
        entry = meta.get("entry_point") or entry_point(t["prompt"])
        if not entry:
            fails.append((tid, "no entry point in prompt"))
            n += 1
            continue
        n += 1
        passed, err = run_case(t["prompt"], strip_code(a["answer"]), meta["test"], entry)
        ok += int(passed)
        if not passed:
            fails.append((tid, err))
    if missing > 0.05 * len(tasks):
        print("partial arm: %d/%d answers present - no percent printed" % (n - missing, len(tasks)))
        return 1
    print("humaneval %d/%d = %.1f%% (executed, checker %s)" % (ok, n, 100.0 * ok / max(n, 1), EXEC_CHECKER))
    for tid, err in fails[:12]:
        print("  FAIL %s %s" % (tid, err))
    model = next((a.get("model") for a in ans.values() if a.get("model")), "unknown")
    temp = next((a.get("temp") for a in ans.values() if a.get("temp") is not None), None)
    row = digest_row(
        os.path.basename(tasks_f).replace(".tasks.jsonl", ""), model, len(tasks),
        hashlib.sha256(open(tasks_f, "rb").read()).hexdigest()[:16],
        "%s; checker %s" % (call_label(list(ans.values()), temp), EXEC_CHECKER), ok, n)
    print("-> %s" % os.path.basename(write_digest(row)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
