#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emit additional-repetition plan rows for the hard-v6 runner (issue #8 protocol).

One rep per stamp cannot separate a contour effect from seed variance: the CROSSCHECK note and the
H probe both show the same cell flipping 1.00/0.33/1.00 across identical repetitions. Extra reps use
FRESH gseeds derived deterministically from (task, rep) with the same hash convention as
scripts/fresh100_build_ws.py, so any third party can re-derive the exact seed set from this file.

Usage: python3 scripts/plan_reps.py <bank.json> <rep> [<rep> ...] > plan-repNN.json
"""
import hashlib
import json
import sys


def gseed(task_id: str, rep: int) -> int:
    return int(hashlib.sha256(("%s|%d" % (task_id, rep)).encode()).hexdigest()[:8], 16) % 999983


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    bank = json.load(open(sys.argv[1], encoding="utf-8"))
    reps = [int(x) for x in sys.argv[2:]]
    rows = []
    for rep in reps:
        for t in bank:
            rows.append({
                "task": t["id"], "cat": t["cat"], "rep": rep, "rep_group": "hardv6",
                "series": "main", "stage": "main", "level": t.get("level", "ex6"),
                "gseed": gseed(t["id"], rep),
                "mode": "loop" if t.get("mode") == "loop" else "plain",
            })
    json.dump(rows, sys.stdout, ensure_ascii=False, indent=1)
    print("", file=sys.stderr)
    print("rows=%d reps=%s seeds[0:3]=%s" % (
        len(rows), reps, [(r["task"], r["rep"], r["gseed"]) for r in rows[:3]]), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
