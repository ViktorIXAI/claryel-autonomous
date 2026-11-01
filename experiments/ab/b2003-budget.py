#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2003 token budget: how many tok/s the machine delivers and how much of it is useful.

Source: results.jsonl, stage 7 = the reasoning-off run (the main reference).
Per category: decode speed, prefill speed, correct-answer share,
useful tokens per second (correct-answer tokens / all model time),
the share of reworked tokens.
"""
import json
import os
import statistics as st
from collections import defaultdict

ROOT = os.path.expanduser("~/.hermes/bench/parb")
NAME = {"A": "finance", "B": "extraction", "C": "logic", "D": "agent plan", "E": "programming",
        "F": "sysadmin", "G": "long contexts", "H": "hallucination",
        "I": "injections", "J": "format", "K": "languages"}

rows = [json.loads(l) for l in open(os.path.join(ROOT, "results.jsonl"), encoding="utf-8")
        if json.loads(l).get("series") == "main" and json.loads(l).get("stage") == 7]

g = defaultdict(list)
for r in rows:
    if r.get("engine_error") or not r.get("total_s"):
        continue
    g[r["cat"]].append(r)

print("%-4s %-26s %5s %7s %7s %8s %8s %8s %8s %8s %8s" % (
    "cat", "category", "rows", "sec", "tok/all", "decode", "prefill", "correct", "mean", "useful", "rework"))
tot = {"n": 0, "s": 0.0, "ct": 0, "ut": 0}
for c in sorted(g):
    rs = g[c]
    secs = sum(r["total_s"] for r in rs)
    ctok = sum(r["ctok"] for r in rs)
    ok = [r for r in rs if (r.get("content") or 0) >= 0.999]
    utok = sum(r["ctok"] for r in ok)
    dec = [r["decode_tps"] for r in rs if r.get("decode_tps")]
    pre = [r["prefill_tps"] for r in rs if r.get("prefill_tps") and r["ptok"] < 6000]
    tot["n"] += len(rs); tot["s"] += secs; tot["ct"] += ctok; tot["ut"] += utok
    mean_c = 100 * st.mean([r.get("content") or 0 for r in rs])
    print("%-4s %-26s %5d %7.2f %7d %8.0f %8.0f %7.0f%% %7.0f%% %8.1f %7.0f%%" % (
        c, NAME.get(c, c), len(rs), secs / len(rs), ctok / len(rs),
        st.mean(dec) if dec else 0, st.mean(pre) if pre else 0,
        100 * len(ok) / len(rs), mean_c, utok / secs, 100 * (1 - utok / max(ctok, 1))))
print("-" * 100)
print("%-4s %-26s %5d %7.2f %7d %8s %8s %7.0f%% %8.1f %7.0f%%" % (
    "", "total (reference, thinking off)", tot["n"], tot["s"] / tot["n"], tot["ct"] / tot["n"], "—", "—",
    100 * sum(1 for r in rows if (r.get("content") or 0) >= 0.999) / max(tot["n"], 1),
    tot["ut"] / tot["s"], 100 * (1 - tot["ut"] / tot["ct"])))

# --- money: two paths on B2003 (direct answer vs contour) ---
mp = os.path.expanduser("~/.hermes-cost/money-measure.jsonl")
if os.path.exists(mp):
    mm = [json.loads(l) for l in open(mp, encoding="utf-8") if json.loads(l).get("brain") == "B2003"]
    print("\nmoney on B2003: direct model answer vs contour (model itemises, code computes):")
    by = defaultdict(list)
    for x in mm:
        by[x["positions"]].append(x)
    for size in sorted(by):
        xs = by[size]
        for mode, key in (("model itself", "direct"), ("contour", "build")):
            secs = [x[key]["s"] for x in xs if x[key].get("s")]
            ctok = [x[key]["ctok"] for x in xs if x[key].get("ctok")]
            okc = sum(1 for x in xs if x.get(key + "_status") == "ok")
            if not secs:
                continue
            print("  %2d lines  %-11s n=%2d  %5.2f s  %4d tokens  decode %6.1f tok/s  correct %d/%d" % (
                size, mode, len(xs), st.mean(secs), st.mean(ctok) if ctok else 0,
                st.mean([c / s for c, s in zip(ctok, secs[:len(ctok)])]), okc, len(xs)))
        ef = [x["error_then_fix"] for x in xs if x.get("error_then_fix", {}).get("seconds")]
        if ef:
            print("  %2d lines  %-11s          %5.2f s  %4d tokens  (price of \"slip then fix\")" % (
                size, "slip+fix", st.mean([e["seconds"] for e in ef]), st.mean([e["tokens"] for e in ef])))
