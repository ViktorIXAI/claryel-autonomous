# PUB preflight reading census (generated)

Written by `scripts/pub_preflight_census.py`; this file is that tool's output, never a
transcription of a tick note. It moves no benchmark byte and registers no contour feature.
Readings are stored outside this repository (the producer command is untracked, like every
connection seam on this line), so this census runs on the workstation only and is not
CI-enrolled; its arithmetic is pinned by `harness/pub_preflight_census_test.py` over
synthetic readings, and `--check` re-derives this table from the retained readings.

Census stamp: `pub-preflight-census-v6`, gate sha16 `dd2f0e4fa0255fa5`, window `as-of 2026-11-16 01:00` (157 readings inside the window). v6 adds three COMPUTED continuity rows over the sliding 24 h window — the trailing consecutive-refusal run ending at the newest reading, readings/hours since the last gate-GO with that GO named and aged, and a window-run-vs-day-run state word — because the v5 DAY table resets at midnight: at the first reading of 2026-11-16 (00:04) the day cells printed a run of 1 and `n/a — no GO of this day` while the box had refused FOUR readings in a row across midnight and its last GO was 162 minutes back, one of the 7 launchable windows this same table counts in the last 24 h. The day cells were correct as labelled and useless as a streak, which is tick 192's class (a figure that lives only in prose stops being recomputed) one level down. v5 adds the DAY rule-band table (8 computed cells: the GO and swap-refusal ratio bands, the refusal median, refusals decided by a rule other than swap, the GO-to-refusal dead zone with its EMPTY/POPULATED state word and the count inside it, the longest consecutive-refusal run, readings since the last GO, and the age of the launchable-footprint maximum with the trailing windows above it) — those figures had lived only in tick prose and had been re-typed from a stale cut: on 2026-11-15 the refusal median is 4.225x at 24 readings, 3.985x at 30 and 3.745x at 31, while two consecutive ticks quoted 4.22x as today's number. v4 adds two COMPUTED footprint ceiling rows — the ceiling dry-run and its state word — because at the 08:57 reading on 2026-11-15 the launchable footprint maximum (8 520 MiB) grew ABOVE the refused-group maximum (6 957 MiB), so the only footprint ceiling the arming rule allows fires on nothing in the corpus; that consequence was hand-derived in a tick note and now belongs to the tool (tick 172's class of defect). v3 removes the CORPUS-WIDE reading count from that window-identity sentence: the number counted every `preflight-*.txt` file present at run time, so taking one reading after the frozen window made `--check` of an untouched snapshot report drift (measured 2026-11-15 01:00 at the committed window `as-of 2026-11-14 23:47`: `123 stored readings` became `124 stored readings`, while the window count, every verdict and every band cell stayed identical). The corpus count is now printed on stdout only, outside the committed file. v2 added two COMPUTED group-state rows — the swap-peak band state and the footprint group separation — because v1 printed "Band: nothing between X and Y" unconditionally, and at 23:13 on 2026-11-14 the order of X and Y reversed: the table went on asserting an empty interval the data had withdrawn. v1, v2, v3, v4, v5 and v6 tables are left as published; a v1, v2, v3, v4, v5 and v6 file are not the same table shape.

Ceilings read out of the gate source at run time, so this table cannot disagree with the rule it reports: `SWAP_RATE_MAX_MIB_S = 20.0` (window MEAN; the peak statistic is reported, not gated), `GPU_UTIL_MAX_MEAN_PCT = 50.0` (the window mean, never the peak), and the device-read ceiling is SCOPE-DEPENDENT: `BLK_READ_MAX_MIB_S_WHOLE = 50.0` applies to every reading carrying `blk_scope=whole-disk`, while `BLK_READ_MAX_MIB_S = 100.0` applies only to readings with NO scope key (the old diskstats sum, which double-counts partitions, i.e. about 2x the device). The two numbers are the SAME physical point; a file with an unrecognised scope value is an input gap the gate never judges. Naming one of these numbers without its scope is exactly how a generated table starts disagreeing with the rule it claims to report (measured 2026-11-14 18:47: a whole-disk reading of 56.2 MiB/s was refused by the gate while the first version of this table printed 100.0 as the whole-disk ceiling).

| census cell | value |
|---|---|
| gate verdict GO | 76 |
| gate verdict NO-GO | 75 |
| gate verdict input gap | 6 |
| device scope of the readings in this window | 58 whole-disk (`50.0` ceiling) / 99 unscoped (`100.0` ceiling) / 0 unknown scope |
| readings of the as-of day | 3 (1 GO / 2 NO-GO / 0 gap) |
| launchable (GO) windows in the last 24 h | 8 |
| leg completions recorded in that window | 0 |
| readings carrying the swap-peak key | 62 (NaN 2, parseable 60) |
| ...of those, gate-JUDGED readings with a parseable peak (the band's set) | 58 (the other 2 sit in readings the gate refuses to judge at all) |
| swap-mean-passing windows with a peak | 24 |
| swap-mean-failing windows with a peak | 34 |
| highest peak inside a swap-mean-PASSING window | 111.4 MiB/s |
| lowest peak inside a swap-mean-FAILING window | 95.4 MiB/s |
| swap-peak band state (computed, never asserted) | CROSSED — the highest launchable peak 111.4 MiB/s already sits AT OR ABOVE the lowest mean-failing peak 95.4 MiB/s, so the groups overlap: a ceiling high enough to spare every launchable window lets a mean-failing window through, and a lower ceiling refuses a window the mean rule launches. On this corpus a peak rule adds no refusal the mean rule does not already make |
| arming counter (launchable windows carrying the peak) | 19 of 30 |

Engine swap FOOTPRINT (added 2026-11-14, tick 159) — reported, never banded:

| footprint cell | value |
|---|---|
| readings carrying `engine_vmswap_mib` | 39 (NaN 0, parseable 39) |
| footprint on gate-GO windows (launchable) | 10 (median 6725 MiB, max 9499 MiB) |
| footprint on gate-NO-GO windows | 29 (median 6528 MiB, min 3357 MiB) |
| footprint group separation (computed, never asserted) | OVERLAPPING (launchable 10 window(s) 3576-9499 MiB, refused 29 window(s) 3357-10279 MiB; n=10/29 cannot support a ceiling in either direction) |
| footprint ceiling dry-run (computed; it arms NOTHING) | ceiling > 9499 MiB fires on 0 of 10 launchable and 3 of 29 refused stored windows. A ceiling above every launchable footprint also refuses at least one refused window, so on this corpus the state rule would have real work to do |
| footprint ceiling state (computed) | FIRING-AT-MINIMUM-CEILING |
| page-cache share of swap in use (`swap_cached_mib` / used) | 39 readings, median 49.9 percent, max 65.2 percent |
| footprint arming counter (launchable windows carrying it) | 10 of 30 |

The as-of **DAY** rule band (added 2026-11-15, tick 192) — today's verdicts only, every
ratio taken against `SWAP_RATE_MAX_MIB_S = 20.0` and every number recomputed at this
reading, because the same three figures quoted in tick prose had been carried forward
from an earlier cut instead of re-derived (the median reads 4.225x at 24 readings,
3.985x at 30 and 3.745x at 31 on this day's files):

| day cell | value |
|---|---|
| day launchable (GO) swap draws | 1 (band 0.00-0.00 x the 20.0 mean ceiling) |
| day refusals at or above the swap-mean ceiling | 2 (band 2.17-5.63 x, **median 3.900 x recomputed at this cut**) |
| day refusals decided by a rule OTHER than swap (window below ceiling) | 0 (none) |
| day dead zone, highest GO draw to lowest swap-rule refusal | 0.00-2.17 x — EMPTY (0 windows inside) |
| longest consecutive NO-GO run inside the day | 1 readings (any-verdict non-GO run: 1) |
| readings since the day's last gate-GO | 1 (last GO 00:19) |
| launchable footprint maximum of the day and its age | 9499 MiB set at 00:19, 1 reading(s) ago |
| trailing consecutive day windows with footprint above that maximum | 0 |

The `rule OTHER than swap` row is the day's honest split of the refusal column: a
refusal whose swap window is quiet was decided by the device or the GPU-mean rule and
must not enter the swap-rule band (the 19:24 reading on 2026-11-15 is that case at
0.00x swap traffic with 179.3 MiB/s of whole-disk reads). The launchable-footprint age
row is the same warning for the state variable: the ceiling the dry-run uses was set by
one launchable window, and every reading since then may sit far above it without that
ceiling meaning anything about the box right now.

Verdict continuity across the sliding window (added 2026-11-16, tick 193) — the day
table above is scoped to the calendar day and resets at midnight, which is correct as
labelled and misleading as a streak. At the first reading of 2026-11-16 (00:04, gate
NO-GO) the day cells printed a longest run of 1 reading and `n/a — no GO of this day`,
while the box had refused four readings in a row across midnight (21:57, 22:32, 23:08
on 15 Nov and 00:04 on 16 Nov) and its last GO sat 162 minutes earlier at 21:22, one of
the 7 launchable windows this same table counts in the last 24 h. A tick that reads only
the day cells would report a fresh day with one refusal, so the streak is computed here
too, from the same per-file gate returncodes, and the scope divergence gets a state word:

| window cell (last 24 h) | value |
|---|---|
| trailing consecutive NO-GO run ending at the newest reading (last 24 h, crosses the day boundary) | 1 readings (any-verdict non-GO run: 1) |
| readings since the last gate-GO (last 24 h, any day) | 1 (last GO preflight-20261116-0019.txt at 2026-11-16 00:19, 41 min before as-of) |
| window run vs day run (computed, never asserted) | MATCHED (the current refusal run starts inside the as-of day) |

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
443.8 MiB/s swap window at 0.1 MiB/s of device reads). The footprint series that joined
the census the same evening shows that state walking on its own: one engine process
(pid unchanged since 16:31) held 3 576 -> 6 291 -> 3 965 MiB of `VmSwap` at 22:39 / 23:13
/ 23:47 — +2 715 MiB between two gate-`GO` readings whose sampled 6 s windows took 0.0 and
18.1 MiB/s in, then -2 326 MiB into a window that sampled 92.7 MiB/s in and 0.0 out while
swap in use fell 12 573 -> 10 967 MiB, i.e. the pages coming back home. A state variable
that moves 2.7 GiB in 34 minutes with no leg running is exactly why the footprint is
censused and NOT banded. No ceiling is proposed here:
arming this statistic needs the same pre-registered threshold as the peak, and the
footprint column starts filling with the first reading that carries the key, so this
table's zeros are a coverage fact about stored history, not a measurement of health.

**The two denominators, side by side, because they are not the same set.** The band above
is defined on the **swap-mean rule**, not on the verdict column: the highest peak in a
gate-`GO` window is 111.4 MiB/s and the lowest peak in a gate-`NO-GO` window is 0.0 MiB/s, and
the second number is the trap - a reading can be NO-GO on the device or the GPU-mean rule
while its swap window is quiet at 0.0, and a NaN-carrying reading is an INPUT GAP the gate
never judges at all (2 such readings carry the peak key).
**The band has CROSSED**: the highest launchable peak (111.4 MiB/s) now sits at or above
the lowest mean-failing peak (95.4 MiB/s), so the two groups overlap. A threshold high
enough to spare every launchable window leaves at least one mean-failing window
unrefused, and any lower threshold refuses a window the mean rule launches — on this
corpus a peak rule adds no refusal the mean rule does not already make. The arming
counter (19 of 30 launchable windows carrying the statistic) counts COVERAGE, not
support for a ceiling, and reaching 30 would not change that conclusion.

