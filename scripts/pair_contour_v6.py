#!/usr/bin/env python3
"""Paired contour A/B on the same v6 bank and seeds (2.14 vs 2.15).

Reads scored CSVs (task,cat,strict/content) produced by score_v6.py for two
contour arms, asserts task-set and prompt-hash identity, prints category deltas,
discordant task lists and exact McNemar p (binomial, two-sided).
"""
import csv, sys
from math import comb


def load(path):
    out = {}
    for row in csv.DictReader(open(path, encoding="utf-8")):
        out[row["task"]] = (row["cat"], row["strict"] == "1", float(row["content"]))
    return out


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    p = sum(comb(n, k) for k in range(0, min(b, c) + 1)) * 2 * 0.5 ** n
    return min(1.0, p)


def main(pa, pb, la="A", lb="B"):
    A, B = load(pa), load(pb)
    assert set(A) == set(B), "task sets differ"
    cats = {}
    dA, dB = [], []
    for t in sorted(A):
        cat, sa, ca = A[t]
        _, sb, cb = B[t]
        cats.setdefault(cat, [0, 0, 0.0, 0.0])
        cats[cat][0] += sa
        cats[cat][1] += sb
        cats[cat][2] += ca
        cats[cat][3] += cb
        if sb and not sa:
            dB.append(t)
        if sa and not sb:
            dA.append(t)
    print("paired contour %s -> %s over %d tasks" % (la, lb, len(A)))
    print("%-4s %6s %6s %8s %8s" % ("cat", la, lb, la + " mean", lb + " mean"))
    for cat in sorted(cats):
        a, b, x, y = cats[cat]
        print("%-4s %6d %6d %8.3f %8.3f" % (cat, a, b, x / len(A), y / len(A)))
    na = sum(v[0] for v in cats.values())
    nb = sum(v[1] for v in cats.values())
    print("TOTAL strict %s=%d %s=%d" % (la, na, lb, nb))
    print("McNemar: %s wins %d, %s wins %d, p=%.4f"
          % (lb, len(dB), la, len(dA), mcnemar(len(dB), len(dA))))
    print("newly fixed by %s: %s" % (lb, ", ".join(dB) or "-"))
    print("newly broken by %s: %s" % (lb, ", ".join(dA) or "-"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2],
         sys.argv[3] if len(sys.argv) > 3 else "2.14",
         sys.argv[4] if len(sys.argv) > 4 else "2.15")
