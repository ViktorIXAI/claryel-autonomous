# 2026-11-06 13:40 CET — pair233: the threshold-table repair never fired; 0.0.2.33 is not adopted

## Context

Pair `pair233` (run ids `f29r0..f29r2`, `f33r0..f33r2`) measured contour 0.0.2.33 (A threshold-table
arithmetic: tariff-chain map values and total recomputed by code from the prompt's own rows) against
the adopted control 0.0.2.29 on bank v6.1, three identical seeds, arms alternating per seed. All six
arms: 77/77 rows, exit 0, no `engine_error`, no zero-token rows, bank sha `f4553aab304f60d7` (v6.1
generated workspace), run-record stamp == behavior (2.29/2.33), answers joined from sibling
`results-*.jsonl` for every rescore. One control attempt (`f29r0` first pass) was killed mid-series
and moved aside as `*.dead1`; the published rows are the fresh full run.

## Measurement

- Control 60/61/64 (mean 61.7), candidate 63/62/64 (mean 63.0): **+1.3 cells** — the same delta pair232
  produced for a different feature.
- Noise floor of this exact comparison: ~2 cells (12 of 231 same-stamp cells flip, mean moves 1.4).
- Per-seed sign tests: 3W/0L (p=0.25), 1W/0L (p=1.0), 1W/1L (p=1.0); pooled 5W/1L p=0.22. Resolves nothing.
- **Mechanism evidence: zero fires.** The ledger `events` column contains no `v233_a_tariff_table` hit
  in any of the three candidate seeds. All four flipped cells (A-ex6-00, A-ex6-08, H-ex6-01, H-ex6-04)
  therefore carry no mechanism event: they are seed/endpoint noise. The pair could not have measured
  the change at all.
- Counterfactual replay on saved bytes (recorded as a replay, not a measurement): the 2.33 grammar
  parses 1 of 9 A prompts (the designed fail-closed behaviour), no-ops byte-exactly on already-correct
  answers, and run over the failed control seed of A-ex6-00 (`fields_mismatch:surcharges,total`) it
  recomputes the map and total from the prompt table and would have converted exactly its target class.
  In the candidate arm the model happened to answer that cell correctly in all three seeds, so the
  repair never had work to do.
- Independent rescore of all flipped cells from saved answer bytes with the pinned scorer: 0 mismatches
  of 24 cell-seed-arm comparisons.
- Energy (board draw windows): control 6.49/4.91/5.11 Wh, candidate 4.99/4.24/4.45 Wh. With zero fires
  and equal call counts (327 vs 326) there is no mechanism cost to measure.

## Decision

**Not adopted.** +1.3 is below the measured floor, and unlike pair232 the arm delta contains zero
on-target cells. Stated plainly: this pair did not show that 0.0.2.33 helps.

The pair does produce one scoreboard-level number: a +1.3 mean shift on an arm whose new mechanism
executed zero times is a direct empirical lower bound on pure resampling, fully consistent with the
~2-cell floor. Two consecutive pairs landing at exactly +1.3 for different (or unfired) features is
what the floor, not the features, produces.

`A_TABLE_ARITH` is frozen to its own stamp: `CONTOUR_REVISION == (2, 33)`, registered in
`CONTOUR_FEATURES` for the record, listed in `UNADOPTED_FEATURES` with `a_table_arith`, and the
`gate_v49_feature_adoption_test.py` flag matrix pins that 0.0.2.34 inherits neither 2.32 nor 2.33.
Adopted control line remains **0.0.2.29**.

## Next step (executed)

0.0.2.34 built from the still-untried half of the same UNSTABLE-CELLS group (group 3,
`fields_mismatch`/`missing`): **B field completeness** — extraction fields recomputed by code from the
prompt's own data block, two narrow grammars (config `key: value`/`- item` block = B-ex6-03 shape;
embedded-JSON echo-with-count rebuild = B-ex6-05 shape), required names read only from the prompt's
own JSON spec, any ambiguity or extra model key refuses the whole repair, reference never read.

**Launch correction (next automated run, 13:27 CET, host clock):** the sentence above claimed a
~13:45 launch that had NOT happened — at 13:25 CET no `g*` artifact and no systemd unit existed. The
launch was performed by the follow-up run at 13:27:55 CET as `parb-pair234.service`
(`run_pair234.sh`, arms alternating per seed, GPU sampler already active), first arm log line
`PGR: release 0.0.2.29, contour behavior 2.29`.

K is deliberately excluded and named as a bank problem, not a contour problem: the failing seeds of
K-ex6-03 need value SHAPES (`FREE_SHIPPING: ?`) the prompt never states — guessing them is the 2.30
mistake (repairing shape over ambiguous content). B-ex6-04 (prose letter) and B-ex6-06 (markdown
table) grammars are recorded as separate future candidates, not bundled.

Pre-launch proof (`gate_v51_b_fields_test.py`, 19 checks): synthetic grammars with invented field names
reproduce; conflicted keys, extra model keys, unreadable required names, prose answers, two drop
instructions and unparseable embedded JSON all refuse; the two bank targets repair into answers the
frozen scorer accepts; the other 5 bank B tasks refuse; no-op safety is byte-exact. Replay over the 42
stored B answer bytes from pair-233: 0 changes, 0 degradations. Paired arms `g29r*` (0.0.2.29) vs
`g34r*` (0.0.2.34) launched ~13:45 CET the same hour.

Honest expectation written before the run: group 3's B cells fail ~1 seed in 6, so a 3-seed pair can
offer this repair only 1-2 opportunities; if the candidate model again answers correctly first, the
pair lands unfired again and only the fire/flip table is quotable — the mean is not, at this coverage.
