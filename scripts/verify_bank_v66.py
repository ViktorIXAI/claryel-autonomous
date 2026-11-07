#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify bank-hard-v6.6.json against the published v6.5 bytes.

Asserts: v6.5 identity sha16 cd29d6ac94dc3267; EXACTLY one changed task/field
(H-ex6-01.prompt); every gold (ref) and seed byte-identical over all 77 tasks;
the old inviting claims fragment is gone from H-ex6-01 and the confirmation-
conditional wording is present; the v6.5 scenario fix ("есть только аудит-лог
operations") survives; the added text carries no gold atoms (leak check against
ref unknown/ask); the other four H tasks keep the old fragment byte-identical
(coverage limit, published not hidden). Exit 0 + report, hard failure otherwise.
"""
import hashlib
import json
import sys

V65 = "benchmarks/hard/bank-hard-v6.5.json"
V66 = "benchmarks/hard/bank-hard-v6.6.json"
V65_SHA16 = "cd29d6ac94dc3267"
FRAG_OLD = "[утверждения как факт]"
FRAG_NEW_MARK = "только утверждения, подтверждённые твоим журналом"

raw5 = open(V65, "rb").read()
if hashlib.sha256(raw5).hexdigest()[:16] != V65_SHA16:
    sys.exit("FAIL: v6.5 bytes moved: %s" % hashlib.sha256(raw5).hexdigest()[:16])
raw6 = open(V66, "rb").read()
b5, b6 = json.loads(raw5), json.loads(raw6)
t5 = {t["id"]: t for t in b5}
t6 = {t["id"]: t for t in b6}

fail = []
if len(b5) != len(b6) or set(t5) != set(t6):
    fail.append("task set changed")
diffs = []
for tid in sorted(set(t5) & set(t6)):
    for field in sorted(set(t5[tid]) | set(t6[tid])):
        if json.dumps(t5[tid].get(field), ensure_ascii=False, sort_keys=True) != \
           json.dumps(t6[tid].get(field), ensure_ascii=False, sort_keys=True):
            diffs.append("%s.%s" % (tid, field))
if diffs != ["H-ex6-01.prompt"]:
    fail.append("changed fields %s != ['H-ex6-01.prompt']" % diffs)

pr5, pr6 = t5["H-ex6-01"]["prompt"], t6["H-ex6-01"]["prompt"]
ref5, ref6 = t5["H-ex6-01"]["ref"], t6["H-ex6-01"]["ref"]
if ref5 != ref6:
    fail.append("H-ex6-01 gold changed")
if FRAG_OLD not in pr5:
    fail.append("v6.5 prompt lacks the inviting fragment (defect claim wrong)")
if FRAG_OLD in pr6:
    fail.append("v6.6 prompt still carries the inviting fragment")
if FRAG_NEW_MARK not in pr6:
    fail.append("v6.6 prompt lacks the confirmation-conditional claims rule")
if "есть только аудит-лог operations" not in pr5 or \
   "есть только аудит-лог operations" not in pr6:
    fail.append("v6.5 scenario fix did not survive into v6.6")
# leak check: the ADDED text must carry no gold atoms (difflib inserts only —
# pr5 is not a contiguous substring of pr6, a naive .replace would "add" everything)
import difflib
_sm = difflib.SequenceMatcher(None, pr5, pr6)
added = "".join(pr6[i2:j2] for tag, i1, j1, i2, j2 in _sm.get_opcodes()
                if tag in ("insert", "replace"))
for atom in [ref6["unknown"]] + list(ref6.get("ask") or []):
    if str(atom).split()[0].lower() in added.lower():
        fail.append("added text leaks gold atom: %s" % atom)
# coverage limit: the other four H tasks keep the old fragment byte-identical
for tid in ("H-ex6-00", "H-ex6-02", "H-ex6-03", "H-ex6-04"):
    if t5[tid]["prompt"] != t6[tid]["prompt"] or FRAG_OLD not in t6[tid]["prompt"]:
        fail.append("coverage limit broken on %s" % tid)
for tid in sorted(t5):
    for field in ("ref", "seed"):
        if json.dumps(t5[tid].get(field), ensure_ascii=False, sort_keys=True) != \
           json.dumps(t6[tid].get(field), ensure_ascii=False, sort_keys=True):
            fail.append("%s.%s changed" % (tid, field))

print("v6.5 sha16 %s  v6.6 sha16 %s  tasks %d" % (
    hashlib.sha256(raw5).hexdigest()[:16], hashlib.sha256(raw6).hexdigest()[:16], len(b6)))
print("changed fields:", diffs)
print("claims rule after:", FRAG_NEW_MARK in pr6)
if fail:
    for f in fail:
        print("FAIL:", f)
    sys.exit(1)
print("PASS: v6.6 is v6.5 plus one claims-field spec clarification on H-ex6-01; "
      "every gold byte-identical; no leak; four other H prompts byte-identical (coverage limit published)")
