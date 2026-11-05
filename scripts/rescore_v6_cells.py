#!/usr/bin/env python3
"""Rescore published hard-v6 arms on saved answer bytes (no model calls).

Why: contour stamps before 0.0.2.21 routed the three plain-D hard-v6 tasks
(D-ex6-p0/p1/p2) through the loop trajectory scorer, so their published per-arm
plain totals understate those cells. The answer bytes are published in the repo,
so the correction is a deterministic rescore with the frozen checker, not a new
model run. Writes v6-results/RESCORE-PLAIN-D.json and prints a table.
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "harness"))
from parb_check_v6 import check_D_plain_v6  # noqa: E402

RES = os.path.join(ROOT, "benchmarks", "hard", "v6-results")
BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")


def strict(content, fmt_ok):
    return 1 if float(content) == 1.0 and bool(fmt_ok) else 0


def plain_d_tasks():
    rows = json.load(open(BANK, encoding="utf-8"))
    if not isinstance(rows, list):
        rows = rows.get("tasks", [])
    return {t["id"]: t for t in rows
            if t.get("cat") == "D" and t.get("mode") != "loop"}


def stamp_of(dirname):
    # arm dir "full-216" is contour stamp 0.0.2.16 (axis 2, revision 16)
    digits = dirname.split("full-")[1]
    return "0.0.2." + (digits[1:] if digits.startswith("2") else digits)


def arm_rows(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        if r.get("task"):
            rows.append(r)
    return rows


def main():
    tasks = plain_d_tasks()
    out = []
    for d in sorted(glob.glob(os.path.join(RES, "full-2*")), key=stamp_of):
        led = sorted(glob.glob(os.path.join(d, "ledger-*.jsonl")))
        res = sorted(glob.glob(os.path.join(d, "results-*.jsonl")))
        if not led or not res:
            continue
        lrows = arm_rows(led[0])
        plain = [r for r in lrows if not r["task"].startswith("D-ex6-l")]
        as_run_plain = sum(strict(r["content"], r.get("format_ok")) for r in plain)
        as_run_d = {(r["task"], r["rep"]): strict(r["content"], r.get("format_ok"))
                    for r in plain if r["task"] in tasks}
        answers = {(r["task"], r["rep"]): r.get("answer")
                   for r in arm_rows(res[0]) if r["task"] in tasks}
        cells, delta = [], 0
        for (tid, rep), ans in sorted(answers.items()):
            score, fmt, notes = check_D_plain_v6(tasks[tid], ans or "")
            good = strict(score, fmt)
            was = as_run_d.get((tid, rep), 0)
            delta += good - was
            cells.append({"task": tid, "rep": rep, "as_run_strict": was,
                          "rescored_score": score, "rescored_fmt": bool(fmt),
                          "rescored_strict": good, "notes": notes})
        out.append({"arm": os.path.basename(d), "stamp": stamp_of(d),
                    "plain_rows": len(plain), "plain_as_run": as_run_plain,
                    "plain_corrected": as_run_plain + delta,
                    "d_plain_as_run": sum(as_run_d.values()),
                    "d_plain_rescored": sum(c["rescored_strict"] for c in cells),
                    "delta": delta, "cells": cells})
        print(f"{stamp_of(d):>10}  plain {as_run_plain:>2}/{len(plain)} -> "
              f"{as_run_plain + delta:>2}  | D-plain {sum(as_run_d.values())}"
              f"->{sum(c['rescored_strict'] for c in cells)} of {len(cells)}")
    with open(os.path.join(RES, "RESCORE-PLAIN-D.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("\nwrote v6-results/RESCORE-PLAIN-D.json")


if __name__ == "__main__":
    main()
