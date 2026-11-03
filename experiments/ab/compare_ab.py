#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summary of A/B arms from gate logs: correctness, tokens, time, repairs, guard trips."""
import json
import sys

for tag in sys.argv[1:]:
    fp = "gate-ledger-%s.jsonl" % tag
    try:
        rows = [json.loads(l) for l in open(fp, encoding="utf-8") if l.strip()]
    except Exception as e:
        print(tag, "no data:", e)
        continue
    if not rows:
        print(tag, "empty log")
        continue
    # Stalled rows (serve returned nothing) are reported separately and kept out of
    # the quality mean: they measure the box, not the contour.
    stalled = [r for r in rows if r.get("engine_stalled")]
    rows = [r for r in rows if not r.get("engine_stalled")] or rows
    pt = sum(r.get("ptok") or 0 for r in rows)
    ct = sum(r.get("ctok") or 0 for r in rows)
    sec = sum(r.get("seconds") or 0 for r in rows)
    ok = sum(1 for r in rows if (r.get("content") or 0) >= 0.999)
    mean = sum(float(r.get("content") or 0) for r in rows) / len(rows)
    ev = [e for r in rows for e in (r.get("events") or [])]
    print("%-7s rows %2d (stalled %d) | correct %2d | mean %3.0f%% | in %5d (per task %5d) | "
          "out %5d | sec %6.1f | repairs %2d | cheap repairs rejected %d"
          % (tag, len(rows), len(stalled), ok, 100 * mean, pt, pt / len(rows), ct, sec,
             sum(r.get("gate_fixes") or 0 for r in rows), ev.count("gate:cheap_repair_rejected")))
