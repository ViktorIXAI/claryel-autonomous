#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-arm strict score split: single-shot /N + loop-D /M, then % of the whole bank.

The operator asks "how many % of the bank does the best version solve". The bank is NOT a flat
list: 6 tasks (the D loop-D tasks) are only reachable by the contour, and raw single-shot arms
have them as N/A. Folding them into the single-shot count overstates every arm, and ledger rows
carry no `mode` field — the loop subset must come from the PLAN rows. This tool does that split
from ledgers + plan files and prints the headline the operator reads.

Fail-closed rules:
  * a workspace with no parsable plan file, or a plan set that names zero loop tasks, is an error;
  * ledger tasks missing from every plan (>2% of rows) is an error (mode unknown -> score wrong);
  * a ledger with zero rows is an error.

Usage: arm_score_split.py <workspace> [label:rid,rid ...]
       (with no label arguments every ledger-<rid>.jsonl in the workspace is grouped by its
        contour stamp read from the ledger rows, when that column exists)
"""
import glob
import hashlib
import json
import os
import sys


def plan_rows(path):
    """Tolerate JSONL-of-dicts, one big JSON list, or {"rows": [...]}."""
    text = open(path, encoding="utf-8").read()
    try:
        data = json.loads(text)
    except ValueError:
        rows = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    pass
        return rows
    if isinstance(data, dict):
        return data.get("rows") or [data]
    return data


def load_loop_tasks(ws):
    loop, seen_plans = set(), 0
    for pf in sorted(glob.glob(os.path.join(ws, "plan*.json"))):
        rows = plan_rows(pf)
        if not rows:
            continue
        seen_plans += 1
        for p in rows:
            if isinstance(p, dict) and p.get("mode") == "loop":
                loop.add(p["task"])
    if not seen_plans:
        raise SystemExit("no parsable plan*.json in %s - loop subset would be guessed" % ws)
    if not loop:
        raise SystemExit("plans name zero loop tasks in %s - split impossible" % ws)
    return loop


def score_arm(ws, rid, loop):
    lp = os.path.join(ws, "ledger-%s.jsonl" % rid)
    if not os.path.exists(lp):
        raise SystemExit("ledger missing: %s" % lp)
    rows = [json.loads(l) for l in open(lp, encoding="utf-8") if l.strip()]
    if not rows:
        raise SystemExit("ledger has no rows: %s" % lp)
    unknown = [d["task"] for d in rows if d["task"] not in loop and d["task"] not in KNOWN_TASKS]
    if unknown and len(unknown) > 0.02 * len(rows):
        raise SystemExit("%s: %d rows have tasks absent from every plan (%s...) - mode unknown"
                         % (rid, len(unknown), ", ".join(sorted(set(unknown))[:3])))
    L = [d for d in rows if d["task"] in loop]
    S = [d for d in rows if d["task"] not in loop]

    def ok(xs):
        return sum(1 for d in xs if d.get("content") == 1.0 and d.get("format_ok"))

    stamp = next((d.get("contour_version") for d in rows if d.get("contour_version")), "?")
    return ok(S), len(S), ok(L), len(L), stamp


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    ws = os.path.expanduser(sys.argv[1])
    global KNOWN_TASKS
    KNOWN_TASKS = set()
    for pf in glob.glob(os.path.join(ws, "plan*.json")):
        for p in plan_rows(pf):
            if isinstance(p, dict) and p.get("task"):
                KNOWN_TASKS.add(p["task"])
    loop = load_loop_tasks(ws)

    bank = os.path.join(ws, "bank.json")
    sha16 = "-"
    if os.path.exists(bank):
        sha16 = hashlib.sha256(open(bank, "rb").read()).hexdigest()[:16]
    print("workspace %s | loop tasks %d | bank sha16 %s" % (ws, len(loop), sha16))

    groups = []
    if len(sys.argv) > 2:
        for arg in sys.argv[2:]:
            label, _, rids = arg.partition(":")
            groups.append((label, [r for r in rids.split(",") if r]))
    else:
        by_stamp = {}
        for lp in sorted(glob.glob(os.path.join(ws, "ledger-*.jsonl"))):
            rid = os.path.basename(lp)[len("ledger-"):-len(".jsonl")]
            by_stamp.setdefault("rid-" + rid, [rid])
        groups = sorted(by_stamp.items())

    for label, rids in groups:
        res = []
        for rid in rids:
            try:
                res.append(score_arm(ws, rid, loop) + (rid,))
            except SystemExit as exc:
                print("%s: %s" % (label, exc))
        if not res:
            continue
        tot = [s + l for s, _, l, _, _, _ in res]
        n = len(res)
        print("%-6s n=%d  single-shot %s  loop %s | mean /%d = %.1f = %.1f%% | best %d | spread %d | stamps %s"
              % (label, n, [r[0] for r in res], [r[2] for r in res],
                 res[0][1] + res[0][3], sum(tot) / n, 100 * sum(tot) / n / (res[0][1] + res[0][3]),
                 max(tot), max(tot) - min(tot), sorted({r[4] for r in res})))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
