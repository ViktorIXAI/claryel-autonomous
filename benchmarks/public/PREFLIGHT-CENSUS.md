# PUB preflight reading census (generated)

Written by `scripts/pub_preflight_census.py`; this file is that tool's output, never a
transcription of a tick note. It moves no benchmark byte and registers no contour feature.
Readings are stored outside this repository (the producer command is untracked, like every
connection seam on this line), so this census runs on the workstation only and is not
CI-enrolled; its arithmetic is pinned by `harness/pub_preflight_census_test.py` over
synthetic readings, and `--check` re-derives this table from the retained readings.

Census stamp: `pub-preflight-census-v1`, gate sha16 `890ed7db1f912f64`, window `as-of 2026-11-14 21:42` (119 stored readings, 119 inside the window).

Ceilings read out of the gate source at run time, so this table cannot disagree with the rule it reports: `SWAP_RATE_MAX_MIB_S = 20.0` (window MEAN; the peak statistic is reported, not gated), `GPU_UTIL_MAX_MEAN_PCT = 50.0` (the window mean, never the peak), and the device-read ceiling is SCOPE-DEPENDENT: `BLK_READ_MAX_MIB_S_WHOLE = 50.0` applies to every reading carrying `blk_scope=whole-disk`, while `BLK_READ_MAX_MIB_S = 100.0` applies only to readings with NO scope key (the old diskstats sum, which double-counts partitions, i.e. about 2x the device). The two numbers are the SAME physical point; a file with an unrecognised scope value is an input gap the gate never judges. Naming one of these numbers without its scope is exactly how a generated table starts disagreeing with the rule it claims to report (measured 2026-11-14 18:47: a whole-disk reading of 56.2 MiB/s was refused by the gate while the first version of this table printed 100.0 as the whole-disk ceiling).

| census cell | value |
|---|---|
| gate verdict GO | 66 |
| gate verdict NO-GO | 47 |
| gate verdict input gap | 6 |
| device scope of the readings in this window | 20 whole-disk (`50.0` ceiling) / 99 unscoped (`100.0` ceiling) / 0 unknown scope |
| readings of the as-of day | 47 (29 GO / 14 NO-GO / 4 gap) |
| launchable (GO) windows in the last 24 h | 32 |
| leg completions recorded in that window | 0 |
| readings carrying the swap-peak key | 24 (NaN 2, parseable 22) |
| ...of those, gate-JUDGED readings with a parseable peak (the band's set) | 20 (the other 2 sit in readings the gate refuses to judge at all) |
| swap-mean-passing windows with a peak | 12 |
| swap-mean-failing windows with a peak | 8 |
| highest peak inside a swap-mean-PASSING window | 67.6 MiB/s |
| lowest peak inside a swap-mean-FAILING window | 107.0 MiB/s |
| arming counter (launchable windows carrying the peak) | 9 of 30 |

Engine swap FOOTPRINT (added 2026-11-14, tick 159) — reported, never banded:

| footprint cell | value |
|---|---|
| readings carrying `engine_vmswap_mib` | 1 (NaN 0, parseable 1) |
| footprint on gate-GO windows (launchable) | 0 (median n/a MiB, max n/a MiB) |
| footprint on gate-NO-GO windows | 1 (median 3357 MiB, min 3357 MiB) |
| page-cache share of swap in use (`swap_cached_mib` / used) | 1 readings, median 65.2 percent, max 65.2 percent |
| footprint arming counter (launchable windows carrying it) | 0 of 30 |

**Why a state variable joins a table of rates.** Every swap rule the gate has is a rate
over one 6 s window, and a rate is blind in BOTH directions: measured 2026-11-14
21:31-21:38, three back-to-back 5 s windows on the endpoint box took 320 MiB / 0 / 0 of
swap-in, a producer-shaped 6 s window read 134.3 MiB/s in and 0.0 out, a second such
window 3 min later read ONE page in, and across that whole span `pswpout` moved
1 741.9 MiB that not one 6 s window saw — a ceiling on a rate can neither stop the
outward storm (which is what the machine note says restarts the engine mid-leg) nor
detect the refault load that precedes it. The footprint is the state behind those rates:
the engine's own `VmSwap` grew 5 478 008 -> 6 004 096 kB across eight minutes while
`MemAvailable` read 19-21 GiB and `SwapFree` 53.6 GiB, 35 359 of 35 361 major faults in
a 6 s window belonged to the engine pid, and 52.5-57.1 % of the swap in use was ALSO
page-cache resident in RAM, which is why the device rule saw 0.1 MiB/s of reads through
the whole event (tick 151 measured the same complementarity from the other side: a
443.8 MiB/s swap window at 0.1 MiB/s of device reads). No ceiling is proposed here:
arming this statistic needs the same pre-registered threshold as the peak, and the
footprint column starts filling with the first reading that carries the key, so this
table's zeros are a coverage fact about stored history, not a measurement of health.

**The two denominators, side by side, because they are not the same set.** The band above
is defined on the **swap-mean rule**, not on the verdict column: the highest peak in a
gate-`GO` window is 67.6 MiB/s and the lowest peak in a gate-`NO-GO` window is 0.0 MiB/s, and
the second number is the trap - a reading can be NO-GO on the device or the GPU-mean rule
while its swap window is quiet at 0.0, and a NaN-carrying reading is an INPUT GAP the gate
never judges at all (2 such readings carry the peak key). Band: nothing between
67.6 and 107.0 MiB/s, so a peak ceiling anywhere in that interval would refuse windows the mean
rule passes. The peak stays REPORTED, not gated, until the pre-registered arming threshold
(30 launchable windows carrying the statistic) is met.

