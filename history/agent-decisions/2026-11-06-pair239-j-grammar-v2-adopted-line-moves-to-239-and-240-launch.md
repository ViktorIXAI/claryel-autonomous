# Decision: pair-239 — J ranking repair with grammar v2 lands clean; 0.0.2.39 ADOPTED as the control line; C-ex6-02 exposed as a bank defect; 0.0.2.40 re-derives J membership from the prompt's own filter rule (2026-11-06)

## Context

pair-239 (arms `l37r*` vs `l39r*`, P2005/Basalt, bank v6.1 `f4553aab304f60d7`, three matched seeds,
77/77 results AND ledger rows per arm, 0 empty/engine-error/zero-prompt/engine-stalled rows,
seed-0 control resumed fresh after one killed first attempt — `*.dead1` aside, 77 unique keys, no
duplicate `(task,rep)` rows) measured contour `0.0.2.39` — the J ranking repair re-landed with
grammar v2 — against the adopted `0.0.2.37`. Pre-registered rule (`PAIR-238-V61.md`, written before
any `l*` row): adopt iff (a) `J-ex6-02` strict-fails in ≥1 control seed (chronic target), (b) the
candidate passes every control-failed seed with `contour:...v239_j_rerank_by_prompt` on every
converted row, no strict-pass regression carries a 2.39 event (mis-sort guard), the adopted B repair
fires identically in both arms, the A arithmetic fires nowhere, (c) candidate not >2 cells below
control.

## Evidence

- Headline: 62/63/64 (63.0) vs 64/62/66 (64.0) = **+1.0 cells, below the ~2-cell resolution floor**
  (exactly the maximum the chronic single-cell target allows by construction); pooled 5W/2L p=0.453;
  flips 8 vs 7 of 71.
- Rule (a): `J-ex6-02` strict-failed 3/3 in control (`order_partial`, content 0.0/0.0/0.125) — the
  chronic cell was live, measurable.
- Rule (b): 3/3 conversions, **every converted row carries the v2 re-rank event**; `ptok=304` and
  `model_calls=2` identical per seed across arms — zero added model tokens. Zero strict-pass
  regressions with a 2.39 event. `contour:v20_j_id_norm_v239_j_membership_untouched` ×2 are the same
  gate's refusal path on failing `J-ex6-01` rows (identical scores both arms, zero delta) — stated
  explicitly under the clean-pattern clause. `v235_b_table_total` ×3 identical in both arms
  (`B-ex6-06` 3/3 both, `ptok=260`). Zero `v233_a_tariff_table` events anywhere — the
  (2,33)/(2,38) pin held.
- Rescore from published sanitized bytes: 18 joins, 0 blanks, 0 mismatches. Loop-D `_loop_rows`
  storage gap persists (third pair) — recorded.
- Energy: control 8.14/4.89/4.49 Wh vs candidate 5.41/4.91/5.00 Wh; matched windows inside noise, the
  seed-0 control window inflated by queue start on a cold-ish serve (median seconds identical); the
  repair itself costs zero tokens, energy plan-identical by construction.

## Decision

**`0.0.2.39` ADOPTED as the new control line** (from `0.0.2.37`). The pre-registered
evented-conversion pattern held exactly; the +1.0 arm mean is published as sub-floor and not quoted
as evidence — the +3 attributable conversions plus event-less lottery jitter is the whole delta.
`J_RERANK_V2 = contour_at_least(2, 39)` inherits into future arms (adopted features inherit;
measured-negative ones stay pinned to their own stamp — 2.30/2.31/2.36/2.38 and the unresolved
2.32/2.34 remain frozen). The 2.32 v1 grammar stays byte-identical at its own stamp.

## Bank finding recorded (owner-commanded remediation only)

`C-ex6-02` (chronic C stable-fail, 0/12) is a **bank defect**: executing the bank's own snippets, A
(`sorted({3,2,1,1})`), C and D all deterministically print `[1, 2, 3]`; the gold `want=['C']` excludes
two semantically-correct options. The model's 0/12 "failures" are correct answers to the task as
written. Logged (like the `K` value-shape and `B-ex6-04` defects); no contour mechanism will chase a
cell whose gold contradicts the task text. Group 1's remaining C cells are content lotteries with
byte-identical failure draws across arms.

## Next: 0.0.2.40 — J membership grammar v3, pre-registered before any `m*` row

The pair surfaced the next chronic class itself: `J-ex6-01` failed seeds 0-1 in BOTH arms with
byte-identical `["skuC","skuB"]` — `skuB` violates the prompt's own filter `срок<=10` (top-2 cheapest
among `срок<=10` is `skuC, skuA`); `J-ex6-06` failed seed 0 in both arms with an empty JSON list. The
selection rules are stated in the prompt in full (`среди срок<=10`, `Топ-2 самых дешёвых` + tie
chain; `Отбрось score<70`), so 2.40 re-derives the id SET from those segments over the same table
parser as grammar v2: stem-matched column names (genitive forms), top-K with fully-stated tie chain,
every ambiguity/formula/unknown-column refusing touch-nothing; then the inherited v2 re-rank orders
the set; zero model tokens, reference never read, sub-2.40 stamps byte-identical. Coverage stated
before launch: 2 of 6 single-shot J prompts parse, mis-derivations 0 by replay over the published
pair-239 J rows (6 failing rows convert, zero regressions), CI-pinned as `gate_v54`. Control for
pair-240 is the new line `0.0.2.39` (`m39r*` vs `m40r0..2`); the chronic-target rule (a)/(b)/(c) is
pre-registered verbatim in `PAIR-239-V61.md` before the first `m*` row.
