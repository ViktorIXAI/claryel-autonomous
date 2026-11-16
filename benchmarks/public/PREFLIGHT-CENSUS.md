# PUB preflight reading census (generated)

Written by `scripts/pub_preflight_census.py`; this file is that tool's output, never a
transcription of a tick note. It moves no benchmark byte and registers no contour feature.
Readings are stored outside this repository (the producer command is untracked, like every
connection seam on this line), so this census runs on the workstation only and is not
CI-enrolled; its arithmetic is pinned by `harness/pub_preflight_census_test.py` over
synthetic readings, and `--check` re-derives this table from the retained readings.

Census stamp: `pub-preflight-census-v9`, gate sha16 `dd2f0e4fa0255fa5`, window `as-of 2026-11-16 05:41` (163 readings inside the window). v9 counts WHICH GATE RULE refused each reading, read out of the gate's own refusal text at the three published scopes, and cross-checks the swap-band refusal set (derived here from the key=value columns) against the set whose gate reason line names the swap rule (the gate's own claim): every tick sentence that attributed a refusal to a rule had never been computed. The rule table is BOUND to the gate source — each anchor prefix must appear in it and the refusal-site count must match — an unmappable reason prints UNATTRIBUTED and moves the exit code to 4, and the preserved-shape sentence at the end of this paragraph is now GENERATED from the stamp number, because the hand-typed one claimed only v1-v6 are preserved: two stamps short of the v7 and v8 changes this same sentence describes. v8 splits one row that carried two denominators: the swap rule's OWN decision boundary (highest window the rule accepted, lowest window it refused, judged on the rule's decision whatever the gate verdict was) and the launchable-column gap (highest gate-GO draw to lowest refusal), which is what v5-v7 printed as 'dead zone' and what every tick quoted as the rule's resolution. At the committed 2026-11-16 02:14 cut the corpus gap is 0.905-1.060 x while the rule boundary is 0.940-1.060 x, because `preflight-20261116-0214.txt` carries swap 18.8 MiB/s = 0.94 x of the 20.0 ceiling, which the swap rule ACCEPTED (the reading was refused instead by the device, state-D and GPU-mean rules): the rule is measured accepting at 0.94 x, and the v7 'POPULATED (1 windows inside)' at all three scopes was produced by exactly that accepted draw. A judged draw inside the rule band is impossible by definition — it would itself be an accepted or a refused point and move the bound that excludes it — so the boundary row prints EMPTY BY CONSTRUCTION and names input-gap readings inside the band separately. v7 prints the v5 rule band at THREE scopes (the as-of calendar day, the sliding 24 h window, the whole corpus) with the scope word inside every row label and a computed dead-zone scope state, because a dead zone is a property of the row set it is measured over and only the day scope was ever published: at the 2026-11-16 01:50 cut the day cell put the GO-to-refusal zone 25.3 MiB/s wide while the corpus put it at 3.1 MiB/s (highest launchable draw 0.905x, lowest swap-rule refusal 1.06x, empty over the 25 launchable draws and 35 swap-rule refusals that carry a swap window — only 70 of the 158 stored files carry those keys at all, so the block prints its band denominator), and the 2026-11-15 tick sentences that said "the dead zone" (0.38-1.06x, then 0.74-1.06x) were day-scoped numbers presented as a property of the rule — tick 192 and 193's scope-word defect a third time in the same column. v6 adds three COMPUTED continuity rows over the sliding 24 h window — the trailing consecutive-refusal run ending at the newest reading, readings/hours since the last gate-GO with that GO named and aged, and a window-run-vs-day-run state word — because the v5 DAY table resets at midnight: at the first reading of 2026-11-16 (00:04) the day cells printed a run of 1 and `n/a — no GO of this day` while the box had refused FOUR readings in a row across midnight and its last GO was 162 minutes back, one of the 7 launchable windows this same table counts in the last 24 h. The day cells were correct as labelled and useless as a streak, which is tick 192's class (a figure that lives only in prose stops being recomputed) one level down. v5 adds the DAY rule-band table (8 computed cells: the GO and swap-refusal ratio bands, the refusal median, refusals decided by a rule other than swap, the GO-to-refusal dead zone with its EMPTY/POPULATED state word and the count inside it, the longest consecutive-refusal run, readings since the last GO, and the age of the launchable-footprint maximum with the trailing windows above it) — those figures had lived only in tick prose and had been re-typed from a stale cut: on 2026-11-15 the refusal median is 4.225x at 24 readings, 3.985x at 30 and 3.745x at 31, while two consecutive ticks quoted 4.22x as today's number. v4 adds two COMPUTED footprint ceiling rows — the ceiling dry-run and its state word — because at the 08:57 reading on 2026-11-15 the launchable footprint maximum (8 520 MiB) grew ABOVE the refused-group maximum (6 957 MiB), so the only footprint ceiling the arming rule allows fires on nothing in the corpus; that consequence was hand-derived in a tick note and now belongs to the tool (tick 172's class of defect). v3 removes the CORPUS-WIDE reading count from that window-identity sentence: the number counted every `preflight-*.txt` file present at run time, so taking one reading after the frozen window made `--check` of an untouched snapshot report drift (measured 2026-11-15 01:00 at the committed window `as-of 2026-11-14 23:47`: `123 stored readings` became `124 stored readings`, while the window count, every verdict and every band cell stayed identical). The corpus count is now printed on stdout only, outside the committed file. v2 added two COMPUTED group-state rows — the swap-peak band state and the footprint group separation — because v1 printed "Band: nothing between X and Y" unconditionally, and at 23:13 on 2026-11-14 the order of X and Y reversed: the table went on asserting an empty interval the data had withdrawn. v1, v2, v3, v4, v5, v6, v7 and v8 tables are left published exactly as written; a file stamped any of them is not the same table shape as this v9 one.

Ceilings read out of the gate source at run time, so this table cannot disagree with the rule it reports: `SWAP_RATE_MAX_MIB_S = 20.0` (window MEAN; the peak statistic is reported, not gated), `GPU_UTIL_MAX_MEAN_PCT = 50.0` (the window mean, never the peak), and the device-read ceiling is SCOPE-DEPENDENT: `BLK_READ_MAX_MIB_S_WHOLE = 50.0` applies to every reading carrying `blk_scope=whole-disk`, while `BLK_READ_MAX_MIB_S = 100.0` applies only to readings with NO scope key (the old diskstats sum, which double-counts partitions, i.e. about 2x the device). The two numbers are the SAME physical point; a file with an unrecognised scope value is an input gap the gate never judges. Naming one of these numbers without its scope is exactly how a generated table starts disagreeing with the rule it claims to report (measured 2026-11-14 18:47: a whole-disk reading of 56.2 MiB/s was refused by the gate while the first version of this table printed 100.0 as the whole-disk ceiling).

| census cell | value |
|---|---|
| gate verdict GO | 77 |
| gate verdict NO-GO | 80 |
| gate verdict input gap | 6 |
| device scope of the readings in this window | 64 whole-disk (`50.0` ceiling) / 99 unscoped (`100.0` ceiling) / 0 unknown scope |
| readings of the as-of day | 9 (2 GO / 7 NO-GO / 0 gap) |
| launchable (GO) windows in the last 24 h | 9 |
| leg completions recorded in that window | 0 |
| readings carrying the swap-peak key | 68 (NaN 2, parseable 66) |
| ...of those, gate-JUDGED readings with a parseable peak (the band's set) | 64 (the other 2 sit in readings the gate refuses to judge at all) |
| swap-mean-passing windows with a peak | 26 |
| swap-mean-failing windows with a peak | 38 |
| highest peak inside a swap-mean-PASSING window | 111.4 MiB/s |
| lowest peak inside a swap-mean-FAILING window | 95.4 MiB/s |
| swap-peak band state (computed, never asserted) | CROSSED — the highest launchable peak 111.4 MiB/s already sits AT OR ABOVE the lowest mean-failing peak 95.4 MiB/s, so the groups overlap: a ceiling high enough to spare every launchable window lets a mean-failing window through, and a lower ceiling refuses a window the mean rule launches. On this corpus a peak rule adds no refusal the mean rule does not already make |
| arming counter (launchable windows carrying the peak) | 20 of 30 |

Engine swap FOOTPRINT (added 2026-11-14, tick 159) — reported, never banded:

| footprint cell | value |
|---|---|
| readings carrying `engine_vmswap_mib` | 45 (NaN 0, parseable 45) |
| footprint on gate-GO windows (launchable) | 11 (median 7094 MiB, max 9499 MiB) |
| footprint on gate-NO-GO windows | 34 (median 7006 MiB, min 3357 MiB) |
| footprint group separation (computed, never asserted) | OVERLAPPING (launchable 11 window(s) 3576-9499 MiB, refused 34 window(s) 3357-10729 MiB; n=11/34 cannot support a ceiling in either direction) |
| footprint ceiling dry-run (computed; it arms NOTHING) | ceiling > 9499 MiB fires on 0 of 11 launchable and 5 of 34 refused stored windows. A ceiling above every launchable footprint also refuses at least one refused window, so on this corpus the state rule would have real work to do |
| footprint ceiling state (computed) | FIRING-AT-MINIMUM-CEILING |
| page-cache share of swap in use (`swap_cached_mib` / used) | 45 readings, median 49.2 percent, max 65.2 percent |
| footprint arming counter (launchable windows carrying it) | 11 of 30 |

The as-of **DAY** rule band (added 2026-11-15, tick 192) — today's verdicts only, every
ratio taken against `SWAP_RATE_MAX_MIB_S = 20.0` and every number recomputed at this
reading, because the same three figures quoted in tick prose had been carried forward
from an earlier cut instead of re-derived (the median reads 4.225x at 24 readings,
3.985x at 30 and 3.745x at 31 on this day's files):

| day cell | value |
|---|---|
| day launchable (GO) swap draws | 2 (band 0.00-0.05 x the 20.0 mean ceiling) |
| day refusals at or above the swap-mean ceiling | 6 (band 1.27-6.91 x, **median 3.900 x recomputed at this cut**) |
| day refusals decided by a rule OTHER than swap (window below ceiling) | 1: preflight-20261116-0214.txt at 0.94 x |
| day swap-rule ACCEPTED draws (any verdict — the rule's own denominator) | 3 (band 0.00-0.94 x) |
| day swap-rule decision boundary (accepted max to refusal min) | accepted up to 0.94 x, refused from 1.27 x, unresolved band 0.325 x (6.5 MiB/s) — EMPTY BY CONSTRUCTION (0 judged draws inside); judged draws inside are impossible by the definition above, input-gap readings inside: none |
| day launchable-column gap (GO max to lowest refusal; VERDICT-scoped, not the rule boundary) | 0.05-1.27 x — POPULATED (1 windows inside) |
| longest consecutive NO-GO run inside the day | 5 readings (any-verdict non-GO run: 5) |
| readings since the day's last gate-GO | 1 (last GO 03:49) |
| launchable footprint maximum of the day and its age | 9499 MiB set at 00:19, 7 reading(s) ago |
| trailing consecutive day windows with footprint above that maximum | 0 |

The `rule OTHER than swap` row is the day's honest split of the refusal column: a
refusal whose swap window is quiet was decided by the device or the GPU-mean rule and
must not enter the swap-rule band (the 19:24 reading on 2026-11-15 is that case at
0.00x swap traffic with 179.3 MiB/s of whole-disk reads). The launchable-footprint age
row is the same warning for the state variable: the ceiling the dry-run uses was set by
one launchable window, and every reading since then may sit far above it without that
ceiling meaning anything about the box right now.

The SAME rule band at three scopes (added 2026-11-16, tick 195) — because a dead zone
is a property of the row set it is measured over, and only the calendar-day row set was
ever published. Measured at the 2026-11-16 01:50 cut (dated, not current): the day cell
spanned a dead zone 25.3 MiB/s wide while the corpus put the highest launchable swap
draw at 0.905x of the ceiling and the lowest swap-rule refusal at 1.06x, a 3.1 MiB/s
band, 8.2x narrower. Every tick
sentence that said "the dead zone" (2026-11-15: "0.38-1.06x", then "0.74-1.06x") was
a day-scoped number presented as a property of the rule, so the scope word now travels
with the cell, and the block prints its own band denominator: only a reading that
carries `swap_in + swap_out` can be banded at all (the producer added those keys
2026-11-14 09:26), so a corpus band describes the sampler era since that hour, never
the whole archive. Each ratio is still the reading's own sampled window against the
gate's current ceiling, which is what the swap-mean rule compares:

| rule band at three scopes (added 2026-11-16, tick 195) | value |
|---|---|
| readings this scope can band at all (verdict GO or NO-GO AND a parseable `swap_in + swap_out` window) | DAY `20261116` 9 of 9, last 24 h 33 of 33, whole corpus 71 of 163 |
| launchable (GO) swap draws, DAY `20261116` | 2, band 0.00-0.05 x the 20.0 mean ceiling |
| launchable (GO) swap draws, last 24 h | 9, band 0.00-0.74 x the 20.0 mean ceiling |
| launchable (GO) swap draws, whole corpus | 26, band 0.00-0.91 x the 20.0 mean ceiling |
| swap-rule ACCEPTED draws (any verdict, the rule's own denominator), DAY `20261116` | 3, band 0.00-0.94 x |
| swap-rule ACCEPTED draws (any verdict, the rule's own denominator), last 24 h | 11, band 0.00-0.94 x |
| swap-rule ACCEPTED draws (any verdict, the rule's own denominator), whole corpus | 33, band 0.00-0.94 x |
| swap-rule refusals (window at/above that ceiling), DAY `20261116` | 6, band 1.27-6.91 x, **median 3.900 x recomputed at this cut** |
| swap-rule refusals (window at/above that ceiling), last 24 h | 22, band 1.06-15.61 x, **median 2.845 x recomputed at this cut** |
| swap-rule refusals (window at/above that ceiling), whole corpus | 38, band 1.06-22.19 x, **median 4.205 x recomputed at this cut** |
| refusals decided by a rule OTHER than swap (window below the ceiling) | DAY `20261116` 1, last 24 h 2, whole corpus 7 |
| swap-rule decision boundary, DAY `20261116` | accepted up to 0.94 x, refused from 1.27 x, unresolved band 0.325 x (6.5 MiB/s) — EMPTY BY CONSTRUCTION (0 judged draws inside); judged draws inside are impossible by the definition above, input-gap readings inside: none |
| swap-rule decision boundary, last 24 h | accepted up to 0.94 x, refused from 1.06 x, unresolved band 0.120 x (2.4 MiB/s) — EMPTY BY CONSTRUCTION (0 judged draws inside); judged draws inside are impossible by the definition above, input-gap readings inside: none |
| swap-rule decision boundary, whole corpus | accepted up to 0.94 x, refused from 1.06 x, unresolved band 0.120 x (2.4 MiB/s) — EMPTY BY CONSTRUCTION (0 judged draws inside); judged draws inside are impossible by the definition above, input-gap readings inside: preflight-20261114-1226.txt at 0.94 x |
| rule-boundary scope state (computed, never asserted) | SCOPE-DEPENDENT — the rule's unresolved band is 0.325 x (6.5 MiB/s) wide at DAY `20261116` and 0.120 x (2.4 MiB/s) at last 24 h: quoting the boundary without its scope word misstates the rule's resolution by up to 2.7x. Quote the scope word with any rule boundary. |
| launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule boundary), DAY `20261116` | POPULATED (1 windows inside), bounds 0.05-1.27 x, width 1.215 x (24.3 MiB/s) |
| launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule boundary), last 24 h | POPULATED (1 windows inside), bounds 0.74-1.06 x, width 0.320 x (6.4 MiB/s) |
| launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule boundary), whole corpus | POPULATED (1 windows inside), bounds 0.91-1.06 x, width 0.155 x (3.1 MiB/s) |
| launchable-column gap scope state (computed, never asserted) | SCOPE-DEPENDENT — the DAY `20261116` dead zone is 1.215 x (24.3 MiB/s) wide and the whole corpus one 0.155 x (3.1 MiB/s): a dead zone quoted without its scope word overstates the rule's resolution by up to 7.8x. Quote the scope word with any dead zone. |

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
| readings since the last gate-GO (last 24 h, any day) | 1 (last GO preflight-20261116-0349.txt at 2026-11-16 03:49, 112 min before as-of) |
| window run vs day run (computed, never asserted) | MATCHED (the current refusal run starts inside the as-of day) |

Which gate RULE refused (added 2026-11-16, tick 197) — the verdict column says a reading
was refused and never says BY WHAT. Every tick attributed refusals in prose ("the night's
first out-heavy swap window", "02:14 died on the device, state-D and GPU-mean rules") and
not one of those sentences was ever computed. The counts below come out of the gate's own
refusal lines, from the same subprocess run that produced the verdict column, so a rule that
starts or stops firing moves a cell here instead of hiding in a report. The rule table is
BOUND to the gate source (every anchor must appear in it and the refusal-site count must
match), an unmappable reason names its file and moves the exit code to 4, and the
cross-check row compares two independent derivations of one set: the refusals whose sampled
swap window sits at or above `SWAP_RATE_MAX_MIB_S` (computed here from the key=value
columns) and the refusals whose gate reason line names the swap rule (the gate speaking
about itself). A rule that fired on nothing still gets a row: a missing row and a zero row
read the same way in prose, which is how a rule that never fires gets mistaken for a rule
nobody counted:

| refusal-rule cell (every scope labelled) | value |
|---|---|
| refusals this scope can attribute (gate NO-GO with captured reason lines) | DAY `20261116`: 7 of 7 refusals / last 24 h: 24 of 24 refusals / whole corpus: 80 of 80 refusals |
| rule fired: `health-loaded-false` (gate reason starts `/health answered 200 but reports`) | DAY `20261116`: 0 fired / last 24 h: 0 fired / whole corpus: 1 fired, 1 sole |
| rule fired: `health-code-not-200` (gate reason starts `/health answered `) | DAY `20261116`: 0 fired / last 24 h: 0 fired / whole corpus: 0 fired |
| rule fired: `engine-process-absent` (gate reason starts `` no `basalt --serve` engine process ``) | DAY `20261116`: 0 fired / last 24 h: 0 fired / whole corpus: 0 fired |
| rule fired: `swap-free-low` (gate reason starts `swap free `) | DAY `20261116`: 0 fired / last 24 h: 0 fired / whole corpus: 15 fired, 13 sole |
| rule fired: `swap-rate` (gate reason starts `live swap throughput `) | DAY `20261116`: 6 fired, 6 sole / last 24 h: 22 fired, 20 sole / whole corpus: 38 fired, 32 sole |
| rule fired: `mem-available-low` (gate reason starts `MemAvailable `) | DAY `20261116`: 0 fired / last 24 h: 0 fired / whole corpus: 0 fired |
| rule fired: `device-read` (gate reason starts `block-device reads `) | DAY `20261116`: 1 fired, 0 sole / last 24 h: 3 fired, 0 sole / whole corpus: 8 fired, 2 sole |
| rule fired: `engine-state-D` (gate reason starts `engine in uninterruptible I/O`) | DAY `20261116`: 1 fired, 0 sole / last 24 h: 4 fired, 0 sole / whole corpus: 12 fired, 4 sole |
| rule fired: `idle-spin` (gate reason starts `idle-spin signature:`) | DAY `20261116`: 0 fired / last 24 h: 0 fired / whole corpus: 17 fired, 15 sole |
| rule fired: `gpu-busy` (gate reason starts `the shared brain was busy`) | DAY `20261116`: 1 fired, 0 sole / last 24 h: 3 fired, 0 sole / whole corpus: 6 fired, 0 sole |
| rule fired: `foreign-legs` (gate reason contains `other leg(s) on this endpoint: one leg per endpoint`) | DAY `20261116`: 0 fired / last 24 h: 0 fired / whole corpus: 0 fired |
| refusals decided by exactly ONE rule | DAY `20261116`: 6 / last 24 h: 20 / whole corpus: 67 |
| refusals where TWO OR MORE rules fired together | DAY `20261116`: 1 / last 24 h: 4 / whole corpus: 13 |
| refusal reasons this rule table cannot attribute (fail closed) | DAY `20261116`: 0 / last 24 h: 0 / whole corpus: 0 |
| readings whose gate verdict line could not be parsed (fail closed) | DAY `20261116`: 0 / last 24 h: 0 / whole corpus: 0 |
| rule cross-check: swap-band refusals (key=value ratio at/above the ceiling) vs the gate's OWN swap-rule reason | DAY `20261116`: AGREES (6 = 6) / last 24 h: AGREES (22 = 22) / whole corpus: AGREES (38 = 38) |
| input-gap reason classes (the gate's own leading phrase, numbers as N) | DAY `20261116`: 0 / last 24 h: 0 / whole corpus: no reading for engine_state, gpu_util_pct, gpu_power_w x1; no reading for mem_total_mib, mem_available_mib, swap_total_mib, swap_free_mib, engine_state, engine_pcpu, engine_rss_mib, gpu_util_pct, gpu_power_w, loadN, health_code, foreign_legs x1; unreadable number(s): engine_pcpu x2; unreadable number(s): swap_total_peak_mib_per_s x2 |

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
counter (20 of 30 launchable windows carrying the statistic) counts COVERAGE, not
support for a ceiling, and reaching 30 would not change that conclusion.

