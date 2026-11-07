#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-arm, per-seed score bands on the common single-shot cell set.

Every published total in this repo comes from one arm under one seed, which is why the independent
review asked for repetitions: a single cell can flip 1.00/0.33/1.00 between identical seeds. This
script scores every available repetition of every arm with the frozen scorer over the same cell set and
prints the band (min..max, mean) plus the contour-vs-arm paired tests on matched cells only.

Category E is excluded unless --e-cache is given, because E requires docker execution and the cache holds
only the four-arm rep0 records. Both sides then use the identical 61-cell set, so nothing is compared
across different denominators.

Usage: python3 scripts/arm_bands_v61.py [--e-cache E-EXEC.json] [--out FILE]
"""
import argparse
import collections
import glob
import importlib.util
import json
import math
import os
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")
V6 = os.path.join(ROOT, "benchmarks", "hard", "v6-results")
WS = os.path.expanduser("~/parb-v61-raw-reps")
MIN_ROWS = 61  # single-shot non-E cells in bank v6.1; fewer rows means the repetition is unfinished


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
    ap.add_argument("--e-cache", default=None, help="E-EXEC.json to include category E cells")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    bank = {t["id"]: t for t in json.load(open(BANK, encoding="utf-8"))}
    loop = {k for k in bank if bank[k].get("mode") == "loop"}
    ecache = json.load(open(args.e_cache, encoding="utf-8")) if args.e_cache else None
    keep_e = bool(ecache)

    bands = collections.defaultdict(dict)   # arm -> rep -> {task: bool}
    contour_stamps = {}                     # contour rep -> set of contour_version in its rows

    def add_raw(path, arm):
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            tid, rep = r["task"], str(r.get("rep", "0"))
            if tid in loop or bank[tid]["cat"] == "E" and not keep_e:
                continue
            if bank[tid]["cat"] == "E":
                assert ecache is not None  # keep_e is set only when the cache was loaded
                hit = ecache.get(arm, {}).get(tid)
                v = strict(hit[0], hit[1]) if hit else False
            else:
                c, f, _ = CK.check(bank[tid], r.get("answer") or "")
                v = strict(c, f)
            bands[arm].setdefault(rep, {})[tid] = v

    def add_contour(path, rep=None):
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            if "_loop_rows" in r or r["task"] in loop:
                continue
            if bank[r["task"]]["cat"] == "E" and not keep_e:
                continue
            rep_id = str(r.get("rep", rep or "0"))
            bands["contour"].setdefault(rep_id, {})[r["task"]] = strict(
                r.get("content") or 0, r.get("format_ok"))
            stamp = r.get("contour_version")
            if stamp:
                contour_stamps.setdefault(rep_id, set()).add(stamp)

    for arm in ("basalt", "codex", "grok"):
        add_raw(os.path.join(V6, "four-arm-v61", "answers-%s-v61.jsonl" % arm), arm)
        # Published repetitions are the authority; the live workspace copy is only a fallback so a run
        # in flight can be inspected before publication.
        pub = os.path.join(V6, "raw-reps-v61", "answers-%s-v61-reps.jsonl" % arm)
        p = pub if os.path.exists(pub) else os.path.join(WS, "answers-%s.jsonl" % arm)
        if os.path.exists(p):
            add_raw(p, arm)
    # A repetition that is still running has partial rows and scores artificially low; drop any seed
    # that did not produce the full single-shot set. This is not cosmetic: a mid-flight Grok rep pulled
    # the contour-vs-Grok margin from +8 to +17.5 cells.
    for arm in list(bands):
        for rep in list(bands[arm]):
            if len(bands[arm][rep]) < MIN_ROWS:
                print("dropping unfinished seed: %s rep%s (%d/%d cells)" % (
                    arm, rep, len(bands[arm][rep]), MIN_ROWS))
                del bands[arm][rep]
    add_contour(os.path.join(V6, "full-229", "ledger-c229full.jsonl"))
    for p in glob.glob(os.path.join(V6, "reps-229", "ledger-*.jsonl")) + glob.glob(
            os.path.join(V6, "full-229", "ledger-*.jsonl")):
        if os.path.basename(p) != "ledger-c229full.jsonl":
            add_contour(p)
    # published repetition ledgers (reps-229) rather than the workspace copies, so the report reads
    # exactly the bytes a reviewer can download
    for p in sorted(glob.glob(os.path.join(V6, "reps-229", "ledger-c229r*.jsonl"))):
        if os.path.basename(p) != "ledger-c229full.jsonl":
            add_contour(p)
    # cadence-240 legs: contour 0.0.2.40 on fresh matched reps 6,7,8 (cadence-240/README note in
    # CADENCE-240-V61.md); stamp provenance is printed below so a mixed-stamp contour band is never
    # read as one stamp.
    for p in sorted(glob.glob(os.path.join(V6, "cadence-240", "ledger-q40r*.jsonl"))):
        add_contour(p)

    cells = set()
    for arm in bands:
        for rep in bands[arm]:
            cells |= set(bands[arm][rep])
    lines = []
    lines.append("common single-shot cell set: %d cells" % len(cells))
    lines.append("")
    lines.append("| arm | seeds scored | per-seed strict | mean | spread |")
    lines.append("|---|---|---|---|---|")
    for arm in ("contour", "basalt", "codex", "grok"):
        if arm not in bands:
            continue
        seeds = sorted(bands[arm])
        vals = [sum(1 for t in cells if bands[arm][s].get(t)) for s in seeds]
        lines.append("| %s | %s | %s | %.1f | %d |" % (
            arm, ", ".join("rep" + s for s in seeds), ", ".join(str(v) for v in vals),
            statistics.mean(vals), max(vals) - min(vals)))
    lines.append("")
    if contour_stamps:
        lines.append("contour seed provenance (contour_version read from the ledger rows):")
        for cs in sorted(contour_stamps):
            lines.append("  rep%s = %s" % (cs, "/".join(sorted(contour_stamps[cs]))))
        lines.append("")
    lines.append("paired tests on matched cells (contour seed vs arm seed, exact sign test):")
    for cs in sorted(bands.get("contour", {})):
        for arm in ("basalt", "codex", "grok"):
            for as_ in sorted(bands.get(arm, {})):
                a = bands["contour"][cs]
                b = bands[arm][as_]
                ids = sorted(set(a) & set(b))
                if len(ids) < 20:
                    continue
                w = sum(1 for t in ids if a[t] and not b[t])
                l = sum(1 for t in ids if b[t] and not a[t])
                lines.append("  contour rep%s vs %-7s rep%s: %2d/%d vs %2d/%d  W%02d L%02d p=%.5f" % (
                    cs, arm, as_, sum(1 for t in ids if a[t]), len(ids),
                    sum(1 for t in ids if b[t]), len(ids), w, l, sign_test(w, l)))
    text = "\n".join(lines)
    print(text)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
