#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sanity contract for the frozen benchmark data (fails CI on drift)."""
import json
import sys

bank = json.load(open("benchmarks/text-gates/bank.json", encoding="utf-8"))
ids = [t["id"] for t in bank]
assert len(ids) == 178, "bank size %d != 178" % len(ids)
assert len(set(ids)) == len(ids), "duplicate task ids"
cats = {i[0] for i in ids}
assert cats <= set("ABCDEFGHIJK"), "unknown categories %s" % (cats - set("ABCDEFGHIJK"))
for t in bank:
    assert t.get("prompt"), "task %s without prompt" % t["id"]
plan = json.load(open("benchmarks/text-gates/plan-example.json", encoding="utf-8"))
pos = plan if isinstance(plan, list) else (plan.get("plan") or plan.get("positions"))
assert len(pos) == 681, "plan-example positions %d != 681" % len(pos)
bank_ids = set(ids)
for p in pos[:681]:
    tid = p["task"] if isinstance(p, dict) else p[0]
    assert tid in bank_ids, "plan references unknown task %s" % tid
holdout = "benchmarks/holdout/bank-holdout.json"
try:
    hb = json.load(open(holdout, encoding="utf-8"))
    hid = {t["id"] for t in hb}
    assert not (hid & bank_ids), "holdout overlaps the dev bank: %s" % (hid & bank_ids)
    print("holdout disjoint ok:", len(hid))
except FileNotFoundError:
    print("holdout bank: absent (not asserted)")
print("SANITY-OK bank=178 plan=681 cats=%d" % len(cats))
sys.exit(0)
