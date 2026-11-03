#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recompute every published aggregate from raw run artifacts.

Raw artifacts are not committed to git (they hold ~40k model outputs); download
the release archive, unpack under ./artifacts/ (layout mirrors logs/INDEX.md),
then:

    PARB_ARTIFACTS=./artifacts python3 analytics/aggregate.py > summary.json

Dedup rule (repo-wide): (task, rep) keeping best content score.
The SPECS table below is exactly what produced analytics/summary.json shipped
in this repo — edit paths to point at your own series instead.
"""
import json, os
from collections import defaultdict, Counter

BASE = os.environ.get("PARB_ARTIFACTS", "./artifacts")

stalled = {}


def load(path):
    d = {}
    if not os.path.exists(path):
        return d
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        k = (r.get("task"), r.get("rep"))
        if None in k:
            continue
        if r.get("engine_stalled"):
            # The serve returned nothing: this row measures the box, not the answer,
            # so it must not enter quality means as a zero.
            stalled[path] = stalled.get(path, 0) + 1
            continue
        if k not in d or float(r.get("content") or 0) > float(d[k].get("content") or 0):
            d[k] = r
    if stalled.get(path):
        import sys
        sys.stderr.write("engine-stalled rows excluded from %s: %d\n" % (path, stalled[path]))
    return d

def load_ledger(path):
    d = defaultdict(list)
    if not os.path.exists(path):
        return d
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        d[(r.get("task"), r.get("rep"))].append(r)
    return d

def stats(rows):
    n = len(rows)
    if not n:
        return None
    c = [float(r.get("content") or 0) for r in rows]
    f = [float(r.get("format_ok") or 0) for r in rows]
    cats = defaultdict(list)
    for r in rows:
        cats[(r.get("task") or "?")[0]].append(float(r.get("content") or 0))
    return {
        "n": n,
        "avg_content": round(sum(c) / n, 4),
        "perfect_share": round(sum(1 for x in c if x == 1.0) / n, 4),
        "format_ok_share": round(sum(1 for x in f if x) / n, 4),
        "cats": {k: round(sum(v) / len(v), 3) for k, v in sorted(cats.items())},
    }

def ledger_stats(led):
    calls = fixes = blocks = ladder = 0
    ptok = ctok = secs = 0.0
    events = Counter()
    attempts = 0
    for lst in led.values():
        for r in lst:
            attempts += 1
            calls += int(r.get("model_calls") or 0)
            fixes += int(r.get("gate_fixes") or 0)
            blocks += int(r.get("gate_blocks") or 0)
            ptok += float(r.get("ptok") or 0)
            ctok += float(r.get("ctok") or 0)
            secs += float(r.get("seconds") or 0)
            for e in r.get("events") or []:
                events[e if isinstance(e, str) else str(e)] += 1
    if not attempts:
        return None
    return {
        "attempts": attempts,
        "model_calls_per_attempt": round(calls / attempts, 2),
        "fixes_per_attempt": round(fixes / attempts, 2),
        "blocks_per_attempt": round(blocks / attempts, 2),
        "ptok_per_attempt": round(ptok / attempts, 1),
        "ctok_per_attempt": round(ctok / attempts, 1),
        "seconds_per_attempt": round(secs / attempts, 1),
        "top_events": events.most_common(15),
    }

def paired(a, b):
    keys = set(a) & set(b)
    if not keys:
        return None
    up = down = same = 0
    ds = []
    for k in keys:
        d = float(b[k].get("content") or 0) - float(a[k].get("content") or 0)
        ds.append(d)
        if d > 1e-9:
            up += 1
        elif d < -1e-9:
            down += 1
        else:
            same += 1
    cats = defaultdict(lambda: [0.0, 0])
    for k in keys:
        c = (k[0] or "?")[0]
        cats[c][0] += float(b[k].get("content") or 0) - float(a[k].get("content") or 0)
        cats[c][1] += 1
    return {"n_pairs": len(keys), "avg_delta": round(sum(ds) / len(ds), 4),
            "improved": up, "regressed": down, "unchanged": same,
            "per_cat_delta": {c: round(v / n, 3) for c, (v, n) in sorted(cats.items())}}

SPECS = {
    "v1.2-b2003": ("results-v12.jsonl", "gate-ledger-v12.jsonl"),
    "v1.2-mac":   ("results-v12m.jsonl", "gate-ledger-v12m.jsonl"),
    "v1.3-b2003": ("results-v13.jsonl", "gate-ledger-v13.jsonl"),
    "v1.3-mac":   ("results-v13m.jsonl", "gate-ledger-v13m.jsonl"),
    "v1.7-b2003": ("v17-final/results-v17-b2003.jsonl", "gate-ledger-v17.jsonl"),
    "v1.7-mac":   ("v17-final/results-v17-mac.jsonl", "gate-ledger-v17m.jsonl"),
    "v1.8-b2003": ("v18-final/results-v18-b2003.jsonl", "v18-final/gate-ledger-v18-b2003.jsonl"),
    "v1.8-mac":   ("v18-final/results-v18-mac.jsonl", "v18-final/gate-ledger-v18-mac.jsonl"),
    "v1.9-b2003": ("v19-final/results-v19-b2003.jsonl", "v19-final/gate-ledger-v19-b2003.jsonl"),
    "v1.9-mac":   ("v19-final/results-v19m.jsonl", "v19-final/gate-ledger-v19m.jsonl"),
    "v2.0-p2005": ("v20-final/results-v20pair19-P2005.jsonl", "v20-final/gate-ledger-v20pair19-P2005.jsonl"),
}

out = {"series": {}, "paired": {}}
loaded = {}
for name, (rp, lp) in SPECS.items():
    rows = load(os.path.join(BASE, rp))
    s = stats(list(rows.values()))
    if s:
        s["ledger"] = ledger_stats(load_ledger(os.path.join(BASE, lp)))
        out["series"][name] = s
    loaded[name] = rows

for a, b in (("v1.7-b2003", "v1.8-b2003"), ("v1.7-mac", "v1.8-mac"),
             ("v1.8-b2003", "v1.9-b2003"), ("v1.8-mac", "v1.9-mac")):
    out["paired"][f"{a} -> {b}"] = paired(loaded.get(a, {}), loaded.get(b, {}))

def drows(rows):
    return {k: v for k, v in rows.items() if v.get("task", "").startswith("D-ea")}

out["D_ea_only"] = {}
for nm in ("v1.7-b2003", "v1.8-b2003", "v1.9-b2003", "v1.7-mac", "v1.8-mac", "v1.9-mac"):
    s = stats(list(drows(loaded.get(nm, {})).values()))
    if s:
        out["D_ea_only"][nm] = {k: v for k, v in s.items() if k != "cats"}

print(json.dumps(out, indent=1, ensure_ascii=False))
