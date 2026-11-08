#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score a public-benchmark arm deterministically and print/append its percent row.

Checkers are the point of this file: a public benchmark is only comparable across arms if the
scorer is fixed and public. `number`, `letter` and `exact` are implemented here; `pytest`
(HumanEval) and `ifeval` (instruction-following) are counted separately as UNSCORED until their
checkers ship, and the percent is then labelled "over the scored subset" instead of silently
dividing by the full task count. A missing answer counts as a loss, but an arm with >5% missing
answers is refused outright (partial arm, no percent).
"""
import hashlib
import json
import os
import re
import sys

NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
LET = re.compile(r"\b([A-J])\b")
FRAC = re.compile(r"^\s*(-?\d[\d,]*(?:\.\d+)?)\s*/\s*(-?\d[\d,]*(?:\.\d+)?)\s*$")
PLAIN_GOLD = re.compile(r"^-?\d[\d,]*(?:\.\d+)?$")

# Checker contract id. Bumped 08.11: `number` used to read a non-plain gold ("3/4", "72%")
# through the same last-number regex as an answer, so a fraction gold silently became its
# denominator and a false verdict was published. Now a gold this contract cannot parse
# returns None (UNSCORED, excluded from the denominator) instead of guessing, and an answer
# written as a fraction ("ANSWER: 3/4") is evaluated. On the pinned gsm8k set (1319/1319
# plain-integer golds, 0 answers with '/', '%' or '$' in the ANSWER line) both changes are
# verdict-neutral - proven by an old-vs-new rescore of every saved answer, not asserted.
CHECKER_CONTRACT = "pub-checkers-v2"


def norm_number(s):
    m = NUM.findall(str(s or ""))
    if not m:
        return None
    try:
        return float(m[-1].replace(",", ""))
    except ValueError:
        return None


def gold_number(g):
    s = str(g if g is not None else "").strip()
    if not PLAIN_GOLD.match(s):
        return None
    return float(s.replace(",", ""))


def answer_number(ans):
    # prefer an explicit ANSWER: line, else the last number in the text
    m = re.search(r"ANSWER:\s*([^\n]+)", ans or "", re.I)
    seg = m.group(1) if m else (ans or "")
    fm = FRAC.match(seg.split(" ")[0] if m else "")
    if fm:
        try:
            return float(fm.group(1).replace(",", "")) / float(fm.group(2).replace(",", ""))
        except ZeroDivisionError:
            return None
    return norm_number(seg)


def answer_letter(ans):
    m = re.search(r"ANSWER:\s*([A-J])\b", ans or "", re.I)
    if m:
        return m.group(1).upper()
    m = LET.search(ans or "")
    return m.group(1).upper() if m else None


def call_label(rows, temp):
    """Name the call parameters that were ACTUALLY used, never an assumed one.

    The local endpoint arm pins temperature/max_tokens and stores them; the cloud CLI arms do
    not expose sampling parameters at all, so printing `temp None` there would be a fabricated
    pin. Label the transport instead and say the parameters are not exposed.
    """
    if temp is not None:
        return "temp %s, max_tokens 1200" % temp
    tr = next((str(r.get("transport")) for r in rows if r.get("transport")), "")
    if tr:
        return "%s CLI (sampling params not exposed by the transport)" % tr
    return "parameters not recorded"


def check(checker, gold, ans):
    if checker == "number":
        g, a = gold_number(gold), answer_number(ans)
        if g is None:
            return None                           # gold outside this contract: unscored, not guessed
        return a is not None and abs(a - g) < 1e-6
    if checker == "letter":
        return answer_letter(ans) == str(gold).strip().upper()
    if checker == "exact":
        return (ans or "").strip().lower() == str(gold).strip().lower()
    return None


def selftest():
    """Checkers are only worth a percent if they separate right from wrong on known examples.

    Mirrors pub_bench_exec.py: the scorer refuses to publish anything while its own examples
    fail, so a regex edit cannot silently turn a benchmark into a scoring artifact.
    """
    cases = [
        # checker, gold, answer, expected (True win / False loss / None unscored)
        ("number", "72", "work...\nANSWER: 72", True),
        ("number", "72", "ANSWER: 73", False),
        ("number", "1200", "ANSWER: 1,200", True),
        ("number", "72", "I cannot solve this", False),
        ("number", "6,250", "ANSWER: 6250", True),
        ("number", "0.75", "ANSWER: 3/4", True),
        ("number", "3/4", "ANSWER: 0.75", None),
        ("number", "72%", "ANSWER: 72", None),
        ("letter", "C", "ANSWER: C", True),
        ("letter", "C", "the answer is (B)", False),
        ("letter", "C", "no letter here", False),
        ("exact", "hello", "  HELLO\n", True),
        ("exact", "hello", "hello world", False),
        ("pytest", "x", "def f(): pass", None),
        ("ifeval", "x", "anything", None),
    ]
    bad = [(ck, gold, exp, check(ck, gold, ans)) for ck, gold, ans, exp in cases
           if check(ck, gold, ans) is not exp]
    labels = [
        ([{"transport": "x"}], 0.7, lambda s: "temp 0.7" in s and "None" not in s),
        ([{"transport": "codex-cli 0.166.0"}], None,
         lambda s: "codex-cli" in s and "not exposed" in s and "None" not in s),
        ([], None, lambda s: "not recorded" in s and "None" not in s),
    ]
    bad += [("call_label", repr((rows, temp)), None, call_label(rows, temp))
            for rows, temp, ok in labels if not ok(call_label(rows, temp))]
    print("selftest cases=%d failures=%d" % (len(cases) + len(labels), len(bad)))
    for b in bad:
        print("  FAIL %s gold=%r expected=%r got=%r" % b)
    if bad:
        return 1
    print("scorer self-test OK")
    return 0


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "selftest":
        return selftest()
    if selftest() != 0:
        print("refusing to score: scorer self-test failed")
        return 1
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    tasks_f, res_f = sys.argv[1], sys.argv[2]
    limit, offset = None, 0
    rest = sys.argv[3:]
    for i, a in enumerate(rest):
        if a == "--limit":
            limit = int(rest[i + 1])
        elif a == "--offset":
            offset = int(rest[i + 1])
    all_tasks = [json.loads(l) for l in open(tasks_f, encoding="utf-8") if l.strip()]
    window = all_tasks[offset:offset + limit] if limit else all_tasks[offset:]
    tasks = {t["id"]: t for t in window}
    ans, model, temp = {}, "unknown", None
    for line in open(res_f, encoding="utf-8"):
        d = json.loads(line)
        if d["id"] not in ans:
            ans[d["id"]] = d
            model = d.get("model", model)
            temp = d.get("temp", temp)
    missing = [t for t in tasks if t not in ans or not (ans[t].get("answer") or "").strip()]
    if len(missing) > 0.05 * len(tasks):
        raise SystemExit("arm is partial: %d/%d answers present - no percent printed"
                         % (len(tasks) - len(missing), len(tasks)))
    by = {}
    for tid, t in tasks.items():
        b, ck = t["bench"], t["checker"]
        ok = check(ck, t["gold"], ans[tid].get("answer", ""))
        r = by.setdefault(b, {"scored": 0, "ok": 0, "unscored": 0})
        if ok is None:
            r["unscored"] += 1
        else:
            r["scored"] += 1
            r["ok"] += int(ok)
    print("checker contract: %s" % CHECKER_CONTRACT)
    for b, r in sorted(by.items()):
        pct = (100.0 * r["ok"] / r["scored"]) if r["scored"] else 0.0
        note = "" if not r["unscored"] else ("  [%d unscored, checker pending]" % r["unscored"])
        print("%-14s %4d/%4d = %5.1f%%  (answers %d/%d)%s"
              % (b, r["ok"], r["scored"], pct, len(tasks) - len(missing), len(tasks), note))
    row = "| %s | %s | %d | %s | %s | %d/%d = **%.1f%%** |" % (
        os.path.basename(tasks_f).replace(".tasks.jsonl", ""), model, len(tasks),
        hashlib.sha256(open(tasks_f, "rb").read()).hexdigest()[:16],
        call_label(list(ans.values()), temp),
        sum(r["ok"] for r in by.values()), sum(r["scored"] for r in by.values()),
        100.0 * sum(r["ok"] for r in by.values()) / max(sum(r["scored"] for r in by.values()), 1))
    dst = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "..", "benchmarks", "public", "PUB-DIGEST.md"))
    head = ("# Public benchmark percent digest\n\n"
            "One row per scored arm, newest first, written by `scripts/pub_bench_score.py`. "
            "Rows are only comparable when the task-file sha16 and the call parameters match; "
            "unscored checkers (pytest, ifeval) are excluded from the denominator and named. "
            "Checker contract in force: `%s` - the scorer refuses to publish while its own "
            "self-test fails, and a gold the contract cannot parse is scored as UNSCORED, never "
            "guessed. A row re-scored under another contract id is a new row, not an edit.\n\n"
            % CHECKER_CONTRACT)
    hdr = "| bench | model | tasks | tasks sha16 | call | strict |\n|---|---|---|---|---|---|"
    old = open(dst, encoding="utf-8").read() if os.path.exists(dst) else ""
    body = [l for l in old.splitlines() if l.startswith("| ") and "bench |" not in l
            and not set(l) <= set("|- ")]
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(head + hdr + "\n" + "\n".join([row] + body) + "\n")
    print("-> %s" % os.path.basename(dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
