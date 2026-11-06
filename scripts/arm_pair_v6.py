#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-score raw single-shot answers with the frozen scorer and pair them against contour reps.

Raw answer rows carry no score, so the published numbers for every cloud arm come from re-running
`harness/parb_check_v6.check` on the answer bytes. Category E needs docker and is excluded by
default (use --with-e-cache to take E from a cached E-EXEC.json), which keeps the comparison
symmetric across arms. Duplicate (task, rep) rows can appear when an arm was resumed after a stop;
the LAST row wins, and the count of duplicates is printed as a provenance note.

Usage:
  python3 scripts/arm_pair_v6.py --raw WS_DIR/answers-codex.jsonl [--raw ...] \
      --contour PUBLISHED_LEDGER_DIR... [--rep N] [--with-e-cache E-EXEC.json]
"""
import argparse
import collections
import importlib.util
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")
_spec = importlib.util.spec_from_file_location("ck", os.path.join(ROOT, "harness", "parb_check_v6.py"))
CK = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CK)


def strict(c, f):
    return c == 1.0 and bool(f)


def sign_test(w, l):
    n = w + l
    if n == 0:
        return 1.0
    k = min(w, l)
    return min(1.0, sum(math.comb(n, i) for i in range(0, k + 1)) * 2 / 2 ** n)


def load_bank():
    bank = {t["id"]: t for t in json.load(open(BANK, encoding="utf-8"))}
    return bank, {k for k in bank if bank[k].get("mode") == "loop"}


def raw_cells(path, bank, loop, e_cache=None, arm=""):
    by_key = {}
    dup = 0
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        key = r["task"]
        if key in by_key:
            dup += 1
        by_key[key] = r
    print("%-34s rows=%d unique=%d duplicates=%d (resumed arm)" % (
        os.path.basename(path), dup + len(by_key), len(by_key), dup))
    # rows are keyed by task; a resumed arm's later row for the same task wins
    out = {}
    for tid, r in by_key.items():
        if tid in loop:
            continue
        if bank[tid]["cat"] == "E":
            if not e_cache:
                continue
            hit = e_cache.get(arm, {}).get(tid)
            out[tid] = strict(hit[0], hit[1]) if hit else None
            continue
        c, f, _ = CK.check(bank[tid], r.get("answer") or "")
        out[tid] = strict(c, f)
    return out


def contour_cells(path, bank, loop, rep="0"):
    out = {}
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        if "_loop_rows" in r or r["task"] in loop or str(r.get("rep")) != str(rep):
            continue
        out[r["task"]] = strict(r.get("content") or 0, r.get("format_ok"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", action="append", default=[], help="answers-*.jsonl path (repeatable)")
    ap.add_argument("--arm", default="", help="arm label used to pick E cells from --with-e-cache")
    ap.add_argument("--contour", action="append", default=[], help="contour ledger path (repeatable)")
    ap.add_argument("--rep", action="append", default=[], help="contour rep to read from --contour files")
    ap.add_argument("--with-e-cache", default=None)
    args = ap.parse_args()
    bank, loop = load_bank()
    e_cache = json.load(open(args.with_e_cache, encoding="utf-8")) if args.with_e_cache else None

    raw_all = {}
    for p in args.raw:
        raw_all.update(raw_cells(p, bank, loop, e_cache, args.arm))
    reps = args.rep or ["0"]
    cont = {}
    for p in args.contour:
        for rep in reps:
            try:
                cont.update(contour_cells(p, bank, loop, rep))
            except (OSError, KeyError):
                pass
    keys = sorted({k for k in raw_all if raw_all[k] is not None} & set(cont))
    if not keys:
        print("no overlap; check --rep values")
        return 1
    rs = sum(1 for k in keys if raw_all[k])
    cs = sum(1 for k in keys if cont[k])
    w = sum(1 for k in keys if cont[k] and not raw_all[k])
    l = sum(1 for k in keys if raw_all[k] and not cont[k])
    print("\npair on %d cells: raw %d/%d vs contour %d/%d  contour wins %d losses %d  exact p=%.5f" % (
        len(keys), rs, len(keys), cs, len(keys), w, l, sign_test(w, l)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
