#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paired loop-D report: two gate arms on the same (task, rep) loop tasks.

Prints one row per loop task with both arms' score, the drive events that produced it,
and the token/second cost, then the paired deltas and an exact sign-test p.
Usage: loop_pair_report.py A_RESULTS A_LEDGER B_RESULTS B_LEDGER [BANK]
"""
import json
import math
import sys

a_res, a_led, b_res, b_led = sys.argv[1:5]
bank_path = sys.argv[5] if len(sys.argv) > 5 else "bank.json"
bank = {t["id"]: t for t in json.load(open(bank_path, encoding="utf-8"))}


def load(res, led):
    rows = {}
    for ln in open(res, encoding="utf-8"):
        r = json.loads(ln)
        rows[(r["task"], r["rep"])] = r
    for ln in open(led, encoding="utf-8"):
        r = json.loads(ln)
        k = (r["task"], r["rep"])
        if k in rows:
            rows[k].update({x: r[x] for x in ("model_calls", "gate_fixes", "gate_blocks",
                                              "ptok", "ctok", "seconds", "events")})
    return rows


A, B = load(a_res, a_led), load(b_res, b_led)
keys = sorted(set(A) & set(B))
print("%-11s | %-22s | %-22s | %s" % ("task", "A content/fmt", "B content/fmt", "delta"))
win = lose = 0
for k in keys:
    a, b = A[k], B[k]
    fa, fb = bool(a.get("format_ok")), bool(b.get("format_ok"))
    sa = (a.get("content") or 0) + (1 if fa else 0)
    sb = (b.get("content") or 0) + (1 if fb else 0)
    if sa > sb:
        lose += 1
        d = "A"
    elif sb > sa:
        win += 1
        d = "B"
    else:
        d = "="
    print("%-11s | %5.2f %-5s %-11s | %5.2f %-5s %-11s | %s" % (
        k[0], a.get("content") or 0.0, fa, ",".join(a.get("notes") or [])[:11],
        b.get("content") or 0.0, fb, ",".join(b.get("notes") or [])[:11], d))
print()
for tag, X in (("A", A), ("B", B)):
    strict = sum(1 for k in keys if A is not None and bool(X[k].get("format_ok"))
                 and (X[k].get("content") or 0) == 1.0)
    calls = sum(X[k].get("model_calls") or 0 for k in keys)
    ptok = sum(X[k].get("ptok") or 0 for k in keys)
    ctok = sum(X[k].get("ctok") or 0 for k in keys)
    secs = sum(X[k].get("seconds") or 0 for k in keys)
    print("%s: strict %d/%d  calls=%d ptok=%d ctok=%d secs=%.1f" % (tag, strict, len(keys),
                                                                    calls, ptok, ctok, secs))
# exact two-sided sign test on discordant pairs
n = win + lose
if n:
    lo = min(win, lose)
    tail = sum(math.comb(n, i) for i in range(lo + 1)) / 2.0 ** n
    p = min(1.0, 2 * tail)
else:
    p = 1.0
print("paired: B wins %d, A wins %d, ties %d  exact sign-test p=%.4f" % (win, lose,
                                                                         len(keys) - n, p))
print("\nper-task drive events")
for k in keys:
    print(" %s A: %s" % (k[0], ",".join(A[k].get("events") or [])))
    print(" %s B: %s" % (k[0], ",".join(B[k].get("events") or [])))
