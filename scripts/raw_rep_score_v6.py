#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score one repetition of a raw single-shot arm and pair it against a contour repetition.

Unlike `arm_pair_v6.py` (which keys by task and therefore collapses repetitions), this takes an explicit
--rep from the raw answer file, so a workspace that holds several repetitions of one arm can be reported
repetition by repetition. Category E needs docker and is excluded here; both sides then use the same
61 single-shot non-E cells, which keeps the comparison symmetric.

Usage:
  python3 scripts/raw_rep_score_v6.py --raw ANSWERS.jsonl --rep 1 \
      --contour LEDGER.jsonl --contour-rep 0
"""
import argparse
import importlib.util
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")


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
    ap.add_argument("--raw", required=True)
    ap.add_argument("--rep", default="1")
    ap.add_argument("--contour", required=True)
    ap.add_argument("--contour-rep", default="0")
    args = ap.parse_args()
    bank = {t["id"]: t for t in json.load(open(BANK, encoding="utf-8"))}
    loop = {k for k in bank if bank[k].get("mode") == "loop"}

    raw = {}
    for line in open(args.raw, encoding="utf-8"):
        r = json.loads(line)
        if str(r.get("rep")) != args.rep or r["task"] in loop:
            continue
        task = bank[r["task"]]
        if task["cat"] == "E":
            continue
        c, f, _ = CK.check(task, r.get("answer") or "")
        raw[r["task"]] = strict(c, f)

    con = {}
    for line in open(args.contour, encoding="utf-8"):
        r = json.loads(line)
        if "_loop_rows" in r or r["task"] in loop or str(r.get("rep")) != args.contour_rep:
            continue
        if bank[r["task"]]["cat"] == "E":
            continue
        con[r["task"]] = strict(r.get("content") or 0, r.get("format_ok"))

    ids = sorted(set(raw) & set(con))
    w = sum(1 for i in ids if con[i] and not raw[i])
    l = sum(1 for i in ids if raw[i] and not con[i])
    print("raw rep%s: %d/%d   contour rep%s: %d/%d" % (
        args.rep, sum(raw[i] for i in ids), len(ids), args.contour_rep,
        sum(con[i] for i in ids), len(ids)))
    print("contour wins %d, losses %d, exact sign-test p=%.5f" % (w, l, sign_test(w, l)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
