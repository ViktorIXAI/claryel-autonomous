#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paired contour stamps on identical seeds: does 0.0.2.30 (contract guarantee) kill the coin flips?

The stability map said 14 of 71 single-shot cells flip between seeds and 12 of them die on a parse
collapse. A mean-only comparison cannot show that a mechanism did that: two arms with the same mean but
different flip counts are different machines. This script reports, per cell, the pass pattern of each stamp
across its seeds, the flip count per stamp, and what the guarantee actually touched (its ledger events).

Usage: python3 scripts/pair_stability_v61.py WS_DIR > PAIR-230-V61.md
"""
import collections
import glob
import importlib.util
import json
import os
import sys
from math import comb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, "missing harness module: " + path
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CK = _load("ck", os.path.join(ROOT, "harness", "parb_check_v6.py"))


def strict(c, f):
    return c == 1.0 and bool(f)


def sign_test(w, l):
    n = w + l
    if n == 0:
        return 1.0
    tail = sum(comb(n, k) for k in range(w, n + 1)) / 2.0 ** n
    return min(1.0, 2 * tail)


def main() -> int:
    ws = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/parb-v61-contour")
    # Two arms are named by their run-id prefix (control, candidate): c29/c30 for the 2.30 pair,
    # d29/d31 for the 2.31 pair. Keeping the prefixes explicit stops a new pair silently reusing
    # the previous pair's ledgers.
    pref_a = sys.argv[2] if len(sys.argv) > 2 else "c29"
    pref_b = sys.argv[3] if len(sys.argv) > 3 else "c30"
    label_a = "0.0.2." + pref_a[1:]
    label_b = "0.0.2." + pref_b[1:]
    bank = {t["id"]: t for t in json.load(open(BANK, encoding="utf-8"))}
    loop = {k for k in bank if bank[k].get("mode") == "loop"}
    arms = collections.defaultdict(dict)   # stamp -> rep -> {task: bool}
    ev_hist = collections.defaultdict(collections.Counter)
    calls = collections.Counter()
    wall = {}
    for p in sorted(glob.glob(os.path.join(ws, "ledger-%sr*.jsonl" % pref_a))) + sorted(
            glob.glob(os.path.join(ws, "ledger-%sr*.jsonl" % pref_b))):
        base = os.path.basename(p)
        stamp = label_a if pref_a in base else label_b
        rep = base.split("r")[-1].split(".")[0]
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            if r["task"] in loop or "_loop_rows" in r:
                continue
            arms[stamp].setdefault(rep, {})[r["task"]] = strict(r.get("content") or 0,
                                                                r.get("format_ok"))
            for e in r.get("events") or []:
                ev_hist[stamp][e] += 1
            calls[stamp] += int(r.get("model_calls") or 1)
        rec = os.path.join(ws, "run-record-%s.json" % base.replace("ledger-", ""))
        if os.path.exists(rec):
            j = json.load(open(rec, encoding="utf-8"))
            wall[stamp] = wall.get(stamp, 0) + int(j.get("wall_s") or 0)
    stamps = [label_a, label_b] if label_a in arms and label_b in arms else sorted(arms)
    if len(stamps) < 2:
        print("need ledgers for both stamps; found:", stamps)
        return 1
    reps = sorted(set(arms[stamps[0]]) & set(arms[stamps[1]]))
    cells = sorted(set.intersection(*[set(arms[s][r]) for s in stamps for r in reps]))
    print("# Paired contour arms on identical seeds (bank v6.1, %d single-shot cells, seeds %s)" % (
        len(cells), ", ".join(reps)))
    print()
    print("| stamp | per-seed total | mean | cells flipping across seeds | model calls | wall s |")
    print("|---|---|---|---|---|---|")
    flip = {}
    for s in stamps:
        vals = [sum(1 for t in cells if arms[s][r][t]) for r in reps]
        f = [t for t in cells if 0 < sum(1 for r in reps if arms[s][r][t]) < len(reps)]
        flip[s] = set(f)
        print("| %s | %s | %.1f | %d of %d | %d | %d |" % (
            s, ", ".join(str(v) for v in vals), sum(vals) / len(vals), len(f), len(cells),
            calls[s], wall.get(s, 0)))
    print()
    print("## Cell by cell (P = passed that seed, . = failed)")
    print()
    print("| cell | %s | %s | change |" % (stamps[0], stamps[1]))
    print("|---|---|---|---|")
    both = []
    for t in sorted(cells):
        a = "".join("P" if arms[stamps[0]][r][t] else "." for r in reps)
        b = "".join("P" if arms[stamps[1]][r][t] else "." for r in reps)
        na, nb = a.count("P"), b.count("P")
        if na == nb:
            continue
        both.append(t)
        tag = "stabilized" if nb == len(reps) and na < len(reps) else (
            "unstable both" if 0 < nb < len(reps) else "broken")
        print("| %s (%s) | %s | %s | %s: %d/%d -> %d/%d |" % (
            t, bank[t]["cat"], a, b, tag, na, len(reps), nb, len(reps)))
    if not both:
        print("| (no cell changed) | | | |")
    print()
    print("## What the guarantee touched")
    print()
    for s in stamps:
        # Show every contour event of the CANDIDATE stamp (the one under test), not a hardcoded tag: a
        # previous version filtered on "v230" and hid the fact that 0.0.2.31 had fired 8 votes.
        # Events are tagged by the stamp that FIRST shipped the mechanism (0.0.2.31 -> v231_*), so a
        # RE-LANDED mechanism keeps its original name — filtering only on the candidate tag hid the single
        # v233_a_tariff_table fire in pair-238 and printed "none". Own-tag and other-tag events are listed
        # separately so a re-land stays visible instead of looking like a no-op stamp.
        tag = "v2" + s.split(".")[-1] + "_"
        mech = {k: v for k, v in ev_hist[s].items() if "v2" in k and "_" in k}
        own = {k: v for k, v in mech.items() if tag in k}
        other = {k: v for k, v in mech.items() if tag not in k}
        line = ", ".join("%s x%d" % (k, v) for k, v in sorted(own.items())) or "none"
        if other:
            line += ("  |  other-tag contour events (inherited or RE-LANDED mechanism, event keeps its "
                     "origin name): " + ", ".join("%s x%d" % (k, v) for k, v in sorted(other.items())))
        print("- %s: %s" % (s, line))
    print()
    print("## Paired sign test per matched seed (strict pass, single-shot cells)")
    for r in reps:
        w = sum(1 for t in cells if arms[stamps[1]][r][t] and not arms[stamps[0]][r][t])
        l = sum(1 for t in cells if arms[stamps[0]][r][t] and not arms[stamps[1]][r][t])
        print("- seed %s: %s %d vs %s %d, W%02d L%02d p=%.4f" % (
            r, stamps[1], sum(1 for t in cells if arms[stamps[1]][r][t]),
            stamps[0], sum(1 for t in cells if arms[stamps[0]][r][t]),
            w, l, sign_test(w, l)))
    print()
    print("Reading rule: the flip count is the claim. A stamp with the same mean but fewer flips is a more")
    print("reliable machine, and per-cell rows above show exactly which cells stopped flipping. If the")
    print("candidate also raises the mean, that is the same effect counted twice — report both, do not add them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
