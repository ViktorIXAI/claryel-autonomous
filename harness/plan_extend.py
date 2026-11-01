#!/usr/bin/env python3
"""Extend plan.json with v1.8 rounds: identical (task, rep, gseed) on every box.
Usage: plan_extend.py END_REP   (start fixed at 307)"""
import hashlib, json, os, sys, shutil

PLAN = os.path.expanduser("~/parb/plan.json")
TASKS = ['A-me-00-0', 'B-ha-03-0', 'C-ha-01-0', 'D-ea-00-0', 'E-ha-04-0',
         'F-ha-01-0', 'F-ha-02-0', 'G-me-04', 'H-ha-04-0', 'I-me-00-0',
         'J-ha-01-0', 'K-ha-04-0']
START = 307
end = int(sys.argv[1])

p = json.load(open(PLAN, encoding="utf-8"))
stage_by_task = {}
for e in p:
    stage_by_task[e["task"]] = e.get("stage", 7)
have = {(e["task"], e["rep"]) for e in p}
add = 0
for rep in range(START, end + 1):
    for tid in TASKS:
        if (tid, rep) in have:
            continue
        g = int(hashlib.sha256(("%s|%d" % (tid, rep)).encode()).hexdigest()[:8], 16) % 999983
        p.append({"task": tid, "rep": rep, "rep_group": "ext-v18",
                  "series": "main", "stage": stage_by_task.get(tid, 7), "gseed": g})
        add += 1
shutil.copy(PLAN, PLAN + ".bak-v18")
json.dump(p, open(PLAN, "w", encoding="utf-8"), ensure_ascii=False)
print("plan total %d, added %d, reps up to %d" % (len(p), add, end))
