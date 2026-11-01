#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deduplication-rule sensitivity (spec 6: alternate aggregation check).

The repo-wide rule is (task, rep) keeping the BEST content score. This tool
recomputes the same series and paired deltas under three rules:
  best   (published)  — per (task,rep), max content
  first                 — first occurrence in file order
  worst                 — min content
If a version delta keeps its sign under all three, the conclusion is
rule-insensitive; if it flips, the published claim is rule-dependent.

Usage: PARB_ARTIFACTS=<dir> python3 analytics/dedup_sensitivity.py <specA-stem> <specB-stem> ...
Stems are file basenames without .jsonl (from the release archive layout).
"""
import json
import os
import sys

BASE = os.environ.get("PARB_ARTIFACTS", "artifacts")


def load(path, rule):
    d = {}
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        k = (r.get("task"), r.get("rep"))
        if None in k:
            continue
        if k not in d:
            d[k] = r
        else:
            c = float(r.get("content") or 0)
            if rule == "best" and c > float(d[k].get("content") or 0):
                d[k] = r
            elif rule == "worst" and c < float(d[k].get("content") or 0):
                d[k] = r
    return d


def mean(rows):
    v = [float(r.get("content") or 0) for r in rows.values()]
    return round(sum(v) / len(v), 4) if v else None


def pair(a, b):
    keys = set(a) & set(b)
    ds = [float(b[k].get("content") or 0) - float(a[k].get("content") or 0) for k in keys]
    return {"n": len(keys), "avg": round(sum(ds) / len(ds), 4) if ds else None,
            "up": sum(1 for x in ds if x > 1e-9), "down": sum(1 for x in ds if x < -1e-9)}


def find(spec):
    p = os.path.join(BASE, spec + ".jsonl")
    if os.path.exists(p):
        return p
    stem = spec.split("/")[-1]
    for root, _d, files in os.walk(BASE):
        if stem + ".jsonl" in files:
            return os.path.join(root, stem + ".jsonl")
    return None


def main():
    pairs = [sys.argv[i] + " " + sys.argv[i + 1] for i in range(1, len(sys.argv), 2)]
    out = {}
    for spec in pairs:
        a, b = spec.split()
        pa, pb = find(a), find(b)
        if not pa or not pb:
            out[spec] = {"error": "file(s) not found under PARB_ARTIFACTS"}
            continue
        row = {}
        for rule in ("best", "first", "worst"):
            da, db = load(pa, rule), load(pb, rule)
            row[rule] = {"mean_a": mean(da), "mean_b": mean(db), "delta": pair(da, db)}
        signs = {r: (row[r]["delta"]["avg"] or 0) > 0 for r in row}
        row["rule_insensitive_positive"] = all(signs.values()) and (row["best"]["delta"]["avg"] or 0) > 0
        out["%s -> %s" % (a, b)] = row
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
