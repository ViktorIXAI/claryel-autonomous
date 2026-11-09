#!/usr/bin/env python3
"""IFEval scorer contract `pub-ifeval-v1`: the upstream Google Research checker, vendored as shipped.

IFEval is instruction following, not answer matching: each task carries a list of instruction ids
plus keyword arguments, and the verdict is the conjunction of per-instruction checks. Only the
vendor's own code may produce that verdict, so this wrapper imports the vendored modules and refuses
to score anything until two self-tests pass:

  1. the upstream unit suite (`instructions_test.py`, 41 tests) runs green in this environment,
     within `SUITE_ATTEMPTS` = 3 attempts — one vendor test (`test_english_capital_checker`) is
     nondeterministic because the checker it exercises calls langdetect; the retry and the measured
     flake rate are documented on `SUITE_ATTEMPTS`;
  2. the upstream reference responses (the GPT-4 sample shipped next to the data) score at the
     recorded band: strict 416/540 = 77.0 % and loose 431/540 = 79.8 %.

The band test is what stops a silent environment break (a missing NLTK word list, a changed
language detector) from quietly turning a real arm into a 0 % arm. If either self-test fails the
scorer exits with a reason and writes no digest row.

Strict is the headline verdict; loose (which tolerates a missing leading/trailing markdown marker
only) is published beside it as a second column, never mixed into the same cell.

Run:  pub_bench_ifeval.py <answers.jsonl> <tasks.jsonl> <bench> <model> <call-label> [--out DIR]
"""
import argparse
import collections
import hashlib
import json
import pathlib
import subprocess
import sys

CHECKER = "pub-ifeval-v1"
HERE = pathlib.Path(__file__).resolve().parent
VENDOR = HERE.parent / "benchmarks" / "public" / "vendor"
REF_STRICT, REF_LOOSE, REF_N = 416, 431, 540
REF_BAND_PP = 2.0  # recorded reference may drift only inside this band, else the env is broken
# Gate 1 is retried, and the reason is published, because the vendor's own suite is not
# deterministic. Measured 2026-11-09, eight suite runs in the pinned venv: 2 failed on exactly one
# test, `test_english_capital_checker`, with the environment intact (the reference band scored
# 417/540 strict in the same session). Root cause is in the vendor's code, not ours:
# `instructions.CapitalLettersEnglishChecker` calls langdetect, which is stochastic on short or
# ambiguous text, so the same bytes can pass or fail that test. The band gate below stays a single
# pass, because a real environment break (missing NLTK word list, dead detector) moves the reference
# score by far more than one flaky unit test ever could.
SUITE_ATTEMPTS = 3
# Measured drift of the vendor checker itself, three runs over identical bytes on 2026-11-09:
# strict 416, 417, 417; loose 431, 430, 431. The upstream checker calls langdetect, which is
# stochastic on ambiguous text, so IFEval carries about one flipping task per 540 runs: any IFEval
# delta under ~0.5 pp is checker noise, not a model difference. The band absorbs that; a real
# environment break (missing NLTK word list, dead language detector) moves far more and is refused.


def sha16(p):
    return hashlib.sha1(pathlib.Path(p).read_bytes()).hexdigest()[:16]


def load_vendor():
    sys.path.insert(0, str(VENDOR))
    from instruction_following_eval import evaluation_lib as ev  # noqa: F401
    return ev


