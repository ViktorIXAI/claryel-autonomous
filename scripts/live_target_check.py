#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pre-launch measurability gate: does the ADOPTED line actually fail the target?

pair-251 burned a reserved endpoint window on a pair whose control arm strict-passed
the target cell in every seed: the pair measured nothing (verdict UNMEASURED) and the
adoption rule got poisoned. This script turns that rule into a mechanical check that
must run BEFORE a pair is launched, reading the CSV emitted by
scripts/unstable_cells_v62.py.

Usage:
  python3 scripts/live_target_check.py --csv UNSTABLE-CELLS-V66-255.csv \
      --task D-ex6-l0 [--task ...] [--min-fails 1] [--max-pass 4]

Exit 0 = at least one target is live (a pair can measure it).
Exit 3 = no live target: freeze the stamp as UNMEASURED, do not reserve the endpoint.
Exit 1 = bad input / stale map (a map may not be used past its stamp).
"""
from __future__ import annotations

import argparse
import csv
import os
import sys


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--csv", required=True, help="cell matrix from unstable_cells_v62.py")
    ap.add_argument("--task", action="append", default=[],
                    help="candidate target task id (repeatable)")
    ap.add_argument("--min-fails", type=int, default=1,
                    help="minimum strict-fail arms for a cell to count as live (default 1)")
    ap.add_argument("--max-pass", type=int, default=None,
                    help="optional headroom cap: target must pass in <= this many arms")
    ap.add_argument("--stamp", help="expected contour stamp of the map (refuse a stale map)")
    ap.add_argument("--bank", help="expected bank version of the map")
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        print("no such map: %s (generate it with scripts/unstable_cells_v62.py first)" % args.csv)
        return 1
    rows = list(csv.DictReader(open(args.csv, encoding="utf-8")))
    if not rows:
        print("map %s has no rows" % args.csv)
        return 1
    if args.stamp and {r["stamp"] for r in rows} != {args.stamp}:
        print("STALE MAP: map stamps %s, candidate assumes %s — rebuild the map on the adopted line"
              % (sorted({r['stamp'] for r in rows}), args.stamp))
        return 1
    if args.bank and {r["bank_version"] for r in rows} != {args.bank}:
        print("STALE MAP: map bank %s, candidate assumes %s"
              % (sorted({r['bank_version'] for r in rows}), args.bank))
        return 1
    meta = rows[0]
    print("map: stamp %s, bank %s published %s, contract %s, %d cells"
          % (meta["stamp"], meta["bank_version"], meta["bank_sha16"], meta["contract"], len(rows)))

    by_task = {r["task"]: r for r in rows}
    live, dead, missing = [], [], []
    for t in args.task:
        r = by_task.get(t)
        if r is None:
            missing.append(t)
            continue
        bits = [k for k in r if k not in ("task", "cat", "loop", "stamp", "bank_version",
                                          "bank_sha16", "contract", "fails", "fail_note_families")]
        passes = sum(1 for k in bits if r[k] == "1")
        fails = int(r["fails"])
        verdict = fails >= args.min_fails and (args.max_pass is None or passes <= args.max_pass)
        line = ("%s: %d/%d strict pass, fails=%d, families=%s"
                % (t, passes, passes + fails, fails, r["fail_note_families"] or "none"))
        (live if verdict else dead).append(line)

    for line in live:
        print("LIVE  " + line)
    for line in dead:
        print("DEAD  " + line)
    for t in missing:
        print("ABSENT " + t + " (not in the map — wrong bank/stamp or a new task id)")
    if missing:
        return 1
    if not args.task:
        print("no --task given: nothing certified")
        return 1
    if not live:
        print("VERDICT: no live target — freeze the candidate as UNMEASURED, do not reserve the "
              "endpoint; re-target from this map or close the failure group.")
        return 3
    print("VERDICT: %d live target(s); a pair on these seeds can measure a change. "
          "Pre-register the rule in REVIEW-INBOX before the first arm row." % len(live))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
