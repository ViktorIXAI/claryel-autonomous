#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paired full-bank A/B report for two gate arms on identical (task, rep) keys.

Prints strict totals, per-category table, the per-cell flip list (what actually changed),
paired win/loss with an exact sign test, and the token/second cost of each arm.
Usage: full_pair_report.py A_RESULTS A_LEDGER B_RESULTS B_LEDGER [BANK]
Strict = content == 1.0 AND format_ok. Deduped by (task, rep) keeping the best score.
"""
import json
import math
import sys
from collections import defaultdict

a_res, a_led, b_res, b_led = sys.argv[1:5]
bank_path = sys.argv[5] if len(sys.argv) > 5 else "bank.json"
bank = {t["id"]: t for t in json.load(open(bank_path, encoding="utf-8"))}
loop = {k for k in bank if bank[k].get("mode") == "loop"}


def load(res, led):
    rows = {}
    for ln in open(res, encoding="utf-8"):
        r = json.loads(ln)
        k = (r["task"], r["rep"])
        s = ((r.get("content") or 0) + (1 if r.get("format_ok") else 0))
        if k not in rows or s > ((rows[k].get("content") or 0) + (1 if rows[k].get("format_ok") else 0)):
            rows[k] = r
    for ln in open(led, encoding="utf-8"):
        r = json.loads(ln)
        k = (r["task"], r["rep"])
        if k in rows:
            rows[k]["_ev"] = r.get("events") or []
            rows[k]["_calls"] = r.get("model_calls") or 0
            rows[k]["_ptok"] = r.get("ptok") or 0
            rows[k]["_ctok"] = r.get("ctok") or 0
            rows[k]["_sec"] = r.get("seconds") or 0
    return rows


A, B = load(a_res, a_led), load(b_res, b_led)
keys = sorted(set(A) & set(B))


def strict(r):
    return (r.get("content") or 0) == 1.0 and bool(r.get("format_ok"))


def part(keys):
    return [k for k in keys if (k[0] in loop) == (keys is not None and k[0] in loop)]


def report(tag, sel):
    st = sum(1 for k in sel if strict(A[k]))
    st2 = sum(1 for k in sel if strict(B[k]))
    print("%-8s n=%-3d strict A=%d B=%d" % (tag, len(sel), st, st2))
    return st, st2


plain = [k for k in keys if k[0] not in loop]
lkeys = [k for k in keys if k[0] in loop]
report("plain", plain)
report("loop", lkeys)

cat = defaultdict(lambda: [0, 0, 0])
for k in keys:
    c = k[0][0]
    cat[c][2] += 1
    cat[c][0] += strict(A[k])
    cat[c][1] += strict(B[k])
print("\ncat    A   B   n")
for c in sorted(cat):
    a, b, n = cat[c]
    print("%-4s %3d %3d %3d%s" % (c, a, b, n, "  <--" if a != b else ""))

print("\nflips (strict)")
win = lose = 0
for k in keys:
    sa, sb = strict(A[k]), strict(B[k])
    if sa == sb:
        continue
    if sb:
        win += 1
        print("  B wins %-11s A c=%.2f f=%s notes=%s" % (
            k[0], A[k].get("content") or 0.0, A[k].get("format_ok"),
            ",".join(str(x) for x in (A[k].get("notes") or []))[:48]))
    else:
        lose += 1
        print("  A wins %-11s B c=%.2f f=%s notes=%s" % (
            k[0], B[k].get("content") or 0.0, B[k].get("format_ok"),
            ",".join(str(x) for x in (B[k].get("notes") or []))[:48]))

n = win + lose
p = 1.0
if n:
    lo = min(win, lose)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(lo + 1)) / 2.0 ** n)
print("\npaired: B wins %d, A wins %d, ties %d, exact sign-test p=%.4f" % (win, lose, len(keys) - n, p))

for tag, X in (("A", A), ("B", B)):
    calls = sum(X[k].get("_calls", 0) for k in keys)
    ptok = sum(X[k].get("_ptok", 0) for k in keys)
    ctok = sum(X[k].get("_ctok", 0) for k in keys)
    sec = sum(X[k].get("_sec", 0.0) for k in keys)
    print("%s cost: calls=%d ptok=%d ctok=%d wall=%.0fs" % (tag, calls, ptok, ctok, sec))
