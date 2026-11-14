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
     GO, and a box with swap partially used (1 GiB free) is GO;
  5. the optional swap_used_mib re-sums the swap columns (2026-11-12: an untracked
     reader fed the USED column as swap_free_mib on a swap-saturated box — used
     8159 / free 32 / total 8191 — which would have GO'd the swap rule; when the
     key is present a mismatch is an input gap, a within-tolerance balance still
     GOes, and an unreadable value fails closed);
     6. the optional live swap-throughput window `swap_in_mib_per_s` / `swap_out_mib_per_s`
     (2026-11-14): present and over the pre-registered ceiling is NO-GO, the launchable bursts
     this line recorded stay GO, the boundary is conditional (19.9 GO / 20.0 NO-GO), an
     unreadable rate, a negative counter delta or a one-sided window is an input gap, an absent
     window changes no verdict and prints a coverage line, and reasons accumulate;
  7. the optional device-read window `blk_read_mib_per_s` plus its attribution `blk_top_reader`
     (2026-11-14, same tooling release): both measured interference windows (1856.8 MiB/s and the
     224.4 MiB/s tail phase of a fleet model push, engine taking 628 major faults/s at idle) are
     NO-GO and name the reader, the measured idle device rate (0.2 MiB/s) stays GO, an over-ceiling
     rate attributed to the engine itself still NO-GOs (the reader is diagnostic), the boundary is
     conditional (99.9 GO / 100.0 NO-GO), an unreadable, non-finite or negative delta is an input
     gap, an absent window changes no verdict and prints a coverage line, and reasons accumulate;
  8. every parsed number must be FINITE: the producer emits NaN when a sample window was cut, and
     Python's `float()` parses `NaN`/`inf`, so a cut sample used to reach the comparison stage where
     every threshold answer is False — a silent GO on all the numeric rules (found 2026-11-14).

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


