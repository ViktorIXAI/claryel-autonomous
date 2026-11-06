#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Time and energy accounting for the bank v6.1 arms, generated from published artifacts.

Two different measurement situations are kept visibly separate:

  * contour arms run on the local inference GPU, whose board draw is sampled every ~2 s by the
    `parb-gpu-samp` unit (`gpu-power.csv`), so their energy is an integral of measured power.
  * cloud arms run outside this machine; what is measurable here is wall seconds, model calls and
    tokens. Their compute energy is not knowable from here and is left blank rather than guessed.

For the local raw arm the sample window may not cover the whole run (the sampler started mid-arm), so
the figure is reported as measured-Wh over the covered tasks plus a per-task rate, and the covered task
count is derived from the run log's own per-task seconds, not assumed.

Usage: python3 scripts/cost_table_v61.py [--power-csv PATH] [--unit NAME ...]
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = os.path.expanduser("~/parb-v61-raw-reps")
CWS = os.path.expanduser("~/parb-v61-contour")


def unit_window(unit):
    out = subprocess.run(["systemctl", "--user", "show", unit,
                          "-p", "ActiveEnterTimestamp", "-p", "InactiveExitTimestamp", "-p", "ActiveState"],
                         capture_output=True, text=True).stdout
    kv = dict(line.split("=", 1) for line in out.strip().splitlines() if "=" in line)
    return kv.get("ActiveEnterTimestamp", ""), kv.get("InactiveExitTimestamp", ""), kv.get("ActiveState", "")


def tasks_in_window(log_path, seconds_back):
    """How many tasks finished in the last `seconds_back` of a sequential run log."""
    if not os.path.exists(log_path):
        return None
    seq = [float(m.group(1)) for m in re.finditer(r"stop ([0-9.]+) s", open(log_path, encoding="utf-8", errors="replace").read())]
    total = sum(seq)
    if total <= seconds_back:
        return len(seq)
    acc = 0.0
    n = 0
    for s in reversed(seq):
        acc += s
        n += 1
        if acc > seconds_back:
            break
    return n


def power_stats(path, start=None, end=None):
    rows = []
    for line in open(path, encoding="utf-8"):
        p = [x.strip() for x in line.strip().split(",")]
        if len(p) < 3:
            continue
        try:
            ts, pw, util = float(p[0]), float(p[1]), float(p[2])
        except ValueError:
            continue
        if start is not None and ts < start:
            continue
        if end is not None and ts > end:
            continue
        rows.append((ts, pw, util))
    if len(rows) < 2:
        return None
    rows.sort()
    e = 0.0
    for (t0, p0, _), (t1, p1, _) in zip(rows, rows[1:]):
        dt = t1 - t0
        if 0 < dt <= 30:
            e += ((p0 + p1) / 2.0) * dt
    return {"samples": len(rows), "span_s": rows[-1][0] - rows[0][0], "wh": e / 3600.0,
            "mean_w": e / (rows[-1][0] - rows[0][0]) if rows[-1][0] > rows[0][0] else 0.0,
            "busy": sum(1 for _, _, u in rows if u >= 90) / len(rows)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--power-csv", default=os.path.join(CWS, "gpu-power.csv"))
    args = ap.parse_args()
    print("# Time and energy accounting, bank v6.1\n")
    print("| arm | tasks | model calls | tokens in/out | wall seconds | GPU energy |")
    print("|---|---|---|---|---|---|")

    # contour arms (local GPU)
    for rid, label in (("c229full", "contour 0.0.2.29 rep0"), ("c229r12", "contour 0.0.2.29 reps 1-2"),
                       ("c229r3", "contour 0.0.2.29 rep3")):
        led = os.path.join(CWS, "ledger-%s.jsonl" % rid)
        if rid == "c229full":
            led = os.path.join(ROOT, "benchmarks/hard/v6-results/full-229", "ledger-c229full.jsonl")
        if not os.path.exists(led):
            continue  # never substitute another arm's ledger: that printed rep0 numbers as rep3
        calls = ptok = ctok = 0
        secs = 0.0
        rows = 0
        for line in open(led, encoding="utf-8"):
            if '"_loop_rows"' in line:
                r0 = None
            r = __import__("json").loads(line)
            if "_loop_rows" in r:
                continue
            rows += 1
            calls += r.get("model_calls", 0) or 0
            ptok += r.get("ptok", 0) or 0
            ctok += r.get("ctok", 0) or 0
            secs += r.get("seconds", 0) or 0
        energy = ""
        st = os.path.join(CWS, "rep3-start.epoch")
        en = os.path.join(CWS, "rep3-end.epoch")
        if rid == "c229r3" and os.path.exists(st) and os.path.exists(en):
            ps = power_stats(args.power_csv, float(open(st).read().strip()), float(open(en).read().strip()))
            if ps:
                energy = "%.2f Wh measured (%.0f s at %.0f W mean, busy %.2f)" % (
                    ps["wh"], ps["span_s"], ps["mean_w"], ps["busy"])
        print("| %s | %d | %d | %d / %d | %.0f s | %s |" % (
            label, rows, calls, ptok, ctok, secs, energy or "see window note"))

    # raw local arm (same GPU, no contour)
    ent, ext, state = unit_window("parb-basalt-r12")
    note = ""
    if ent:
        import datetime
        f = "%a %Y-%m-%d %H:%M:%S %Z"
        try:
            t0 = datetime.datetime.strptime(ent, f).timestamp()
        except ValueError:
            t0 = None
        t1 = None
        if ext:
            try:
                t1 = datetime.datetime.strptime(ext, f).timestamp()
            except ValueError:
                t1 = None
        if t0 and t1:
            ps = power_stats(args.power_csv, t0, t1)
            covered = tasks_in_window(os.path.join(WS, "basalt-r12.log"), t1 - t0)
            if ps and covered:
                per = ps["wh"] / covered if covered else 0.0
                note = ("%.2f Wh measured over %d tasks covered by the sampler (%.0f s at %.0f W, "
                        "busy %.2f) -> %.4f Wh/task -> %.2f Wh per 71-task arm (scaled from the "
                        "sampled window)" % (ps["wh"], covered, ps["span_s"], ps["mean_w"], ps["busy"],
                                             per, per * 71))
    secs = 0.0
    rows = 0
    import json as _json
    for line in open(os.path.join(WS, "answers-basalt.jsonl"), encoding="utf-8"):
        r = _json.loads(line)
        rows += 1
        secs += r.get("seconds", 0) or 0
    print("| bare basalt reps 1-2 (local GPU, no contour) | %d | %d (one shot each) | not reported | %.0f s | %s |" % (
        rows, rows, secs, note or "sampler window pending"))

    for arm, label in (("codex", "ChatGPT (codex CLI)"), ("grok", "Grok (hermes CLI)")):
        p = os.path.join(WS, "answers-%s.jsonl" % arm)
        if not os.path.exists(p):
            continue
        import json as _json
        rows = 0
        secs = 0.0
        for line in open(p, encoding="utf-8"):
            r = _json.loads(line)
            rows += 1
            secs += r.get("seconds", 0) or 0
        print("| %s rep1 | %d | %d | not reported by the CLI transport | %.0f s | not measurable from this machine |" % (
            label, rows, rows, secs))
    print("\nReproduce: `scripts/gpu_energy.py` integrates the same trace; the sampler command is in")
    print("`ENERGY-METHOD.md`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
