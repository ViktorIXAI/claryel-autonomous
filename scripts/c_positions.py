#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Issue #15 checkbox: C options must sit at varied positions, and the distribution of correct
answer positions must be reported (v5 leaked the correct answer into leading letters).

Writes benchmarks/hard/v6-results/C-POSITIONS.md. Fails if any letter is the correct answer in
more than 80% of C tasks (the v5 leak pattern).
"""
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")
OUT = os.path.join(ROOT, "benchmarks", "hard", "v6-results", "C-POSITIONS.md")

bank = json.load(open(BANK, encoding="utf-8"))
tasks = [t for t in bank if t["cat"] == "C"]
first_pos = collections.Counter()
letters = collections.Counter()
rows = []
for t in tasks:
    ref = t.get("ref") or {}
    want = list(ref.get("letters") or [])
    n = int(ref.get("n_cand") or 0)
    if not want:
        rows.append((t["id"], "-", "-", "no_ref_letters"))
        continue
    positions = [ord(x) - ord("A") + 1 for x in want]
    first_pos[positions[0]] += 1
    for x in want:
        letters[x] += 1
    rows.append((t["id"], n, ",".join(want), "positions " + ",".join(str(p) for p in positions)))

total = len([r for r in rows if r[3] != "no_ref_letters"])
worst = max(first_pos.values()) if first_pos else 0
share = (worst / total) if total else 0.0

lines = ["# C answer-position distribution (bank v6.1)", "",
         "The v5 bank put the correct C option in the same leading position across tasks (issue #15).",
         "Distribution of the FIRST correct option's position over %d C tasks:" % total, "",
         "| first-correct position | tasks |",
         "|---|---|"]
for pos in sorted(first_pos):
    lines.append("| %d | %d |" % (pos, first_pos[pos]))
lines += ["", "Per-task detail:", "", "| task | options | correct | position(s) |", "|---|---|---|---|"]
for r in rows:
    lines.append("| %s | %s | %s | %s |" % r)
lines += ["", "Most-used first position share: **%.0f%%** (leak guard threshold 80%%)." % (100 * share), ""]
open(OUT, "w", encoding="utf-8").write("\n".join(lines))
print("wrote", OUT)
print("first-position counts:", dict(sorted(first_pos.items())), "share=%.2f" % share)
if share > 0.8:
    print("FAIL: correct C option concentrates in one position (v5 leak pattern)")
    sys.exit(1)
print("OK: C answer positions are varied")
