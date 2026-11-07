#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paired-arm guard census + cell attribution for contour pairs (P0 measurement stack).

`full_pair_report.py` answers "what moved"; this answers the pre-registered pair questions that
decide ADOPT vs FREEZE, and prints them as one publishable block:

  * join integrity — ledger rows score, results rows carry bytes; abort on a missing sibling or on
    blank answers (an analysis that re-scores empty strings fabricates a diagnosis),
  * the candidate mechanism's event census (fires per side, on which tasks, in which arm),
  * frozen-band parity — a behaviour pinned to an older stamp must never appear in a new arm,
  * adopted-family parity — every other contour family's event count per side,
  * engine-stall rows, loop pass->fail guard, and the K/monotonicity guard (candidate strict-fails
    a cell the control passed),
  * per-target-cell attribution (scores, codes, events, answer bytes, per-cell cost),
  * pooled strict totals with the exact sign test (an arm-mean delta under ~2 cells at three seeds
    is UNRESOLVABLE; the claim is cell-level),
  * the per-arm energy-window file consumed by scripts/gpu_energy.py.

Usage: pair_guard_census.py <ws-dir> <target-task> [-e EVENT] [-k KEY_PREFIX] <arm:side> [<arm:side> ...]
  -e EVENT   the candidate event stem to census (default: any contour: event unique to the
             candidate side)
  -k PREFIX  task-key prefix for the monotonicity guard (default: target task's category letter)
"""
import collections
import json
import math
import os
import sys

FROZEN = ("v30", "v31", "v32", "v33", "v36", "v38", "v41", "v42", "v242", "v244")


def strict(r):
    return r.get("content") == 1.0 and bool(r.get("format_ok"))


def sign_p(w, l):
    if w + l == 0:
        return 1.0
    tail = sum(math.comb(w + l, i) for i in range(min(w, l), w + l + 1)) / 2.0 ** (w + l)
    return min(1.0, 2 * tail)


def main(argv):
    ws = os.path.expanduser(argv[0])
    target = argv[1]
    rest = argv[2:]
    stem = None
    if "-e" in rest:
        i = rest.index("-e"); stem = rest[i + 1]; rest = rest[:i] + rest[i + 2:]
    prefix = None
    if "-k" in rest:
        i = rest.index("-k"); prefix = rest[i + 1]; rest = rest[:i] + rest[i + 2:]
    arms = [tuple(a.split(":")) for a in rest]
    side = dict(arms)

    def load(name):
        with open(os.path.join(ws, name), encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]

    led, res = {}, {}
    for a, _ in arms:
        for r in load("ledger-%s.jsonl" % a):
            led[(a, r["task"], int(r["rep"]))] = r
        for r in load("results-%s.jsonl" % a):
            res[(a, r["task"], int(r["rep"]))] = r

    missing = [k for k in led if k not in res]
    blank = [k for k in led if not str((res.get(k) or {}).get("answer") or "").strip()]
    print("join: ledger=%d results=%d missing=%d blank=%d (%.2f%%)"
          % (len(led), len(res), len(missing), len(blank), 100.0 * len(blank) / max(1, len(led))))
    if missing or 100.0 * len(blank) / max(1, len(led)) > 5.0:
        print("ABORT: ledger/results join is not trustworthy (missing siblings or >5% blank answers)")
        return 3

    ev = collections.Counter()
    fires = []
    fam = collections.Counter()
    stalls = 0
    for (a, t, rp), r in sorted(led.items()):
        for e in r["events"]:
            if stem and stem in e:
                ev[(side[a], e)] += 1
                fires.append((a, side[a], t, rp, e))
            if any(x in e for x in FROZEN):
                fam[(side[a], "FROZEN:" + e.split(":")[1][:24])] += 1
            if e.startswith("contour:") or e.startswith("fix:"):
                fam[(side[a], e.split(":")[1].split("_att")[0][:32])] += 1
        if r.get("engine_stalled"):
            stalls += 1

    print("event census (%s): %s" % (stem or "auto", dict(ev) or "none"))
    for x in fires:
        print("   fire: arm=%s side=%-4s task=%-11s rep=%s %s" % x)
    print("candidate-event fires in a control arm:", any(x[1] == "ctrl" for x in fires))
    print("candidate-event tasks:", sorted({x[2] for x in fires}))
    print("engine_stalled rows:", stalls)
    fz = sorted({k[1] for k in fam if k[1].startswith("FROZEN")})
    print("frozen-band events (must be empty): %s" % (fz or "none"))

    tasks = sorted({k[1] for k in led})
    reps = sorted({k[2] for k in led})
    # monotonicity guard on the guard-relevant task family
    pref = prefix or target[0]
    bad = []
    for rp in reps:
        for t in tasks:
            if not t.startswith(pref):
                continue
            ca = [a for a, s in arms if s == "ctrl" and (a, t, rp) in led]
            cb = [a for a, s in arms if s == "cand" and (a, t, rp) in led]
            if not ca or not cb:
                continue
            if strict(led[(ca[0], t, rp)]) and not strict(led[(cb[0], t, rp)]):
                bad.append((t, rp, led[(cb[0], t, rp)]["codes"]))
    print("GUARD candidate strict-fails a cell the control passed (%s*): %s"
          % (pref, bad or "none"))

    print("\nTARGET %s per rep:" % target)
    conv = 0
    for rp in reps:
        ca = next((x for x in led if side[x[0]] == "ctrl" and x[1] == target and x[2] == rp), None)
        cb = next((x for x in led if side[x[0]] == "cand" and x[1] == target and x[2] == rp), None)
        if not ca or not cb:
            continue
        ra, rb = res[ca], res[cb]
        la, lb = led[ca], led[cb]
        print("  rep %d ctrl: c=%s f=%s codes=%s ev=%s" % (rp, la["content"], la["format_ok"], la["codes"], la["events"]))
        print("          ANS=%r" % str(ra["answer"])[:110])
        print("  rep %d cand: c=%s f=%s codes=%s ev=%s" % (rp, lb["content"], lb["format_ok"], lb["codes"], lb["events"]))
        print("          ANS=%r" % str(rb["answer"])[:110])
        print("          cost ctrl ptok=%s ctok=%s calls=%s s=%.2f | cand ptok=%s ctok=%s calls=%s s=%.2f"
              % (la["ptok"], la["ctok"], la["model_calls"], la["seconds"],
                 lb["ptok"], lb["ctok"], lb["model_calls"], lb["seconds"]))
        if stem and strict(lb) and not strict(la) and any(stem in e for e in lb["events"]):
            conv += 1
    print("evented conversions (candidate strict-PASS over control strict-FAIL carrying %s): %d"
          % (stem, conv))

    ctrl = sum(1 for k, r in led.items() if side[k[0]] == "ctrl" and strict(r))
    cand = sum(1 for k, r in led.items() if side[k[0]] == "cand" and strict(r))
    W = L = 0
    for rp in reps:
        for t in tasks:
            ca = next((x for x in led if side[x[0]] == "ctrl" and x[1] == t and x[2] == rp), None)
            cb = next((x for x in led if side[x[0]] == "cand" and x[1] == t and x[2] == rp), None)
            if not ca or not cb:
                continue
            if strict(led[cb]) and not strict(led[ca]):
                W += 1
            elif strict(led[ca]) and not strict(led[cb]):
                L += 1
    print("\npooled %d cells: ctrl strict=%d cand strict=%d | candidate W=%d L=%d exact sign p=%.4f"
          % (len(tasks) * len(reps), ctrl, cand, W, L, sign_p(W, L)))

    print("\nadopted-family event census (ctrl vs cand, |diff|>0):")
    for k in sorted({k[1] for k in fam}):
        a, b = fam[("ctrl", k)], fam[("cand", k)]
        if a != b:
            print("   %-36s ctrl=%d cand=%d" % (k, a, b))

    out = os.path.join(ws, "energy-windows.txt")
    with open(out, "w", encoding="utf-8") as f:
        for a, s in arms:
            sp = os.path.join(ws, "%s-start.epoch" % a)
            ep = os.path.join(ws, "%s-end.epoch" % a)
            if os.path.exists(sp) and os.path.exists(ep):
                f.write("%s %s %s %s\n" % (a, s, open(sp).read().strip(), open(ep).read().strip()))
    print("\nwrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