def run_text(text: str) -> tuple[int, str]:
    """Feed a raw readings file exactly as a producer writes it (any shape)."""
    fd, path = tempfile.mkstemp(prefix="preflight-", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
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

    # Swap-column balance (2026-11-12): the untracked reader fed the USED column as
    # swap_free_mib on a box with total 8191 / used 8159 / free 32, so the swap rule
    # would have GO'd a fully swapped-out endpoint. When swap_used_mib is present the
    # gate re-sums the columns; the producer's own numbers reproduce the mix-up.
    rc, out = run(variant(swap_used_mib=391))
    ck(rc == 0, f"balanced swap columns must still GO, got exit {rc}: {out}")
    rc, out = run(variant(swap_used_mib=8159, swap_free_mib=8159))
    ck(rc == 1 and "do not add up" in out,
       f"the used-as-free mix-up must be an input gap, got exit {rc}: {out}")
    rc, out = run(variant(swap_used_mib=390, swap_free_mib=7740))
    ck(rc == 0, f"a 61 MiB rounding gap is inside tolerance and must GO, got exit {rc}: {out}")
    rc, out = run(variant(swap_used_mib="n/a"))
    ck(rc == 1, f"an unreadable swap_used_mib must exit 1, got {rc}")

    # Reading-file shapes (2026-11-12): the docstring teaches the single-line form and the
    # remote producer pads some values (`ps -o pcpu=` emits `engine_pcpu= 459`). A live read
    # that day hit both, and the gate answered INPUT GAP then `unreadable number(s):
    # engine_pcpu, gpu_power_w` — fail-closed, but the documented shape was unusable.
    one_line = " ".join(f"{k}={v}" for k, v in HEALTHY.items())
    rc, out = run_text(one_line + "\n")
    ck(rc == 0, f"the docstring's one-line shape must parse, got exit {rc}: {out}")
    ck("PREFLIGHT GO" in out, "the one-line shape must reach the verdict, not the parser")
    padded = ("mem_total_mib=61953 mem_available_mib=14047 swap_total_mib=8191 "
              "swap_free_mib=7800 engine_state=Sl engine_pcpu= 12.0 engine_rss_mib=57409 "
              "gpu_util_pct=0.0 gpu_power_w= 34.0 load1=1.2 health_code=200 foreign_legs=0")
    rc, out = run_text(padded + "\n")
    ck(rc == 0, f"a padded value (ps output) must still be one reading, got exit {rc}: {out}")
    rc, out = run_text(padded.replace("swap_free_mib=7800", "swap_free_mib=0") + "\n")
    ck(rc == 3 and "swap free" in out,
       f"a padded live reading with a spent swap device must NO-GO, got {rc}: {out}")
    rc, out = run_text("engine_pcpu=\n459\n"
                       + "\n".join(f"{k}={v}" for k, v in HEALTHY.items() if k != "engine_pcpu")
                       + "\n")
    ck(rc == 1 and "INPUT GAP" in out,
       f"an empty value must NOT borrow the next line, got exit {rc}: {out}")
    rc, out = run_text(" ".join(f"{k}={v}" for k, v in HEALTHY.items() if k != "health_code") + "\n")
    ck(rc == 1 and "INPUT GAP" in out,
       f"a dropped key in the one-line shape must fail closed, got exit {rc}: {out}")

    # The loaded flag (2026-11-13): a config-ladder restart on the endpoint box killed the engine
    # child while the serve.server wrapper kept answering HTTP 200 with "loaded": false, and this
    # gate answered GO at 09:03 and 09:28 on exactly those bytes. health_code==200 proves a
    # listener, not a model.
    live0928 = {
        "mem_total_mib": 61953, "mem_available_mib": 58884,
        "swap_total_mib": 8191, "swap_free_mib": 7187, "swap_used_mib": 1004,
        "engine_state": "S", "engine_pcpu": 0.0, "engine_rss_mib": 516,
        "gpu_util_pct": 0.0, "gpu_power_w": 7.82,
        "load1": 0.27, "health_code": 200, "foreign_legs": 0,
    }
    rc, out = run(live0928)
    ck(rc == 0, f"a pre-fix reading with no loaded flag keeps its verdict (no retro-active rule), "
                f"got exit {rc}: {out}")
    ck("(coverage)" in out, "an uncovered reading must say so in the audit trail")
    rc, out = run(dict(live0928, health_loaded="false", engine_serve_procs=0))
    ck(rc == 3, f"the same bytes WITH the loaded flag must NO-GO, got exit {rc}: {out}")
    ck('"loaded": false' in out, "the NO-GO must name the loaded flag")
    ck("basalt --serve" in out, "the NO-GO must name the missing engine process")
    rc, out = run(variant(health_loaded="false"))
    ck(rc == 3 and '"loaded": false' in out,
       f"a loaded=false model must NO-GO even with every other reading healthy, got {rc}: {out}")
    rc, out = run(variant(health_loaded="true", engine_serve_procs=1))
    ck(rc == 0, f"loaded=true with one engine process must GO, got exit {rc}: {out}")
    ck("swap_in_mib_per_s" in out and "predates that fix" in out,
       f"a loaded-covered reading with no counter window must still report the swap-rate gap, "
       f"got exit {rc}: {out}")
    rc, out = run(dict(live0928, health_loaded="true", engine_serve_procs=1,
                       swap_in_mib_per_s=0.0, swap_out_mib_per_s=0.0,
                       blk_read_mib_per_s=0.0, blk_top_reader="basalt"))
    ck(rc == 0 and "(coverage)" not in out,
       f"a fully covered reading must not print a coverage warning, got exit {rc}: {out}")
    rc, out = run(dict(live0928, health_loaded="true", engine_serve_procs=1,
                       swap_in_mib_per_s=0.0, swap_out_mib_per_s=0.0))
    ck(rc == 0 and "blk_read_mib_per_s device window" in out and "not covered" in out,
       f"a reading covered by every older rule but not the device window must say so, "
       f"got exit {rc}: {out}")

    # Live swap throughput (2026-11-14, tooling release, no contour stamp and no published byte).
    # The stored swap rule sees a device that is ALREADY spent; it cannot see 50 GiB free with
    # gigabytes moving through it now, and load1 cannot proxy the traffic at all — measured on the
    # endpoint box 2026-11-13/14: load1 9.8 -> 14.6 -> 11.0 -> 14.0 across three minutes with three
    # /proc/vmstat counter windows at ~0.2 MiB/s in / 0 out, then load1 12.6-13.5 with `vmstat 1 8`
    # showing r=0 and b=0 in EVERY sample, idle 99-100 %, PSI cpu 0.00, no D-state process. The
    # threshold is pre-registered above every launchable window this line recorded (the recorded
    # 11.9 MiB/s burst is a GO; the 87.5 MiB/s burst was the day the engine flickered Sl<->D).
    live_today = dict(live0928, health_loaded="true", engine_serve_procs=1,
                      swap_total_mib=65535, swap_free_mib=50703, swap_used_mib=14832,
                      mem_available_mib=19776, engine_rss_mib=56247, load1=12.59,
                      gpu_power_w=27.26)
    rc, out = run(dict(live_today, swap_in_mib_per_s=0.0, swap_out_mib_per_s=0.0))
    ck(rc == 0 and "live swap throughput" not in out,
       f"the 2026-11-14 live idle window (0.0 in / 0.0 out at load1 12.59) must GO, got {rc}: {out}")
    rc, out = run(dict(live_today, swap_in_mib_per_s=5.3, swap_out_mib_per_s=6.6))
    ck(rc == 0 and "live swap throughput" not in out,
       f"the recorded launchable burst (11.9 MiB/s sum) must stay GO, got {rc}: {out}")
    rc, out = run(dict(live_today, swap_in_mib_per_s=77.9, swap_out_mib_per_s=9.6))
    ck(rc == 3 and "live swap throughput" in out,
       f"an 87.5 MiB/s window must NO-GO and name the reason, got {rc}: {out}")
    ck("load1 cannot see" in out, "the reason must say why load1 is not a substitute")
    rc, out = run(variant(swap_in_mib_per_s=19.9, swap_out_mib_per_s=0.0))
    ck(rc == 0, f"19.9 MiB/s sits under the pre-registered ceiling and must GO, got {rc}: {out}")
    rc, out = run(variant(swap_in_mib_per_s=20.0, swap_out_mib_per_s=0.0))
    ck(rc == 3, f"exactly the ceiling must NO-GO, got {rc}")
    rc, out = run(variant(swap_in_mib_per_s="n/a", swap_out_mib_per_s=0.0))
    ck(rc == 1 and "unreadable number(s): swap_in_mib_per_s" in out,
       f"an unreadable rate must be an input gap, got {rc}: {out}")
    rc, out = run(variant(swap_in_mib_per_s=1.0, swap_out_mib_per_s=-3.0))
    ck(rc == 1 and "cannot run backwards" in out,
       f"a negative counter delta is a broken window, never healthy, got {rc}: {out}")
    rc, out = run(variant(swap_in_mib_per_s=9.9))
    ck(rc == 1 and "ONE counter window" in out,
       f"a one-sided counter window must be an input gap, got {rc}: {out}")
    rc, out = run(dict(variant(swap_in_mib_per_s=88.0, swap_out_mib_per_s=9.0), engine_state="Dl"))
    ck(rc == 3 and "live swap throughput" in out and "uninterruptible" in out,
       f"reasons must accumulate (thrash + D state), got {rc}: {out}")
    rc, out = run(variant(engine_serve_procs=0))
    ck(rc == 3 and "launcher" in out,
       f"engine_serve_procs=0 must NO-GO and name the wrong-process trap, got {rc}: {out}")
    rc, out = run(variant(health_loaded="maybe"))
    ck(rc == 1 and "not a boolean" in out,
       f"an unparseable loaded flag must be an input gap, got exit {rc}: {out}")
    rc, out = run(variant(engine_serve_procs="n/a"))
    ck(rc == 1, f"an unreadable engine_serve_procs must exit 1, got {rc}")

    # Foreign block I/O (2026-11-14, tooling release, no contour stamp, no published benchmark byte).
    # The swap-throughput rule measured 17.4 MiB/s on this box at 10:59 — the highest value this line
    # has recorded, 87 % of its own ceiling — and answered GO. The device counters name the cause the
    # swap window cannot see: a fleet model push (`rsync -a .../models/IQ3_S/ -> <LAN_IP>`, started
    # 10:54, recorded by the ops line the same morning) read the device at 1856.8 MiB/s over one 8 s
    # window (nvme0n1 read 1856.8 / write 0.2) with 755 MiB/s of pgpgin in another, `pgscan_kswapd`
    # stole 420 769 pages in 8 s, and the engine took 5021 major faults in 8 s (628/s) while every
    # other rule was green (/health 200, loaded true, 49.9 GiB swap free, GPU util 2 %, Sl/Rl).
    # The same box AFTER the push finished (11:12, idle) answers 0.2 MiB/s of device reads in two
    # 10 s windows, engine 0.1 MiB/s, 0 major faults/s, pswpin/pswpout 0.00, vmstat si=so=0 idle 100 %
    # — a 1000x gap the ceiling sits inside. The network-limited tail phase measured 224.4 MiB/s with
    # `rsync` as the largest attributed reader.
    live_push = dict(live_today, swap_in_mib_per_s=17.4, swap_out_mib_per_s=0.0,
                     swap_free_mib=49935, swap_used_mib=15600, mem_available_mib=18591,
                     engine_rss_mib=54299, load1=15.67, gpu_util_pct=3.0, gpu_power_w=36.33)
    rc, out = run(live_push)
    ck(rc == 0 and "blk_read_mib_per_s device window" in out,
       f"the 2026-11-14 10:59 live bytes keep their verdict with no device window (no retro-active "
       f"rule), got exit {rc}: {out}")
    rc, out = run(dict(live_push, blk_read_mib_per_s=1856.8, blk_top_reader="rsync"))
    ck(rc == 3 and "block-device reads" in out and "rsync" in out,
       f"the measured interference window must NO-GO and name the reader, got exit {rc}: {out}")
    ck("major faults" in out, "the reason must name the engine-side cost (refaults), not just MiB/s")
    rc, out = run(dict(live_push, blk_read_mib_per_s=224.4, blk_top_reader="rsync"))
    ck(rc == 3 and "block-device reads" in out,
       f"the measured tail-phase window (224.4 MiB/s) must also NO-GO, got exit {rc}: {out}")
    rc, out = run(dict(live_push, blk_read_mib_per_s=99.9, blk_top_reader="basalt"))
    ck(rc == 0, f"99.9 MiB/s sits under the pre-registered ceiling and must GO, got exit {rc}: {out}")
    rc, out = run(dict(live_push, blk_read_mib_per_s=100.0))
    ck(rc == 3, f"exactly the ceiling must NO-GO, got exit {rc}")
    ck("largest attributed reader" not in out,
       f"a NO-GO with no reader attribution must not invent one, got: {out}")
    rc, out = run(dict(live_push, blk_read_mib_per_s=0.2, blk_top_reader="basalt"))
    ck(rc == 0, f"the measured idle device rate (0.2 MiB/s) must stay GO — the rule is not 'any disk "
                f"activity': got exit {rc}: {out}")
    rc, out = run(dict(live_push, blk_read_mib_per_s=120.0, blk_top_reader="basalt"))
    ck(rc == 3 and "basalt" in out,
       f"an over-ceiling rate attributed to the ENGINE itself still NO-GOs — the gate reads the "
       f"device, the reader is diagnostic only, got exit {rc}: {out}")
    rc, out = run(dict(live_push, blk_read_mib_per_s=17.4, blk_top_reader="rsync"))
    ck(rc == 0 and "rsync" in out and "block-device reads" not in out,
       f"an attribution below the ceiling must be printed for the audit trail and must not gate, "
       f"got exit {rc}: {out}")
    rc, out = run(dict(live_push, blk_read_mib_per_s="n/a"))
    ck(rc == 1 and "unreadable number(s): blk_read_mib_per_s" in out,
       f"an unreadable device rate must be an input gap, got exit {rc}: {out}")
    rc, out = run(dict(live_push, blk_read_mib_per_s=-1.0))
    ck(rc == 1 and "cannot run backwards" in out,
       f"a negative device counter delta is a broken window, never healthy, got exit {rc}: {out}")
    rc, out = run(dict(variant(blk_read_mib_per_s=1400.0, blk_top_reader="rsync"), engine_state="Dl"))
    ck(rc == 3 and "block-device reads" in out and "uninterruptible" in out,
       f"reasons must accumulate (foreign I/O + D state), got exit {rc}: {out}")

    # NaN fails CLOSED (found 2026-11-14 while wiring the device window). The producer emits NaN by
    # design when its sample window was cut, and Python's float() parses "NaN"/"inf" — so before this
    # fix a NaN reading reached the comparison stage, where `NaN >= ceiling` and `NaN > threshold` are
    # both False: a cut sample used to be a SILENT GO on every numeric rule in this gate.
    for key in ("load1", "engine_pcpu", "swap_in_mib_per_s", "blk_read_mib_per_s"):
        over = {key: "NaN"}
        if key.startswith("swap_"):
            over["swap_out_mib_per_s"] = "0.0"
        rc, out = run(variant(**over))
        ck(rc == 1 and "unreadable number(s)" in out,
           f"{key}=NaN must be an input gap, never a silent GO, got exit {rc}: {out}")
    rc, out = run(variant(blk_read_mib_per_s="inf"))
    ck(rc == 1, f"blk_read_mib_per_s=inf must be an input gap, got exit {rc}")

    if FAILED:
        print(f"PUB PREFLIGHT TEST: {CHECKS - len(FAILED)}/{CHECKS} FAILED:")
        for f in FAILED:
            print("  - " + f)
        return 1
    print(f"PUB PREFLIGHT TEST: {CHECKS}/{CHECKS} checks green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
