#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diff two summary JSONs (recomputed vs published) key-by-key.
Exits 1 listing any numeric mismatch. Structural additions tolerated only
when the published side lacks them (recompute = superset check is strict)."""
import json
import sys

a = json.load(open(sys.argv[1], encoding="utf-8"))   # recomputed
b = json.load(open(sys.argv[2], encoding="utf-8"))   # published
diffs = []


def walk(pa, pb, key=""):
    if isinstance(pb, dict):
        for k, v in pb.items():
            if k not in (pa or {}):
                diffs.append("%s.%s: missing in recomputed" % (key, k))
            else:
                walk(pa[k], v, "%s.%s" % (key, k))
    elif isinstance(pb, list):
        if pa != pb:
            diffs.append("%s: list differs" % key)
    else:
        try:
            if pb is not None and (pa is None or abs(float(pa) - float(pb)) > 1e-9):
                diffs.append("%s: recomputed=%s published=%s" % (key, pa, pb))
        except (TypeError, ValueError):
            if pa != pb:
                diffs.append("%s: %r vs %r" % (key, pa, pb))


walk(a, b)
print("diffs=%d" % len(diffs))
for d in diffs[:40]:
    print(" ", d)
sys.exit(1 if diffs else 0)
