#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Four-arm cadence closure table for reps 6,7,8 (CADENCE-240-V61.md).

Seeds are matched across arms by rep number (gseed = sha256(task|rep) in the plan, raw runner
seed = 1000+rep, same rep set for every arm), so contour cell (task, rep k) and raw cell
(task, rep k) are seed-matched. Contour legs are read from published cadence-240 ledgers
(stamp 0.0.2.40, printed as provenance), raw legs from published raw-reps-v61 answer rows —
exactly the bytes a reviewer can download. E and loop-D are excluded symmetrically
(61-cell common set, identical to ARM-BANDS-V61.md).

Emits: per-rep seed-matched pairs with exact sign test, pooled 183-cell pair tests,
per-category pooled strict cells for all four arms, and the cloud transport window.
"""
import argparse
import collections
import glob
import hashlib
import importlib.util
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")
V6 = os.path.join(ROOT, "benchmarks", "hard", "v6-results")
REPS = ("6", "7", "8")
ARMS = ("contour", "basalt", "codex", "grok")


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
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    bank = {t["id"]: t for t in json.load(open(BANK, encoding="utf-8"))}
    loop = {k for k in bank if bank[k].get("mode") == "loop"}
    bank_sha = hashlib.sha256(open(BANK, "rb").read()).hexdigest()[:16]

    bands = collections.defaultdict(lambda: collections.defaultdict(dict))
    stamps = collections.defaultdict(set)
    seen_sha = collections.defaultdict(set)
    for arm in ("basalt", "codex", "grok"):
        for line in open(os.path.join(V6, "raw-reps-v61", "answers-%s-v61-reps.jsonl" % arm),
                         encoding="utf-8"):
            r = json.loads(line)
            rep = str(r.get("rep", "0"))
            if rep not in REPS or r["task"] in loop or bank[r["task"]]["cat"] == "E":
                continue
            seen_sha[arm].add(r.get("bank_sha16"))
            c, f, _ = CK.check(bank[r["task"]], r.get("answer") or "")
            bands[arm][rep][r["task"]] = strict(c, f)
    for p in sorted(glob.glob(os.path.join(V6, "cadence-240", "ledger-q40r*.jsonl"))):
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            if "_loop_rows" in r or r["task"] in loop or bank[r["task"]]["cat"] == "E":
                continue
            rep = str(r.get("rep"))
            if rep not in REPS:
                continue
            if r.get("contour_version"):
                stamps[rep].add(r["contour_version"])
            bands["contour"][rep][r["task"]] = strict(r.get("content") or 0, r.get("format_ok"))

    cells = sorted(set().union(*[set(bands[a][r]) for a in ARMS for r in bands[a]]))
    for arm in ARMS:
        for rep in REPS:
            assert len(bands[arm][rep]) == 61, "unfinished seed: %s rep%s (%d/61)" % (
                arm, rep, len(bands[arm][rep]))
    assert len(cells) == 61, "cell set drifted: %d" % len(cells)

    lines = []
    lines.append("common set: 61 single-shot non-E cells; contour reps 6,7,8 = %s (stamp read from "
                 "ledger rows); bank sha16 %s" %
                 ("/".join(sorted({x for r in REPS for x in stamps[r]})), bank_sha))
    for arm in ("basalt", "codex", "grok"):
        lines.append("  %s rows carry bank_sha16 %s" % (arm, sorted(seen_sha[arm])))
    lines.append("")
    lines.append("| rep | contour | basalt | codex | grok | pair vs codex (W/L, p) | pair vs grok (W/L, p) |")
    lines.append("|---|---|---|---|---|---|---|")
    for rep in REPS:
        a = bands["contour"][rep]
        row = [rep, str(sum(1 for t in cells if a[t]))]
        for arm in ("basalt", "codex", "grok"):
            row.insert(2 + ("basalt", "codex", "grok").index(arm),
                       str(sum(1 for t in cells if bands[arm][rep].get(t))))
        for arm in ("codex", "grok"):
            b = bands[arm][rep]
            w = sum(1 for t in cells if a[t] and not b.get(t))
            l = sum(1 for t in cells if b.get(t) and not a[t])
            row.append("%d/%d, p=%.5f" % (w, l, sign_test(w, l)))
        lines.append("| rep%s | %s |" % (rep, " | ".join(row[1:])))
    lines.append("")
    for arm in ("codex", "grok"):
        tw = tl = 0
        ca = cb = 0
        for rep in REPS:
            a, b = bands["contour"][rep], bands[arm][rep]
            tw += sum(1 for t in cells if a[t] and not b.get(t))
            tl += sum(1 for t in cells if b.get(t) and not a[t])
            ca += sum(1 for t in cells if a[t])
            cb += sum(1 for t in cells if b.get(t))
        lines.append("pooled (%d cells): contour %d vs %s %d, W%d L%d, exact p=%.3g" %
                     (len(cells) * len(REPS), ca, arm, cb, tw, tl, sign_test(tw, tl)))
    lines.append("")
    lines.append("per-category pooled strict cells over reps 6,7,8 (max 3 per cell):")
    lines.append("| cat | contour | basalt | codex | grok | cells |")
    lines.append("|---|---|---|---|---|---|")
    for cat in sorted({bank[t]["cat"] for t in cells}):
        sub = [t for t in cells if bank[t]["cat"] == cat]
        vals = [sum(1 for r in REPS for t in sub if bands[arm][r].get(t)) for arm in ARMS]
        lines.append("| %s | %d | %d | %d | %d | %d |" % (cat, *vals, len(sub) * len(REPS)))
    text = "\n".join(lines)
    print(text)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
