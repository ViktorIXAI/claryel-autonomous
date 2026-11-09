#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A/B rescore of HumanEval arms under pytest-v1 vs pytest-v2 on the SAME stored answer bytes.

Publishes no digest row; it prints the per-arm percents and the per-cell flip table (v2 flips
can only be 0->1 by construction: extract_code keeps the v1 bytes whenever they compile).
Used for the checker-correction table in benchmarks/public/HUMANEVAL-RESULT.md.

Usage: pub_exec_v2_ab.py <tasks.jsonl> <label>=<answers.jsonl> [...]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pub_bench_exec import (EXEC_CHECKER, entry_point, extract_code, run_case,
                            selftest, strip_code)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    if selftest() != 0:
        print("refusing: checker self-test failed")
        return 1
    tasks = {}
    for line in open(sys.argv[1], encoding="utf-8"):
        d = json.loads(line)
        tasks[d["id"]] = d
    for spec in sys.argv[2:]:
        label, ans_f = spec.split("=", 1)
        ans = {}
        for line in open(ans_f, encoding="utf-8"):
            d = json.loads(line)
            if d["id"] not in ans:
                ans[d["id"]] = d
        v1_pass, v2_pass, flips = set(), set(), []
        for tid in sorted(tasks):
            a = ans.get(tid)
            if not a or not (a.get("answer") or "").strip():
                continue
            t = tasks[tid]
            meta = t["meta"] if isinstance(t["meta"], dict) else json.loads(t["meta"])
            entry = meta.get("entry_point") or entry_point(t["prompt"])
            p1, _ = run_case(t["prompt"], strip_code(a["answer"]), meta["test"], entry)
            p2, e2 = run_case(t["prompt"],
                              extract_code(a["answer"], t["prompt"], entry),
                              meta["test"], entry)
            if p1:
                v1_pass.add(tid)
            if p2:
                v2_pass.add(tid)
            if p2 and not p1:
                flips.append(tid)
        n = len(ans)
        print("%s: v1 %d/%d  v2 %d/%d  flips(+%d): %s"
              % (label, len(v1_pass), n, len(v2_pass), n, len(flips),
                 ",".join(t.replace("humaneval-", "") for t in flips) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
