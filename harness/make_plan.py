#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publication convenience: build plan.json from benchmarks/text-gates/bank.json into PARB_ROOT.
(NOT part of the original runs: there the plan was prepared by parb_prep.py and
frozen; this wrapper reproduces the same freeze: plan + plan_hash printed, then
never edited mid-series.)"""
import json, os, sys

ROOT = os.path.expanduser(os.environ.get("PARB_ROOT", "~/parb"))
BANK = os.environ.get("PARB_BANK", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "..", "benchmarks", "text-gates", "bank.json"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parb_plan as PL

tasks = json.load(open(BANK, encoding="utf-8"))
plan = PL.build(tasks)
os.makedirs(ROOT, exist_ok=True)
# the runner reads BOTH plan.json and bank.json from PARB_ROOT (parb_prep staged
# them there in the original runs; this wrapper does the same staging)
import shutil
shutil.copyfile(BANK, os.path.join(ROOT, "bank.json"))
path = os.path.join(ROOT, "plan.json")
json.dump(plan, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("plan: %d positions -> %s, plan_hash=%s" % (len(plan), path, PL.plan_hash(plan)))
