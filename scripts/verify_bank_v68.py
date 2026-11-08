#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify bank-hard-v6.8.json vs published v6.7: exactly H-ex6-00/H-ex6-03 prompts
move; all seeds/refs byte-identical (C-ex6-01 gold [C,F] preserved); old v6.7 claims
fragment gone from those two tasks and replaced by the session-state exclusion;
H-ex6-01/H-ex6-02/H-ex6-04 prompts byte-identical; exit 0 + report else FAIL."""
import hashlib, json, sys
V67="benchmarks/hard/bank-hard-v6.7.json"; V68="benchmarks/hard/bank-hard-v6.8.json"
V67_SHA16="b4464127dc5b5b97"
OLD='данными, а не текстом задачи; если таких нет — пустой список]'
NEW='самого акта ответа сюда не пишутся'
raw7=open(V67,"rb").read()
if hashlib.sha256(raw7).hexdigest()[:16]!=V67_SHA16: sys.exit("FAIL: v6.7 bytes moved")
b7,b8=json.loads(raw7),json.loads(open(V68,"rb").read())
t7={t["id"]:t for t in b7}; t8={t["id"]:t for t in b8}
fail=[]
diffs=set()
for tid in sorted(set(t7)&set(t8)):
    for f in sorted(set(t7[tid])|set(t8[tid])):
        if json.dumps(t7[tid].get(f),ensure_ascii=False,sort_keys=True)!=json.dumps(t8[tid].get(f),ensure_ascii=False,sort_keys=True):
            diffs.add("%s.%s"%(tid,f))
if diffs!={"H-ex6-00.prompt","H-ex6-03.prompt"}: fail.append("diff set %s"%sorted(diffs))
for tid in t7:
    if json.dumps(t7[tid].get("ref"),ensure_ascii=False,sort_keys=True)!=json.dumps(t8[tid].get("ref"),ensure_ascii=False,sort_keys=True): fail.append("ref moved "+tid)
    if t7[tid].get("seed")!=t8[tid].get("seed"): fail.append("seed moved "+tid)
for tid in ("H-ex6-00","H-ex6-03"):
    p=t8[tid]["prompt"]
    if OLD in p or NEW not in p: fail.append("claims wording not updated "+tid)
    if p.count("claims")<1: fail.append("claims field missing "+tid)
for tid in ("H-ex6-01","H-ex6-02","H-ex6-04"):
    if t7[tid]["prompt"]!=t8[tid]["prompt"]: fail.append("H byte drift "+tid)
if t8["C-ex6-01"]["ref"]!={"letters":["C","F"],"n_cand":6}: fail.append("C gold not preserved")
if fail: sys.exit("FAIL\n"+"\n".join(fail))
print("VERIFY v6.8 PASS | v6.8 sha16", hashlib.sha256(open(V68,"rb").read()).hexdigest()[:16])
