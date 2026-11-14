# PUB preflight reading census (generated)

Written by `scripts/pub_preflight_census.py`; this file is that tool's output, never a
transcription of a tick note. It moves no benchmark byte and registers no contour feature.
Readings are stored outside this repository (the producer command is untracked, like every
connection seam on this line), so this census runs on the workstation only and is not
CI-enrolled; its arithmetic is pinned by `harness/pub_preflight_census_test.py` over
synthetic readings, and `--check` re-derives this table from the retained readings.

Census stamp: `pub-preflight-census-v1`, gate sha16 `68705b7b41cb1239`, window `as-of 2026-11-14 18:47` (114 stored readings, 114 inside the window).

Ceilings read out of the gate source at run time, so this table cannot disagree with the rule it reports: `SWAP_RATE_MAX_MIB_S = 20.0` (window MEAN; the peak statistic is reported, not gated), `GPU_UTIL_MAX_MEAN_PCT = 50.0` (the window mean, never the peak), and the device-read ceiling is SCOPE-DEPENDENT: `BLK_READ_MAX_MIB_S_WHOLE = 50.0` applies to every reading carrying `blk_scope=whole-disk`, while `BLK_READ_MAX_MIB_S = 100.0` applies only to readings with NO scope key (the old diskstats sum, which double-counts partitions, i.e. about 2x the device). The two numbers are the SAME physical point; a file with an unrecognised scope value is an input gap the gate never judges. Naming one of these numbers without its scope is exactly how a generated table starts disagreeing with the rule it claims to report (measured 2026-11-14 18:47: a whole-disk reading of 56.2 MiB/s was refused by the gate while the first version of this table printed 100.0 as the whole-disk ceiling).

| census cell | value |
|---|---|
| gate verdict GO | 65 |
| gate verdict NO-GO | 43 |
| gate verdict input gap | 6 |
| device scope of the readings in this window | 15 whole-disk (`50.0` ceiling) / 99 unscoped (`100.0` ceiling) / 0 unknown scope |
| readings of the as-of day | 42 (28 GO / 10 NO-GO / 4 gap) |
| launchable (GO) windows in the last 24 h | 35 |
| leg completions recorded in that window | 0 |
| readings carrying the swap-peak key | 19 (NaN 2, parseable 17) |
| ...of those, gate-JUDGED readings with a parseable peak (the band's set) | 15 (the other 2 sit in readings the gate refuses to judge at all) |
| swap-mean-passing windows with a peak | 11 |
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

