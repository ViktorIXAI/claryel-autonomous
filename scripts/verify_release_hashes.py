#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify unpacked release artifacts against logs/INDEX.md hashes (first 16 hex)."""
import hashlib
import os
import re
import sys

base = sys.argv[1] if len(sys.argv) > 1 else "artifacts"
row = re.compile(r"\|\s*`?([^`|\s]+\.jsonl)`?\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*`?([0-9a-f]{16})")
idx = open("logs/INDEX.md", encoding="utf-8").read()
want = {}
for name, h in row.findall(idx):
    want[os.path.basename(name)] = h
# required set = every file the pinned aggregate reads (analytics/aggregate.py SPECS)
specs_src = open("analytics/aggregate.py", encoding="utf-8").read()
required = {os.path.basename(p) for p in re.findall(r'"([^"]+\.jsonl)"', specs_src)}
have = {}
for root, _d, files in os.walk(base):
    for fn in files:
        if fn.endswith(".jsonl"):
            have[fn] = os.path.join(root, fn)
ok = bad = 0
for fn, p in sorted(have.items()):
    if fn not in want:
        continue  # supplementary samples not in the archive index: not claimed here
    got = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    if got == want[fn]:
        ok += 1
    else:
        bad += 1
        print("HASH-MISMATCH", fn, "want", want[fn], "got", got)
missing_required = sorted(f for f in required if f not in have)
for fn in missing_required:
    print("MISSING-REQUIRED", fn)
print("verified=%d mismatch=%d missing_required=%d (index rows=%d)" % (ok, bad, len(missing_required), len(want)))
sys.exit(1 if bad or missing_required else 0)