def selftest(ev):
    """Both gates must pass; returns (ok, reason)."""
    suite_note, last_fail = "", ""
    suite_ok = False
    for attempt in range(1, SUITE_ATTEMPTS + 1):
        proc = subprocess.run([sys.executable, "-m", "unittest",
                               "instruction_following_eval.instructions_test", "-v"],
                              cwd=str(VENDOR), capture_output=True, text=True)
        tail = (proc.stderr or proc.stdout).strip().splitlines()
        ran = next((l for l in tail if l.startswith("Ran ")), "Ran ?")
        if proc.returncode == 0:
            suite_ok = True
            suite_note = ("unit suite %s, green on attempt %d of %d" % (ran, attempt, SUITE_ATTEMPTS)
                          if attempt > 1 else "unit suite %s" % ran)
            break
        names = [l.split(" ")[1] for l in tail if l.startswith("FAIL:")]
        last_fail = "%s | %s" % (", ".join(names) or (tail[-1] if tail else ""), ran)
    if not suite_ok:
        return False, ("upstream unit suite failed on all %d attempts: %s"
                       % (SUITE_ATTEMPTS, last_fail))
    data = VENDOR / "instruction_following_eval" / "data"
    tasks = [json.loads(l) for l in (data / "input_data.jsonl").read_text().splitlines()]
    ref_path = data / "gpt4_sample.jsonl"
    if not ref_path.exists():
        return False, "reference response file missing: %s" % ref_path
    prompts = {t["prompt"] for t in tasks}
    p2r = {r["prompt"]: r["response"] for r in
           (json.loads(l) for l in ref_path.read_text().splitlines()) if r["prompt"] in prompts}
    inps = [ev.InputExample(key=t["key"], instruction_id_list=t["instruction_id_list"],
                            prompt=t["prompt"], kwargs=t["kwargs"])
            for t in tasks if t["prompt"] in p2r]
    s = sum(1 for i in inps if ev.test_instruction_following_strict(i, p2r).follow_all_instructions)
    lo = sum(1 for i in inps if ev.test_instruction_following_loose(i, p2r).follow_all_instructions)
    n = len(inps)
    if n != REF_N:
        return False, "reference set joined %d prompts, expected %d (upstream bytes changed?)" % (n, REF_N)
    for name, got, want in (("strict", s, REF_STRICT), ("loose", lo, REF_LOOSE)):
        if abs(100.0 * (got - want) / n) > REF_BAND_PP:
            return False, "reference %s moved: %d/%d = %.1f %% vs recorded %d/%d = %.1f %%" % (
                name, got, n, 100.0 * got / n, want, n, 100.0 * want / n)
    return True, "%s; reference strict %d/%d, loose %d/%d" % (suite_note, s, n, lo, n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("answers"); ap.add_argument("tasks")
    ap.add_argument("bench"); ap.add_argument("model"); ap.add_argument("call")
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest-only", action="store_true")
    a = ap.parse_args()

    if str(VENDOR) not in sys.path:
        sys.path.insert(0, str(VENDOR))
    ev = load_vendor()
    ok, why = selftest(ev)
    if not ok:
        sys.exit("REFUSING TO SCORE: %s" % why)
    print("self-test: %s" % why)
    if a.selftest_only:
        return

    tasks = [json.loads(l) for l in pathlib.Path(a.tasks).read_text().splitlines()]
    by_prompt = {t["prompt"]: t for t in tasks}
    ans = {}
    for line in pathlib.Path(a.answers).read_text().splitlines():
        r = json.loads(line)
        ans.setdefault(r["id"], r.get("answer", ""))

    missing = [t["id"] for t in tasks if t["id"] not in ans]
    if len(missing) > 0.05 * len(tasks):
        sys.exit("REFUSING TO SCORE: arm is partial - %d/%d answers present" % (len(tasks) - len(missing), len(tasks)))

    p2r = {t["prompt"]: ans[t["id"]] for t in tasks if t["id"] in ans}
    per_task, rows = [], []
    fails = collections.Counter()
    for t in tasks:
        if t["id"] not in ans:
            continue
        inp = ev.InputExample(key=int(t["id"].rsplit("-", 1)[1]),
                              instruction_id_list=t["instruction_id_list"],
                              prompt=t["prompt"], kwargs=t["kwargs"])
        s = ev.test_instruction_following_strict(inp, p2r)
        lo = ev.test_instruction_following_loose(inp, p2r)
        per_task.append((t["id"], bool(s.follow_all_instructions), bool(lo.follow_all_instructions),
                         list(s.follow_instruction_list)))
        for cid, okc in zip(t["instruction_id_list"], s.follow_instruction_list):
            if not okc:
                fails[cid] += 1
        rows.append({"id": t["id"], "strict": bool(s.follow_all_instructions),
                     "loose": bool(lo.follow_all_instructions),
                     "per_instruction": list(s.follow_instruction_list)})

    n = len(per_task)
    st = sum(1 for r in per_task if r[1])
    ls = sum(1 for r in per_task if r[2])
    checks = sum(len(r[3]) for r in per_task)
    checks_ok = sum(sum(1 for x in r[3] if x) for r in per_task)
    print("%s %s n=%d strict %d/%d = %.1f %% | loose %d/%d = %.1f %% | instruction checks %d/%d = %.1f %%"
          % (a.bench, CHECKER, n, st, n, 100.0 * st / n, ls, n, 100.0 * ls / n, checks_ok, checks,
             100.0 * checks_ok / checks))
    print("hardest checks:", ", ".join("%s=%d" % kv for kv in fails.most_common(6)))
    out = pathlib.Path(a.out or str(pathlib.Path(a.answers).parent))
    (out / ("%s-%s-verdicts.jsonl" % (a.bench, CHECKER))).write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n")
    (out / ("%s-%s-verdicts.sha16" % (a.bench, CHECKER))).write_text(
        hashlib.sha1((out / ("%s-%s-verdicts.jsonl" % (a.bench, CHECKER))).read_bytes()).hexdigest()[:16] + "\n")

    dig = HERE.parent / "benchmarks" / "public" / "PUB-DIGEST.md"
    task_sha = sha16(a.tasks)
    # One writer, one format: the row goes through `pub_bench_score.write_digest`, which owns the
    # table header, the newest-first order and the separator line. The partition hack that used to
    # live here inserted the row ABOVE the `|---|` separator (a table GitHub renders as prose) and
    # let the header drift from the contract in force.
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import pub_bench_score as pbs                                # noqa: E402
    line = ("| %s | %s | %d | %s | %s; checker %s | %d/%d = **%.1f%%** strict (%d/%d loose) |"
            % (a.bench, a.model, n, task_sha, a.call, CHECKER, st, n, 100.0 * st / n, ls, n))
    key = "\n| %s | %s | %d | %s |" % (a.bench, a.model, n, task_sha)
    body = dig.read_text() if dig.exists() else ""
    if key in body:
        print("digest row already present - not duplicated")
    else:
        pbs.write_digest(line, str(dig))
        print("digest row appended")


if __name__ == "__main__":
    main()
