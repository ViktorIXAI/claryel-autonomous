#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Where the margin actually lives: contract-sensitive categories vs the rest.

The independent review is right that this bank is contract-heavy, and the per-category table in
`audits/` showed the contour edge concentrated in F/H/K. This script makes that explicit instead of
letting it hide inside a single total: it scores each arm twice, on the F/H/K cells and on the
remaining single-shot cells, using the frozen scorer over published answer bytes (category E taken
from the docker E-EXEC cache so every arm is treated the same).

Usage: python3 scripts/category_split_v6.py [--contour-rep N]
"""
import argparse
import importlib.util
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")
FOUR = os.path.join(ROOT, "benchmarks", "hard", "v6-results", "four-arm-v61")
FHK = ("F", "H", "K")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, "missing harness module: " + path
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CK = _load("ck", os.path.join(ROOT, "harness", "parb_check_v6.py"))


def strict(c, f):
    return c == 1.0 and bool(f)


def sign_test(w, l):
    n = w + l
    if n == 0:
        return 1.0
    k = min(w, l)
    return min(1.0, sum(math.comb(n, i) for i in range(0, k + 1)) * 2 / 2 ** n)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contour-rep", default="0")
    ap.add_argument("--contour-ledger", default=os.path.join(
        ROOT, "benchmarks", "hard", "v6-results", "full-229", "ledger-c229full.jsonl"))
    args = ap.parse_args()
    bank = {t["id"]: t for t in json.load(open(BANK, encoding="utf-8"))}
    loop = {k for k in bank if bank[k].get("mode") == "loop"}
    ecache = json.load(open(os.path.join(FOUR, "E-EXEC.json"), encoding="utf-8"))

    contour = {}
    for line in open(args.contour_ledger, encoding="utf-8"):
        r = json.loads(line)
        if r["task"] in loop or str(r.get("rep")) != args.contour_rep:
            continue
        contour[r["task"]] = strict(r.get("content") or 0, r.get("format_ok"))

    print("contour rep%s ledger: %s" % (args.contour_rep, os.path.basename(args.contour_ledger)))
    print("cells = F/H/K (%d) + other single-shot (%d)\n" % (
        sum(1 for t in contour if bank[t]["cat"] in FHK),
        sum(1 for t in contour if bank[t]["cat"] not in FHK)))
    for arm in ("basalt", "codex", "grok"):
        cf = kf = co = ao = 0
        nf = no = 0
        wf = lf = wo = lo = 0
        for line in open(os.path.join(FOUR, "answers-%s-v61.jsonl" % arm), encoding="utf-8"):
            r = json.loads(line)
            tid = r["task"]
            if tid in loop or tid not in contour:
                continue
            task = bank[tid]
            if task["cat"] == "E":
                hit = ecache.get(arm, {}).get(tid)
                a = strict(hit[0], hit[1]) if hit else False
            else:
                c, f, _ = CK.check(task, r.get("answer") or "")
                a = strict(c, f)
            k = contour[tid]
            if task["cat"] in FHK:
                nf += 1
                cf += k; kf += a
                wf += k and not a; lf += a and not k
            else:
                no += 1
                co += k; ao += a
                wo += k and not a; lo += a and not k
        print("%-7s FHK   contour %2d/%2d vs arm %2d/%2d  W%02d L%02d p=%.3f" % (
            arm, cf, nf, kf, nf, wf, lf, sign_test(wf, lf)))
        print("        other contour %2d/%2d vs arm %2d/%2d  W%02d L%02d p=%.3f" % (
            co, no, ao, no, wo, lo, sign_test(wo, lo)))
    print("\nRead: if the contour's margin sits in F/H/K and the 'other' column is parity or a loss,"
          " the claim is 'wins on contract-sensitive tasks', not 'wins everywhere'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
