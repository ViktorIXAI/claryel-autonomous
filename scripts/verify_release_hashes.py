#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify unpacked release artifacts against logs/INDEX.md hashes (first 16 hex)."""
import hashlib
import os
import re
import sys

base = sys.argv[1] if len(sys.argv) > 1 else "artifacts"
row = re.compile(r"\|\s*`([^`]+\.jsonl)`[^|]*\|\s*\d+\s*\|\s*\d+\s*\|\s*`([0-9a-f]{16})")
idx = open("logs/INDEX.md", encoding="utf-8").read()
want = {}
for name, h in row.findall(idx):
    want[os.path.basename(name)] = h
ok = miss = bad = 0
for root, _d, files in os.walk(base):
    for fn in files:
        if not fn.endswith(".jsonl") or fn not in want:
            continue
        p = os.path.join(root, fn)
        got = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
        if got == want[fn]:
            ok += 1
        else:
            bad += 1
            print("HASH-MISMATCH", fn, "want", want[fn], "got", got)
for fn in want:
    if not any(fn == f for _r, _d, fs in os.walk(base) for f in fs):
        miss += 1
print("verified=%d mismatch=%d not-in-archive=%d" % (ok, bad, miss))
sys.exit(1 if bad or miss else 0)
