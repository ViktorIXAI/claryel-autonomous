#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify bank-hard-v6.7.json against published v6.6 bytes.

Asserts: v6.6 identity sha16 5c86252b2ef2f422; the changed (task,field) set is
EXACTLY C-ex6-01.ref + prompts of F-ex6-01,H-ex6-00,H-ex6-03,K-ex6-00,K-ex6-01;
every seed and every other ref byte-identical over all 77 tasks; the C gold is
[C,F] with n_cand untouched; F carries the id-form pin and the grounded N2 danger
line; H00/H03 carry the confirmation-conditional claims wording and lost the
inviting fragment; K00/K01 carry the boolean pin and K01 the non-gold Latin
SERVICE example (example != gold, v6.4 doctrine); H-ex6-02/H-ex6-04 keep the old
claims fragment byte-identical — coverage limit, published not hidden (raw arms
pass those cells, so they are NOT defect verdicts). Exit 0 + report otherwise FAIL.
"""
import hashlib, json, sys

V66 = "benchmarks/hard/bank-hard-v6.6.json"
V67 = "benchmarks/hard/bank-hard-v6.7.json"
V66_SHA16 = "5c86252b2ef2f422"
EXPECT_DIFF = {"C-ex6-01.ref", "F-ex6-01.prompt", "H-ex6-00.prompt",
               "H-ex6-03.prompt", "K-ex6-00.prompt", "K-ex6-01.prompt"}
FRAG_OLD = "[утверждения как факт]"
FRAG_NEW = "а не текстом задачи"

raw6 = open(V66, "rb").read()
if hashlib.sha256(raw6).hexdigest()[:16] != V66_SHA16:
    sys.exit("FAIL: v6.6 bytes moved: %s" % hashlib.sha256(raw6).hexdigest()[:16])
raw7 = open(V67, "rb").read()
b6, b7 = json.loads(raw6), json.loads(raw7)
t6 = {t["id"]: t for t in b6}
t7 = {t["id"]: t for t in b7}

fail = []
if len(b6) != len(b7) or set(t6) != set(t7):
    fail.append("task set changed")
diffs = set()
for tid in sorted(set(t6) & set(t7)):
    for field in sorted(set(t6[tid]) | set(t7[tid])):
        if json.dumps(t6[tid].get(field), ensure_ascii=False, sort_keys=True) != \
           json.dumps(t7[tid].get(field), ensure_ascii=False, sort_keys=True):
            diffs.add("%s.%s" % (tid, field))
if diffs != EXPECT_DIFF:
    fail.append("unexpected diff set: %s" % sorted(diffs))

for tid in t6:
    if t6[tid].get("seed") != t7[tid].get("seed"):
        fail.append("seed moved: " + tid)
    if tid != "C-ex6-01" and json.dumps(t6[tid].get("ref"), ensure_ascii=False, sort_keys=True) != \
       json.dumps(t7[tid].get("ref"), ensure_ascii=False, sort_keys=True):
        fail.append("ref moved: " + tid)
if t7["C-ex6-01"]["ref"] != {"letters": ["C", "F"], "n_cand": 6}:
    fail.append("C-ex6-01 gold unexpected: %r" % t7["C-ex6-01"]["ref"])

pF = t7["F-ex6-01"]["prompt"]
if "в значении — ровно id: N1, N2 или N3" not in pF or "Опасно при текущем инциденте: N2" not in pF:
    fail.append("F-ex6-01 missing form-pin or danger line")
for tid in ("H-ex6-00", "H-ex6-03"):
    p = t7[tid]["prompt"]
    if FRAG_OLD in p or FRAG_NEW not in p:
        fail.append("claims fragment not repaired in " + tid)
for tid in ("H-ex6-02", "H-ex6-04"):
    if t7[tid]["prompt"] != t6[tid]["prompt"]:
        fail.append("H coverage limit violated: " + tid)
pK0 = t7["K-ex6-00"]["prompt"]; pK1 = t7["K-ex6-01"]["prompt"]
if "ровно yes или no" not in pK0 or "ровно yes или no" not in pK1:
    fail.append("boolean pin missing")
if "например, delivery" not in pK1 or "delivery" in json.dumps(t7["K-ex6-01"]["ref"], ensure_ascii=False):
    fail.append("K-ex6-01 SERVICE example missing or equals gold")

if fail:
    sys.exit("FAIL\n" + "\n".join(fail))
print("VERIFY v6.7 PASS | v6.6 sha16 %s | v6.7 sha16 %s" % (
    V66_SHA16, hashlib.sha256(raw7).hexdigest()[:16]))
print("changed:", ", ".join(sorted(diffs)))
