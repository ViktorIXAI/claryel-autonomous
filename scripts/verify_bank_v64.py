#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify bank-hard-v6.4.json against the published v6.3 bytes.

Asserts: v6.3 identity sha16; EXACTLY one changed task/field (B-ex6-04.prompt);
every gold and seed byte-identical over all 77 tasks; the v6.3 stated year is
still present twice; the corrected spec types `penalty_per_week` as a percent
string with an example that is NOT the gold value; the gold value does not
appear anywhere in the corrected prompt (no answer leakage); the fact sentence
carrying the penalty is untouched. Exit 0 + report, hard failure otherwise.
"""
import hashlib
import json
import re
import sys

V63 = "benchmarks/hard/bank-hard-v6.3.json"
V64 = "benchmarks/hard/bank-hard-v6.4.json"
V63_SHA16 = "73f7a04d57473545"

raw3 = open(V63, "rb").read()
if hashlib.sha256(raw3).hexdigest()[:16] != V63_SHA16:
    sys.exit("FAIL: v6.3 bytes moved: %s" % hashlib.sha256(raw3).hexdigest()[:16])
raw4 = open(V64, "rb").read()
b3, b4 = json.loads(raw3), json.loads(raw4)
t3 = {t["id"]: t for t in b3}
t4 = {t["id"]: t for t in b4}

fail = []
if len(b3) != len(b4) or set(t3) != set(t4):
    fail.append("task set changed")
diffs = []
for tid in sorted(set(t3) & set(t4)):
    for field in sorted(set(t3[tid]) | set(t4[tid])):
        if json.dumps(t3[tid].get(field), ensure_ascii=False, sort_keys=True) != \
           json.dumps(t4[tid].get(field), ensure_ascii=False, sort_keys=True):
            diffs.append("%s.%s" % (tid, field))
if diffs != ["B-ex6-04.prompt"]:
    fail.append("changed fields %s != ['B-ex6-04.prompt']" % diffs)

gold = t4["B-ex6-04"]["ref"]
pr3, pr4 = t3["B-ex6-04"]["prompt"], t4["B-ex6-04"]["prompt"]
if gold != t3["B-ex6-04"]["ref"]:
    fail.append("gold changed")
if not re.search(r'"penalty_per_week":"[^"]*%[^"]*"', pr4):
    fail.append("penalty_per_week is not typed with a percent example")
hint_m = re.search(r'"penalty_per_week":"([^"]*)"', pr4)
hint_txt = hint_m.group(1) if hint_m else ""
ex = re.findall(r"(\d+%)", hint_txt)
if not ex:
    fail.append("no percent example inside the typed spec field")
elif ex[0] == gold["penalty_per_week"]:
    fail.append("the percent example equals the gold value (leak)")
if pr4.count("2026") != 2:
    fail.append("v6.3 stated year lost")
fact = "штраф за просрочку 2% в неделю."
if fact not in pr4 or fact not in pr3:
    fail.append("the fact sentence carrying the penalty changed on either side")
for tid in sorted(t3):
    for field in ("ref", "seed"):
        if json.dumps(t3[tid].get(field), ensure_ascii=False, sort_keys=True) != \
           json.dumps(t4[tid].get(field), ensure_ascii=False, sort_keys=True):
            fail.append("%s.%s changed" % (tid, field))

print("v6.3 sha16 %s  v6.4 sha16 %s  tasks %d" % (
    hashlib.sha256(raw3).hexdigest()[:16], hashlib.sha256(raw4).hexdigest()[:16], len(b4)))
print("changed fields:", diffs)
spec_m = re.search(r"JSON.*", pr4)
print("spec after:", spec_m.group(0)[:200] if spec_m else "?")
if fail:
    for f in fail:
        print("FAIL:", f)
    sys.exit(1)
print("PASS: v6.4 is v6.3 plus one value-form hint; every gold byte-identical, no leak")
