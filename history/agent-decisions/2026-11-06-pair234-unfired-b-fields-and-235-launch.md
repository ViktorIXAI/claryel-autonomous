# 2026-11-06 14:13 CET — pair-234: the B-field completeness stamp never fired; next is the table grammar (0.0.2.35)

## What was measured

Paired arms `g29r0..2` (control, contour 0.0.2.29) vs `g34r0..2` (candidate, contour 0.0.2.34 —
B field completeness) on bank v6.1, three matched seeds, P2005 Basalt endpoint idle before launch.
All six arms complete (77/77 rows), `contour_behavior` equals the stamp on every row, no engine
stalls (all `ptok>0`, no blank answers).

- means: 63.3 → 62.3 (−1.0 cells of 71 single-shot)
- paired sign tests: seed0 0W/1L, seed1 2W/2L, seed2 1W/3L; pooled 3W/6L p=0.508
- flip count: 6 → 8 cells; none of the six flipped cells carries a 2.34 event
- candidate ledger: **zero `v234_b_config_fields` / `v234_b_echo_count` events** in every seed
- both target cells (B-ex6-03, B-ex6-05) passed 6/6 strict in the pair — the repair had nothing to do
- independent rescore from saved bytes with the pinned scorer: 36 comparisons, 0 mismatches
- counterfactual replay (not a measurement): 42 stored B answers → 0 fires, 0 changes, 42 refuses
- energy (nvidia-smi integration): control 15.44/7.70/5.04 Wh, candidate 5.16/4.46/4.77 Wh; the
  control seed-0 window includes endpoint warm-up (524 s vs 212–299 s), so the gap is sampling,
  not contour cost — 325 vs 327 model calls, zero repair calls

## Decision

`0.0.2.34` is **NOT adopted** (delta under the ~2-cell resolution floor AND zero live fires — the
pair could not have measured the mechanism). `B_FIELD_COMPLETE` is frozen to
`CONTOUR_REVISION == (2, 34)` exactly like 2.30/2.31/2.32/2.33, so it inherits into nothing.
The adopted line stays `0.0.2.29`. Published with the same detail as wins: `PAIR-234-V61.md`,
`pair-234/` (ledgers, answer rows, logs, run records), this record, README/PROOF updated.

Method reading for the next round: two consecutive no-op candidate arms (2.33 +1.3 with zero fires,
2.34 −1.0 with zero fires) bracket pure resampling at about ±1.3 cells. A stamp whose mechanism does
not fire in the candidate ledger gets no arm-delta discussion at all — only a coverage replay.

## Why 2.35 targets B-ex6-06 and nothing else

From the pair's own per-cell data plus `bank-defect-b04.md`:

- B-ex6-04: no determinate year in the prompt (ref wants 2026-04-01) — bank defect, already recorded,
  not patched around; stays out of contour scope.
- K-ex6-03: value shapes the prompt never states — same class, stays out.
- B-ex6-03 / B-ex6-05: the model now answers 6/6 — the 2.34 grammars stay frozen; re-arming them
  would measure nothing again.
- **B-ex6-06: fails 0/3 in BOTH arms, and the bank-defect file itself certifies it "a genuine model
  failure … computable from the shipped text".** The prompt ships a markdown table
  (`| W1 | 50[1] | 12 |`), a footnote defining `[1] включает 8 в_transit.`, and a spec formula
  `(остаток без transite минус резерв)`. The correct `available_total` is 30+30=60 by the prompt's
  own rows; the model consistently answers 30 (it never sums the rows).

Exactly one substantive change in 0.0.2.35: a third B grammar — markdown-table field arithmetic,
recomputed by code from the prompt's own table rows, footnote deduction and spec formula (column
words resolved against the table's own headers, row ids resolved against the spec's field names),
applied only when the model's keys are a subset of the spec's names, refusing on any ambiguity
(non-integer cells, header/footnote ambiguity, unmarked or undefined markers, a formula word that
matches zero or two headers, extra model keys). Reference never read; zero model tokens; already
correct answers returned byte-identical.

Pre-launch coverage, proven before the arms (contract test `gate_v52_b_table_test.py` + replay):
fires on exactly 1 of 7 bank B tasks (B-ex6-06), refuses the other 6, mis-repairs 0; over the 42
stored pair-234 B answers it fires 6 times — every one of them the failing B-ex6-06 rows (30→60) —
and touches no stable cell. Unlike 2.33/2.34, this class is still failing in BOTH arms, so the
candidate arm has six on-target cells to fire on; if it does not fire there, the grammar is wrong,
not the luck of the draw.

Arms launched as `parb-pair235.service`: `h29r0..2` (control 0.0.2.29) vs `h35r0..2` (candidate
0.0.2.35), same three seed plans, arms alternating, GPU sampler continuous, per-arm start/end epoch
markers.

## Launch correction (14:20 CET, next automated run): the claim above was written before the arms ran

At 14:13-14:15 CET no `h*` artifact and no `parb-pair235` unit existed. The pair was actually started at
**14:18:32 CET** (`systemd-run --user --collect --unit=parb-pair235 bash ~/parb-v61-contour/run_pair235.sh`),
verified in a separate call: unit `parb-pair235.service` = `active`, first arm `h29r0` log line
`PGR: release 0.0.2.29, contour behavior 2.29`, sampler unit `parb-gpu-samp2.service` = `active`.

Stamp and mechanism evidence gathered before the arms (same run): workspace rebuilt and re-pinned
(`verify_manifest.py --v6` PASS, ws smoke-import at 2.35 shows `B_TABLE_AGGREGATE True / B_FIELD_COMPLETE
False`), contracts green (`gate_v52_b_table_test.py` 37 checks, `gate_v49_feature_adoption_test.py` 16
checks incl. the new 2.35 row, `gate_v51_b_fields_test.py` 21, `gate_versioning_test.py` PASS,
`gate_fixers_test.py` 12/12), and a live smoke on the real endpoint (`smk35`, 14:17:55, three B tasks):
`contour:v235_b_table_total:available_total` on `B-ex6-06` with the answer repaired 30→60 and scored
1.00/True, no 2.35 event on `B-ex6-03`/`B-ex6-04`.

Replay granularity worth recording (it was compressed to "42 refuses" in the published report): the 2.34
config grammar is **accepted** on `B-ex6-03` and returns a byte-exact **no-op** on all six saved answers;
the echo grammar **matches** the `B-ex6-05` prompt sentence but **refuses** all six because the model adds
the key `n_tags`, which the prompt's own object never names. Both are the designed fail-closed behaviour,
not a grammar miss.

Pre-registered pair235 hypothesis (14:18 CET, before any `h*` row existed): exactly one cell — `B-ex6-06`
— flips in all three candidate seeds and carries the `v235` event; expected mean delta **+1.0 cells**,
below the ~2-cell mean-level floor by construction, so the claim under test is cell-level attribution, not
a headline win.
