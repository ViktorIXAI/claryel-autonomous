#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pre-launch gate for a LOCAL public-line leg on the shared inference endpoint.

Why this exists (measured, not hypothetical): the machine note for this line says P2005 swap
saturation can restart the engine mid-leg, and ticks 13, 19, 20, 21 and 22 of 2026-11-10 each read
`free -m`, `ps` and `nvidia-smi` by hand to decide whether a local leg could be launched. Five hand
readings is a rule waiting to be mechanical. This script is the public-line analogue of
`scripts/live_target_check.py` on the hard bank: a check that must run BEFORE an endpoint window is
reserved, and that fails closed.

The readings come from a one-line remote read over the repo-standard key (the command itself stays
untracked so no connection material lands in this repo) and are passed in as a `key=value` file:

    mem_total_mib=61953 mem_available_mib=14047 swap_total_mib=8191 swap_free_mib=3
    engine_state=Dl engine_pcpu=602 engine_rss_mib=57409 gpu_util_pct=0 gpu_power_w=35.8
    load1=13.38 health_code=200 foreign_legs=0

Usage:
    python3 scripts/pub_preflight.py READINGS.TXT

Exit 0 = GO: the endpoint can take a local leg.
Exit 3 = NO-GO: the readings show a condition this line refuses to launch into.
Exit 1 = bad or missing input (a missing reading is never treated as healthy).
"""
from __future__ import annotations

import sys

# Thresholds carry the measurement that set them. They are deliberately conservative: a false NO-GO
# costs one idle tick, a false GO costs a discarded partial leg.
SWAP_FREE_MIN_MIB = 256     # legs ran while the swap device was nearly free; the refused window
                            # measured 48 MiB free (tick 21) then 3.6 MiB free (tick 23)
MEM_AVAILABLE_MIN_MIB = 2048  # the resident engine plus its cache needs headroom to re-admit KV
IDLE_SPIN_PCPU = 200        # idle-spin signature: engine >200 % CPU with GPU util 0 %; measured
                            # 602-629 % CPU at 0 % GPU / 35-37 W. Per-task seconds in that state run
                            # 20-220x the last paired median, so the leg scores but the timing and
                            # energy columns are garbage.
REQUIRED = (
    "mem_total_mib", "mem_available_mib", "swap_total_mib", "swap_free_mib",
    "engine_state", "engine_pcpu", "engine_rss_mib", "gpu_util_pct", "gpu_power_w",
    "load1", "health_code", "foreign_legs",
)
FLOATS = ("engine_pcpu", "gpu_util_pct", "gpu_power_w", "load1")


def read(path: str) -> dict:
    vals: dict[str, str] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip()
    return vals


def num(vals: dict, key: str):
    return float(vals[key])


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print((__doc__ or "").strip())
        return 1
    vals = read(sys.argv[1])

    missing = [k for k in REQUIRED if k not in vals]
    if missing:
        print("PREFLIGHT INPUT GAP: no reading for " + ", ".join(missing)
              + " — a missing reading is never healthy.")
        return 1
    bad = []
    for k in FLOATS:
        try:
            num(vals, k)
        except ValueError:
            bad.append(k)
    for k in ("mem_total_mib", "mem_available_mib", "swap_total_mib", "swap_free_mib",
              "engine_rss_mib", "health_code", "foreign_legs"):
        try:
            int(vals[k])
        except ValueError:
            bad.append(k)
    if bad:
        print("PREFLIGHT INPUT GAP: unreadable number(s): " + ", ".join(bad))
        return 1

    reasons: list[str] = []
    if int(vals["health_code"]) != 200:
        reasons.append(f"/health answered {vals['health_code']}, not 200")
    if int(vals["swap_free_mib"]) < SWAP_FREE_MIN_MIB:
        reasons.append(
            f"swap free {vals['swap_free_mib']} MiB of {vals['swap_total_mib']} MiB "
            f"(< {SWAP_FREE_MIN_MIB}): the engine can be OOM-restarted mid-leg")
    if int(vals["mem_available_mib"]) < MEM_AVAILABLE_MIN_MIB:
        reasons.append(f"MemAvailable {vals['mem_available_mib']} MiB < {MEM_AVAILABLE_MIN_MIB}")
    if "D" in vals["engine_state"]:
        reasons.append(f"engine in uninterruptible I/O (state {vals['engine_state']}): thrashing")
    if num(vals, "engine_pcpu") > IDLE_SPIN_PCPU and num(vals, "gpu_util_pct") == 0:
        reasons.append(
            f"idle-spin signature: engine {vals['engine_pcpu']} % CPU at GPU "
            f"{vals['gpu_util_pct']} % — per-task seconds and energy columns would be junk")
    if int(vals["foreign_legs"]) > 0:
        reasons.append(f"{vals['foreign_legs']} other leg(s) on this endpoint: one leg per endpoint")

    print("endpoint readings:")
    for k in REQUIRED:
        print(f"  {k:<18} {vals[k]}")
    if reasons:
        print("PREFLIGHT NO-GO:")
        for r in reasons:
            print("  - " + r)
        print("Remedy is a box decision (engine restart / park the keep-up load), never a contour "
              "or bank change. Cloud legs are unaffected by this gate.")
        return 3
    print("PREFLIGHT GO: launch one local leg (own systemd unit + fresh GPU sampler csv).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
