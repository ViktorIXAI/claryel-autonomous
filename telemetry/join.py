#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Join run results with telemetry (run_id binding, stage 6 of the roadmap).

For every results row (task, rep, t_wall, box) finds telemetry samples of the
same machine inside the attempt window [t_wall - seconds, t_wall] (seconds
from the ledger when available, else the row's own timing), and reports the
median of each metric inside that window. Machines/windows with no samples
yield `not_available` — never interpolation.

Usage: python3 telemetry/join.py <results.jsonl> <ledger.jsonl> <telem.jsonl>
       prints a per-run conditions JSON (published next to the artifacts).
"""
import json
import sys
from collections import defaultdict

def med(xs):
    xs = sorted(xs)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else round((xs[n // 2 - 1] + xs[n // 2]) / 2, 2)


def main():
    res = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
    led = defaultdict(list)
    for l in open(sys.argv[2], encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        led[(r.get("task"), r.get("rep"))].append(r)
    samples = []
    header = None
    for l in open(sys.argv[3], encoding="utf-8"):
        if not l.strip():
            continue
        s = json.loads(l)
        if s.get("kind") == "telemetry-header":
            header = s
        else:
            samples.append(s)
    by_machine = defaultdict(list)
    for s in samples:
        by_machine[s["machine"]].append(s)

    # box passport name -> collector PARB_MACHINE name (documented mapping)
    name_map = {"P2005SAH": "P2005SAH", "B2003": "B2003", "mac-studio": "mac-studio"}
    per_attempt = {}
    win_all = defaultdict(list)
    for r in res:
        secs = 0.0
        for e in led.get((r["task"], r.get("rep")), []):
            secs += float(e.get("seconds") or 0)
        secs = max(secs, 1.0)
        tw = float(r.get("t_wall") or 0)
        mach = name_map.get(r.get("box"), r.get("box"))
        w = [s for s in by_machine.get(mach, []) if tw - secs <= s["ts"] <= tw + 1]
        for s in w:
            win_all[r["task"]].append(s)
        metrics = {}
        for k in ("cpu_pct", "cpu_ghz", "cpu_temp_c", "ram_avail_mb", "load1",
                  "gpu_util_pct", "gpu_power_w", "gpu_temp_c", "vram_used_mb"):
            vals = [s[k] for s in w if isinstance(s.get(k), (int, float))]
            metrics[k] = med(vals) if vals else "not_available"
        per_attempt["%s#%s" % (r["task"], r.get("rep"))] = {
            "machine": mach, "window_s": round(secs, 1), "samples_in_window": len(w),
            "median": metrics}

    run_metrics = {}
    for s_key in by_machine:
        ss = by_machine[s_key]
        run_metrics[s_key] = {
            "samples": len(ss),
            "span_s": round(ss[-1]["ts"] - ss[0]["ts"], 1) if len(ss) > 1 else 0,
            "run_id": ss[0].get("run_id"),
            "peak": {k: (max((x[k] for x in ss if isinstance(x.get(k), (int, float))), default="not_available"))
                     for k in ("cpu_pct", "cpu_temp_c", "gpu_util_pct", "gpu_power_w",
                               "gpu_temp_c", "vram_used_mb", "load1")},
            "mean": {k: (med([x[k] for x in ss if isinstance(x.get(k), (int, float))]) or "not_available")
                     for k in ("cpu_pct", "cpu_temp_c", "gpu_util_pct", "gpu_power_w",
                               "gpu_temp_c", "vram_used_mb", "load1")},
        }
    print(json.dumps({"header": header, "run_level": run_metrics,
                      "per_attempt": per_attempt}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
