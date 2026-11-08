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


def norm_number(s):
    m = NUM.findall(str(s or ""))
    if not m:
        return None
    try:
        return float(m[-1].replace(",", ""))
    except ValueError:
        return None


def answer_number(ans):
    # prefer an explicit ANSWER: line, else the last number in the text
    m = re.search(r"ANSWER:\s*([^\n]+)", ans or "", re.I)
    return norm_number(m.group(1) if m else ans)


def answer_letter(ans):
    m = re.search(r"ANSWER:\s*([A-J])\b", ans or "", re.I)
    if m:
        return m.group(1).upper()
    m = LET.search(ans or "")
    return m.group(1).upper() if m else None


def check(checker, gold, ans):
    if checker == "number":
        g, a = norm_number(gold), answer_number(ans)
        return a is not None and g is not None and abs(a - g) < 1e-6
    if checker == "letter":
        return answer_letter(ans) == str(gold).strip().upper()
    if checker == "exact":
        return (ans or "").strip().lower() == str(gold).strip().lower()
    return None


def main():
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
    for b, r in sorted(by.items()):
        pct = (100.0 * r["ok"] / r["scored"]) if r["scored"] else 0.0
        note = "" if not r["unscored"] else ("  [%d unscored, checker pending]" % r["unscored"])
        print("%-14s %4d/%4d = %5.1f%%  (answers %d/%d)%s"
              % (b, r["ok"], r["scored"], pct, len(tasks) - len(missing), len(tasks), note))
    row = "| %s | %s | %d | %s | %s | %d/%d = **%.1f%%** |" % (
        os.path.basename(tasks_f).replace(".tasks.jsonl", ""), model, len(tasks),
        hashlib.sha256(open(tasks_f, "rb").read()).hexdigest()[:16],
        "temp %s" % temp,
        sum(r["ok"] for r in by.values()), sum(r["scored"] for r in by.values()),
        100.0 * sum(r["ok"] for r in by.values()) / max(sum(r["scored"] for r in by.values()), 1))
    dst = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "..", "benchmarks", "public", "PUB-DIGEST.md"))
    head = ("# Public benchmark percent digest\n\n"
            "One row per scored arm, newest first, written by `scripts/pub_bench_score.py`. "
            "Rows are only comparable when the task-file sha16 and the call parameters match; "
            "unscored checkers (pytest, ifeval) are excluded from the denominator and named.\n\n")
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
