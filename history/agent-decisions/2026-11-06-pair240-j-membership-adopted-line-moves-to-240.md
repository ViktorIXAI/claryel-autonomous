# 2026-11-06 pair-240: J membership adopted — line moves to 0.0.2.40; pair-241 targets the chronic A-ex6-03

## Context

Third J pair on bank v6.1 (`f4553aab304f60d7`), P2005 Basalt endpoint, three matched seeds,
control = the adopted `0.0.2.39` (`m39r*`), candidate = `0.0.2.40` (`m40r*`) re-deriving the J id
SET from the prompt's own filter/top-K/tie-chain rule (pre-registered in `PAIR-239-V61.md` before
any `m*` row; coverage recorded in `gate-versions.log` 18:23Z: derives-gold 4/7 J tasks, refuses
3/7, zero derived-set != gold).

## Evidence (pair-240/)

- Chronic target live: `J-ex6-01` failed seeds 0-1 in BOTH the rule and the data — control draws
  the byte-identical `["skuC","skuB"]` (skuB violates `срок<=10`), candidate converts both at
  identical `ptok=312`/`calls=2` with `contour:...v240_j_membership_from_prompt`; `J-ex6-06`
  converts from the empty seed-0 draw; `J-ex6-01` seed 2 (model was right) re-states the rule set
  with the event, no score delta.
- Mis-derivation guard: zero strict-pass regressions carry a 2.40 event across 231 paired cells;
  the losing `J-ex6-03` seed carries `j_id_norm` only (formula rule, membership never attempted).
- Inherited mechanisms identical in both arms (`J-ex6-02` re-rank ×3, `v235_b_table_total` ×3);
  A arithmetic zero fires everywhere (pin holds).
- Arm means 64.3 vs 64.3 (+0.0, far below the ~2-cell floor — never quoted as reason);
  stability map: J-ex6-01 1/3→3/3, J-ex6-06 2/3→3/3.
- Energy matched-inside-noise (control 6.20/5.35/5.13, candidate 4.86/4.71/5.61 Wh); rescore from
  published bytes: 30 joins, 0 blanks, 0 mismatches; all arms 77+77 rows with zero quality defects.

## Decision

**ADOPT `0.0.2.40` as the new control line.** The pre-registered rule held exactly; the flag is
registered in `CONTOUR_FEATURES` and stays byte-identical below 2.40 (gate_v49 matrix pins 2.39
without membership). Group 2 (J order + J membership) is now closed on the line.

## What is NOT closed

- Group 1 C set lotteries: live, but per-option content lotteries with no deterministic grammar
  proven; per the map, the next group-1 mechanism must be per-option-grounded — selection (2.31)
  and form contracts are frozen and must not be re-chased.
- `A-ex6-03` chronic 0/6 (both arms, `fields_mismatch:net,social,tax`) and `B-ex6-04`
  0/6 (`fields_mismatch:start_date,...`): outside the proven grammars; the 2.34 B-field
  mechanism stays frozen at its stamp (measured negative), the A arithmetic stays pinned to
  (2,33)/(2,38) with coverage 1/10.
- `C-ex6-02` / `K-ex6-03`: bank defects, owner-commanded clarification pending; no contour chase.

## Next (pair-241, pre-launch gate)

Candidate direction: extend the A tariff-table grammar (v2 of the 2.33 mechanism) to reproduce
`A-ex6-03` — a CHRONIC live target, which is exactly what the two UNMEASURED A pairs (233 zero-fire,
238 no live cell) lacked. Registration rule: dry-run over the published 0/6 bytes must convert
every A-ex6-03 loss AND change zero other published A-row verdicts (the gate_v50 replay contract,
extended), coverage restated honestly BEFORE any n* row; the flag re-lands only from 2.41 and stays
pinned out of every earlier stamp. If the dry-run refuses, no pair is launched and the class is
reported as grammar-capped, not re-chased.

GATE RESULT (same session, after publication): the dry-run never reached grammar work — the target
itself is defective. `A-ex6-03`'s printed rules (`22% от базы (gross), но не более 6100`, `19% от
(gross − соцвзнос − вычет 1200), не менее 0`) execute deterministically to `social=2090.0,
tax=1179.9, net=6230.1`; the bank gold is `social=1254.0, tax=616.74, net=7629.26`, and 1254.0
implies a 13.2% rate the prompt never states — no reading of the printed rule reaches the gold.
Five of the six published arms answered the faithful `social=2090.0` and scored 0. **A-ex6-03 is
a bank defect** (third in the queue after `C-ex6-02` and `K-ex6-03`); a no-contour arm executing
the task text would score 0 too, so it is unmeasurable by construction and no contour mechanism
may chase it. **pair-241 does not launch**: with A-ex6-03/C-ex6-02/K-ex6-03 bank-capped, B-ex6-04
owned by the frozen-negative 2.34 class, and group-1 `C` lotteries lacking any proven per-option
grammar, line `0.0.2.40` is at the bank's ceiling. Next actions, in order: owner-commanded bank
clarification (A-ex6-03 re-gold, same queue as C-ex6-02), and design + dry-run of a
per-option-grounded group-1 mechanism over published bytes before any stamp is spent.
