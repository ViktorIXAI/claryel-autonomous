#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rescore every published arm's A-ex6-03 / C-ex6-02 answer bytes under bank v6.2.

Both sides are RE-COMPUTED from the same stored bytes: v6.1 reference (published
9ec86dfca4a6f85f) vs v6.2 reference (3c866ea7daae611c), with the frozen scorer
harness/parb_check_v6.py (check_json_obj for A, check_C_v6 for C). No model call,
no contour: pure text replay. A row counts only if its answer field is non-empty;
blank/missing answers are counted separately and never scored.

Writes rescore-v62/rescore-v62.csv (one row per joined (arm,task,rep)) and prints
the summary. Strict = content==1.0 and format_ok (the published scoreboard rule).
"""
import csv
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "harness"))
import parb_check_v6 as CK  # noqa: E402

V61 = json.load(open(os.path.join(ROOT, "benchmarks/hard/bank-hard-v6.json")))
V62 = json.load(open(os.path.join(ROOT, "benchmarks/hard/bank-hard-v6.2.json")))
T61 = {t["id"]: t for t in V61}
T62 = {t["id"]: t for t in V62}
TASKS = ["A-ex6-03", "C-ex6-02"]
for tid in TASKS:
    if T61[tid]["ref"] == T62[tid]["ref"]:
        sys.exit("FATAL: %s refs identical - bank v6.2 file wrong" % tid)

BASE = os.path.join(ROOT, "benchmarks/hard/v6-results")
files = []
for pat in ("*/results-*.jsonl", "answers-*.jsonl", "raw-reps-v61/answers-*.jsonl",
            "four-arm-v61/answers-*.jsonl"):
    files += sorted(glob.glob(os.path.join(BASE, pat)))
files = [f for f in files if "/pair-244/" not in f and "/reps-229/" not in f
         and "/j-probe" not in f and "/k-218" not in f and "/ABLATION" not in f]

def scorer(tid):
    return CK.check_C_v6 if tid == "C-ex6-02" else CK.check_json_obj

def strict_score(task, ans):
    c, f, _ = scorer(task["id"])(task, ans)
    return c, bool(f)

rows = []
blanks = {}
for fp in files:
    rel = os.path.relpath(fp, BASE)
    blanks.setdefault(rel, 0)
    with open(fp, encoding="utf-8") as fh:
        for ln in fh:
            if not ln.strip():
                continue
            r = json.loads(ln)
            tid = r.get("task")
            if tid not in TASKS:
                continue
            ans = r.get("answer") or ""
            if not ans.strip():
                blanks[rel] += 1
                continue
            c1, f1 = strict_score(T61[tid], ans)
            c2, f2 = strict_score(T62[tid], ans)
            s1 = c1 == 1.0 and f1
            s2 = c2 == 1.0 and f2
            stored = r.get("content"), r.get("format_ok")
            rows.append({
                "arm": rel, "task": tid, "rep": r.get("rep"),
                "old_content": c1, "old_fmt": int(f1), "old_strict": int(s1),
                "new_content": c2, "new_fmt": int(f2), "new_strict": int(s2),
                "flip": "WIN" if (s2 and not s1) else ("LOSE" if (s1 and not s2) else ""),
                "stored_content": stored[0], "stored_fmt": int(bool(stored[1])),
                "stored_mismatch": int(stored[0] != c1 or bool(stored[1]) != f1),
            })

out_dir = os.path.join(BASE, "rescore-v62")
os.makedirs(out_dir, exist_ok=True)
csv_path = os.path.join(out_dir, "rescore-v62.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

per = {t: dict(rows=0, v61=0, v62=0, win=0, lose=0, mismatch=0) for t in TASKS}
arm_flips = {}
for r in rows:
    p = per[r["task"]]
    p["rows"] += 1
    p["v61"] += r["old_strict"]
    p["v62"] += r["new_strict"]
    p["win"] += r["flip"] == "WIN"
    p["lose"] += r["flip"] == "LOSE"
    p["mismatch"] += r["stored_mismatch"]
    if r["flip"]:
        arm_flips[(r["arm"], r["task"], r["rep"])] = r["flip"]

print("files scanned: %d; joined cells: %d; blank answers skipped: %d"
      % (len(files), len(rows), sum(blanks.values())))
for t in TASKS:
    p = per[t]
    print("%s: rows=%d strict v6.1=%d v6.2=%d WIN=%d LOSE=%d stored-score-mismatch=%d"
          % (t, p["rows"], p["v61"], p["v62"], p["win"], p["lose"], p["mismatch"]))
print("flip cells:")
for k, v in sorted(arm_flips.items()):
    print(" ", v, k)
print("wrote", csv_path)
