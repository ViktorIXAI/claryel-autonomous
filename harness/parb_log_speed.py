#!/usr/bin/env python3
"""Parse PARB gate runner logs into per-box speed/load summaries.

Usage:
  PARB_SPEED_INCLUDE='v19 probe smoke' python3 parb_log_speed.py HH:MM v18.log v19.log

`HH:MM` is the clock cutoff for the requested window. Logs whose basename
contains a token from PARB_SPEED_INCLUDE are included whole; use that for
vNN/probe/smoke logs that start after midnight when the cutoff is a previous
daytime clock.
"""
import os
import re
import sys
from collections import defaultdict

if not sys.argv[1:]:
    raise SystemExit("usage: [PARB_SPEED_INCLUDE=...] cutoff_HH:MM logs...")

cutoff = tuple(int(x) for x in sys.argv[1].split(":"))
if len(cutoff) == 2:
    cutoff = (cutoff[0], cutoff[1], 0)

include_tokens = [x for x in os.environ.get("PARB_SPEED_INCLUDE", "").split() if x]
row_re = re.compile(
    r"^(?P<t>\d\d:\d\d:\d\d)\s+(?P<cat>[A-K])\s+(?P<task>\S+)\s+rep(?P<rep>\d+)\s+"
    r"c=(?P<c>[\d.]+)\s+f=(?P<f>\d).*?"
    r"(?P<d>[\d.]+)s\s+tok=(?P<itok>\d+)\s+/(?P<otok>\d+)"
    r"(?:\s+c=(?P<fixes>\d+))?(?:\s+tps_eff=(?P<tps>[\d.]+|None))?"
)

rows = []
for p in sys.argv[2:]:
    if not os.path.exists(p):
        continue
    base = os.path.basename(p)
    include_all = any(tok in base for tok in include_tokens)
    for line in open(p, encoding="utf-8", errors="ignore"):
        m = row_re.match(line.strip())
        if not m:
            continue
        if not include_all:
            h, mi, sec = (int(x) for x in m.group("t").split(":"))
            if (h, mi, sec) < cutoff:
                continue
        d = float(m.group("d"))
        otok = int(m.group("otok"))
        itok = int(m.group("itok"))
        rows.append({
            "t": m.group("t"),
            "cat": m.group("cat"),
            "task": m.group("task"),
            "rep": int(m.group("rep")),
            "d": d,
            "itok": itok,
            "otok": otok,
            "c": float(m.group("c")),
            "f": int(m.group("f")),
            "tps": otok / d if d > 0.05 and otok > 0 else None,
        })

print("file(s):", [os.path.basename(p) for p in sys.argv[2:]])
print("rows_in_window", len(rows), "unique task-rep", len({(r["task"], r["rep"]) for r in rows}))
if not rows:
    raise SystemExit

by_cat = defaultdict(list)
by_task = defaultdict(list)
for r in rows:
    by_cat[r["cat"]].append(r)
    by_task[r["task"]].append(r)


def agg(rs):
    if not rs:
        return None
    speed_rows = [r for r in rs if r["tps"]]
    gen_out = sum(r["otok"] for r in rs if r["otok"] > 0)
    gen_sec = sum(r["d"] for r in rs if r["otok"] > 0)
    med = sorted(r["tps"] for r in speed_rows)[len(speed_rows) // 2] if speed_rows else 0.0
    return (
        f"rows={len(rs)} outs={gen_out} avg_in={sum(r['itok'] for r in rs)/len(rs):.0f} "
        f"avg_out={sum(r['otok'] for r in rs)/len(rs):.1f} "
        f"avg_task_s={sum(r['d'] for r in rs)/len(rs):.2f} "
        f"agg_tok/s={gen_out/gen_sec if gen_sec else 0:.1f} median_tok/s={med:.1f} "
        f"avg_c={sum(r['c'] for r in rs)/len(rs):.3f}"
    )

print("\nOVERALL", agg(rows))
print("\nBY CATEGORY")
for cat, rs in sorted(by_cat.items()):
    print(cat, agg(rs))
print("\nTOP 10 most repeated tasks in window")
for task, rs in sorted(by_task.items(), key=lambda x: -len(x[1]))[:10]:
    print(task, agg(rs))
