# Decision: pair-237 — the B table repair passes its all-or-nothing rule; 0.0.2.37 becomes the control line; 2.38 re-lands the A threshold arithmetic (2026-11-06)

## Context

pair-237 (arms `j29r*` vs `j37r*`, P2005/Basalt, bank v6.1 `f4553aab304f60d7`, three matched seeds,
77/77 results AND ledger rows per arm, 0 empty/engine-error/zero-prompt/engine-stalled rows) measured
contour `0.0.2.37` — the adopted 2.29 behaviour plus the re-landed 2.35 B markdown-table aggregation —
against `0.0.2.29`. Pre-registered rule (PAIR-236-V61.md, written before any `j*` row): adopt iff
(a) `B-ex6-06` strict-fails 3/3 in control and strict-passes 3/3 in candidate, (b) every converted row
carries `contour:v235_b_table_total` and no other 2.37-gated event fires anywhere, (c) candidate not
>2 cells below control; otherwise the flag freezes again at 2.37.

## Evidence

- Headline: 62/63/66 (63.7) vs 62/59/63 (61.3) = **+2.4 cells**; per-seed sign tests 1W1L / 5W1L /
  4W1L, pooled 10W/3L p=0.0923. Only the +1.0/seed carried by the target cell is attributable; the
  rest is the series' event-less flip background and is explicitly NOT credited to the repair.
- Rule (a) held exactly: `B-ex6-06` `...` -> `PPP`, the chronic 0/12 profile (control notes
  `fields_mismatch:available_total`), candidate answers 1.00/True note-free.
- Rule (b) held exactly: all three converted rows carry `contour:v235_b_table_total:available_total` at
  `ptok=260, model_calls=2` identical to the control rows (zero extra tokens, zero extra calls); the
  candidate-only contour-event set is that type plus one `contour:v19_d_order_to_steps` on a loop-D
  task — an inherited 2.19 feature preceded on the same row by its own `gate:order_violation` (model
  resample, fireable at any stamp, cell excluded from single-shot scoring). No other 2.37-gated event
  anywhere.
- Rule (c) held: +2.4, not below.
- Off-target flips (all event-less, no mechanism credited): A-ex6-00 +2, I +1, C-ex6-00 +1, H-ex6-01 +1,
  J-ex6-06 +1; losses K-ex6-03 (`value:FREE_SHIPPING`, documented bank value-shape defect), F-ex6-00
  and H-ex6-03 (group-4 lotteries, class closed).
- Rescore: all 13 discordant cells re-scored from published answer bytes, 26 joins, 0 blanks,
  0 mismatches.
- Energy: 4.36–10.38 Wh per arm-window, mean power 72.8–102.8 W; matched seed-2 windows 4.89 vs
  5.00 Wh — the zero-token repair costs nothing measurable.

## Decision

**`0.0.2.37` ADOPTED; the control line moves from `0.0.2.29` to `0.0.2.37`.** The pre-registered
all-or-nothing attribution rule passed exactly; the headline +2.4 is published with the honest split
(+1.0/seed attributable, the rest noise), and adoption rests on deterministic cell-level attribution,
not on the mean. `B_TABLE_AGGREGATE = CONTOUR_REVISION == (2, 35) or contour_at_least(2, 37)` is now
adopted-line behaviour; the 2.35 measurement entry stays frozen at 2.35 byte-identically. Every
measured-negative behaviour (2.30/2.31/2.36) and every unresolved-without-conversion feature
(2.32/2.34) remains pinned to its own stamp (`gate_v49`, 21 checks).

## Next: 0.0.2.38 — re-adoption of the 2.33 A threshold-table arithmetic, pre-registered before any `k*` row

Group 3 (`fields_mismatch`/`missing`) is the newest live class after group 4 closed, and this pair
supplied the live on-target cells pair-233 never got: the adopted line lost `A-ex6-00` in seeds 1-2
with `fields_mismatch:surcharges,total`. Replaying the frozen 2.33 grammar over exactly those published
bytes repairs both to 1.00 strict with its `v233_a_tariff_table` event and no-ops the two passing
candidate bytes (`gate_v50`, 25 checks, pins the replay and the OFF state at 2.37). Bank coverage
before launch: reproduces 1/9 A tasks, refuses 8, mis-computes 0. `0.0.2.38` = adopted line +
`A_TABLE_ARITH` re-land, nothing else.

Pre-registered pair-238 rule (arms `k37r*` vs `k38r*`, three matched seeds, control = the new adopted
`0.0.2.37`): adopt iff (a) `A-ex6-00` strict-fails in >=1 control seed — without a live on-target cell
the pair is UNMEASURED, the flag stays frozen at 2.38, zero-fire is not a pass (the pair-233/234
lesson); (b) the candidate passes every control-failed seed with `contour:v233_a_tariff_table` on each
converted row, no other row anywhere carries a 2.38-gated event, and the adopted `B-ex6-06` repair
fires identically in both arms; (c) candidate not >2 cells below control. Off-target flips are always
stated as noise; a converted row without its event, an off-target fire, or a non-converting target
freezes the flag at 2.38 and the line stays `0.0.2.37`.
