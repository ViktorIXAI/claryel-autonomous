#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seed-variance report for one contour stamp measured over several repetitions.

One rep cannot separate an effect from seed noise: the published pairs show 3W/1L-type steps, and
the H probe showed single cells moving 1.00/0.33/1.00 between identical repetitions. This script
takes the PUBLISHED ledgers of the same stamp under different gseeds and reports, per repetition:
plain strict, loop strict, model calls, tokens and wall seconds; then per cell how many reps pass
(stable / unstable), and the exact paired sign test between every pair of repetitions.

Usage: python3 scripts/rep_variance_v6.py LEDGER1 [LEDGER2 ...]
A ledger file may hold several repetitions; each rep inside it becomes one row.
"""
import collections
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")


def strict(r):
    return (r.get("content") or 0) == 1.0 and bool(r.get("format_ok"))


def sign_test(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    return min(1.0, sum(math.comb(n, i) for i in range(0, k + 1)) * 2 / (2 ** n))


def load(path, loop_ids):
    by_rep = collections.defaultdict(dict)
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        if "_loop_rows" in r:
            continue
        by_rep[r["rep"]][(r["task"], r["rep"])] = r
    out = []
    for rep in sorted(by_rep):
        rows = by_rep[rep]
        pl = [r for k, r in rows.items() if k[0] not in loop_ids]
        lp = [r for k, r in rows.items() if k[0] in loop_ids]
        out.append({
            "label": "rep%s" % rep,
            "path": os.path.basename(path),
            "cells": {k[0]: strict(r) for k, r in rows.items() if k[0] not in loop_ids},
            "plain": sum(strict(r) for r in pl), "plain_n": len(pl),
            "loop": sum(strict(r) for r in lp), "loop_n": len(lp),
            "calls": sum(r.get("model_calls", 0) for r in rows.values()),
            "ptok": sum(r.get("ptok", 0) for r in rows.values()),
            "ctok": sum(r.get("ctok", 0) for r in rows.values()),
            "sec": round(sum(r.get("seconds", 0) for r in rows.values()), 1),
        })
    return out


def main() -> int:
    paths = sys.argv[1:]
    if len(paths) < 2:
        print(__doc__)
        return 2
    bank = {t["id"]: t for t in json.load(open(BANK, encoding="utf-8"))}
    loop_ids = {k for k in bank if bank[k].get("mode") == "loop"}
    reps = []
    for p in paths:
        reps += load(p, loop_ids)
    print("repetitions of the same stamp (different gseeds):")
    for r in reps:
        print("  %-6s plain %2d/%d  loop %d/%d  calls %3d  ptok %6d  ctok %5d  wall %6.1fs" % (
            r["label"], r["plain"], r["plain_n"], r["loop"], r["loop_n"], r["calls"],
            r["ptok"], r["ctok"], r["sec"]))
    totals = [r["plain"] for r in reps]
    print("plain strict across reps: %s  spread=%d  mean=%.2f" % (
        totals, max(totals) - min(totals), sum(totals) / float(len(totals))))

    ids = sorted(set().union(*[set(r["cells"]) for r in reps]))
    stable_pass, stable_fail, unstable = [], [], []
    for tid in ids:
        vals = [r["cells"].get(tid) for r in reps]
        if all(vals):
            stable_pass.append(tid)
        elif not any(vals):
            stable_fail.append(tid)
        else:
            unstable.append(tid)
    print("\nover %d cells: stable pass %d, stable fail %d, seed-unstable %d" % (
        len(ids), len(stable_pass), len(stable_fail), len(unstable)))
    if unstable:
        print("seed-unstable cells: " + ", ".join(unstable))

    print("\npaired sign tests between repetitions (same stamp, different seeds):")
    for i in range(len(reps)):
        for j in range(i + 1, len(reps)):
            a, b = reps[i], reps[j]
            w = l = 0
            for tid in ids:
                x, y = a["cells"].get(tid), b["cells"].get(tid)
                if x and not y:
                    l += 1
                elif y and not x:
                    w += 1
            print("  %s vs %s: %d wins / %d losses  exact p=%.4f" % (
                b["label"], a["label"], w, l, sign_test(w, l)))
    print("\nBound: the rep-to-rep spread is the noise floor. A stamp-to-stamp or arm-to-arm delta"
          " inside that band cannot be attributed to the stamp or the contour.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
