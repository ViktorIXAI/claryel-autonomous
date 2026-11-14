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
     every threshold answer is False — a silent GO on all the numeric rules (found 2026-11-14);
  9. the optional in-window peak `swap_total_peak_mib_per_s` (2026-11-14, tick 146) is validated and
     REPORTED but never a refusal reason in this release: the measured storm peak (34.6 MiB/s swap-in
     in one 8 s window, matched by 34.7 MiB/s of nvme0n1 reads) must print and must not flip the
     verdict, a missing key must leave the report unchanged, a peak below the window mean / NaN /
     negative / unreadable is an input gap, and a peak equal to the mean is the legal GO boundary.
     Registering a peak ceiling is a deliberate future change, pinned by the 1000 MiB/s-stays-GO check.
  10. the optional `blk_scope` marker (2026-11-14, tick 146): the producer's original device sum
     counted disk AND partition lines and so printed ~2x the device (measured: nvme0n1 35.8 against
     p2 10.3 + p3 25.5), which means every stored `blk_read_mib_per_s` is on an inflated scale. Files
     with no scope key keep the 100.0 ceiling (never re-judged); `blk_scope=whole-disk` is judged at
     50.0, the same physical point — the two scales must verdict-match on the measured window, the
     corrected boundary is conditional (49.9 GO / 50.0 NO-GO) and the NO-GO names the scope; an
     unknown scope value is an input gap, never a borrowed ceiling.
  11. the optional GPU contention WINDOW `gpu_util_mean_pct` + `gpu_util_peak_pct` (2026-11-14, tick
     148): the 6 saturated stored readings and the 13:54 live sample that read `gpu_util_pct=0` at
     108.35 W while 93k/96k-token prefills ran on the shared brain are the motivation. A window mean
     at or above GPU_UTIL_MAX_MEAN_PCT NO-GOs and names the state; the CEILING IS ON THE MEAN ONLY, so
     a 96 % peak inside a 12 % mean stays GO and is reported (registering a peak ceiling would gate a
     quantity with no measured idle band, the same mistake the swap peak deliberately avoids); a peak
     of exactly 100 % in a quiet mean must still print; one key without the other, a non-finite
     number, a negative, a value above GPU_UTIL_MAX_PCT, or a peak below the window mean is an input
     gap; absent keys change no verdict, so all 105 stored readings keep their verdicts.

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
                       blk_read_mib_per_s=0.0, blk_top_reader="basalt",
                       gpu_util_mean_pct=0.0, gpu_util_peak_pct=0))
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

    # Peak swap throughput INSIDE the window (2026-11-14, tick 146): validated and reported, not gated.
    # Measured on the live endpoint with a MATCHED instrument — the swap counters and the device
    # counter read in the SAME 8 s window: pswpin +70 876 pages = 276.9 MiB = 34.6 MiB/s in / 0.0 out,
    # nvme0n1 +568 568 sectors = 277.6 MiB = 34.7 MiB/s. The two counters agree to 99.7 %, so they
    # name ONE physical event (a refault burst off the NVMe swapfiles; zswap is disabled there and
    # SwapCached grew by the same 277 MiB), and the two producer readings bracketing the burst
    # (12:05, 12:07) recorded 8.2 and 0.0 MiB/s: a once-per-tick mean cannot see a burst that lives
    # between samples. The producer now reports a peak; the ceiling stays unregistered until a peak
    # band exists, because SWAP_RATE_MAX_MIB_S = 20.0 was pre-registered against MEAN windows and this
    # box runs permanently over-committed (engine 57.3 GiB RSS of 61.9 GiB, 15.5 GiB in swap) —
    # published legs already ran inside that state.
    storm = variant(swap_in_mib_per_s=8.2, swap_out_mib_per_s=0.0,
                    swap_total_peak_mib_per_s=34.6)
    rc, out = run(storm)
    ck(rc == 0 and "(diagnostic) peak swap throughput" in out and "34.6" in out,
       f"the measured storm peak must be printed and must NOT flip the verdict in this release, got {rc}: {out}")
    rc, out = run(variant(swap_in_mib_per_s=8.2, swap_out_mib_per_s=0.0))
    ck(rc == 0 and "(diagnostic)" not in out,
       f"without the peak key the report must stay byte-identical to the old reading, got {rc}: {out}")
    rc, out = run(variant(swap_in_mib_per_s=0.0, swap_out_mib_per_s=0.0,
                          swap_total_peak_mib_per_s=1000.0))
    ck(rc == 0, "a 1000 MiB/s peak must still GO while NO peak ceiling is registered — this check pins "
                f"that decision on purpose; a release that gates the peak must change it deliberately, got {rc}")
    rc, out = run(variant(swap_in_mib_per_s=5.3, swap_out_mib_per_s=6.6,
                          swap_total_peak_mib_per_s=11.9))
    ck(rc == 0 and "(diagnostic)" in out,
       f"a peak EQUAL to the window mean is the legal boundary and must not be an input gap, got {rc}: {out}")
    rc, out = run(variant(swap_in_mib_per_s=5.3, swap_out_mib_per_s=6.6,
                          swap_total_peak_mib_per_s=5.0))
    ck(rc == 1 and "below the window mean" in out,
       f"a peak below the window mean is arithmetically impossible and must be an input gap, got {rc}: {out}")
    rc, out = run(variant(swap_in_mib_per_s=0.0, swap_out_mib_per_s=0.0,
                          swap_total_peak_mib_per_s="NaN"))
    ck(rc == 1 and "unreadable number(s): swap_total_peak_mib_per_s" in out,
       f"a NaN peak (the producer's cut-window marker) must be an input gap, got {rc}: {out}")
    rc, out = run(variant(swap_in_mib_per_s=0.0, swap_out_mib_per_s=0.0,
                          swap_total_peak_mib_per_s=-4.0))
    ck(rc == 1 and "cannot be below zero" in out,
       f"a negative peak must be an input gap, got {rc}: {out}")
    rc, out = run(variant(swap_in_mib_per_s=0.0, swap_out_mib_per_s=0.0,
                          swap_total_peak_mib_per_s="n/a"))
    ck(rc == 1, f"an unreadable peak must exit 1, got {rc}")
    rc, out = run(variant(swap_total_peak_mib_per_s=34.6))
    ck(rc == 0 and "not present in this reading" in out,
       f"a peak with no mean window in the file is still reportable (no cross-check possible), got {rc}: {out}")

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

    # Device-read SCOPE (2026-11-14, tick 146). The producer's first version summed /proc/diskstats
    # DISK lines AND PARTITION lines, and the disk line already aggregates its partitions, so every
    # number it emitted was ~2x the device. Proven live in one 8 s window on the endpoint box:
    # nvme0n1 35.8 MiB/s against nvme0n1p2 10.3 + nvme0n1p3 25.5 = 35.8, sum 71.6. Files with no
    # blk_scope keep the inflated scale and the 100.0 ceiling they were judged with (no stored reading
    # is re-judged); blk_scope=whole-disk is judged at 50.0 — the same physical point, truthful number.
    whole = dict(live_push, blk_scope="whole-disk")
    rc, out = run(dict(whole, blk_read_mib_per_s=35.8, blk_top_reader="basalt"))
    ck(rc == 0, f"a measured engine refault window (35.8 MiB/s whole-disk) must GO on the corrected "
                f"scale, got exit {rc}: {out}")
    rc, out = run(dict(live_push, blk_read_mib_per_s=71.6, blk_top_reader="basalt"))
    ck(rc == 0, f"the SAME physical state on the stored inflated scale (71.6, no scope key) must also "
                f"GO — the two scales verdict-match, got exit {rc}: {out}")
    rc, out = run(dict(whole, blk_read_mib_per_s=49.9))
    ck(rc == 0, f"49.9 MiB/s whole-disk sits under the corrected ceiling and must GO, got exit {rc}: {out}")
    rc, out = run(dict(whole, blk_read_mib_per_s=50.0))
    ck(rc == 3 and "(>= 50.0, scope whole-disk)" in out,
       f"exactly the corrected ceiling must NO-GO and NAME the scope, got exit {rc}: {out}")
    rc, out = run(dict(live_push, blk_read_mib_per_s=60.0))
    ck(rc == 0, f"60.0 on the stored scale stays GO — stored files are never re-judged by the new "
                f"scope rule, got exit {rc}: {out}")
    rc, out = run(dict(whole, blk_read_mib_per_s=60.0))
    ck(rc == 3, f"60.0 whole-disk is a real 60 MiB/s storm and must NO-GO on the corrected scale, got exit {rc}")
    rc, out = run(dict(live_push, blk_read_mib_per_s=10.0, blk_scope="diskstats-all"))
    ck(rc == 1 and "not a known device scope" in out,
       f"an unknown scope must be an input gap, never a borrowed ceiling, got exit {rc}: {out}")

    # GPU contention WINDOW (2026-11-14, tooling release, no contour stamp, no published benchmark
    # byte). `gpu_util_pct` was one instantaneous nvidia-smi read, and it is burst-blind: live at
    # 13:54 it printed 0 % at 108.35 W / 59 C while the serve log's last two lines were completions of
    # prefills of 93 554 and 96 301 prompt tokens. The census over 105 stored readings makes the other
    # half of the blindness mechanical: 94 of the 104 numeric readings report 0 %, 3 report 0-20 %, and
    # only 7 report >= 20 % (five at 96-100 % at 114.13-153.62 W, plus 29 % at 39.4 W and 47 % at
    # 27.2 W), and foreign_legs=0 in EVERY stored reading because that key counts
    # only this line's two runners — so a saturated SHARED brain never blocked this gate on its own
    # evidence: the pre-fix gate answered GO on 2026-11-11 10:30 and 2026-11-13 15:50 of those five, and
    # blocked the other three only by accident (one engine state D, two engine_pcpu NaN input gaps).
    # 2026-11-14: the current serve log on that box holds 59 876 completed requests, 2 793 of them with
    # prompts over 150 000 tokens (largest pp=260052 with a 78.3 s prefill), and `pgrep` for this line's
    # runners on the endpoint box is empty — all of that traffic is other tenants. The cost here is
    # comparability, not safety: the frozen hard-bank
    # rule measures 2-4 discordant cell flips from a parallel consumer on the same serve.
    live_burst = dict(live_today, gpu_util_pct=0.0, gpu_power_w=108.35)
    rc, out = run(live_burst)
    ck(rc == 0 and "carries no gpu_util_mean_pct" in out,
       f"the 2026-11-14 13:54 live bytes (gpu_util_pct=0 at 108.35 W) have no window and must stay "
       f"not covered, got exit {rc}: {out}")
    rc, out = run(dict(live_burst, gpu_util_mean_pct=99.4, gpu_util_peak_pct=100))
    ck(rc == 3 and "the shared brain was busy in the sample window" in out,
       f"a window mean of 99.4 % (2026-11-13 15:50 stored shape) must NO-GO, got exit {rc}: {out}")
    rc, out = run(dict(live_burst, gpu_util_mean_pct=6.6, gpu_util_peak_pct=100))
    ck(rc == 0 and "peak 100 %" in out,
       f"a quiet mean with a saturated burst is launchable and must be REPORTED (the single sample "
       f"used to print 0 here), got exit {rc}: {out}")
    rc, out = run(dict(live_burst, gpu_util_mean_pct=12.0, gpu_util_peak_pct=96))
    ck(rc == 0, f"the ceiling gates the MEAN only, a peak of 96 % in a 12 % mean must GO, got {rc}")
    rc, out = run(dict(live_burst, gpu_util_mean_pct=49.9, gpu_util_peak_pct=60))
    ck(rc == 0, f"a 49.9 % window mean sits under the 50.0 ceiling and must GO, got exit {rc}: {out}")
    rc, out = run(dict(live_burst, gpu_util_mean_pct=50.0, gpu_util_peak_pct=91))
    ck(rc == 3, f"a 50.0 % window mean is at the ceiling and must NO-GO, got exit {rc}: {out}")
    rc, out = run(dict(live_burst, gpu_util_mean_pct=99.4, gpu_util_peak_pct=100, foreign_legs=1))
    ck(rc == 3 and "other leg(s) on this endpoint" in out and "shared brain was busy" in out,
       f"a busy window AND a live leg must both be named, got exit {rc}: {out}")
    for bad, why in (("gpu_util_mean_pct=NaN", "cut sample window"),
                     ("gpu_util_peak_pct=NaN", "cut peak sample"),
                     ("gpu_util_mean_pct=101.5", "impossible percentage"),
                     ("gpu_util_peak_pct=-3", "negative utilization"),
                     ("gpu_util_mean_pct=n/a", "non-numeric"),
                     ("gpu_util_peak_pct=2.0", "peak below the window mean")):
        key, val = bad.split("=", 1)
        other: dict[str, object] = {"gpu_util_mean_pct": 30.0, "gpu_util_peak_pct": 40.0}
        other[key] = val
        rc, out = run(dict(live_burst, **other))
        ck(rc == 1, f"{bad} ({why}) must be an input gap, never a GO, got exit {rc}: {out}")
    for half in ("gpu_util_mean_pct", "gpu_util_peak_pct"):
        rc, out = run(dict(live_burst, **{half: 30.0}))
        ck(rc == 1 and "the window is incomplete" in out,
           f"{half} alone cannot be judged as a window, got exit {rc}: {out}")
    rc, out = run(dict(live_burst, gpu_util_mean_pct=0.0, gpu_util_peak_pct=0))
    ck(rc == 0 and "mean 0.0 %" in out,
       f"a genuinely idle endpoint must GO and print its window, got exit {rc}: {out}")

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
