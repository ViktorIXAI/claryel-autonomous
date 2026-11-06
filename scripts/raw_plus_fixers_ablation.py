#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fair-controls ablation: raw cloud/local answers PLUS the contour's deterministic repair only.

The published contour win is a system-vs-model comparison: the contour gets verification, retries and
task gates, the raw arms get one unassisted answer (see `audits/2026-11-06-*`). The cheapest honest
cut is to give the raw arms exactly one contour component and nothing else: the deterministic
post-normalizer from `harness/gate_run.post_normalize_answer` (zero model tokens, no checker feedback,
no second inference, content preserved), then re-score with the frozen scorer.

    strict(raw)            -> model alone
    strict(raw + repair)   -> model + contour's format plumbing
    strict(contour)        -> model + full contour trajectory

Usage: python3 scripts/raw_plus_fixers_ablation.py OUT_DIR
Reads the published four-arm answer files and the published contour ledgers.
"""
import collections
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PARB_GATE_VERSION", "0.0.2.29")
BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")
ARMS_DIR = os.path.join(ROOT, "benchmarks", "hard", "v6-results", "four-arm-v61")

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, "missing harness module: " + path
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CK = _load("ck", os.path.join(ROOT, "harness", "parb_check_v6.py"))
GR = _load("gr", os.path.join(ROOT, "harness", "gate_run.py"))


def strict(c, f):
    return c == 1.0 and bool(f)


def main() -> int:
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "benchmarks/hard/v6-results")
    bank = {t["id"]: t for t in json.load(open(BANK, encoding="utf-8"))}
    loop = {k for k in bank if bank[k].get("mode") == "loop"}
    ecache = json.load(open(os.path.join(ARMS_DIR, "E-EXEC.json"), encoding="utf-8"))
    contour = {}
    for line in open(os.path.join(ROOT, "benchmarks/hard/v6-results/full-229/ledger-c229full.jsonl"),
                     encoding="utf-8"):
        r = json.loads(line)
        if r["task"] in loop or str(r.get("rep")) != "0":
            continue
        contour[r["task"]] = strict(r.get("content") or 0, r.get("format_ok"))

    report = {}
    for arm in ("basalt", "codex", "grok"):
        before = {}
        after = {}
        events = collections.Counter()
        kind = collections.Counter()
        flips = []
        for line in open(os.path.join(ARMS_DIR, "answers-%s-v61.jsonl" % arm), encoding="utf-8"):
            row = json.loads(line)
            tid = row["task"]
            if tid in loop:
                continue
            task = bank[tid]
            ans = row.get("answer") or ""
            if task["cat"] == "E":
                hit = ecache.get(arm, {}).get(tid)
                before[tid] = strict(hit[0], hit[1]) if hit else False
                after[tid] = before[tid]
                continue
            cb, fb, _ = CK.check(task, ans)
            rep, ev = GR.post_normalize_answer(task["cat"], task, ans)
            ca, fa, _ = CK.check(task, rep if rep else ans)
            if not strict(cb, fb):
                kind["content" if cb < 1.0 else "format_only"] += 1
            before[tid] = strict(cb, fb)
            after[tid] = strict(ca, fa)
            if ev:
                for e in ev:
                    events[e] += 1
            if after[tid] and not before[tid]:
                flips.append(tid + "+" + ",".join(ev or []))
            if before[tid] and not after[tid]:
                flips.append(tid + "-" + ",".join(ev or []))
        cats = collections.defaultdict(lambda: [0, 0])
        for tid in before:
            c = bank[tid]["cat"]
            cats[c][0] += 1 if before[tid] else 0
            cats[c][1] += 1 if after[tid] else 0
        report[arm] = {
            "raw": sum(before.values()), "raw_plus_repair": sum(after.values()),
            "cells": len(before),
            "repair_events": dict(events), "flips": sorted(flips),
            "by_cat_before_after": {k: v for k, v in sorted(cats.items()) if v[0] != v[1]},
            "failing_cells_content_vs_format_only": dict(kind),
        }
        print("        failures by kind: content %d, format_only %d" % (kind["content"], kind["format_only"]))
        print("%-7s raw %d/%d -> raw+repair %d/%d  repaired_cells=%d  flips=%s" % (
            arm, report[arm]["raw"], len(before), report[arm]["raw_plus_repair"], len(before),
            sum(events.values()), ", ".join(sorted(flips)) or "none"))
    cont_n = sum(contour.values())
    print("\ncontour 0.0.2.29 rep0: %d/%d (full trajectory, same scorer)" % (cont_n, len(contour)))
    os.makedirs(out_dir, exist_ok=True)
    json.dump({"contour_rep0": cont_n, "contour_cells": len(contour), "arms": report},
              open(os.path.join(out_dir, "ABLATION-RAW-FIXERS.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\nComponent split: (raw+repair - raw) is what the contour's deterministic plumbing alone is"
          " worth; (contour - (raw+repair)) is what verification, retries and task gates add on top.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
