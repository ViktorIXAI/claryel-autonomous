#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for `scripts/pub_preflight.py` (added 2026-11-10).

What it pins:

  1. a healthy reading set returns GO (exit 0) and prints every reading;
  2. the gate is not vacuous — six independent tamper controls each return NO-GO
     (exit 3): exhausted swap, a low-MemAvailable box, an engine stuck in
     uninterruptible I/O, the idle-spin pair (high engine CPU at 0 % GPU), a
     non-200 /health, and a foreign leg on the same endpoint;
  3. the gate fails CLOSED on input gaps: a missing reading and an unreadable
     number both exit 1, never GO;
  4. two non-vacuity controls prove the thresholds are conditional, not
     "any swap used / any CPU is fatal": engine at high CPU WITH the GPU busy is
     GO, and a box with swap partially used (1 GiB free) is GO.

The real readings that motivated this gate (2026-11-10, tick 23) are reproduced as
the swap/D-state tamper case: 3 MiB swap free, engine state Dl, 602 % CPU at 0 % GPU.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "scripts", "pub_preflight.py")

FAILED = []
CHECKS = 0

HEALTHY = {
    "mem_total_mib": 61953, "mem_available_mib": 14047,
    "swap_total_mib": 8191, "swap_free_mib": 7800,
    "engine_state": "Sl", "engine_pcpu": 12.0, "engine_rss_mib": 57409,
    "gpu_util_pct": 0.0, "gpu_power_w": 34.0,
    "load1": 1.2, "health_code": 200, "foreign_legs": 0,
}


def ck(cond: bool, msg: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(msg)


def run(vals: dict) -> tuple[int, str]:
    fd, path = tempfile.mkstemp(prefix="preflight-", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for k, v in vals.items():
                fh.write(f"{k}={v}\n")
        p = subprocess.run([sys.executable, SCRIPT, path], capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr
    finally:
        os.unlink(path)


def variant(**over) -> dict:
    v = dict(HEALTHY)
    v.update(over)
    return v


def main() -> int:
    rc, out = run(HEALTHY)
    ck(rc == 0, f"healthy readings should GO, got exit {rc}: {out}")
    ck("PREFLIGHT GO" in out, "healthy run must print GO")
    ck("health_code" in out, "the readings themselves must be printed for the audit trail")

    tamper = [
        ("exhausted swap", variant(swap_free_mib=3), "swap free"),
        ("low MemAvailable", variant(mem_available_mib=512), "MemAvailable"),
        ("engine in D state", variant(engine_state="Dl"), "uninterruptible"),
        ("idle spin", variant(engine_pcpu=602.0, gpu_util_pct=0.0), "idle-spin"),
        ("health not 200", variant(health_code=503), "/health"),
        ("foreign leg", variant(foreign_legs=1), "one leg per endpoint"),
    ]
    for name, vals, needle in tamper:
        rc, out = run(vals)
        ck(rc == 3, f"tamper {name!r} should NO-GO (3), got {rc}")
        ck(needle in out, f"tamper {name!r} must name its reason ({needle!r}) in the output")

    # Non-vacuity of the two numeric thresholds.
    rc, out = run(variant(engine_pcpu=610.0, gpu_util_pct=42.0))
    ck(rc == 0, f"high engine CPU WITH a busy GPU is real work, not idle spin: {out}")
    rc, out = run(variant(swap_free_mib=1024))
    ck(rc == 0, f"1 GiB swap free is inside the threshold, should GO: {out}")

    # Input gaps fail closed, never GO.
    partial = dict(HEALTHY)
    del partial["swap_free_mib"]
    rc, out = run(partial)
    ck(rc == 1, f"missing reading must exit 1, got {rc}")
    ck("INPUT GAP" in out, "missing reading must name the gap")
    rc, out = run(variant(load1="n/a"))
    ck(rc == 1, f"unreadable number must exit 1, got {rc}")

    if FAILED:
        print(f"PUB PREFLIGHT TEST: {CHECKS - len(FAILED)}/{CHECKS} FAILED:")
        for f in FAILED:
            print("  - " + f)
        return 1
    print(f"PUB PREFLIGHT TEST: {CHECKS}/{CHECKS} checks green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
