#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify bank-hard-v6.3.json against the published v6.2 bytes.

Asserts:
  * v6.2 source file is byte-identical to its published identity (sha16);
  * v6.3 differs from v6.2 in EXACTLY one task and one field (B-ex6-04.prompt);
    every other task and every other field — including EVERY gold — is
    byte-identical;
  * the v6.3 prompt for B-ex6-04 states the gold's full date (day, month and
    year all present in the fact phrase), i.e. the gold is now
    contract-derivable from the shipped prompt alone;
  * the distractor clause is untouched;
  * task count, ids, seeds and golds are unchanged.
Exit 0 + a per-field report on PASS, hard failure otherwise.
"""
import hashlib
import json
import re
import sys

V62 = "benchmarks/hard/bank-hard-v6.2.json"
V63 = "benchmarks/hard/bank-hard-v6.3.json"
V62_SHA16 = "3c866ea7daae611c"

raw2 = open(V62, "rb").read()
if hashlib.sha256(raw2).hexdigest()[:16] != V62_SHA16:
    sys.exit("FAIL: v6.2 bytes moved: %s" % hashlib.sha256(raw2).hexdigest()[:16])
raw3 = open(V63, "rb").read()
b2 = json.loads(raw2)
b3 = json.loads(raw3)

fail = []
if len(b2) != len(b3):
    fail.append("task count changed %d -> %d" % (len(b2), len(b3)))
t2 = {t["id"]: t for t in b2}
t3 = {t["id"]: t for t in b3}
if set(t2) != set(t3):
    fail.append("task ids changed")

diffs = []
for tid in sorted(set(t2) & set(t3)):
    for field in sorted(set(t2[tid]) | set(t3[tid])):
        if json.dumps(t2[tid].get(field), ensure_ascii=False, sort_keys=True) != \
           json.dumps(t3[tid].get(field), ensure_ascii=False, sort_keys=True):
            diffs.append("%s.%s" % (tid, field))
if diffs != ["B-ex6-04.prompt"]:
    fail.append("changed fields are %s, expected exactly ['B-ex6-04.prompt']" % diffs)

gold = t3["B-ex6-04"]["ref"]["start_date"]
year, mon, day = gold.split("-")
pr = t3["B-ex6-04"]["prompt"]
MONTHS = {"01": "января", "02": "февраля", "03": "марта", "04": "апреля",
          "05": "мая", "06": "июня", "07": "июля", "08": "августа",
          "09": "сентября", "10": "октября", "11": "ноября", "12": "декабря"}
if not re.search(r"%d %s %s" % (int(day), MONTHS[mon], year), pr):
    fail.append("B-ex6-04 gold date %s is still not stated in the prompt" % gold)
if t3["B-ex6-04"]["ref"] != t2["B-ex6-04"]["ref"]:
    fail.append("B-ex6-04 gold changed — the correction must be prompt-only")
if "Мой отпуск 10-20 марта к этому не относится" not in pr:
    fail.append("B-ex6-04 distractor clause changed")
if year in t2["B-ex6-04"]["prompt"]:
    fail.append("v6.2 prompt already carried the year — the published defect claim would be wrong")

# every gold in the whole bank must be identical between the two versions
for tid in sorted(t2):
    if json.dumps(t2[tid]["ref"], ensure_ascii=False, sort_keys=True) != \
       json.dumps(t3[tid]["ref"], ensure_ascii=False, sort_keys=True):
        fail.append("gold changed for %s" % tid)

for tid in sorted(t2):
    if t2[tid].get("seed") != t3[tid].get("seed"):
        fail.append("seed changed for %s" % tid)

print("v6.2 sha16 %s  v6.3 sha16 %s  tasks %d" % (
    hashlib.sha256(raw2).hexdigest()[:16], hashlib.sha256(raw3).hexdigest()[:16], len(b3)))
print("changed fields:", diffs)
print("B-ex6-04 gold %s now stated in prompt: %s" % (gold, bool(re.search(
    r"%d %s %s" % (int(day), MONTHS[mon], year), pr))))
if fail:
    for f in fail:
        print("FAIL:", f)
    sys.exit(1)
print("PASS: v6.3 is v6.2 plus exactly one prompt correction; every gold byte-identical")
