#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analysis for the budget-matched simple-baselines experiment.

Joins the four simple arms (baselines-results.jsonl) with two contour
reference series:
  S3_p2005  contour v1.9 re-run on the SAME box/engine as the arms
            (contour-p2005.jsonl + ledger) — the primary paired comparison
  S3_b2003  published contour v1.9 B2003 finals (cross-box reference)

Prints the tables published in results/baselines.md.

Usage:
  PARB_V19=<results-v19-b2003.jsonl> PARB_V19_LEDGER=<gate-ledger-v19-b2003.jsonl> \
  python3 experiments/baselines/analyze_baselines.py [data-dir]
"""
import json, os, sys
from collections import defaultdict

D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "data")
ARMS = ("S0_direct", "S1_generic", "S2_min_gate", "S4_best_of_2")


def rows(p):
    out = []
    for ln in open(p, encoding="utf-8", errors="ignore"):
        try:
            out.append(json.loads(ln))
        except Exception:
            pass
    return out


def dedup_best(rs):
    d = {}
    for r in rs:
        k = (r["task"], r["rep"])
        if k not in d or float(r.get("content") or 0) > float(d[k].get("content") or 0):
            d[k] = r
    return d


def agg(d, tok_key=("ptok", "ctok"), s_key="total_s", c_key="content", f_key="format_ok", calls_key="calls"):
    n = len(d)
    if not n:
        return None
    return {"n": n,
            "mean_c": sum(float(r.get(c_key) or 0) for r in d.values()) / n,
            "fmt": sum(float(r.get(f_key) or 0) for r in d.values()) / n,
            "tok": sum((r.get(tok_key[0]) or 0) + (r.get(tok_key[1]) or 0) for r in d.values()) / n,
            "s": sum(float(r.get(s_key) or 0) for r in d.values()) / n,
            "calls": sum(float(r.get(calls_key) or 0) for r in d.values()) / n}


def contour_from_ledger(ledger_rows, pairs):
    led = defaultdict(lambda: {"calls": 0, "ptok": 0, "ctok": 0, "total_s": 0.0})
    for r in ledger_rows:
        k = (r.get("task"), r.get("rep"))
        if k in pairs:
            a = led[k]
            a["calls"] += r.get("model_calls") or 0
            a["ptok"] += r.get("ptok") or 0
            a["ctok"] += r.get("ctok") or 0
            a["total_s"] += r.get("seconds") or 0.0
    return led


def main():
    arms = {}
    for r in rows(os.path.join(D, "baselines-results.jsonl")):
        arms.setdefault(r["arm"], {})[(r["task"], r["rep"])] = r
    pairs = set()
    for d in arms.values():
        pairs |= set(d)

    c2005 = dedup_best(rows(os.path.join(D, "contour-p2005.jsonl")))
    c2005 = {k: v for k, v in c2005.items() if k in pairs}
    led2005 = contour_from_ledger(rows(os.path.join(D, "contour-p2005-ledger.jsonl")), pairs)
    for k, r in c2005.items():
        a = led2005.get(k)
        if a:
            r["calls"] = a["calls"]
            r["ptok"], r["ctok"], r["total_s"] = a["ptok"], a["ctok"], a["total_s"]

    v19p = os.environ.get("PARB_V19")
    v19l = os.environ.get("PARB_V19_LEDGER")
    c1803 = {}
    if v19p and os.path.exists(v19p):
        c1803 = {k: v for k, v in dedup_best(rows(v19p)).items() if k in pairs}
        if v19l and os.path.exists(v19l):
            led1803 = contour_from_ledger(rows(v19l), pairs)
            for k, r in c1803.items():
                a = led1803.get(k)
                if a:
                    r["calls"] = a["calls"]
                    r["ptok"], r["ctok"], r["total_s"] = a["ptok"], a["ctok"], a["total_s"]

    print("paired pairs:", len(pairs))
    print("\n| arm | n | mean content | format_ok | tokens/task | seconds/task | model calls/task |")
    print("|---|---|---|---|---|---|---|")
    for name, d in [(a, arms[a]) for a in ARMS] + [("S3_contour_v1.9 (P2005, same box)", c2005),
                                                   ("S3_contour_v1.9 (B2003, published)", c1803)]:
        g = agg(d)
        if not g:
            continue
        print("| %s | %d | %.3f | %.0f%% | %.0f | %.1f | %.2f |" %
              (name, g["n"], g["mean_c"], 100 * g["fmt"], g["tok"], g["s"], g["calls"]))

    print("\npaired vs contour on the SAME box (content delta = contour - arm):")
    print("\n| arm | n | mean delta | contour better | arm better | tie |")
    print("|---|---|---|---|---|---|")
    for a in ARMS:
        dl = []
        for k, r in arms[a].items():
            v = c2005.get(k)
            if not v:
                continue
            dl.append(float(v.get("content") or 0) - float(r.get("content") or 0))
        up = sum(1 for x in dl if x > 1e-9)
        dn = sum(1 for x in dl if x < -1e-9)
        print("| %s | %d | %+.4f | %d | %d | %d |" % (a, len(dl), sum(dl) / len(dl), up, dn, len(dl) - up - dn))

    print("\nper-category mean content (P2005 contour column is the paired one):")
    cats = defaultdict(lambda: defaultdict(list))
    for a in ARMS:
        for k, r in arms[a].items():
            cats[k[0][0]][a].append(float(r.get("content") or 0))
    for k, r in c2005.items():
        cats[k[0][0]]["S3_p2005"].append(float(r.get("content") or 0))
    for k, r in c1803.items():
        cats[k[0][0]]["S3_b2003"].append(float(r.get("content") or 0))
    cols = list(ARMS) + ["S3_p2005", "S3_b2003"]
    print("\n| cat | " + " | ".join(cols) + " |")
    print("|---|" + "---|" * len(cols))
    for c in sorted(cats):
        cells = []
        for col in cols:
            v = cats[c].get(col)
            cells.append("%.3f" % (sum(v) / len(v)) if v else "—")
        print("| %s | %s |" % (c, " | ".join(cells)))


if __name__ == "__main__":
    main()
