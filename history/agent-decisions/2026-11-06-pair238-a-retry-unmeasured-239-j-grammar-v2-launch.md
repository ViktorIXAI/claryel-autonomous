# Decision: pair-238 — the A retry lands without its target (UNMEASURED); 2.38 pinned out of the line; 0.0.2.39 re-lands the J ranking repair with grammar v2 on a chronic target (2026-11-06)

## Context

pair-238 (arms `k37r*` vs `k38r*`, P2005/Basalt, bank v6.1 `f4553aab304f60d7`, three matched seeds,
77/77 results AND ledger rows per arm, 0 empty/engine-error/zero-prompt/engine-stalled rows) measured
contour `0.0.2.38` — the re-landed 2.33 A threshold-table arithmetic — against the adopted
`0.0.2.37`. Pre-registered rule (PAIR-237-V61.md, written before any `k*` row): adopt iff
(a) `A-ex6-00` strict-fails in ≥1 control seed (no on-target cell = UNMEASURED, flag stays frozen),
(b) every converted row carries `contour:v233_a_tariff_table`, no other 2.38-gated event anywhere,
the adopted B repair fires identically in both arms, (c) candidate not >2 cells below control.

## Evidence

- Headline: 62/62/66 (63.3) vs 62/60/65 (62.3) = +1.0 cells, BELOW the ~2-cell resolution floor;
  pooled 4W/1L p=0.375. Flip counts 9 vs 10 of 71.
- Rule (a) failed: `A-ex6-00` strict-passed all three control seeds (prompt tokens 703/433/703
  identical to the candidate rows — same contour path, the model simply answered correctly that draw).
  The pair-237 loss that motivated 2.38 was a lottery: across the six-seed map and four control pairs
  the cell sits at 14/21, flipping both directions.
- The mechanism fired once — `contour:v233_a_tariff_table` on the target task in candidate seed 2
  (`ptok=703, calls=3`, zero extra tokens/calls), a seed where its repaired row passed and control had
  not failed. Mechanism activity, no measurement opportunity: the pair-233 zero-opportunity failure
  mode for the second time.
- Rule (b)'s identity clause held: `contour:v235_b_table_total` ×3 in BOTH arms on exactly the
  `B-ex6-06` rows; candidate-only 2.38 event set contains nothing else. All cell flips (`H-ex6-04`,
  `H-ex6-01` seeds, `J-ex6-06`, `K-ex6-03`) carry no 2.38 event.
- Rescore: all 5 discordant cells re-scored from published bytes, 10 joins, 0 blanks, 0 mismatches.
- Energy: 4.68–9.27 Wh per window; the seed-0 candidate window is inflated by two serve-slow B rows
  (68.7 s / 29.6 s, no stall flags, both passed); matched windows 5.07/4.79 and 4.74/4.68 — noise.

## Decision

**`0.0.2.38` NOT adopted; the pair is UNMEASURED by its own pre-registered rule.** The control line
stays `0.0.2.37`. `A_TABLE_ARITH` is re-pinned from `CONTOUR_REVISION == (2,33) or
contour_at_least(2,38)` to `CONTOUR_REVISION in ((2,33),(2,38))`: an unadopted, never-on-target
experiment must not inherit into 2.39+ through an `at_least` floor (the same inheritance discipline
that froze 2.30/2.31/2.36); `gate_v49` now pins the 2.38-ON / 2.39-OFF matrix. The mechanism itself
is not retired — a future re-land is legitimate only as that stamp's single candidate change with a
fresh pre-registered rule and a CHRONIC target.

## Process rule recorded

Second zero-opportunity pair in the series (2.33 at pair-233, 2.38 at pair-238). A pair hypothesis
must be pinned to a **chronic** cell — stable-fail in the six-seed map or 0/N in both arms of the
preceding pair — never to one pair's lottery loss. This rule decided the next candidate.

## Next: 0.0.2.39 — the J ranking repair re-landed with grammar v2, pre-registered before any `l*` row

Group 2 (`order_partial`) is the newest live class: `J-ex6-02` is chronic (stable fail in the six-seed
map, 0/6 across BOTH pair-238 arms, every loss the right id set in the wrong order), `J-ex6-06`
flipped again this pair. Grammar v2 closes exactly the four v1 refusal gaps the published bytes name
(ё adjective; genitive/primary-clause column forms + `при равенстве <col>` lead; unique-prefix filter
names; explicit `A*B` product key with a fully-stated tie chain), keeps every fail-closed refusal
(formulas, ambiguity, unknown tie columns, membership), reproduces 6/7 J prompts with mis-sorts 0,
and replays over this pair's published rows converting all six `J-ex6-02` losses and one `J-ex6-06`
flip with zero regressions (`gate_v48` 36 checks, CI-pinned replay).

The pre-launch smoke caught a real wiring bug before paying for an arm: the decorated-ids repair
(`j_id_norm`) early-returned BEFORE the ordering re-rank, so a dict-shaped J answer stored unrepaired
(`smk39j`: `J-ex6-02 c=0.00`, no re-rank event). From 2.39 the two repairs compose with both events;
at 2.32 the early return stays byte-identical (`gate_v49`, 31 checks, pins both sides). Resmoke
`smk39j2`: `J-ex6-02 c=1.00` with `contour:v20_j_id_norm_v239_j_rerank_by_prompt`.

Adoption rule for 2.39 itself is pair-239's, pre-registered in `PAIR-238-V61.md` (chronic-target
clause (a), evented-conversion + mis-sort-guard + no-A-fire clause (b), −2-cell bound (c)). Arms
`l37r*` vs `l39r*` launched 17:45 CET via `parb-pair239.service`; GPU sampler `parb-gpu-samp2` active.
