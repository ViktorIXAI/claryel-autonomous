# PUB preflight reading census (generated)

Written by `scripts/pub_preflight_census.py`; this file is that tool's output, never a
transcription of a tick note. It moves no benchmark byte and registers no contour feature.
Readings are stored outside this repository (the producer command is untracked, like every
connection seam on this line), so this census runs on the workstation only and is not
CI-enrolled; its arithmetic is pinned by `harness/pub_preflight_census_test.py` over
synthetic readings, and `--check` re-derives this table from the retained readings.

Census stamp: `pub-preflight-census-v1`, gate sha16 `68705b7b41cb1239`, window `as-of 2026-11-14 17:51` (113 stored readings, 113 inside the window).

Ceilings read out of the gate source at run time, so this table cannot disagree with the
rule it reports: `SWAP_RATE_MAX_MIB_S = 20.0`, `GPU_UTIL_MAX_MEAN_PCT = 50.0`, `BLK_READ_MAX_MIB_S = 100.0` (whole-disk scope; readings without a scope key stay on the old
inflated scale and are judged by the ceiling they were judged with).

| census cell | value |
|---|---|
| gate verdict GO | 65 |
| gate verdict NO-GO | 42 |
| gate verdict input gap | 6 |
| readings of the as-of day | 41 (28 GO / 9 NO-GO / 4 gap) |
| launchable (GO) windows in the last 24 h | 36 |
| leg completions recorded in that window | 0 |
| readings carrying the swap-peak key | 18 (NaN 2, parseable 16) |
| ...of those, gate-JUDGED readings with a parseable peak (the band's set) | 14 (the other 2 sit in readings the gate refuses to judge at all) |
| swap-mean-passing windows with a peak | 10 |
| swap-mean-failing windows with a peak | 4 |
| highest peak inside a swap-mean-PASSING window | 67.6 MiB/s |
| lowest peak inside a swap-mean-FAILING window | 107.0 MiB/s |
| arming counter (launchable windows carrying the peak) | 8 of 30 |

**The two denominators, side by side, because they are not the same set.** The band above
is defined on the **swap-mean rule**, not on the verdict column: the highest peak in a
gate-`GO` window is 67.6 MiB/s and the lowest peak in a gate-`NO-GO` window is 0.0 MiB/s, and
the second number is the trap - a reading can be NO-GO on the device or the GPU-mean rule
while its swap window is quiet at 0.0, and a NaN-carrying reading is an INPUT GAP the gate
never judges at all (2 such readings carry the peak key). Band: nothing between
67.6 and 107.0 MiB/s, so a peak ceiling anywhere in that interval would refuse windows the mean
rule passes. The peak stays REPORTED, not gated, until the pre-registered arming threshold
(30 launchable windows carrying the statistic) is met.

