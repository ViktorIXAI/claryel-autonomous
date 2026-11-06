#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integrate the sampled GPU power trace into watt-hours for a named window.

The inference host exposes no joule counter that this session can read, so energy is measured the only
honest way left: `nvidia-smi --query-gpu=power.draw` sampled every ~2 s over the whole arm, integrated
as sum(power_W * dt). That is board-level draw for the GPU doing the work (plus serve idle), not a wall
outlet reading, and it excludes the CPU/RAM of the inference box — the difference is stated in
`ENERGY-METHOD.md` rather than hidden.

Usage:
  python3 scripts/gpu_energy.py GPU_POWER_CSV [--start EPOCH] [--end EPOCH] [--label TEXT]

CSV rows: epoch_seconds,power_draw_W,utilization_pct,memory_used_MiB,temperature_C
"""
import argparse
import csv
from datetime import datetime


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--start", type=float, default=None)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--label", default="window")
    args = ap.parse_args()

    rows = []
    for line in open(args.csv_path, encoding="utf-8"):
        parts = [p.strip() for p in line.strip().split(",")]
        if len(parts) < 3:
            continue
        try:
            ts = float(parts[0]); pw = float(parts[1]); util = float(parts[2])
        except ValueError:
            continue
        if args.start is not None and ts < args.start:
            continue
        if args.end is not None and ts > args.end:
            continue
        rows.append((ts, pw, util))
    if len(rows) < 2:
        print("not enough samples in the window")
        return 1
    rows.sort()
    energy_j = 0.0
    for (t0, p0, _), (t1, p1, _) in zip(rows, rows[1:]):
        dt = t1 - t0
        if 0 < dt <= 30:
            energy_j += ((p0 + p1) / 2.0) * dt
    span = rows[-1][0] - rows[0][0]
    wh = energy_j / 3600.0
    mean_w = energy_j / span if span else 0.0
    busy = sum(1 for _, _, u in rows if u >= 90) / len(rows)
    print("%s: samples=%d span=%.0fs mean_power=%.1fW gpu_busy_fraction=%.2f energy=%.2fWh (%d J)" % (
        args.label, len(rows), span, mean_w, busy, wh, int(energy_j)))
    print("  window %s -> %s" % (
        datetime.fromtimestamp(rows[0][0]).strftime("%H:%M:%S"),
        datetime.fromtimestamp(rows[-1][0]).strftime("%H:%M:%S")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
