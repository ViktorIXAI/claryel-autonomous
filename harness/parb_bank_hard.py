#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PARB HARD bank — the "extreme" difficulty tier (2026-11-05).

Operator request: 99% looked like saturation, so every scalable knob was
multiplied (A items x2, B fields x2, C 9 conditions/14 candidates, D 30 rows +
danger kinds, E 5 injected bugs/100 tests, G 32k-char docs, J 90 rows) on a
fresh seed disjoint from dev and holdout ids (level code "ex"). Purpose: create
measurable headroom — a contour that scores 99% on the normal bank should show
its real remaining failure classes here.

Deterministic: seed 20261205. Guards inherited: scorer-shape guard + C-ref
semantic validation (scripts/validate_c_refs.py in the parb skill) must pass
before use.
Usage: python3 harness/parb_bank_hard.py
Output: benchmarks/hard/bank-hard.json
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parb_bank import build, FILLER, CITIES  # same deterministic generators, new level


def assemble_G(t):
    """G tasks need the document materialized (dev-bank prep stage does this;
    the first hard bank shipped bare questions, invalidating G for EVERY brain
    — contour and external — found by the external comparison on 2026-11-05)."""
    known = "\n".join(t["head_units"] + t["mid_units"] + t["tail_units"] + [t["prompt"]])
    target_chars = int(t["target_tokens"] * 3.5)
    need = max(0, int((target_chars - len(known)) // 150))
    fillers = [FILLER % (CITIES[j % len(CITIES)], 1000 + j, (j % 7) + 1, (j % 11) + 6)
               if "%s" in FILLER else
               FILLER.format(c=CITIES[j % len(CITIES)], n=1000 + j, d=(j % 7) + 1, y=(j % 11) + 6)
               for j in range(need)]
    half = need // 2
    t["assembled_doc"] = "\n".join(t["head_units"] + fillers[:half] + t["mid_units"] +
                                   fillers[half:] + t["tail_units"])
    t["filler_units"] = need
    return t

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "benchmarks", "hard", "bank-hard.json")
HARD_SEED = 20261205

COUNTS = {"A": {"extreme": 4}, "B": {"extreme": 4}, "C": {"extreme": 6},
          "D": {"extreme": 3}, "E": {"extreme": 6}, "F": {"extreme": 3},
          "G": {"extreme": 6}, "H": {"extreme": 4}, "I": {"extreme": 3},
          "J": {"extreme": 4}, "K": {"extreme": 4}}


def main():
    tasks = build(HARD_SEED, COUNTS)
    # scorer-shape guard (same class of protection as the holdout bank v3)
    import parb_check as CK
    import parb_loop as LP
    SC = {c: getattr(CK, "check_" + c) for c in "ABCEFGHIJK"}
    bad = []
    for t in tasks:
        try:
            if t["cat"] == "D":
                LP.check_D_loop(t, {"agent_steps": [], "agent_final": ""})
            else:
                SC[t["cat"]](t, "0")
        except KeyError as e:
            bad.append((t["id"], "ref key missing: %s" % e))
    for tid, why in bad:
        print("BANK GUARD FAIL:", tid, why)
    if bad:
        raise SystemExit(1)
    for t in tasks:
        if t["cat"] == "G":
            assemble_G(t)
    print("bank guard: all %d tasks scorable" % len(tasks))
    ids = [t["id"] for t in tasks]
    assert len(set(ids)) == len(ids), "duplicate hard ids"
    h = hashlib.sha256(json.dumps(ids).encode()).hexdigest()[:16]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(tasks, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("hard tasks=%d hash16=%s -> %s" % (len(tasks), h, OUT))


if __name__ == "__main__":
    main()
