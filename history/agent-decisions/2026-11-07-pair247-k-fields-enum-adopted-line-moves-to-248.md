# 2026-11-07 — pair-247: K fields-gate key enumeration MEASURED and ADOPTED; line moves to 0.0.2.48

Decision by the autonomous contour loop under the owner's 2026-11-07 delegation ("decisions are
yours... version every element"). Recorded here because it moves the adopted line.

- **What was fixed is a contour bug, not a model gap.** `want_fields` derives the required
  `KEY:` set by scanning the prompt for UPPERCASE tokens followed by a colon. In a K prompt the only
  such tokens are the instruction's own example (`вида FIELD: значение`) plus a parenthetical value
  form, so `K-ex6-03`'s required set was `[FIELD, FREE_SHIPPING]`, the contour's own hint told the
  model to use the literal placeholder `FIELD` as a key, and the gate then reported `fields_ok`.
  The published bank-v6.2 line strict-fails that cell **9/9** (code `missing`, content 0.25) while
  every value the gold needs is printed in the prompt. The contour was destroying its own target.
- Pre-registered rule (REVIEW-INBOX 2026-11-07 11:33 CET, `run_pair247.sh` header, commit `639f2f5`):
  ADOPT iff (a) live target — >=1 control K-ex6-03 cell strict-fails with a `missing` code, (b) >=1
  conversion carrying `contour:v48_fields_enum_from_prompt:4`, (c) guards clean. Otherwise freeze
  `K_FIELDS_ENUM` to exactly (2,48).
- Measured (arms t47r22/t48r22/t47r23/t48r23/t47r24/t48r24, bank v6.2 `3c866ea7daae611c`, ws copy
  `d1e8d11df5840dcc`, contract v6.2 `c8c0c7dd114dfc32`, sp1 reps 22/23/24, idle endpoint, harness
  `639f2f54ee74` in every run record): (a) **3/3** live-target cells; (b) **3/3 evented
  conversions** (K pool 9/12 -> 12/12, every converted row carries the v48 event and the model's own
  values under the real keys); (c) **all guards clean** (zero v48 events in a control arm, zero
  outside the target task, zero candidate K regressions, zero frozen-band events, zero loop P->F,
  zero engine stalls, zero blank joined answers, adopted-family parity within seed noise).
- Cost: zero extra model calls — naming the right keys in the first hint is enough (+8 ptok,
  +5..11 ctok per converted cell). Serve-board energy control 19.55 Wh vs candidate 17.41 Wh; not
  attributed (the difference tracks unrelated draw length, candidate made 400 model calls vs 414).
- Full-pool movement (204 -> 203, 5W/6L, exact sign p=1.0000) sits at the published noise floor and
  is **not** the adoption basis — the basis is the pre-registered cell-level rule, and the whole
  on-target effect is evented.
- New experimental fact for the queue: the bank's K category is now strict-clean (12/12). The
  remaining chronic cells are of different classes — `B-ex6-04` is a **published bank defect**
  (gold year never stated in the prompt; bank v6.3 next), `A-ex6-03` is a genuine arithmetic
  near-miss (fixing it for the model would be answer synthesis — closed), and the H cells are
  content-biased lottery where resampling is already spent (pair-246 lesson).
- Tooling published with the pair: `scripts/pair_guard_census.py` — a reusable pre-registered-pair
  judge (join integrity with fail-closed blank-answer abort, candidate-event census per side and per
  task, frozen-band parity, adopted-family parity, monotonicity guard, per-target-cell attribution
  with per-cell cost, pooled exact sign test, energy-window file). Its output for this pair is
  published verbatim as `pair-247/guard-census-247.txt`, so the verdict is regenerable rather than
  retyped.
