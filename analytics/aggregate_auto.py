#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auto-discovery aggregation over ALL staged artifacts (new work, v2 era).

Frozen analytics/aggregate.py stays untouched for byte-identical reproduction
of the pinned release; this variant walks a directory tree, groups every
results-*.jsonl into series keyed by (directory/machine, file stem, box field,
contour_version), dedups (task, rep[, box]), pairs every adjacent contour
generation within a box, and pairs contour-free baseline -> first gated run.

Usage: PARB_ARTIFACTS=<dir> python3 analytics/aggregate_auto.py > out.json
"""
import json, os, sys
from collections import defaultdict, Counter

BASE = os.environ.get("PARB_ARTIFACTS", "./artifacts")
ORDER = {"contour-free": -1, None: -2, "v1.0": 0, "v1.1": 1, "v1.2": 2, "v1.3": 3,
         "v1.4": 4, "v1.5": 5, "v1.6": 6, "v1.7": 7, "v1.8": 8, "v1.9": 9, "v2.0": 10}


def rows_of(path):
    out = []
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            if r.get("task"):
                out.append(r)
        except Exception:
            continue
    return out


def stats(rows):
    n = len(rows)
    if not n:
        return None
    c = [float(r.get("content") or 0) for r in rows]
    f = [float(r.get("format_ok") or 0) for r in rows]
    cats = defaultdict(list)
    for r in rows:
        cats[(r.get("task") or "?")[0]].append(float(r.get("content") or 0))
    tw = [float(r.get("t_wall") or 0) for r in rows if r.get("t_wall")]
    return {"n": n, "avg_content": round(sum(c) / n, 4),
            "perfect_share": round(sum(1 for x in c if x == 1.0) / n, 4),
            "format_ok_share": round(sum(1 for x in f if x) / n, 4),
            "cats": {k: round(sum(v) / len(v), 3) for k, v in sorted(cats.items())}}


def dedup(rows):
    d = {}
    for r in rows:
        k = (r["task"], r.get("rep"))
        if k not in d or float(r.get("content") or 0) > float(d[k].get("content") or 0):
            d[k] = r
    return d


def paired(a, b):
    keys = set(a) & set(b)
    if not keys:
        return None
    ds = [float(b[k].get("content") or 0) - float(a[k].get("content") or 0) for k in keys]
    return {"n_pairs": len(keys), "avg_delta": round(sum(ds) / len(ds), 4),
            "improved": sum(1 for d in ds if d > 1e-9),
            "regressed": sum(1 for d in ds if d < -1e-9)}


series = {}
for root, _dirs, files in os.walk(BASE):
    for fn in sorted(files):
        if not fn.startswith("results-") or not fn.endswith(".jsonl"):
            continue
        rows = rows_of(os.path.join(root, fn))
        if not rows:
            continue
        machine = os.path.relpath(root, BASE).replace(os.sep, "/")
        # per-row grouping: a file can span contour generations; each row joins
        # the series named by ITS OWN contour_version/box fields (no rewriting)
        for r in rows:
            box = r.get("box") or "?"
            cv = r.get("contour_version") or "contour-free"
            series.setdefault("%s|%s|%s" % (machine, box, cv), []).append(r)

out = {"series": {}, "paired": {}}
bybox = defaultdict(dict)
for name, rows in sorted(series.items()):
    d = dedup(rows)
    st = stats(list(d.values()))
    st["source_rows"] = len(rows)
    out["series"][name] = st
    machine, box, cv = name.split("|")
    # pairing happens only WITHIN one physical directory: the recorded box field
    # can be wrong (early mac runner inherited PARB_BOX=B2003) — history kept,
    # but comparisons are guarded by the directory the rows came from
    bybox[machine][ORDER.get(cv, 90 + len(cv))] = (name, cv, d)

for machine, versions in bybox.items():
    names = [versions[k] for k in sorted(versions)]
    for (na, ca, da), (nb, cb, db) in zip(names, names[1:]):
        p = paired(da, db)
        if p and p["n_pairs"] >= 8:
            out["paired"][f"{machine}: {ca} -> {cb}"] = p

print(json.dumps(out, indent=1, ensure_ascii=False))
