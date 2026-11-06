#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cell-level bootstrap confidence intervals for arm-to-arm margins after seed averaging.

Per-cell pass fraction is averaged over that arm's repetitions first, so seed noise inside one arm does
not masquerade as an arm difference. The uncertainty then comes from resampling **cells** (the unit the
bank was written in): 10 000 bootstrap resamples of the 61 common single-shot cells, percentile CI on
the difference of mean pass fractions. This is a different question from the exact sign test in
`arm_bands_v61.py` (which pairs one seed against one seed) and the two are reported side by side.

Usage: python3 scripts/margin_bootstrap_v61.py
"""
import collections
import glob
import importlib.util
import json
import os
import random
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")
V6 = os.path.join(ROOT, "benchmarks", "hard", "v6-results")
WS = os.path.expanduser("~/parb-v61-raw-reps")
N_BOOT = 10000


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, "missing harness module: " + path
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CK = _load("ck", os.path.join(ROOT, "harness", "parb_check_v6.py"))


def strict(c, f):
    return c == 1.0 and bool(f)


def main() -> int:
    bank = {t["id"]: t for t in json.load(open(BANK, encoding="utf-8"))}
    loop = {k for k in bank if bank[k].get("mode") == "loop"}
    per = collections.defaultdict(lambda: collections.defaultdict(dict))  # arm -> rep -> task -> bool

    def raw(path, arm):
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            tid = r["task"]
            if tid in loop or bank[tid]["cat"] == "E":
                continue
            c, f, _ = CK.check(bank[tid], r.get("answer") or "")
            per[arm][str(r.get("rep", "0"))][tid] = strict(c, f)

    def contour(path):
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            if "_loop_rows" in r or r["task"] in loop or bank[r["task"]]["cat"] == "E":
                continue
            per["contour"][str(r.get("rep", "0"))][r["task"]] = strict(
                r.get("content") or 0, r.get("format_ok"))

    for arm in ("basalt", "codex", "grok"):
        raw(os.path.join(V6, "four-arm-v61", "answers-%s-v61.jsonl" % arm), arm)
        p = os.path.join(WS, "answers-%s.jsonl" % arm)
        if os.path.exists(p):
            raw(p, arm)
    contour(os.path.join(V6, "full-229", "ledger-c229full.jsonl"))
    contour(os.path.join(V6, "reps-229", "ledger-c229r12.jsonl"))
    for p in sorted(glob.glob(os.path.join(V6, "reps-229", "ledger-c229r3.jsonl"))):
        contour(p)

    def mean_frac(arm, ids):
        seeds = [per[arm][s] for s in per[arm]]
        return [statistics.mean([1.0 if s.get(i) else 0.0 for s in seeds]) for i in ids]

    common: set = set()
    for arm in per:
        s = set()
        for rep in per[arm]:
            s |= set(per[arm][rep])
        common = s if not common else (common & s)
    ids = sorted(common)
    assert ids, "no cells shared across all arms"
    print("common cells: %d" % len(ids))
    random.seed(20261106)
    base = {arm: mean_frac(arm, ids) for arm in per}
    for arm in per:
        print("  %-8s mean pass fraction over its seeds: %.3f (%d seeds)" % (
            arm, statistics.mean(base[arm]), len(per[arm])))
    print()
    for other in ("basalt", "codex", "grok"):
        d_obs = statistics.mean(base["contour"]) - statistics.mean(base[other])
        boots = []
        pairs = list(zip(base["contour"], base[other]))
        for _ in range(N_BOOT):
            samp = [pairs[random.randrange(len(pairs))] for _ in pairs]
            boots.append(statistics.mean(a for a, _ in samp) - statistics.mean(b for _, b in samp))
        boots.sort()
        lo, hi = boots[int(0.025 * N_BOOT)], boots[int(0.975 * N_BOOT)]
        sig = "yes" if lo > 0 else "no"
        print("contour - %-7s = %+.3f  95%% CI [%+.3f, %+.3f]  CI excludes 0: %s  (%+.1f cells over %d)" % (
            other, d_obs, lo, hi, sig, d_obs * len(ids), len(ids)))
    print("\nMethod: seeds averaged per cell first, then %d bootstrap resamples of the %d common cells." % (
        N_BOOT, len(ids)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
