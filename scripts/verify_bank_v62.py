#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify bank-hard-v6.2.json against the published v6.1 bytes.

Asserts:
  * v6.1 source file is byte-identical to its published identity (sha16);
  * v6.2 differs from v6.1 in EXACTLY three tasks, and only in these fields:
      A-ex6-03.ref, C-ex6-02.ref, K-ex6-03.prompt — every other task and
      every other field is byte-identical;
  * every v6.2 gold is still re-derivable from the shipped task bytes
    (A from the prompt's printed chain, C by executing the shipped options
    on this CPython);
  * task count, ids and seeds are unchanged.
Exit 0 + a per-field report on PASS, hard failure otherwise.
"""
import hashlib
import json
import re
import sys

V61 = "benchmarks/hard/bank-hard-v6.json"
V62 = "benchmarks/hard/bank-hard-v6.2.json"
V61_SHA16 = "9ec86dfca4a6f85f"

raw1 = open(V61, "rb").read()
if hashlib.sha256(raw1).hexdigest()[:16] != V61_SHA16:
    sys.exit("FAIL: v6.1 bytes moved: %s" % hashlib.sha256(raw1).hexdigest()[:16])
raw2 = open(V62, "rb").read()
b1 = json.loads(raw1)
b2 = json.loads(raw2)
if len(b1) != len(b2):
    sys.exit("FAIL: task count differs %d vs %d" % (len(b1), len(b2)))

t1 = {t["id"]: t for t in b1}
t2 = {t["id"]: t for t in b2}
if set(t1) != set(t2):
    sys.exit("FAIL: task ids differ")

allowed = {"A-ex6-03": {"ref"}, "C-ex6-02": {"ref"}, "K-ex6-03": {"prompt"}}
diff_fields = {}
for tid in sorted(t1):
    for field in sorted(set(t1[tid]) | set(t2[tid])):
        if t1[tid].get(field) != t2[tid].get(field):
            diff_fields.setdefault(tid, set()).add(field)
if {k: v for k, v in diff_fields.items()} != allowed:
    sys.exit("FAIL: unexpected diff: %s" % {k: sorted(v) for k, v in diff_fields.items()})
for tid in t1:
    if t1[tid].get("seed") != t2[tid].get("seed"):
        sys.exit("FAIL: seed moved on %s" % tid)

# re-derive the two derived golds from the v6.2 bytes themselves
a = t2["A-ex6-03"]
gross = float(re.search(r"gross=([0-9]+(?:\.[0-9]+)?)", a["prompt"]).group(1))
soc = min(float(re.search(r"Соцвзнос (\d+)%", a["prompt"]).group(1)) / 100 * gross,
          float(re.search(r"не более (\d+)", a["prompt"]).group(1)))
tax = max(float(re.search(r"Налог (\d+)%", a["prompt"]).group(1)) / 100 * (
    gross - soc - float(re.search(r"вычет (\d+)", a["prompt"]).group(1))), 0.0)
want = {"net": round(gross - soc - tax, 2), "social": round(soc, 2), "tax": round(tax, 2)}
if a["ref"] != want:
    sys.exit("FAIL: A-ex6-03 v6.2 ref %s != derived %s" % (a["ref"], want))

c = t2["C-ex6-02"]
opts = dict(re.findall(r"^([A-F]): (.*)$", c["prompt"], re.M))
truth = []
for letter in sorted(opts):
    ns = {}
    exec(compile("val=" + opts[letter], "<opt>", "exec"), ns)
    if ns["val"] == [1, 2, 3]:
        truth.append(letter)
if c["ref"]["letters"] != truth:
    sys.exit("FAIL: C-ex6-02 v6.2 letters %s != executed truth %s" % (c["ref"]["letters"], truth))

k = t2["K-ex6-03"]
if not k["prompt"].startswith(t1["K-ex6-03"]["prompt"]) or \
        k["prompt"] != t1["K-ex6-03"]["prompt"] + " (FREE_SHIPPING: yes/no)":
    sys.exit("FAIL: K-ex6-03 v6.2 prompt must be the v6.1 prompt + the form spec, nothing else")
if k["ref"] != ["кресла Oslo", "200", "14", "yes"]:
    sys.exit("FAIL: K-ex6-03 ref must stay byte-identical to v6.1")
if t1["K-ex6-03"]["ref"] != k["ref"]:
    sys.exit("FAIL: K-ex6-03 ref changed (only prompt may)")

print("PASS: v6.1 sha16 %s intact; v6.2 sha16 %s; tasks %d; diff exactly %s" % (
    V61_SHA16, hashlib.sha256(raw2).hexdigest()[:16], len(b2),
    {tid: sorted(f) for tid, f in diff_fields.items()}))
