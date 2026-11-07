#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify bank-hard-v6.5.json against the published v6.4 bytes.

Asserts: v6.4 identity sha16; EXACTLY one changed task/field (H-ex6-01.prompt);
every gold (ref) and seed byte-identical over all 77 tasks; the scenario sentence
now names the artifact the reference asks for ("аудит-лог operations"); under the
frozen scorer's own _token_cover semantics the gold ask item is derivable from the
fixed prompt, and was NOT derivable from the v6.4 prompt; the JSON field spec and
the "do not attribute actions to yourself" sentence are untouched. Exit 0 + report,
hard failure otherwise.
"""
import hashlib
import json
import sys

V64 = "benchmarks/hard/bank-hard-v6.4.json"
V65 = "benchmarks/hard/bank-hard-v6.5.json"
V64_SHA16 = "85a0cd0dd6fa1fab"

raw4 = open(V64, "rb").read()
if hashlib.sha256(raw4).hexdigest()[:16] != V64_SHA16:
    sys.exit("FAIL: v6.4 bytes moved: %s" % hashlib.sha256(raw4).hexdigest()[:16])
raw5 = open(V65, "rb").read()
b4, b5 = json.loads(raw4), json.loads(raw5)
t4 = {t["id"]: t for t in b4}
t5 = {t["id"]: t for t in b5}

sys.path.insert(0, "harness")
import parb_check_v6 as CK

fail = []
if len(b4) != len(b5) or set(t4) != set(t5):
    fail.append("task set changed")
diffs = []
for tid in sorted(set(t4) & set(t5)):
    for field in sorted(set(t4[tid]) | set(t5[tid])):
        if json.dumps(t4[tid].get(field), ensure_ascii=False, sort_keys=True) != \
           json.dumps(t5[tid].get(field), ensure_ascii=False, sort_keys=True):
            diffs.append("%s.%s" % (tid, field))
if diffs != ["H-ex6-01.prompt"]:
    fail.append("changed fields %s != ['H-ex6-01.prompt']" % diffs)

pr4, pr5 = t4["H-ex6-01"]["prompt"], t5["H-ex6-01"]["prompt"]
ref4, ref5 = t4["H-ex6-01"]["ref"], t5["H-ex6-01"]["ref"]
if ref4 != ref5:
    fail.append("H-ex6-01 gold changed")
if "аудит-лог operations" in pr4:
    fail.append("v6.4 prompt already named the artifact (defect claim wrong)")
if "есть только аудит-лог operations" not in pr5:
    fail.append("v6.5 prompt does not name the artifact")
# the frozen scorer's own coverage rule must now derive every ask item from the prompt
for a in ref5["ask"]:
    if not CK._token_cover(pr5, [a]):
        fail.append("ask item still not derivable: %s" % a)
    if CK._token_cover(pr4, [a]):
        fail.append("ask item was already derivable on v6.4: %s" % a)
for keep in ("Верни JSON:", "Не приписывай себе действия",
             "claims\": [утверждения как факт]"):
    if keep not in pr4 or keep not in pr5:
        fail.append("spec/fact sentence changed on either side: %s" % keep)
for tid in sorted(t4):
    for field in ("ref", "seed"):
        if json.dumps(t4[tid].get(field), ensure_ascii=False, sort_keys=True) != \
           json.dumps(t5[tid].get(field), ensure_ascii=False, sort_keys=True):
            fail.append("%s.%s changed" % (tid, field))

print("v6.4 sha16 %s  v6.5 sha16 %s  tasks %d" % (
    hashlib.sha256(raw4).hexdigest()[:16], hashlib.sha256(raw5).hexdigest()[:16], len(b5)))
print("changed fields:", diffs)
print("scenario after:", pr5.split("\n")[0])
if fail:
    for f in fail:
        print("FAIL:", f)
    sys.exit(1)
print("PASS: v6.5 is v6.4 plus one scenario sentence naming the artifact; "
      "every gold byte-identical; ask derivable only after the fix")
