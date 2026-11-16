# PUB preflight reading census (generated)

Written by `scripts/pub_preflight_census.py`; this file is that tool's output, never a
transcription of a tick note. It moves no benchmark byte and registers no contour feature.
Readings are stored outside this repository (the producer command is untracked, like every
connection seam on this line), so this census runs on the workstation only and is not
CI-enrolled; its arithmetic is pinned by `harness/pub_preflight_census_test.py` over
synthetic readings, and `--check` re-derives this table from the retained readings.

Census stamp: `pub-preflight-census-v15`, gate sha16 `624d0d3cc50718c2`, window `as-of 2026-11-16 15:29` (175 readings inside the window). v15 adds the BUILD axis the corpus never had (tick 208, 2026-11-16): the producer now emits `health_body_sha16` (SHA-256/16 of the /health body the `health_loaded` rule already fetches — zero extra fetches) and `health_max_context` (the same body's advertised context); the gate validates the pair as INPUT — exactly one key, or a value failing its format, is an input gap, absence is a coverage line, and no refusal rule reads either key, so every stored reading keeps a byte-identical verdict — and the table groups readings by build, crosswalks build against pid, and names the pid<->build anomalies, because at the 16.11 cut the two axes disagreed: all nine refusals of the day sat on pid 175316 (retired 09:59) while live pid 438502 knew only GOs, and the 09:59 restart that also swapped the build (serve context 262 144 -> 196 608, sampling header gone, binary path moved) was invisible to every stored byte. Until a reading carries a valid pair, every build cell prints its coverage split and no verdict may be credited or blamed to a named build. v14 gives the READINGS half of the headroom projection its cadence denominator: v13 converted a projected number of MINUTES into a number of READINGS by dividing by the monotone run's MEAN cadence and printed one integer, while the intervals inside that same run were 28, 39, 35, 51, 9, 16 and 32 min (a 5.7x spread), so at the 2026-11-16 13:37 cut its `about 9 further readings` was one value drawn from a 5-33 range — the projection was labelled a projection, but its second number rested on an unstated uniform-cadence assumption, which is the producer rule 'divide by a measured window, never a nominal count' arriving one level further down. v14 keeps the minutes primary (rate over a measured span), prints the reading count as the band the run's own intervals support, names that denominator in the cell (interval count, min-max, mean), collapses to a single count only when the intervals are uniform within `MEM_INTERVAL_FLAT_RATIO`, and prints NO reading count when no positive interval exists, because two draws sharing a timestamp must never reach a denominator. v10 derives the engine-state-D refusal set from the readings' own `engine_state` key and requires it to equal the set the gate's reason line names, at all three scopes, and prints how many state-D refusals sat on a device the device rule calls quiet, with the denominator of state-D refusals that carry a device window: until now only the swap rule was ever re-derived from the columns, and the state rule is the one rule with no ceiling to disagree about (the gate fires when `engine_state` contains `D`, so a `Dl` state fires). v9 counts WHICH GATE RULE refused each reading, read out of the gate's own refusal text at the three published scopes, and cross-checks the swap-band refusal set (derived here from the key=value columns) against the set whose gate reason line names the swap rule (the gate's own claim): every tick sentence that attributed a refusal to a rule had never been computed. The rule table is BOUND to the gate source — each anchor prefix must appear in it and the refusal-site count must match — an unmappable reason prints UNATTRIBUTED and moves the exit code to 4, and the preserved-shape sentence at the end of this paragraph is now GENERATED from the stamp number, because the hand-typed one claimed only v1-v6 are preserved: two stamps short of the v7 and v8 changes this same sentence describes. v8 splits one row that carried two denominators: the swap rule's OWN decision boundary (highest window the rule accepted, lowest window it refused, judged on the rule's decision whatever the gate verdict was) and the launchable-column gap (highest gate-GO draw to lowest refusal), which is what v5-v7 printed as 'dead zone' and what every tick quoted as the rule's resolution. At the committed 2026-11-16 02:14 cut the corpus gap is 0.905-1.060 x while the rule boundary is 0.940-1.060 x, because `preflight-20261116-0214.txt` carries swap 18.8 MiB/s = 0.94 x of the 20.0 ceiling, which the swap rule ACCEPTED (the reading was refused instead by the device, state-D and GPU-mean rules): the rule is measured accepting at 0.94 x, and the v7 'POPULATED (1 windows inside)' at all three scopes was produced by exactly that accepted draw. A judged draw inside the rule band is impossible by definition — it would itself be an accepted or a refused point and move the bound that excludes it — so the boundary row prints EMPTY BY CONSTRUCTION and names input-gap readings inside the band separately. v7 prints the v5 rule band at THREE scopes (the as-of calendar day, the sliding 24 h window, the whole corpus) with the scope word inside every row label and a computed dead-zone scope state, because a dead zone is a property of the row set it is measured over and only the day scope was ever published: at the 2026-11-16 01:50 cut the day cell put the GO-to-refusal zone 25.3 MiB/s wide while the corpus put it at 3.1 MiB/s (highest launchable draw 0.905x, lowest swap-rule refusal 1.06x, empty over the 25 launchable draws and 35 swap-rule refusals that carry a swap window — only 70 of the 158 stored files carry those keys at all, so the block prints its band denominator), and the 2026-11-15 tick sentences that said "the dead zone" (0.38-1.06x, then 0.74-1.06x) were day-scoped numbers presented as a property of the rule — tick 192 and 193's scope-word defect a third time in the same column. v6 adds three COMPUTED continuity rows over the sliding 24 h window — the trailing consecutive-refusal run ending at the newest reading, readings/hours since the last gate-GO with that GO named and aged, and a window-run-vs-day-run state word — because the v5 DAY table resets at midnight: at the first reading of 2026-11-16 (00:04) the day cells printed a run of 1 and `n/a — no GO of this day` while the box had refused FOUR readings in a row across midnight and its last GO was 162 minutes back, one of the 7 launchable windows this same table counts in the last 24 h. The day cells were correct as labelled and useless as a streak, which is tick 192's class (a figure that lives only in prose stops being recomputed) one level down. v5 adds the DAY rule-band table (8 computed cells: the GO and swap-refusal ratio bands, the refusal median, refusals decided by a rule other than swap, the GO-to-refusal dead zone with its EMPTY/POPULATED state word and the count inside it, the longest consecutive-refusal run, readings since the last GO, and the age of the launchable-footprint maximum with the trailing windows above it) — those figures had lived only in tick prose and had been re-typed from a stale cut: on 2026-11-15 the refusal median is 4.225x at 24 readings, 3.985x at 30 and 3.745x at 31, while two consecutive ticks quoted 4.22x as today's number. v4 adds two COMPUTED footprint ceiling rows — the ceiling dry-run and its state word — because at the 08:57 reading on 2026-11-15 the launchable footprint maximum (8 520 MiB) grew ABOVE the refused-group maximum (6 957 MiB), so the only footprint ceiling the arming rule allows fires on nothing in the corpus; that consequence was hand-derived in a tick note and now belongs to the tool (tick 172's class of defect). v3 removes the CORPUS-WIDE reading count from that window-identity sentence: the number counted every `preflight-*.txt` file present at run time, so taking one reading after the frozen window made `--check` of an untouched snapshot report drift (measured 2026-11-15 01:00 at the committed window `as-of 2026-11-14 23:47`: `123 stored readings` became `124 stored readings`, while the window count, every verdict and every band cell stayed identical). The corpus count is now printed on stdout only, outside the committed file. v2 added two COMPUTED group-state rows — the swap-peak band state and the footprint group separation — because v1 printed "Band: nothing between X and Y" unconditionally, and at 23:13 on 2026-11-14 the order of X and Y reversed: the table went on asserting an empty interval the data had withdrawn. v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13 and v14 tables are left published exactly as written; a file stamped any of them is not the same table shape as this v15 one.

Ceilings read out of the gate source at run time, so this table cannot disagree with the rule it reports: `SWAP_RATE_MAX_MIB_S = 20.0` (window MEAN; the peak statistic is reported, not gated), `GPU_UTIL_MAX_MEAN_PCT = 50.0` (the window mean, never the peak), and the device-read ceiling is SCOPE-DEPENDENT: `BLK_READ_MAX_MIB_S_WHOLE = 50.0` applies to every reading carrying `blk_scope=whole-disk`, while `BLK_READ_MAX_MIB_S = 100.0` applies only to readings with NO scope key (the old diskstats sum, which double-counts partitions, i.e. about 2x the device). The two numbers are the SAME physical point; a file with an unrecognised scope value is an input gap the gate never judges. Naming one of these numbers without its scope is exactly how a generated table starts disagreeing with the rule it claims to report (measured 2026-11-14 18:47: a whole-disk reading of 56.2 MiB/s was refused by the gate while the first version of this table printed 100.0 as the whole-disk ceiling).

| census cell | value |
|---|---|
| gate verdict GO | 87 |
| gate verdict NO-GO | 82 |
| gate verdict input gap | 6 |
| device scope of the readings in this window | 76 whole-disk (`50.0` ceiling) / 99 unscoped (`100.0` ceiling) / 0 unknown scope |
| readings of the as-of day | 21 (12 GO / 9 NO-GO / 0 gap) |
| launchable (GO) windows in the last 24 h | 15 |
| leg completions recorded in that window | 0 |
| readings carrying the swap-peak key | 80 (NaN 2, parseable 78) |
| ...of those, gate-JUDGED readings with a parseable peak (the band's set) | 76 (the other 2 sit in readings the gate refuses to judge at all) |
| swap-mean-passing windows with a peak | 36 |
| swap-mean-failing windows with a peak | 40 |
| highest peak inside a swap-mean-PASSING window | 111.4 MiB/s |
| lowest peak inside a swap-mean-FAILING window | 95.4 MiB/s |
| swap-peak band state (computed, never asserted) | CROSSED — the highest launchable peak 111.4 MiB/s already sits AT OR ABOVE the lowest mean-failing peak 95.4 MiB/s, so the groups overlap: a ceiling high enough to spare every launchable window lets a mean-failing window through, and a lower ceiling refuses a window the mean rule launches. On this corpus a peak rule adds no refusal the mean rule does not already make |
| arming counter (launchable windows carrying the peak) | 30 of 30 |

Engine swap FOOTPRINT (added 2026-11-14, tick 159) — reported, never banded:

| footprint cell | value |
|---|---|
| readings carrying `engine_vmswap_mib` | 57 (NaN 0, parseable 57) |
| footprint on gate-GO windows (launchable) | 21 (median 3576 MiB, max 9499 MiB) |
| footprint on gate-NO-GO windows | 36 (median 7130 MiB, min 3357 MiB) |
| footprint group separation (computed, never asserted) | OVERLAPPING (launchable 21 window(s) 0-9499 MiB, refused 36 window(s) 3357-10770 MiB; n=21/36 cannot support a ceiling in either direction) |
| footprint ceiling dry-run (computed; it arms NOTHING) | ceiling > 9499 MiB fires on 0 of 21 launchable and 6 of 36 refused stored windows. A ceiling above every launchable footprint also refuses at least one refused window, so on this corpus the state rule would have real work to do |
| footprint ceiling state (computed) | FIRING-AT-MINIMUM-CEILING |
| page-cache share of swap in use (`swap_cached_mib` / used) | 57 readings, median 44.7 percent, max 65.2 percent |
| footprint arming counter (launchable windows carrying it) | 21 of 30 |
| ...of those launchable draws: non-zero footprint / exactly 0 MiB | 11 non-zero / 10 zero (the counter above counts COVERAGE; a 0 MiB draw says that process held no swap in that window, which is a measurement and sets no ceiling) |
| ...the same split on the refused side | 36 non-zero / 0 zero (the non-zero refused draws are the only work a footprint rule could ever be given) |
| footprint informative-coverage state (computed) | INFORMATIVE — a non-zero footprint in 11 of the 21 launchable draws (highest 9499 MiB), exactly 0 MiB in 10; the refused side holds 36 non-zero draw(s) |

The as-of **DAY** rule band (added 2026-11-15, tick 192) — today's verdicts only, every
ratio taken against `SWAP_RATE_MAX_MIB_S = 20.0` and every number recomputed at this
reading, because the same three figures quoted in tick prose had been carried forward
from an earlier cut instead of re-derived (the median reads 4.225x at 24 readings,
3.985x at 30 and 3.745x at 31 on this day's files):

| day cell | value |
|---|---|
| day launchable (GO) swap draws | 12 (band 0.00-0.05 x the 20.0 mean ceiling) |
| day refusals at or above the swap-mean ceiling | 8 (band 1.27-10.69 x, **median 6.223 x recomputed at this cut**) |
| day refusals decided by a rule OTHER than swap (window below ceiling) | 1: preflight-20261116-0214.txt at 0.94 x |
| day swap-rule ACCEPTED draws (any verdict — the rule's own denominator) | 13 (band 0.00-0.94 x) |
| day swap-rule decision boundary (accepted max to refusal min) | accepted up to 0.94 x, refused from 1.27 x, unresolved band 0.325 x (6.5 MiB/s) — EMPTY BY CONSTRUCTION (0 judged draws inside); judged draws inside are impossible by the definition above, input-gap readings inside: none |
| day launchable-column gap (GO max to lowest refusal; VERDICT-scoped, not the rule boundary) | 0.05-1.27 x — POPULATED (1 windows inside) |
| longest consecutive NO-GO run inside the day | 5 readings (any-verdict non-GO run: 5) |
| readings since the day's last gate-GO | 0 (last GO 15:29) |
| launchable footprint maximum of the day and its age | 9499 MiB set at 00:19, 19 reading(s) ago |
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
| readings this scope can band at all (verdict GO or NO-GO AND a parseable `swap_in + swap_out` window) | DAY `20261116` 21 of 21, last 24 h 32 of 32, whole corpus 83 of 175 |
| launchable (GO) swap draws, DAY `20261116` | 12, band 0.00-0.05 x the 20.0 mean ceiling |
| launchable (GO) swap draws, last 24 h | 15, band 0.00-0.74 x the 20.0 mean ceiling |
| launchable (GO) swap draws, whole corpus | 36, band 0.00-0.91 x the 20.0 mean ceiling |
| swap-rule ACCEPTED draws (any verdict, the rule's own denominator), DAY `20261116` | 13, band 0.00-0.94 x |
| swap-rule ACCEPTED draws (any verdict, the rule's own denominator), last 24 h | 17, band 0.00-0.94 x |
| swap-rule ACCEPTED draws (any verdict, the rule's own denominator), whole corpus | 43, band 0.00-0.94 x |
| swap-rule refusals (window at/above that ceiling), DAY `20261116` | 8, band 1.27-10.69 x, **median 6.223 x recomputed at this cut** |
| swap-rule refusals (window at/above that ceiling), last 24 h | 15, band 1.06-10.69 x, **median 2.305 x recomputed at this cut** |
| swap-rule refusals (window at/above that ceiling), whole corpus | 40, band 1.06-22.19 x, **median 4.310 x recomputed at this cut** |
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
| trailing consecutive NO-GO run ending at the newest reading (last 24 h, crosses the day boundary) | 0 readings (any-verdict non-GO run: 0) |
| readings since the last gate-GO (last 24 h, any day) | 0 (last GO preflight-20261116-1529.txt at 2026-11-16 15:29, 0 min before as-of) |
| window run vs day run (computed, never asserted) | NO TRAILING REFUSAL RUN (the newest reading is a gate GO; any-verdict non-GO run 0 reading(s)) |

Which gate RULE refused (added 2026-11-16, tick 197) — the verdict column says a reading
was refused and never says BY WHAT. Every tick attributed refusals in prose ("the night's
first out-heavy swap window", "02:14 died on the device, state-D and GPU-mean rules") and
not one of those sentences was ever computed. The counts below come out of the gate's own
refusal lines, from the same subprocess run that produced the verdict column, so a rule that
starts or stops firing moves a cell here instead of hiding in a report. The rule table is
BOUND to the gate source (every anchor must appear in it and the refusal-site count must
match), an unmappable reason names its file and moves the exit code to 4, and TWO rows
compare two independent derivations of one set. The swap row (v9) takes the refusals whose
sampled window sits at or above `SWAP_RATE_MAX_MIB_S` against the refusals whose gate
reason line names the swap rule. The state row (v10) takes the refusals whose own
`engine_state` key contains `D` — the gate's exact substring test, so `Dl` fires, read
through the gate's own key=value parser — against the refusals whose reason line names the
state rule; a gate that sampled the launcher instead of the model, or a reason string
renamed under the rule table, moves that cell instead of quietly changing refusals. The
device-quiet row then splits the state-D refusals physically: a state-D wait on a device
the device rule calls quiet is a page wait served from RAM (tick 200's re-admission class),
a state-D wait at a saturated device is the foreign-reader class that motivated that rule,
and the row prints how many state-D refusals have a device window at all, because a
refusal taken before that key existed belongs to neither class. A rule that fired on
nothing still gets a row: a missing row and a zero row
read the same way in prose, which is how a rule that never fires gets mistaken for a rule
nobody counted:

| refusal-rule cell (every scope labelled) | value |
|---|---|
| refusals this scope can attribute (gate NO-GO with captured reason lines) | DAY `20261116`: 9 of 9 refusals / last 24 h: 17 of 17 refusals / whole corpus: 82 of 82 refusals |
| rule fired: `health-loaded-false` (gate reason starts `/health answered 200 but reports`) | DAY `20261116`: 0 fired / last 24 h: 0 fired / whole corpus: 1 fired, 1 sole |
| rule fired: `health-code-not-200` (gate reason starts `/health answered `) | DAY `20261116`: 0 fired / last 24 h: 0 fired / whole corpus: 0 fired |
| rule fired: `engine-process-absent` (gate reason starts `` no `basalt --serve` engine process ``) | DAY `20261116`: 0 fired / last 24 h: 0 fired / whole corpus: 0 fired |
| rule fired: `swap-free-low` (gate reason starts `swap free `) | DAY `20261116`: 0 fired / last 24 h: 0 fired / whole corpus: 15 fired, 13 sole |
| rule fired: `swap-rate` (gate reason starts `live swap throughput `) | DAY `20261116`: 8 fired, 7 sole / last 24 h: 15 fired, 13 sole / whole corpus: 40 fired, 33 sole |
| rule fired: `mem-available-low` (gate reason starts `MemAvailable `) | DAY `20261116`: 0 fired / last 24 h: 0 fired / whole corpus: 0 fired |
| rule fired: `device-read` (gate reason starts `block-device reads `) | DAY `20261116`: 1 fired, 0 sole / last 24 h: 3 fired, 0 sole / whole corpus: 8 fired, 2 sole |
| rule fired: `engine-state-D` (gate reason starts `engine in uninterruptible I/O`) | DAY `20261116`: 2 fired, 0 sole / last 24 h: 4 fired, 0 sole / whole corpus: 13 fired, 4 sole |
| rule fired: `idle-spin` (gate reason starts `idle-spin signature:`) | DAY `20261116`: 0 fired / last 24 h: 0 fired / whole corpus: 17 fired, 15 sole |
| rule fired: `gpu-busy` (gate reason starts `the shared brain was busy`) | DAY `20261116`: 1 fired, 0 sole / last 24 h: 3 fired, 0 sole / whole corpus: 6 fired, 0 sole |
| rule fired: `foreign-legs` (gate reason contains `other leg(s) on this endpoint: one leg per endpoint`) | DAY `20261116`: 0 fired / last 24 h: 0 fired / whole corpus: 0 fired |
| refusals decided by exactly ONE rule | DAY `20261116`: 7 / last 24 h: 13 / whole corpus: 68 |
| refusals where TWO OR MORE rules fired together | DAY `20261116`: 2 / last 24 h: 4 / whole corpus: 14 |
| refusal reasons this rule table cannot attribute (fail closed) | DAY `20261116`: 0 / last 24 h: 0 / whole corpus: 0 |
| readings whose gate verdict line could not be parsed (fail closed) | DAY `20261116`: 0 / last 24 h: 0 / whole corpus: 0 |
| rule cross-check: swap-band refusals (key=value ratio at/above the ceiling) vs the gate's OWN swap-rule reason | DAY `20261116`: AGREES (8 = 8) / last 24 h: AGREES (15 = 15) / whole corpus: AGREES (40 = 40) |
| state-rule cross-check: the reading's own `engine_state` contains `D` (the gate's substring test, so `Dl` fires) vs the gate's engine-state-D reason | DAY `20261116`: AGREES (2 = 2) / last 24 h: AGREES (4 = 4) / whole corpus: AGREES (13 = 13) |
| readings with no `engine_state` key (this cross-check cannot see them; the gate judges such a reading an input gap, never healthy) | DAY `20261116`: 0 of 21 readings / last 24 h: 0 of 32 readings / whole corpus: 2 of 175 readings |
| state-D refusals on a device the device rule calls quiet (device window present and below its ceiling, 50.0 whole-disk / 100.0 unscoped; denominator named) | DAY `20261116`: 1 of 2 state-D refusals carry a device window (2 named by the gate) / last 24 h: 1 of 4 state-D refusals carry a device window (4 named by the gate) / whole corpus: 6 of 9 state-D refusals carry a device window (13 named by the gate) |
| rule re-derived from the reading's own columns and compared with the gate's reason line: `health-loaded-false` (gate reason starts `/health answered 200 but reports`) | DAY `20261116`: AGREES (0 = 0; 0 of 9 attributed refusals cannot be evaluated from the columns) / last 24 h: AGREES (0 = 0; 0 of 17 attributed refusals cannot be evaluated from the columns) / whole corpus: AGREES (1 = 1; 30 of 82 attributed refusals cannot be evaluated from the columns) |
| rule re-derived from the reading's own columns and compared with the gate's reason line: `health-code-not-200` (gate reason starts `/health answered `) | DAY `20261116`: AGREES (0 = 0; 0 of 9 attributed refusals cannot be evaluated from the columns) / last 24 h: AGREES (0 = 0; 0 of 17 attributed refusals cannot be evaluated from the columns) / whole corpus: AGREES (0 = 0; 0 of 82 attributed refusals cannot be evaluated from the columns) |
| rule re-derived from the reading's own columns and compared with the gate's reason line: `engine-process-absent` (gate reason starts `` no `basalt --serve` engine process ``) | DAY `20261116`: AGREES (0 = 0; 0 of 9 attributed refusals cannot be evaluated from the columns) / last 24 h: AGREES (0 = 0; 0 of 17 attributed refusals cannot be evaluated from the columns) / whole corpus: AGREES (0 = 0; 30 of 82 attributed refusals cannot be evaluated from the columns) |
| rule re-derived from the reading's own columns and compared with the gate's reason line: `swap-free-low` (gate reason starts `swap free `) | DAY `20261116`: AGREES (0 = 0; 0 of 9 attributed refusals cannot be evaluated from the columns) / last 24 h: AGREES (0 = 0; 0 of 17 attributed refusals cannot be evaluated from the columns) / whole corpus: AGREES (15 = 15; 0 of 82 attributed refusals cannot be evaluated from the columns) |
| rule re-derived from the reading's own columns and compared with the gate's reason line: `mem-available-low` (gate reason starts `MemAvailable `) | DAY `20261116`: AGREES (0 = 0; 0 of 9 attributed refusals cannot be evaluated from the columns) / last 24 h: AGREES (0 = 0; 0 of 17 attributed refusals cannot be evaluated from the columns) / whole corpus: AGREES (0 = 0; 0 of 82 attributed refusals cannot be evaluated from the columns) |
| rule re-derived from the reading's own columns and compared with the gate's reason line: `device-read` (gate reason starts `block-device reads `) | DAY `20261116`: AGREES (1 = 1; 0 of 9 attributed refusals cannot be evaluated from the columns) / last 24 h: AGREES (3 = 3; 0 of 17 attributed refusals cannot be evaluated from the columns) / whole corpus: AGREES (8 = 8; 35 of 82 attributed refusals cannot be evaluated from the columns) |
| rule re-derived from the reading's own columns and compared with the gate's reason line: `idle-spin` (gate reason starts `idle-spin signature:`) | DAY `20261116`: AGREES (0 = 0; 0 of 9 attributed refusals cannot be evaluated from the columns) / last 24 h: AGREES (0 = 0; 0 of 17 attributed refusals cannot be evaluated from the columns) / whole corpus: AGREES (17 = 17; 1 of 82 attributed refusals cannot be evaluated from the columns) |
| rule re-derived from the reading's own columns and compared with the gate's reason line: `gpu-busy` (gate reason starts `the shared brain was busy`) | DAY `20261116`: AGREES (1 = 1; 0 of 9 attributed refusals cannot be evaluated from the columns) / last 24 h: AGREES (3 = 3; 0 of 17 attributed refusals cannot be evaluated from the columns) / whole corpus: AGREES (6 = 6; 38 of 82 attributed refusals cannot be evaluated from the columns) |
| rule re-derived from the reading's own columns and compared with the gate's reason line: `foreign-legs` (gate reason contains `other leg(s) on this endpoint: one leg per endpoint`) | DAY `20261116`: AGREES (0 = 0; 0 of 9 attributed refusals cannot be evaluated from the columns) / last 24 h: AGREES (0 = 0; 0 of 17 attributed refusals cannot be evaluated from the columns) / whole corpus: AGREES (0 = 0; 0 of 82 attributed refusals cannot be evaluated from the columns) |
| gate rules whose firing set is computed from the stored columns at this cut | DAY `20261116`: 11 of 11 (v9 swap band, v10 engine state, v11 the other 9) / last 24 h: 11 of 11 (v9 swap band, v10 engine state, v11 the other 9) / whole corpus: 11 of 11 (v9 swap band, v10 engine state, v11 the other 9) |
| input-gap reason classes (the gate's own leading phrase, numbers as N) | DAY `20261116`: 0 / last 24 h: 0 / whole corpus: no reading for engine_state, gpu_util_pct, gpu_power_w x1; no reading for mem_total_mib, mem_available_mib, swap_total_mib, swap_free_mib, engine_state, engine_pcpu, engine_rss_mib, gpu_util_pct, gpu_power_w, loadN, health_code, foreign_legs x1; unreadable number(s): engine_pcpu x2; unreadable number(s): swap_total_peak_mib_per_s x2 |

**Which engine process a pooled statistic describes (census v11).** The producer names
the pid it actually sampled in a comment line, and the gate's parser skips comments — so
every footprint, RSS and page-cache figure above has always been pooled over whatever
engine processes the corpus happened to contain. That is harmless while one process
serves the whole window and wrong the moment the endpoint's engine is restarted (a
version bump, a config ladder, a watchdog restart): a footprint maximum recorded by a
retired process is not a property of the endpoint, and the pre-registered footprint
ceiling would be drawn from precisely such a maximum. Generation counts are printed
before the per-generation detail, the unattributable readings are printed as their own
row, and the state word is computed:

| engine generations sampled in this scope (the producer's own `# engine pid=` comment; the count precedes the list, at most 8 generations listed) | DAY `20261116`: 2 generations over 21 readings: pid 175316 — 11 readings (2 GO / 9 NO-GO / 0 input gap), first preflight-20261116-0004.txt last preflight-20261116-0719.txt, footprint max launchable 9499 MiB / refused 10770 MiB, non-zero footprint draws 2 of 2 launchable / 9 of 9 refused; pid 438502 — 10 readings (10 GO / 0 NO-GO / 0 input gap), first preflight-20261116-1007.txt last preflight-20261116-1529.txt, footprint max launchable 0 MiB / refused no key, non-zero footprint draws 0 of 10 launchable / 0 of 0 refused / last 24 h: 2 generations over 32 readings: pid 175316 — 22 readings (5 GO / 17 NO-GO / 0 input gap), first preflight-20261115-1554.txt last preflight-20261116-0719.txt, footprint max launchable 9499 MiB / refused 10770 MiB, non-zero footprint draws 5 of 5 launchable / 17 of 17 refused; pid 438502 — 10 readings (10 GO / 0 NO-GO / 0 input gap), first preflight-20261116-1007.txt last preflight-20261116-1529.txt, footprint max launchable 0 MiB / refused no key, non-zero footprint draws 0 of 10 launchable / 0 of 0 refused / whole corpus: 15 generations over 173 readings (8 listed, 7 not printed): pid 3284575 — 32 readings (2 GO / 30 NO-GO / 0 input gap), first preflight-20261111-0336.txt last preflight-20261112-2032.txt, footprint max launchable no key / refused no key, non-zero footprint draws 0 of 0 launchable / 0 of 0 refused; pid 1116984 — 1 readings (1 GO / 0 NO-GO / 0 input gap), first preflight-20261112-2131.txt last preflight-20261112-2131.txt, footprint max launchable no key / refused no key, non-zero footprint draws 0 of 0 launchable / 0 of 0 refused; pid 1133852 — 1 readings (1 GO / 0 NO-GO / 0 input gap), first preflight-20261112-2222.txt last preflight-20261112-2222.txt, footprint max launchable no key / refused no key, non-zero footprint draws 0 of 0 launchable / 0 of 0 refused; pid 1142697 — 7 readings (7 GO / 0 NO-GO / 0 input gap), first preflight-20261112-2311.txt last preflight-20261113-0331.txt, footprint max launchable no key / refused no key, non-zero footprint draws 0 of 0 launchable / 0 of 0 refused; pid 1173996 — 6 readings (6 GO / 0 NO-GO / 0 input gap), first preflight-20261113-0418.txt last preflight-20261113-0820.txt, footprint max launchable no key / refused no key, non-zero footprint draws 0 of 0 launchable / 0 of 0 refused; pid 1195251 — 1 readings (1 GO / 0 NO-GO / 0 input gap), first preflight-20261113-0903.txt last preflight-20261113-0903.txt, footprint max launchable no key / refused no key, non-zero footprint draws 0 of 0 launchable / 0 of 0 refused; pid 1196174 — 1 readings (1 GO / 0 NO-GO / 0 input gap), first preflight-20261113-0928.txt last preflight-20261113-0928.txt, footprint max launchable no key / refused no key, non-zero footprint draws 0 of 0 launchable / 0 of 0 refused; pid 1214520 — 1 readings (0 GO / 1 NO-GO / 0 input gap), first preflight-20261113-0955.txt last preflight-20261113-0955.txt, footprint max launchable no key / refused no key, non-zero footprint draws 0 of 0 launchable / 0 of 0 refused |
| readings in this scope whose producer comment carries no engine pid (unattributable by this block; the gate never reads comments, so its verdict is unaffected) | DAY `20261116`: 0 of 21 readings / last 24 h: 0 of 32 readings / whole corpus: 2 of 175 readings |
| launchable windows and refused windows on the same engine generation? | DAY `20261116`: PARTIALLY OVERLAPPING (1 generation(s) carry both) / last 24 h: PARTIALLY OVERLAPPING (1 generation(s) carry both) / whole corpus: PARTIALLY OVERLAPPING (3 generation(s) carry both) |
| the footprint dry-run ceiling's binding value, and the generation that produced it | DAY `20261116`: launchable footprint maximum 9499 MiB (`preflight-20261116-0019.txt`) belongs to pid 175316, while the newest reading in this scope sampled pid 438502 (`preflight-20261116-1529.txt`); pid 175316 was last sampled by `preflight-20261116-0719.txt` → GENERATION-STALE: a footprint ceiling drawn from this value describes a process this cut no longer samples / last 24 h: launchable footprint maximum 9499 MiB (`preflight-20261116-0019.txt`) belongs to pid 175316, while the newest reading in this scope sampled pid 438502 (`preflight-20261116-1529.txt`); pid 175316 was last sampled by `preflight-20261116-0719.txt` → GENERATION-STALE: a footprint ceiling drawn from this value describes a process this cut no longer samples / whole corpus: launchable footprint maximum 9499 MiB (`preflight-20261116-0019.txt`) belongs to pid 175316, while the newest reading in this scope sampled pid 438502 (`preflight-20261116-1529.txt`); pid 175316 was last sampled by `preflight-20261116-0719.txt` → GENERATION-STALE: a footprint ceiling drawn from this value describes a process this cut no longer samples |
| has the newest sampled engine generation ever recorded a footprint above 0 MiB? | DAY `20261116`: 2 generation(s) carry the footprint key here: 1 recorded a footprint above 0 MiB in at least one window (175316), 1 recorded only zeros in every window it produced (438502); the NEWEST generation pid 438502 (`preflight-20261116-1529.txt`) carries the key in 10 window(s) and answered exactly 0 MiB in every one → ZERO-FOOTPRINT GENERATION: the only ceiling this coverage admits is `> 0 MiB`, so arming on it arms a rule whose failure mode this very process has never demonstrated once / last 24 h: 2 generation(s) carry the footprint key here: 1 recorded a footprint above 0 MiB in at least one window (175316), 1 recorded only zeros in every window it produced (438502); the NEWEST generation pid 438502 (`preflight-20261116-1529.txt`) carries the key in 10 window(s) and answered exactly 0 MiB in every one → ZERO-FOOTPRINT GENERATION: the only ceiling this coverage admits is `> 0 MiB`, so arming on it arms a rule whose failure mode this very process has never demonstrated once / whole corpus: 2 generation(s) carry the footprint key here: 1 recorded a footprint above 0 MiB in at least one window (175316), 1 recorded only zeros in every window it produced (438502); the NEWEST generation pid 438502 (`preflight-20261116-1529.txt`) carries the key in 10 window(s) and answered exactly 0 MiB in every one → ZERO-FOOTPRINT GENERATION: the only ceiling this coverage admits is `> 0 MiB`, so arming on it arms a rule whose failure mode this very process has never demonstrated once |

**A pid generation and a build generation are different axes, and on 2026-11-16 they
disagreed (census v15, tick 208).** Every generation row above is a PROCESS id, and a
pid answers only "did this process swap?". At the 14:38 cut the live pid 438502 had
nine readings and zero refusals while all nine of the day's refusals belonged to pid
175316, retired at 09:59 — and that same 09:59 restart was a BUILD swap (serve context
262 144 -> 196 608, sampling header gone, binary path moved) that not one of the 174
stored readings named in a byte. A refusal set that belongs to a retired PROCESS tells
you nothing about the endpoint you are about to launch into, and it tells you less about
the BUILD you are actually quoting. The producer now hashes the /health body it already
fetches for the `health_loaded` rule (`health_body_sha16`, SHA-256/16) and emits the
context that body advertises (`health_max_context`); the gate validates the pair and
never gates on it, so the whole stored corpus keeps byte-identical verdicts. The
build rows below print the coverage split first — until the first post-change reading
lands, every scope says 0 pairs and no verdict may be credited to a named build:
| readings carrying a VALID build-identity pair (`health_body_sha16` + `health_max_context`, both keys from ONE /health body; census v15) | DAY `20261116`: 1 of 21 readings / last 24 h: 1 of 32 readings / whole corpus: 1 of 175 readings |
| readings carrying a BROKEN identity (exactly one key, or a value failing the format — the gate answers an input gap on every one of these, so they credit no build and lose no verdict) | DAY `20261116`: 0 one-sided / 0 malformed / last 24 h: 0 one-sided / 0 malformed / whole corpus: 0 one-sided / 0 malformed |
| readings carrying NO identity key (the pre-v15 corpus: the verdict stands, the BUILD is unnamed — every statistic pooled over them pools processes, not builds) | DAY `20261116`: 20 of 21 readings / last 24 h: 31 of 32 readings / whole corpus: 174 of 175 readings |
| distinct engine BUILDs recorded in this scope (body sha16 -> advertised context, verdict mix, span, pid set; at most 8 listed, count precedes the list) | DAY `20261116`: 1 distinct build(s) over 1 identity-bearing reading(s): `b4d6a41750d9eafd` (ctx 196608) — 1 reading(s) (1 GO / 0 NO-GO / 0 input gap), first preflight-20261116-1529.txt last preflight-20261116-1529.txt, engine pids: 438502 / last 24 h: 1 distinct build(s) over 1 identity-bearing reading(s): `b4d6a41750d9eafd` (ctx 196608) — 1 reading(s) (1 GO / 0 NO-GO / 0 input gap), first preflight-20261116-1529.txt last preflight-20261116-1529.txt, engine pids: 438502 / whole corpus: 1 distinct build(s) over 1 identity-bearing reading(s): `b4d6a41750d9eafd` (ctx 196608) — 1 reading(s) (1 GO / 0 NO-GO / 0 input gap), first preflight-20261116-1529.txt last preflight-20261116-1529.txt, engine pids: 438502 |
| the newest reading's BUILD vs its engine pid (the two axes crosswalked; a pid whose readings split recorded/unrecorded means the KEY arrived mid-process, not the build) | DAY `20261116`: newest reading `preflight-20261116-1529.txt` (pid 438502) -> build `b4d6a41750d9eafd` ctx 196608; that pid carries a valid pair in 1 of its 10 reading(s) in scope -> COVERAGE BOUNDARY INSIDE ONE PID: pid 438502 has 9 reading(s) here without an identity key — the coverage boundary is the KEY shipping, not the process, and the pid rows must not be read as build rows / last 24 h: newest reading `preflight-20261116-1529.txt` (pid 438502) -> build `b4d6a41750d9eafd` ctx 196608; that pid carries a valid pair in 1 of its 10 reading(s) in scope -> COVERAGE BOUNDARY INSIDE ONE PID: pid 438502 has 9 reading(s) here without an identity key — the coverage boundary is the KEY shipping, not the process, and the pid rows must not be read as build rows / whole corpus: newest reading `preflight-20261116-1529.txt` (pid 438502) -> build `b4d6a41750d9eafd` ctx 196608; that pid carries a valid pair in 1 of its 10 reading(s) in scope -> COVERAGE BOUNDARY INSIDE ONE PID: pid 438502 has 9 reading(s) here without an identity key — the coverage boundary is the KEY shipping, not the process, and the pid rows must not be read as build rows |
| pid<->build anomalies (a pid spanning builds = a live change of build, never happens on this engine and gets NAMED the day it does; a build under several pids = the same build restarted, ordinary) | DAY `20261116`: one pid naming more than one build: none / one build under more than one pid (restart of the SAME build, normal): none / last 24 h: one pid naming more than one build: none / one build under more than one pid (restart of the SAME build, normal): none / whole corpus: one pid naming more than one build: none / one build under more than one pid (restart of the SAME build, normal): none |

**Coverage is not information (census v12, 2026-11-16, tick 204).** The footprint arming
counter counts launchable windows that CARRY `engine_vmswap_mib`, and a window reading
`engine_vmswap_mib=0` carries it. Tick 203 caught the consequence on live bytes: the
generation the endpoint runs now answered 0 MiB in every window it produced — including
one taken inside its own GPU-99 %/157 W campaign — while the pooled dry-run ceiling still
bound to a retired process. Arming a footprint rule off that coverage admits exactly one
value, `> 0 MiB`, i.e. a guard against a failure mode the live process has never
demonstrated once. The split is now printed rather than argued: the footprint block
separates non-zero from exactly-zero draws on BOTH sides and states what the counter is
buying (INFORMATIVE / ZERO-DRAW-DOMINATED / ALL-ZERO), and the generation block reports
per generation how many of its footprint draws are non-zero and whether the NEWEST
sampled generation has ever recorded a footprint above 0 MiB (ZERO-FOOTPRINT GENERATION).
A zero draw is never dropped from the coverage count — it is a real measurement — it just
stops being able to pose as a ceiling.

**The two FREE columns, and the regime change that prose had been hiding (census v13,
2026-11-16, tick 205).** Every rule this table bands is a RATE over one 6 s window, and
the gate's memory rule (`mem-available-low`, floor `MEM_AVAILABLE_MIN_MIB`, read out of
the gate source at run time like every other ceiling) was the one threshold in force that
no published cell ever quoted a distance to. 204 ticks of prose wrote MemAvailable into a
sentence next to a verdict and never trended it, and that prose hid a regime change:
generation 175316 ran 15-16 Nov at MemAvailable 17 675-21 441 MiB with 16 062-16 839 MiB
of swap in use, and the live generation 438502 runs at 4 938-6 618 MiB with swap in use
flat at 65 MiB. The two free columns moved in OPPOSITE directions across that restart —
which is also why the morning's page-in storms (6.82x, 6.91x and 10.69x of the swap
ceiling, ticks 196/199/200) simply stopped: there was nothing left swapped to page in.
The block below therefore states headroom as a per-generation STATE with a computed
trend, attributes a headroom fall to the sampled process's own RSS growth or names it
UNATTRIBUTED, and labels its own forward look a projection in the cell that prints it.
No ceiling is registered here and no rule is armed: the numbers this block prints are the
evidence a decision would need, not the decision.

| memory-headroom coverage in this scope | DAY `20261116`: 21 of 21 readings carry a parseable `mem_available_mib` / last 24 h: 32 of 32 readings carry a parseable `mem_available_mib` / whole corpus: 174 of 175 readings carry a parseable `mem_available_mib`, 1 do not |
| MemAvailable band in this scope | DAY `20261116`: min 4135 MiB (`preflight-20261116-1529.txt`), median 17675 MiB, max 21441 MiB over 21 reading(s) / last 24 h: min 4135 MiB (`preflight-20261116-1529.txt`), median 18611 MiB, max 21446 MiB over 32 reading(s) / whole corpus: min 4135 MiB (`preflight-20261116-1529.txt`), median 18918 MiB, max 58884 MiB over 174 reading(s) |
| the newest reading's headroom against that floor | DAY `20261116`: newest draw `preflight-20261116-1529.txt` reads 4135 MiB against the gate's own floor `MEM_AVAILABLE_MIN_MIB` = 2048 MiB (rule `mem-available-low`) → ABOVE the floor by 2087 MiB (2.02x the floor; verdict GO) / last 24 h: newest draw `preflight-20261116-1529.txt` reads 4135 MiB against the gate's own floor `MEM_AVAILABLE_MIN_MIB` = 2048 MiB (rule `mem-available-low`) → ABOVE the floor by 2087 MiB (2.02x the floor; verdict GO) / whole corpus: newest draw `preflight-20261116-1529.txt` reads 4135 MiB against the gate's own floor `MEM_AVAILABLE_MIN_MIB` = 2048 MiB (rule `mem-available-low`) → ABOVE the floor by 2087 MiB (2.02x the floor; verdict GO) |
| closest approach to that floor in this scope | DAY `20261116`: closest approach to the floor in this scope: 4135 MiB (`preflight-20261116-1529.txt`), 2087 MiB above it; THE MINIMUM IS THE NEWEST DRAW (headroom is falling, not resting) / last 24 h: closest approach to the floor in this scope: 4135 MiB (`preflight-20261116-1529.txt`), 2087 MiB above it; THE MINIMUM IS THE NEWEST DRAW (headroom is falling, not resting) / whole corpus: closest approach to the floor in this scope: 4135 MiB (`preflight-20261116-1529.txt`), 2087 MiB above it; THE MINIMUM IS THE NEWEST DRAW (headroom is falling, not resting) |
| MemAvailable / swap-in-use / engine-RSS trajectory per engine generation (the free columns belong to a process, not to the box) | DAY `20261116`: 2 generation(s) with headroom draws: pid 175316 — 11 draw(s), MemAvailable 18647 → 19297 MiB (Δ + 650 MiB, monotonically down over the last 2 draw(s)), swap in use 16062 → 16839 MiB, engine RSS 57048 → 56654 MiB; pid 438502 — 10 draw(s), MemAvailable 6618 → 4135 MiB (Δ − 2483 MiB, monotonically down over the last 10 draw(s)), swap in use 65 → 65 MiB, engine RSS 52711 → 55206 MiB / last 24 h: 2 generation(s) with headroom draws: pid 175316 — 22 draw(s), MemAvailable 19802 → 19297 MiB (Δ − 505 MiB, monotonically down over the last 2 draw(s)), swap in use 14102 → 16839 MiB, engine RSS 56869 → 56654 MiB; pid 438502 — 10 draw(s), MemAvailable 6618 → 4135 MiB (Δ − 2483 MiB, monotonically down over the last 10 draw(s)), swap in use 65 → 65 MiB, engine RSS 52711 → 55206 MiB / whole corpus: 15 generation(s) with headroom draws: pid 10597 — 53 draw(s), MemAvailable 17688 → 20492 MiB (Δ + 2804 MiB, monotonically up over the last 2 draw(s)), swap in use 24 → 16267 MiB, engine RSS 59088 → 56495 MiB; pid 175316 — 55 draw(s), MemAvailable 23516 → 19297 MiB (Δ − 4219 MiB, monotonically down over the last 2 draw(s)), swap in use 59 → 16839 MiB, engine RSS 48290 → 56654 MiB; pid 438502 — 10 draw(s), MemAvailable 6618 → 4135 MiB (Δ − 2483 MiB, monotonically down over the last 10 draw(s)), swap in use 65 → 65 MiB, engine RSS 52711 → 55206 MiB (12 not printed) |
| how much of the newest generation's headroom change its own RSS change explains | DAY `20261116`: newest generation pid 438502, `preflight-20261116-1007.txt` → `preflight-20261116-1529.txt` over 322 min: MemAvailable 6618 → 4135 MiB, engine RSS 52711 → 55206 MiB. ATTRIBUTED TO THE SAMPLED ENGINE: RSS grew 2495 MiB against a headroom fall of 2483 MiB — the sampled engine accounts for 100 % of it, residual 12 MiB / last 24 h: newest generation pid 438502, `preflight-20261116-1007.txt` → `preflight-20261116-1529.txt` over 322 min: MemAvailable 6618 → 4135 MiB, engine RSS 52711 → 55206 MiB. ATTRIBUTED TO THE SAMPLED ENGINE: RSS grew 2495 MiB against a headroom fall of 2483 MiB — the sampled engine accounts for 100 % of it, residual 12 MiB / whole corpus: newest generation pid 438502, `preflight-20261116-1007.txt` → `preflight-20261116-1529.txt` over 322 min: MemAvailable 6618 → 4135 MiB, engine RSS 52711 → 55206 MiB. ATTRIBUTED TO THE SAMPLED ENGINE: RSS grew 2495 MiB against a headroom fall of 2483 MiB — the sampled engine accounts for 100 % of it, residual 12 MiB |
| headroom trend of the newest generation, and what it projects against that floor | DAY `20261116`: newest generation pid 438502: 10 consecutive decreasing draws `preflight-20261116-1007.txt` → `preflight-20261116-1529.txt` lost 2483 MiB over 322 min = −462.7 MiB/h, mean cadence 35.8 min; PROJECTION (not a promise, one generation, n=10): at that constant slope the gate's own 2048 MiB floor arrives ≈271 min after `preflight-20261116-1529.txt`; in READINGS 4-30 further draws, because the run's own intervals span 9-61 min (9 interval(s), 9-61 min, mean 35.8), a 6.8x spread: v13 divided the minutes by that mean alone and printed the single number 7, which this run's interval range refutes by 6.8x / last 24 h: newest generation pid 438502: 10 consecutive decreasing draws `preflight-20261116-1007.txt` → `preflight-20261116-1529.txt` lost 2483 MiB over 322 min = −462.7 MiB/h, mean cadence 35.8 min; PROJECTION (not a promise, one generation, n=10): at that constant slope the gate's own 2048 MiB floor arrives ≈271 min after `preflight-20261116-1529.txt`; in READINGS 4-30 further draws, because the run's own intervals span 9-61 min (9 interval(s), 9-61 min, mean 35.8), a 6.8x spread: v13 divided the minutes by that mean alone and printed the single number 7, which this run's interval range refutes by 6.8x / whole corpus: newest generation pid 438502: 10 consecutive decreasing draws `preflight-20261116-1007.txt` → `preflight-20261116-1529.txt` lost 2483 MiB over 322 min = −462.7 MiB/h, mean cadence 35.8 min; PROJECTION (not a promise, one generation, n=10): at that constant slope the gate's own 2048 MiB floor arrives ≈271 min after `preflight-20261116-1529.txt`; in READINGS 4-30 further draws, because the run's own intervals span 9-61 min (9 interval(s), 9-61 min, mean 35.8), a 6.8x spread: v13 divided the minutes by that mean alone and printed the single number 7, which this run's interval range refutes by 6.8x |
| do the two free columns move in OPPOSITE directions when the engine generation changes? | DAY `20261116`: pid 175316 (`preflight-20261116-0719.txt`) → pid 438502 (`preflight-20261116-1007.txt`): REGIME FLIP — swap in use fell 16774 MiB (16839 → 65) while MemAvailable fell 12679 MiB (19297 → 6618) across the restart: the new process re-admitted what the old one held in swap and spent RAM headroom doing it, so the rate rules went quiet while the memory floor got closer / last 24 h: pid 175316 (`preflight-20261116-0719.txt`) → pid 438502 (`preflight-20261116-1007.txt`): REGIME FLIP — swap in use fell 16774 MiB (16839 → 65) while MemAvailable fell 12679 MiB (19297 → 6618) across the restart: the new process re-admitted what the old one held in swap and spent RAM headroom doing it, so the rate rules went quiet while the memory floor got closer / whole corpus: pid 10597 (`preflight-20261114-1603.txt`) → pid 175316 (`preflight-20261114-1640.txt`): RECOVERY — swap in use fell 16208 MiB while headroom ROSE 3024 MiB; pid 175316 (`preflight-20261116-0719.txt`) → pid 438502 (`preflight-20261116-1007.txt`): REGIME FLIP — swap in use fell 16774 MiB (16839 → 65) while MemAvailable fell 12679 MiB (19297 → 6618) across the restart: the new process re-admitted what the old one held in swap and spent RAM headroom doing it, so the rate rules went quiet while the memory floor got closer (12 older restart pair(s) not printed) |
| readings in this scope with no engine pid, excluded from every trajectory above | DAY `20261116`: 0 of 21 readings / last 24 h: 0 of 32 readings / whole corpus: 2 of 175 readings |
| readings whose `engine_rss_mib` exceeds the box's own `mem_total_mib` (an impossible field value: reported, named, and never used in arithmetic) | DAY `20261116`: none (every `engine_rss_mib` in this scope is at or below `mem_total_mib`) / last 24 h: none (every `engine_rss_mib` in this scope is at or below `mem_total_mib`) / whole corpus: 1 reading(s) carry an engine RSS larger than the machine's total memory and are excluded from every delta above: `preflight-20261111-0336.txt` reads 58929928 MiB against `mem_total_mib` = 61953 MiB |

**A projection that counts READINGS has a sampling cadence in its denominator (census v14, 2026-11-16, tick 206).** The trend row above answers two different questions and v13 answered the second one badly. `≈298 min after the newest draw` is a rate over a measured span and is quotable. `about 9 further readings` is that same quantity divided by a CADENCE, and v13 used the run's mean cadence without naming it. At the 2026-11-16 13:37 cut the newest generation's monotone fall spans 210 min over 8 draws, so the mean cadence is 30.0 min — and the intervals behind that mean are 28, 39, 35, 51, 9, 16 and 32 min, a 5.7x spread with a 9-minute interval inside it, because these readings are taken by ticks and reports, not by a scheduler. The projected 298 minutes is therefore 5 readings at the run's slowest interval and 33 at its fastest, and v13's printed `9` was neither bound: it was the mean assumption wearing the costume of a measurement. This is the same defect the producer rules already forbid one level up (MiB/s computed over a nominal 6 s loop instead of the measured 6.17 s, tick 14.11) and the same one the band rows were corrected for twice (scope, then denominator): a rate or a conversion may only be quoted with the window it was divided by. The row now prints the interval count, the min-max range and the mean beside the count, states the count as a band whenever the intervals are not uniform within `MEM_INTERVAL_FLAT_RATIO` = 1.5, and prints NO count at all when the monotone draws share timestamps — a zero interval must never reach a denominator. Nothing in the gate moved: the projection describes when the gate's own `mem-available-low` floor would be reached at the observed slope, and the floor, the ceiling set and the rule order are byte-identical to the run that produced every stored verdict in this table.
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
counter (30 of 30 launchable windows carrying the statistic) counts COVERAGE, not
support for a ceiling, and reaching 30 would not change that conclusion.

