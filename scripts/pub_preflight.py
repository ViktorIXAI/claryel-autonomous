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
    swap_used_mib=8188 engine_state=Dl engine_pcpu=602 engine_rss_mib=57409
    gpu_util_pct=0 gpu_power_w=35.8 load1=13.38 health_code=200 foreign_legs=0

An OPTIONAL `swap_used_mib` lets the gate check the producer's arithmetic: the Swap row of
`free -m` is `total used free`, so the free column is the FOURTH token. Measured 2026-11-12 the
untracked reader fed the third token (used) as swap_free_mib: on a box with swap completely spent
(total 8191, used 8159-8191, free 0-32 MiB) it emitted swap_free_mib≈8184 and the swap rule would
have GO'd into the exact condition this gate exists to refuse. When the key is present the gate
requires used + free ≈ total (within SWAP_BALANCE_TOL_MIB, absorbing free(1)'s per-column rounding)
and answers INPUT GAP, never GO, on a mismatch — a column mix-up is a broken reading, not a box
state, and every stored reading of that lineage has an untrusted swap column.

Two file shapes are accepted, because both are produced in practice: one `key=value` per line (every
contract-test fixture) and the single space-separated line the remote read prints (the shape above).
A value padded by its producer is still one reading — `ps -o pcpu=` emits `engine_pcpu= 459`, and a
2026-11-12 live read hit exactly that, with the gate answering `unreadable number(s): engine_pcpu,
gpu_power_w`. That fails CLOSED (never a false GO), but it meant the documented shape could not be
fed at all, so the parser now takes `= <value>` as well as `=<value>`. A key with an EMPTY value on
its own line is still an input gap: the value never jumps to the next line.

`engine_pcpu` must be an INSTANTANEOUS sample, not a lifetime average. Measured 2026-11-12: an engine
up 3.57 days answered `ps -o pcpu=` = 459 % while a 6-second delta of `/proc/<pid>/stat` utime+stime
gave 1.0 % — `ps` averages over the whole process life, so the idle-spin branch fires as a FALSE NO-GO
on any long-lived engine that once did real work. The honest reading is two `/proc/<pid>/stat` reads
N seconds apart: pcpu = 100 * (d(utime+stime) / CLK_TCK) / N. The thresholds themselves are unchanged;
this is the semantics of the number the gate must be fed (that day the NO-GO stood on swap free 0 MiB
with `so=100` pages/s swapped out, which is an instantaneous reading).

Two OPTIONAL readings close a class the `health_code == 200` rule cannot see — measured 2026-11-13,
this gate answered GO twice (09:03, 09:28) while the endpoint had NO engine child at all:

    health_loaded=true|false      the `"loaded"` field of the same /health body
    engine_serve_procs=N          how many `basalt --serve` engine processes exist

An operator config-ladder campaign on that box (`p2005_v4..v8_ab.sh`, one restart per arm) stopped the
engine child at ~09:21 while the `serve.server` LIFECYCLE wrapper stayed up, so `/health` kept
answering HTTP 200 with `"loaded": false, "loading": false` — a 200 that proves an HTTP listener, not
a serving model. The same event broke the reader's own process pick: selecting the largest-RSS
`bin/basalt` match landed on the launcher (whose argv carries `--engine-bin .../bin/basalt`), so
`engine_rss_mib=516` with state `S` and pcpu `0.0` — every per-process rule read a healthy-looking
number off the wrong process. A leg launched on that GO would have burned its whole call budget
against a dead engine (the harness's known `tok=0` / instant-row signature).

Semantics kept deliberately narrow: when either optional key is PRESENT it is binding (a false
`health_loaded` or `engine_serve_procs=0` is NO-GO); when it is ABSENT the verdict is unchanged and the
report prints a coverage line, because the 51 readings stored before this change cannot be re-judged
by a rule they were never fed. A non-boolean `health_loaded` is an input gap, never a guess.

Two more OPTIONAL readings carry the standing swap read of ticks 139-142, which no stored rule could
see (tooling release 2026-11-14, no contour stamp, no published benchmark byte):

    swap_in_mib_per_s=<float>   d(pswpin)  over the producer's sample window, MiB/s
    swap_out_mib_per_s=<float>  d(pswpout) over the same window, MiB/s

The `swap_free_mib` rule sees a swap device that is ALREADY spent; it cannot see a device with 50 GiB
free that is moving gigabytes through it right now, which is the condition the machine note blames for
mid-leg engine restarts. And `load1` cannot proxy this traffic at all: measured 2026-11-13/14 the box
answered load1 9.8 -> 14.6 -> 11.0 -> 14.0 across three minutes while three counter windows stayed at
~0.2 MiB/s in / 0 out, and the next tick answered load1 12.6-13.5 with `vmstat 1 8` showing r=0 and
b=0 in EVERY sample, idle 99-100 %, PSI cpu 0.00 and no D-state process. The counter delta decides;
load1 is reported for the audit trail and never gates.

Values must be LIVE counter deltas, never vmstat's first line: that row is a SINCE-BOOT AVERAGE
(measured 2026-11-14: 2239/2425 KiB/s on a box whose live window was 0.0/0.0, and 2239 KiB/s x 20.2 h
= 155.6 GiB = exactly the pswpin counter, so the boot row is arithmetic, not a sample). Ticks 138-139
of this line published a swap claim off that row and retracted it the same day.

Same optional-but-binding semantics: present and above `SWAP_RATE_MAX_MIB_S` (sum of both directions)
is NO-GO, absent is not covered, a non-number or a negative rate is an input gap, never a guess.

One more OPTIONAL reading closes the class the swap window could only see half of — measured
2026-11-14 10:54-11:02 on this line's endpoint box:

    blk_read_mib_per_s=<float>    d(sectors read) over the whole non-removable device set, over
                                  the producer's own sample window, MiB/s
    blk_top_reader=<comm>         OPTIONAL attribution: process name of the largest block reader
                                  in that window (never a path, never a pid; informational only)

The swap-rate rule caught this box moving 17.4 MiB/s through swap — the highest value this line has
recorded, 87 % of its own ceiling — and still answered GO. The reason the box was moving pages is
visible only in the device counters: a foreign fleet push (`rsync -a .../models/IQ3_S/ -> <LAN_IP>`,
launched by the ops line at 10:54) was reading the model device at **1856.8 MiB/s** (`/proc/diskstats`
delta over 8 s, nvme0n1 1856.8 read / 0.2 write) while pushing it over ssh, `pgscan_kswapd` was at
429 007 pages per 8 s (1.6 GiB of reclaim in 8 s) and the engine was taking **5021 major faults in
8 s (628/s)** against a lifetime average of 142.7/s — the engine's mapped pages were being evicted by
the rsync's page-cache pressure and re-read from a device the rsync already saturated. `/health`
answered 200, `health_loaded=true`, 49.9 GiB of swap free, GPU util 2 %, engine state Sl/Rl. Every
existing rule was green on a box where a leg would pay an I/O queue on every refault. This is also the
first named cause behind the load-1 climbs this line spent four ticks falsifying as a swap proxy
(load1 12.9-15.7 in that window): a foreign reader, not idle reclaim.

Same optional-but-binding semantics: present and at or above `BLK_READ_MAX_MIB_S` is NO-GO, absent is
not covered, a non-number or a negative delta is an input gap. A leg adds no new working set — the
engine is already resident — so the settled endpoint answers 0.2 MiB/s of device reads at idle (two
10 s windows, engine 0.1 MiB/s, 0 major faults/s) and any sustained hundred-MiB/s stream is somebody
else saturating the device the model weights live on.

Two OPTIONAL readings describe the GPU itself (tooling release 2026-11-14, tick 148):

    gpu_util_mean_pct=<float>   GPU utilization sampled at 1 Hz over the producer's own window, mean
    gpu_util_peak_pct=<float>   the worst 1 s sample inside that same window

`gpu_util_pct` is ONE instantaneous nvidia-smi read, and it is burst-blind: at 13:54 the same reading
printed `gpu_util_pct=0` at 108.35 W / 59 C while the serve log's last two lines were completions of
prefills of 93 554 and 96 301 prompt tokens. Worse, the endpoint is the park's SHARED brain and
`foreign_legs` counts only this line's two runners: five stored readings show a saturated GPU
(96-100 %, 114.13-153.62 W) with `foreign_legs=0` — somebody else decoding — and the pre-fix gate
answered GO on two of them (2026-11-11 10:30, 2026-11-13 15:50), the other three being blocked by
unrelated rules. A leg
launched into that window is not comparable to a quiet-leg pair (the hard bank measured 2-4 discordant
cell flips from a parallel consumer on the same serve, with no contour event on them). Same
optional-but-binding semantics: present and at or above `GPU_UTIL_MAX_MEAN_PCT` (the MEAN only, the
peak is reported) is NO-GO, absent is not covered so all 106 stored readings keep their verdicts, and
a non-number, a negative, a value above 100 %, only one of the two keys, or a peak below the window
mean is an input gap.

Usage:
    python3 scripts/pub_preflight.py READINGS.TXT

Exit 0 = GO: the endpoint can take a local leg.
Exit 3 = NO-GO: the readings show a condition this line refuses to launch into.
Exit 1 = bad or missing input (a missing reading is never treated as healthy).
"""
from __future__ import annotations

import math
import re
import sys

# Thresholds carry the measurement that set them. They are deliberately conservative: a false NO-GO
# costs one idle tick, a false GO costs a discarded partial leg.
SWAP_FREE_MIN_MIB = 256     # legs ran while the swap device was nearly free; the refused window
                            # measured 48 MiB free (tick 21) then 3.6 MiB free (tick 23)
SWAP_BALANCE_TOL_MIB = 64   # used + free must re-sum to total within this: free(1) rounds each
                            # column independently (measured 2026-11-12: 8159 + 32 = 8191 exactly),
                            # so a bigger gap means the producer moved columns, not that RAM moved
MEM_AVAILABLE_MIN_MIB = 2048  # the resident engine plus its cache needs headroom to re-admit KV
IDLE_SPIN_PCPU = 200        # idle-spin signature: engine >200 % CPU with GPU util 0 %; measured
                            # 602-629 % CPU at 0 % GPU / 35-37 W. Per-task seconds in that state run
                            # 20-220x the last paired median, so the leg scores but the timing and
                            # energy columns are garbage.
SWAP_RATE_MAX_MIB_S = 20.0  # live swap throughput ceiling, pre-registered ABOVE every launchable
                            # window this line recorded: 0.0/0.0 (2026-11-14, r=0 b=0 at eight
                            # vmstat samples), ~0.2 MiB/s in + 0 out (2026-11-14 tick 142), and
                            # si 5.3 + so 6.6 = 11.9 MiB/s (2026-11-14 tick 140, recorded GO at
                            # idle). The one recorded window an order of magnitude higher
                            # (si 77.9 MiB/s over 9.24 s, 2026-11-13 tick 139) coincided with the
                            # engine flickering Sl<->D and that day was already a NO-GO on state.
                            # A leg adds no new working set here — the engine is already resident —
                            # so a box thrashing with NOTHING asking for RAM is the predictor of the
                            # mid-leg restart the machine note warns about.
OPTIONAL_FLOATS = ("swap_in_mib_per_s", "swap_out_mib_per_s")
# Peak swap throughput INSIDE the sample window: validated and reported, deliberately NOT a refusal
# reason in this release. Measured 2026-11-14 12:12 with a matched instrument on the endpoint box:
# an 8 s window took pswpin +70 876 pages = 276.9 MiB = **34.6 MiB/s in / 0.0 out** (1.73x the
# window-mean ceiling above) while the two producer readings bracketing it (12:05, 12:07) reported
# 8.2 and 0.0 MiB/s — the burst lives between samples, so a once-per-tick mean cannot see it. The
# same window read nvme0n1 +568 568 sectors = 277.6 MiB = 34.7 MiB/s: the swap counter and the
# device counter agree to 99.7 %, i.e. they name ONE physical event (a refault burst off the NVMe
# swapfiles; zswap is disabled on that box, `SwapCached` grew by the same 277 MiB), which is why the
# 100.0 MiB/s device ceiling MISSES it while a swap-rate sample inside it would catch it.
# No ceiling is registered for this statistic yet: a peak is a different quantity from a window mean
# and SWAP_RATE_MAX_MIB_S = 20.0 was pre-registered against MEAN windows. This endpoint runs
# permanently over-committed (engine RSS 57.3 GiB of 61.9 GiB, 15.5 GiB already in swap) and refault
# bursts are its steady state — legs this line published ran inside exactly that state — so a peak
# ceiling of 20.0 would retroactively refuse published legs. The band comes first, the ceiling after.
# Absent key = no line printed, so the 95 stored readings keep byte-identical output.
SWAP_PEAK_KEY = "swap_total_peak_mib_per_s"
# Device-read SCOPE (2026-11-14, tick 146). The first producer summed every non-loop line in
# /proc/diskstats, which counts each partition again on top of its parent disk (the disk line already
# aggregates them). Proven live in one 8 s window: nvme0n1 35.8 MiB/s against p2 10.3 + p3 25.5 =
# 35.8, so the old sum printed 71.6 = exactly 2x the device. Readings without a scope key are therefore
# on the INFLATED scale and keep the 100.0 ceiling they were judged with — no stored file is
# re-judged. `blk_scope=whole-disk` marks the corrected scale, whose ceiling is the SAME physical
# point (100.0 / 2 = 50.0): the two scales verdict-match everywhere, the number is just now truthful.
# An unrecognised scope value is an input gap, never a guess.
BLK_SCOPE_KEY = "blk_scope"
BLK_SCOPE_WHOLE = "whole-disk"
BLK_READ_MAX_MIB_S_WHOLE = 50.0
BLK_READ_MAX_MIB_S = 100.0   # device-read ceiling, pre-registered INSIDE a measured 1000x gap.
                             # Idle endpoint (2026-11-14 11:12, push finished): the whole non-removable
                             # device set answers **0.2 MiB/s** across two 10 s windows, the engine
                             # itself 0.1 MiB/s with **0 major faults/s**, pswpin/pswpout 0.00 MiB/s and
                             # `vmstat 2 4` showing si=so=0, bi≈100 blocks/s, idle 100 %. Interference
                             # on the same box one hour earlier (a fleet model push to <LAN_IP>):
                             # 224.4 MiB/s in the network-limited tail phase and 1856.8 MiB/s in the
                             # burst phase, where the engine took 5021 major faults in 8 s (628/s) and
                             # kswapd stole 420 769 pages in the same 8 s. 100 sits 500x above the idle
                             # device rate and 2.2x below the mildest interference window. The reader
                             # attribution is diagnostic only: the gate refuses on DEVICE reads,
                             # whoever is doing them, because an engine refaulting at 100 MiB/s at idle
                             # is exactly as sick as an external reader streaming the device — and a
                             # model still loading is a state a leg must not start into either.
BLK_KEY = "blk_read_mib_per_s"
BLK_READER_KEY = "blk_top_reader"
# GPU contention window (2026-11-14, tick 148, tooling release: no contour stamp, no benchmark byte).
# The endpoint is the park's SHARED brain, and this gate could not see anyone using it. Census over
# the 106 stored readings: 105 carry `gpu_util_pct` (one, 2026-11-11 11:44, carries it EMPTY and is an
# input gap by rule), and of the 104 numeric ones 94 read exactly 0.0, 3 read 0-20 % and only 7 read
# >= 20 %. FIVE of those seven read 96-100 % at 114.13-153.62 W with `foreign_legs=0` in the same file:
# 2026-11-11 10:30 (99 %, 126.50 W), 2026-11-13 13:00 (99 %, 116.58 W), 2026-11-13 15:50 (96 %,
# 139.19 W), 2026-11-14 12:23 (99 %, 153.62 W) and 2026-11-14 12:26 (100 %, 114.13 W).
# `foreign_legs` is 0 in EVERY stored reading and counts only THIS line's runners (`pub_bench_run.py` +
# `gate_run.py`), so a busy brain with no runner of this line is another tenant decoding. Re-running the
# pre-fix gate over exactly those five files names the size of the hole honestly: 2026-11-11 10:30 and
# 2026-11-13 15:50 were answered GO (the GPU never entered the decision), 2026-11-13 13:00 NO-GOed on
# engine state D and the two 2026-11-14 readings were input gaps (engine_pcpu NaN, fail-closed by the
# tick-146 NaN rule) — so the gate blocked three of five by accident, never by seeing the contention.
# That costs measurement, not safety: the paired-delta rule of the hard bank says a parallel arm on the
# same serve changes batching/queue state and flips 2-4 discordant cells with no contour event on them.
# Why a WINDOW and not the existing single sample: `gpu_util_pct` is one instantaneous nvidia-smi
# read and it is burst-blind. Live probe 2026-11-14 13:54 read `gpu_util_pct=0` at 108.35 W / 59 C
# (a direct nvidia-smi read, not a stored reading) while the serve log's adjacent lines are
# `pp=93554/92483c 1.3s 832t/s` and `pp=96301/94341c 1.7s 1145t/s` — re-verified by grep at 14:12.
# The pairing was re-measured at 14:1x: five consecutive 1 Hz reads gave utilization 0 % with power
# falling 96.49 -> 40.66 -> 34.43 -> 31.05 -> 27.51 W, i.e. utilization is 0 between requests while
# the power tail names the burst that just happened. The log itself sizes the traffic this line never
# sees: 59 876 completed requests in the current serve log, 2 793 of them with prompts over 150 000
# tokens, the largest `pp=260052/0c 78.3s 3322t/s ... end=length` — none of it produced by this line
# (`pgrep` for gate_run/pub_bench_run on the endpoint box: empty). A 1 Hz sample over the producer's
# own 6 s window sees the excursions; the single sample did not.
# 50.0 is pre-registered INSIDE the measured gap: every idle-class reading is <= 19 % (94 of the 104
# numeric readings are exactly 0.0) and the mildest saturated reading is 96 %, so the ceiling sits
# 31 pp above the idle class and 46 pp below the busy class. The two partial single-sample catches
# (29 % at 39.4 W, 47 % at 27.2 W) fall BELOW the ceiling on purpose: un-windowed single samples
# cannot be told from the tail of a leg that just finished, and a false GO here is recoverable while
# a false NO-GO is paid by every tick.
# Absent key = not covered, so all 106 stored readings keep byte-identical output and verdicts.
GPU_UTIL_MEAN_KEY = "gpu_util_mean_pct"
GPU_UTIL_PEAK_KEY = "gpu_util_peak_pct"
GPU_UTIL_MAX_MEAN_PCT = 50.0
GPU_UTIL_MAX_PCT = 100.0
REQUIRED = (
    "mem_total_mib", "mem_available_mib", "swap_total_mib", "swap_free_mib",
    "engine_state", "engine_pcpu", "engine_rss_mib", "gpu_util_pct", "gpu_power_w",
    "load1", "health_code", "foreign_legs",
)
FLOATS = ("engine_pcpu", "gpu_util_pct", "gpu_power_w", "load1")
BOOL_TRUE = ("true", "1", "yes")
BOOL_FALSE = ("false", "0", "no")


KEY_VALUE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=\s*(\S+)")


def read(path: str) -> dict:
    """Parse every `key=value` token per line, so both the fixture form (one pair per
    line) and the one-line remote reading parse identically. `=\\s*(\\S+)` also accepts a
    padded value (`ps -o pcpu=` emits `engine_pcpu= 459`); the whitespace never reaches the
    next line, so a key with an empty value stays an input gap and fails closed."""
    vals: dict[str, str] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            for m in KEY_VALUE.finditer(line):
                vals[m.group(1)] = m.group(2)
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
            v = num(vals, k)
        except ValueError:
            bad.append(k)
            continue
        if not math.isfinite(v):
            # The producer prints NaN on purpose when its sample window was cut (a pid that died
            # mid-sample). Python's float() accepts "NaN", "nan" and "inf", so a bare ValueError
            # check let those reach the comparison stage, where every threshold answer is False —
            # a NaN reading used to be a SILENT GO. Found 2026-11-14 while wiring the device-read
            # window; the same trap sits in `load1` and `engine_pcpu`.
            bad.append(k)
    for k in ("mem_total_mib", "mem_available_mib", "swap_total_mib", "swap_free_mib",
              "engine_rss_mib", "health_code", "foreign_legs"):
        try:
            int(vals[k])
        except ValueError:
            bad.append(k)
    if bad:
        print("PREFLIGHT INPUT GAP: unreadable number(s): " + ", ".join(bad)
              + " — a number that is not finite (NaN/inf) is a cut sample, never healthy.")
        return 1

    if "swap_used_mib" in vals:
        try:
            used = int(vals["swap_used_mib"])
        except ValueError:
            print("PREFLIGHT INPUT GAP: unreadable number(s): swap_used_mib")
            return 1
        free, total = int(vals["swap_free_mib"]), int(vals["swap_total_mib"])
        if abs(total - used - free) > SWAP_BALANCE_TOL_MIB:
            print(f"PREFLIGHT INPUT GAP: the swap columns do not add up: used {used} + free {free}"
                  f" != total {total} (tolerance {SWAP_BALANCE_TOL_MIB} MiB) — this is the producer"
                  " column mix-up class (`free -m` Swap row is total used free; the free column is"
                  " the fourth token); a broken reading is never healthy.")
            return 1

    reasons: list[str] = []

    # Optional loaded flag (2026-11-13): HTTP 200 is not a serving model. Measured twice that
    # morning (09:03, 09:28) a config-ladder restart left the serve.server WRAPPER up with
    # "loaded": false and NO engine child, and a gate that only reads health_code answered GO.
    # Absent = NOT COVERED (the pre-fix readings cannot be re-judged by a rule they were never
    # fed); present = binding; unparseable = input gap, never a guess.
    loaded_flag = None
    if "health_loaded" in vals:
        flag = vals["health_loaded"].strip().lower()
        if flag in BOOL_TRUE:
            loaded_flag = True
        elif flag in BOOL_FALSE:
            loaded_flag = False
        else:
            print(f"PREFLIGHT INPUT GAP: health_loaded={vals['health_loaded']!r} is not a boolean "
                  "(true/false) — the loaded flag is never guessed.")
            return 1
    serve_procs = None
    if "engine_serve_procs" in vals:
        try:
            serve_procs = int(vals["engine_serve_procs"])
        except ValueError:
            print("PREFLIGHT INPUT GAP: unreadable number(s): engine_serve_procs")
            return 1

    # Live swap throughput (2026-11-14): two counter deltas over the producer's own sample window.
    # Present = binding; absent = not covered; ONE of the two = a broken producer, because the two
    # counters are read in the same window and a one-sided window proves the window was cut.
    swap_rate: dict[str, float] = {}
    for k in OPTIONAL_FLOATS:
        if k in vals:
            try:
                v = num(vals, k)
            except ValueError:
                print(f"PREFLIGHT INPUT GAP: unreadable number(s): {k}")
                return 1
            if not math.isfinite(v):
                print(f"PREFLIGHT INPUT GAP: unreadable number(s): {k} — the producer emits NaN "
                      "when its counter window was cut, and a NaN fails every threshold "
                      "comparison silently; a cut sample is never healthy.")
                return 1
            if v < 0:
                print(f"PREFLIGHT INPUT GAP: {k}={vals[k]} is negative — a /proc/vmstat counter "
                      "delta cannot run backwards (counters reset only at boot), so the window is "
                      "broken, not the box; a broken reading is never healthy.")
                return 1
            swap_rate[k] = v
    if 0 < len(swap_rate) < len(OPTIONAL_FLOATS):
        print("PREFLIGHT INPUT GAP: only " + ", ".join(sorted(swap_rate))
              + " is present — swap_in_mib_per_s and swap_out_mib_per_s come from ONE counter "
              "window, so a one-sided window is a cut sample, never a healthy reading.")
        return 1

    # Peak swap throughput inside the window (2026-11-14, tick 146): validated and reported, never a
    # refusal reason in this release (see SWAP_PEAK_KEY for why the ceiling is not registered yet).
    # A peak below the window mean is arithmetically impossible for a non-negative sub-series, so it
    # can only mean the two numbers came from different windows — the producer-column bug family this
    # gate already refuses on the swap columns, and it is an input gap here too.
    swap_peak = None
    if SWAP_PEAK_KEY in vals:
        try:
            swap_peak = num(vals, SWAP_PEAK_KEY)
        except ValueError:
            print(f"PREFLIGHT INPUT GAP: unreadable number(s): {SWAP_PEAK_KEY}")
            return 1
        if not math.isfinite(swap_peak):
            print(f"PREFLIGHT INPUT GAP: unreadable number(s): {SWAP_PEAK_KEY} — a NaN peak is a "
                  "cut sub-window (the producer emits NaN), never healthy.")
            return 1
        if swap_peak < 0:
            print(f"PREFLIGHT INPUT GAP: {SWAP_PEAK_KEY}={vals[SWAP_PEAK_KEY]} is negative — a "
                  "throughput peak cannot be below zero, so the sample is broken, not the box.")
            return 1
        if len(swap_rate) == len(OPTIONAL_FLOATS):
            mean_total = sum(swap_rate.values())
            if swap_peak + 1e-9 < mean_total:
                print(f"PREFLIGHT INPUT GAP: {SWAP_PEAK_KEY}={vals[SWAP_PEAK_KEY]} is below the "
                      f"window mean {mean_total:.1f} MiB/s — a peak inside a window can never sit "
                      "below that window's mean, so the two numbers were not sampled from one "
                      "window; this is a producer bug and is never treated as healthy.")
                return 1

    # Foreign block I/O (2026-11-14, tooling release, no contour stamp, no published byte): the
    # device counter is the only reading that names WHY the pages are moving. Measured the same
    # morning, a fleet model push on this endpoint read the device at 1856.8 MiB/s while every other
    # rule was green (swap free 49.9 GiB, health 200 + loaded, GPU 2 %, engine Sl/Rl) and the
    # swap-throughput rule itself passed at 17.4 MiB/s — 87 % of its ceiling.
    blk_rate = None
    if BLK_KEY in vals:
        try:
            blk_rate = num(vals, BLK_KEY)
        except ValueError:
            print(f"PREFLIGHT INPUT GAP: unreadable number(s): {BLK_KEY}")
            return 1
        if not math.isfinite(blk_rate):
            print(f"PREFLIGHT INPUT GAP: unreadable number(s): {BLK_KEY} — a NaN device rate is a "
                  "cut sample (the producer emits NaN), never healthy.")
            return 1
        if blk_rate < 0:
            print(f"PREFLIGHT INPUT GAP: {BLK_KEY}={vals[BLK_KEY]} is negative — a /proc/diskstats "
                  "sector counter cannot run backwards outside a reboot, so the sample window is "
                  "broken, not the box; a broken reading is never healthy.")
            return 1

    # Which SCALE this device number is on (2026-11-14, tick 146): absent = the producer's original
    # diskstats sum, which double-counts partitions (about 2x the device), and such files keep the
    # ceiling they were judged with. `whole-disk` = the corrected scope, judged at half the number,
    # i.e. the same physical point.
    blk_ceiling = BLK_READ_MAX_MIB_S
    blk_scope = vals.get(BLK_SCOPE_KEY)
    if blk_scope is not None:
        blk_scope = blk_scope.strip()
        if blk_scope == BLK_SCOPE_WHOLE:
            blk_ceiling = BLK_READ_MAX_MIB_S_WHOLE
        else:
            print(f"PREFLIGHT INPUT GAP: {BLK_SCOPE_KEY}={vals[BLK_SCOPE_KEY]!r} is not a known "
                  f"device scope ('{BLK_SCOPE_WHOLE}') — the ceiling depends on the scope, so an "
                  "unknown scope is never judged by borrowing one.")
            return 1

    # GPU contention WINDOW (2026-11-14, tick 148): mean and peak utilization sampled at 1 Hz over
    # the producer's own 6 s window. Present = binding; absent = not covered (the 106 stored readings
    # keep their verdicts); NaN / negative / above 100 % = input gap; a peak below the window mean is
    # arithmetically impossible and means the two numbers came from different windows.
    gpu_mean = gpu_peak = None
    for key in (GPU_UTIL_MEAN_KEY, GPU_UTIL_PEAK_KEY):
        if key in vals:
            try:
                v = num(vals, key)
            except ValueError:
                print(f"PREFLIGHT INPUT GAP: unreadable number(s): {key}")
                return 1
            if not math.isfinite(v):
                print(f"PREFLIGHT INPUT GAP: unreadable number(s): {key} — a NaN GPU sample is a "
                      "cut window (the producer emits NaN), never healthy.")
                return 1
            if v < 0 or v > GPU_UTIL_MAX_PCT:
                print(f"PREFLIGHT INPUT GAP: {key}={vals[key]} is outside 0..{GPU_UTIL_MAX_PCT} — "
                      "a GPU utilization percentage cannot leave that range, so the sample or its "
                      "units are broken; a broken reading is never treated as healthy.")
                return 1
            if key == GPU_UTIL_MEAN_KEY:
                gpu_mean = v
            else:
                gpu_peak = v
    if (gpu_mean is None) != (gpu_peak is None):
        present = GPU_UTIL_MEAN_KEY if gpu_mean is not None else GPU_UTIL_PEAK_KEY
        missing = GPU_UTIL_PEAK_KEY if gpu_mean is not None else GPU_UTIL_MEAN_KEY
        print(f"PREFLIGHT INPUT GAP: {present} is present but {missing} is not — the window is "
              "incomplete, and a mean without its peak (or the reverse) cannot be reported as one "
              "window; an incomplete reading is never treated as healthy.")
        return 1
    if gpu_mean is not None and gpu_peak is not None and gpu_peak + 1e-9 < gpu_mean:
        print(f"PREFLIGHT INPUT GAP: {GPU_UTIL_PEAK_KEY}={vals[GPU_UTIL_PEAK_KEY]} is below the "
              f"window mean {gpu_mean:.1f} % — a peak inside a window can never sit below that "
              "window's mean, so the two numbers were not sampled from one window; this is a "
              "producer bug and is never treated as healthy.")
        return 1

    if int(vals["health_code"]) != 200:
        reasons.append(f"/health answered {vals['health_code']}, not 200")
    if loaded_flag is False:
        reasons.append('/health answered 200 but reports "loaded": false — no model is serving '
                       "(the lifecycle wrapper survives an engine-child death and keeps answering)")
    if serve_procs is not None and serve_procs < 1:
        reasons.append("no `basalt --serve` engine process on the box: engine_state/pcpu/rss in this "
                       "reading describe the launcher, not the model")
    if int(vals["swap_free_mib"]) < SWAP_FREE_MIN_MIB:
        reasons.append(
            f"swap free {vals['swap_free_mib']} MiB of {vals['swap_total_mib']} MiB "
            f"(< {SWAP_FREE_MIN_MIB}): the engine can be OOM-restarted mid-leg")
    if len(swap_rate) == len(OPTIONAL_FLOATS):
        total_rate = sum(swap_rate.values())
        if total_rate >= SWAP_RATE_MAX_MIB_S:
            reasons.append(
                f"live swap throughput {vals['swap_in_mib_per_s']} MiB/s in + "
                f"{vals['swap_out_mib_per_s']} MiB/s out = {total_rate:.1f} MiB/s over the sample "
                f"window (>= {SWAP_RATE_MAX_MIB_S}): the box is moving pages while nothing is "
                "asking for RAM — the free-swap column still looks healthy and load1 cannot see "
                "this traffic, but this is the state from which the engine gets restarted mid-leg")
    if int(vals["mem_available_mib"]) < MEM_AVAILABLE_MIN_MIB:
        reasons.append(f"MemAvailable {vals['mem_available_mib']} MiB < {MEM_AVAILABLE_MIN_MIB}")
    if blk_rate is not None and blk_rate >= blk_ceiling:
        who = vals.get(BLK_READER_KEY)
        reasons.append(
            f"block-device reads {blk_rate:.1f} MiB/s over the sample window "
            f"(>= {blk_ceiling}, scope {blk_scope or 'diskstats-sum (partitions double-counted)'})"
            + (f", largest attributed reader: {who}" if who else "")
            + " — a foreign reader is saturating the device the model weights live on, and the "
              "engine pays for it in major faults (measured 2026-11-14: 1856.8 MiB/s of rsync "
              "device reads while the engine took 5021 major faults in 8 s at idle, kswapd stealing "
              "1.6 GiB of pages in the same window). The swap-free column and load1 both stay green "
              "in this state; a leg launched here pays the I/O queue on every refault")
    if "D" in vals["engine_state"]:
        reasons.append(f"engine in uninterruptible I/O (state {vals['engine_state']}): thrashing")
    if num(vals, "engine_pcpu") > IDLE_SPIN_PCPU and num(vals, "gpu_util_pct") == 0:
        reasons.append(
            f"idle-spin signature: engine {vals['engine_pcpu']} % CPU at GPU "
            f"{vals['gpu_util_pct']} % — per-task seconds and energy columns would be junk")
    if gpu_mean is not None and gpu_mean >= GPU_UTIL_MAX_MEAN_PCT:
        peak_txt = (f", peak {gpu_peak:.0f} % inside the same window" if gpu_peak is not None else "")
        reasons.append(
            f"the shared brain was busy in the sample window: GPU utilization "
            f"{gpu_mean:.1f} % mean{peak_txt} over the producer's window "
            f"(>= {GPU_UTIL_MAX_MEAN_PCT}) with {vals['foreign_legs']} leg(s) of this line running "
            "— someone else is decoding on this endpoint. A leg launched here is not comparable to "
            "a quiet-leg pair: batching/queue state changes under a parallel consumer and flips "
            "2-4 discordant cells with no contour event on them (hard-bank paired-delta rule), and "
            "the single instantaneous gpu_util_pct sample cannot see this state at all (live probe "
            "2026-11-14 13:54: gpu_util_pct=0 at 108.35 W while 93 554- and 96 301-token prefills "
            "completed in the serve log)")
    if int(vals["foreign_legs"]) > 0:
        reasons.append(f"{vals['foreign_legs']} other leg(s) on this endpoint: one leg per endpoint")

    print("endpoint readings:")
    for k in REQUIRED:
        print(f"  {k:<18} {vals[k]}")
    for k in (("health_loaded", "engine_serve_procs") + OPTIONAL_FLOATS
              + (BLK_KEY, BLK_READER_KEY, SWAP_PEAK_KEY, BLK_SCOPE_KEY,
                 GPU_UTIL_MEAN_KEY, GPU_UTIL_PEAK_KEY)):
        if k in vals:
            print(f"  {k:<18} {vals[k]}")
    if loaded_flag is None or serve_procs is None:
        print("  (coverage) this reading carries no "
              + "/".join(k for k, v in (("health_loaded", loaded_flag),
                                        ("engine_serve_procs", serve_procs)) if v is None)
              + " — a 200 alone cannot prove a model is loaded; the live producer emits both since "
                "2026-11-13, so this file predates that fix.")
    if len(swap_rate) < len(OPTIONAL_FLOATS):
        print("  (coverage) this reading carries no swap_in_mib_per_s/swap_out_mib_per_s counter "
              "window — the live swap-throughput rule is not covered; the live producer emits both "
              "since 2026-11-14, so this file predates that fix.")
    if blk_rate is None:
        print("  (coverage) this reading carries no blk_read_mib_per_s device window — the foreign "
              "block-I/O rule is not covered; the live producer emits it since 2026-11-14, so this "
              "file predates that fix.")
    if gpu_mean is None:
        print("  (coverage) this reading carries no gpu_util_mean_pct/gpu_util_peak_pct window — the "
              "shared-brain contention rule is not covered, and the single `gpu_util_pct` sample is "
              "burst-blind; the live producer emits the 1 Hz window since 2026-11-14 14:00, so this "
              "file predates that fix.")
    elif gpu_peak is not None:
        print(f"  (diagnostic) GPU utilization over the producer's window: mean {gpu_mean:.1f} %, "
              f"peak {gpu_peak:.0f} %, against one instantaneous nvidia-smi sample of "
              f"{vals['gpu_util_pct']} % at {vals['gpu_power_w']} W — the ceiling "
              f"GPU_UTIL_MAX_MEAN_PCT = {GPU_UTIL_MAX_MEAN_PCT} gates the MEAN only, the peak is "
              "reported because a burst inside a quiet mean is exactly what the single sample used "
              "to miss")
    if swap_peak is not None:
        mean_txt = (f"{sum(swap_rate.values()):.1f} MiB/s"
                    if len(swap_rate) == len(OPTIONAL_FLOATS) else "not present in this reading")
        print(f"  (diagnostic) peak swap throughput inside the window: {swap_peak:.1f} MiB/s against "
              f"a window mean of {mean_txt} — reported, NOT gated in this release: "
              f"SWAP_RATE_MAX_MIB_S = {SWAP_RATE_MAX_MIB_S} is a mean-window ceiling and a peak "
              "statistic needs its own measured band before it may refuse a leg (measured 2026-11-14 "
              "12:12: a 34.6 MiB/s peak in an 8 s matched window while the bracketing producer "
              "samples read 8.2 and 0.0)")
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
