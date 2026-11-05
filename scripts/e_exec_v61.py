#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Execute the category-E batteries for the v6.1 four arms and cache the results.

`run_battery` needs docker; each battery is isolated (oracle_isolated_v3). Output:
benchmarks/hard/v6-results/four-arm-v61/E-EXEC.json  {arm: {task: [content, format_ok, notes]}}
Safe to re-run; existing entries are skipped.
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "harness"))
_spec = importlib.util.spec_from_file_location("parb_check_v6", os.path.join(ROOT, "harness", "parb_check_v6.py"))
assert _spec and _spec.loader
CK = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CK)

RAW = os.path.expanduser("~/parb-v61-raw")
WS = os.path.expanduser("~/parb-v61-contour")
OUT = os.path.join(ROOT, "benchmarks", "hard", "v6-results", "four-arm-v61", "E-EXEC.json")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

bank = {t["id"]: t for t in json.load(open(os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json"), encoding="utf-8"))}
E_IDS = [t["id"] for t in bank.values() if t["cat"] == "E"]

SOURCES = {
    "contour": os.path.join(WS, "results-c228v61.jsonl"),
    "basalt": os.path.join(RAW, "answers-basalt.jsonl"),
    "codex": os.path.join(RAW, "answers-codex.jsonl"),
    "grok": os.path.join(RAW, "answers-grok.jsonl"),
}

cache = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
for arm, path in SOURCES.items():
    if not os.path.exists(path):
        print("%-8s missing answers file" % arm)
        continue
    answers = {}
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        if r["task"] in E_IDS:
            answers[r["task"]] = r.get("answer")
    slot = cache.setdefault(arm, {})
    for tid in E_IDS:
        if tid in slot:
            continue
        try:
            c, f, notes = CK.check(bank[tid], answers.get(tid) or "")
        except Exception as exc:
            c, f, notes = 0.0, False, ["exec_error:%s" % type(exc).__name__]
        slot[tid] = [c, bool(f), list(notes)]
        print("%-8s %-10s c=%.2f fmt=%s %s" % (arm, tid, c, f, ",".join(notes) or "-"), flush=True)
        json.dump(cache, open(OUT, "w", encoding="utf-8"), indent=1)
print("wrote", OUT)
