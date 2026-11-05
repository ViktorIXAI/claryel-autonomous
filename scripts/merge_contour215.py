#!/usr/bin/env python3
"""Merge contour 2.15 arm: 71 single-shot rows from hardv6-215 + loop rows from hardv6-215e."""
import json, sys

BASE = "/home/viktor/parb-2005-hardv6"
out = open("/home/viktor/parb-v6-raw/answers-contour215.jsonl", "w", encoding="utf-8")


def conv(r, loop_src=False):
    row = {"task": r["task"], "rep": r["rep"], "cat": r["cat"],
           "answer": r.get("answer") or ""}
    if r["task"].startswith("D-ex6-l"):
        steps = r.get("agent_steps") or []
        rows = []
        for s in steps:
            r0 = (s.get("parsed") if s.get("parsed") is not None
                  else {"gate_block": s.get("gate_block")})
            if s.get("gate_rejected") and isinstance(r0, dict):
                r0 = dict(r0, gate_rejected=True)
            rows.append(r0)
        row["answer"] = json.dumps({"_loop_rows": rows}, ensure_ascii=False)
    return row


base = {}
for l in open(BASE + "/results-hardv6-215f.jsonl", encoding="utf-8"):
    r = json.loads(l)
    base[(r["task"], r["rep"])] = r  # keep-last on resume duplicates
loops = {}
for l in open(BASE + "/results-hardv6-215f.jsonl", encoding="utf-8"):
    r = json.loads(l)
    loops[(r["task"], r["rep"])] = r
n = 0
for k in sorted(base):
    if k[0].startswith("D-ex6-l"):
        if k in loops:
            out.write(json.dumps(conv(loops[k], True), ensure_ascii=False) + "\n")
            n += 1
        continue
    out.write(json.dumps(conv(base[k]), ensure_ascii=False) + "\n")
    n += 1
out.close()
print("merged rows:", n, "loops replaced:", len(loops))
