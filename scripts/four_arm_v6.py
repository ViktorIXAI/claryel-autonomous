#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Four-arm v6 scoreboard: contour / basalt-bare / codex / grok.
Common set = 71 single-shot tasks (loop D applies to the contour arm only).
Exact McNemar on paired strict-perfect outcomes. Everything printed is
recomputed from stored answer files + pinned scorer (no manual numbers).
"""
import importlib.util, json, os, sys
from math import comb

ROOT = os.path.expanduser("~/parb-v6-raw")
spec = importlib.util.spec_from_file_location("parb_check_v6", os.path.join(ROOT, "parb_check_v6.py"))
c6 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c6)

bank = {t["id"]: t for t in json.load(open(os.path.join(ROOT, "bank.json")))}
ARMS = ["contour", "basalt", "codex", "grok"]


def score(arm):
    path = os.path.join(ROOT, "answers-%s.jsonl" % arm)
    res = {}
    for l in open(path, encoding="utf-8"):
        r = json.loads(l)
        t = bank[r["task"]]
        try:
            if t["cat"] == "D" and t.get("mode") == "loop":
                if arm != "contour":
                    continue
                c, f, n = c6.check_D_loop_v6(t, json.loads(r["answer"]).get("_loop_rows", []))
            else:
                c, f, n = c6.check(t, r["answer"])
        except Exception as e:
            c, f, n = 0.0, False, ["scorer_error"]
        res[r["task"]] = (c, f)
    return res


def strict(t):
    c, f = t
    return 1 if c == 1.0 and f else 0


def mcnemar(a, b):
    common = sorted(set(a) & set(b) - {k for k in a if bank[k]["cat"] == "D" and bank[k].get("mode") == "loop"})
    p_ = sum(1 for k in common if strict(a[k]) and not strict(b[k]))
    q = sum(1 for k in common if not strict(a[k]) and strict(b[k]))
    n = p_ + q
    if n == 0:
        pval = 1.0
    else:
        k = min(p_, q)
        tail = sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
        pval = min(1.0, 2 * tail)
    return p_, q, pval, len(common)


S = {arm: score(arm) for arm in ARMS}
common = sorted(set(S["contour"]) & set(S["basalt"]) & set(S["codex"]) & set(S["grok"]))
common = [k for k in common if not (bank[k]["cat"] == "D" and bank[k].get("mode") == "loop")]

print("COMMON SET (single-shot): %d tasks" % len(common))
print("%-8s %8s %8s" % ("arm", "strict", "content"))
for arm in ARMS:
    st = sum(strict(S[arm][k]) for k in common)
    co = sum(1 for k in common if S[arm][k][0] == 1.0)
    print("%-8s %5d/%-3d %5d/%-3d" % (arm, st, len(common), co, len(common)))

print("\nCONTOUR-ONLY loop tasks (6): strict %d/6 mean %.3f" % (
    sum(1 for k in S["contour"] if bank[k]["cat"] == "D" and bank[k].get("mode") == "loop" and strict(S["contour"][k])),
    sum(S["contour"][k][0] for k in S["contour"] if bank[k]["cat"] == "D" and bank[k].get("mode") == "loop") / 6))

print("\nMcNemar exact (strict, paired on common set):")
pairs = [("contour", "basalt"), ("grok", "codex"), ("grok", "contour"), ("codex", "basalt"), ("grok", "basalt"),
         ("contour", "codex")]
for x, y in pairs:
    p_, q, pv, n = mcnemar(S[x], S[y])
    print("  %-8s vs %-8s: +%d/-%d  p=%.4f  (n=%d)" % (x, y, p_, q, pv, n))

print("\nPer-category strict on common set:")
cats = sorted({bank[k]["cat"] for k in common})
print("%-4s " % "cat" + " ".join("%8s" % a[:8] for a in ARMS))
for cat in cats:
    ks = [k for k in common if bank[k]["cat"] == cat]
    print("%-4s " % cat + " ".join("%5d/%-3d" % (sum(strict(S[a][k]) for k in ks), len(ks)) for a in ARMS))
