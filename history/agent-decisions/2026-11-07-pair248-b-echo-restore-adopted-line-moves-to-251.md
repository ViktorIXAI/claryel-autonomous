# 2026-11-07 — pair-248: B echo restore re-armed, MEASURED and ADOPTED; line moves to 0.0.2.51

Decision by the autonomous contour loop under the owner's 2026-11-07 delegation ("decisions are
yours... version every element"). Recorded here because it moves the adopted line and because it
establishes a reusable meta-rule about frozen-UNMEASURED stamps.

- **The class was made live by the line itself.** Pair-234 built the B field grammars, measured
  zero fires, and froze the flag to exactly (2,34) — correct at the time (that revision's guard
  refused any answer adding the declared count key, so the pair carried zero live target). Days
  later the guard had been extended (drop-names + count-key tolerance) but the flag stayed frozen,
  and on the ADOPTED line (bank v6.2, behavior 2.48, arms t48r22/23/24) B-ex6-05 strict-fails 2/3
  seeds with one single failure mode: the model copies `items` but injects its own per-item
  `n_tags`, violating the prompt's «Items не меняй», scored `fields_mismatch:items`. A frozen-
  UNMEASURED mechanism is a frozen CLAIM ABOUT DATA, not a permanent rejection of the idea: when
  new published draws make the class live, a NEW stamp may re-arm it (new flag, new event name,
  coverage re-proven on current bytes) — the older stamp's published bytes never move.
- Pre-registered rule (REVIEW-INBOX 2026-11-07 20:28 CET, `run_pair248.sh` header, commit
  `7186be7`): ADOPT iff (a) live target — >=1 control B-ex6-05 strict-fail at reps 34/35/36, (b)
  >=1 matched (task,rep) control-fail -> candidate strict-PASS carrying `contour:v51_b_echo_restore`,
  (c) guards clean (no v51 events in control/outside the task, no candidate B-ex6-05 P->F, frozen
  bands silent, adopted-family parity). Otherwise freeze `B_ECHO_RESTORE` to exactly (2,51).
- Same-seed smoke rep 40 (20:29 CET, subset, before the pair): both arms strict-PASS, ZERO echo
  fires — the already-equal no-op branch proven on live bytes at zero cost.
- Measured (arms u48r34/u51r34/u48r35/u51r35/u48r36/u51r36, bank v6.2 `3c866ea7daae611c`, ws copy
  `d1e8d11df5840dcc`, contract v6.2 `c8c0c7dd114dfc32`, sp1 reps 34/35/36, idle endpoint, harness
  `7186be795a7e` in every run record): (a) live target met — u48r35 c=0.0 `fields_mismatch:items`;
  (b) ONE evented conversion — (B-ex6-05, rep35): candidate strict-PASS, answer byte-equal to the
  prompt's own JSON literal, ptok/ctok IDENTICAL to control (264/71) in 1.44 s — zero extra model
  calls, the repair is post-hoc code; (c) all guards clean — `contour:v51_b_echo_restore` fired
  exactly 2 times in the entire pair (both candidate arms, both on B-ex6-05), zero in control,
  zero outside the 1/77 coverage census, zero candidate B-ex6-05 P->F, frozen bands silent,
  candidate-only non-v51 events are single-shot lottery differences inside already-adopted
  families, zero stalls / zero blank joins.
- Pool movement (210/231 -> 214/231, per-rep 68/69, 70/72, 72/73; pooled 7W/3L exact sign
  p=0.3438; 10 flips, 9 event-less — 7 inside the six-cell loop pool 11/18 -> 16/18, structurally
  unreachable to a cat=="B" repair) is CONTEXT ONLY, not the adoption basis — cell-level rule as
  pre-registered. The loop-pool swing is recorded as a draw observation, nothing concluded.
- Energy: control 20.24 Wh vs candidate 21.87 Wh (+8.1%): candidate-side arm windows are longer
  (874 s vs 819 s wall) because of D-loop ladder draws; model calls 401 vs 405. Mechanism cost
  zero on target by construction (byte-identical tokens on the converted cell).
- Consequences: `B_ECHO_RESTORE` stays `>= (2,51)` and inherits as line behavior (adoption keeps
  the floor — no code move); the 2.34 config-fields grammar stays frozen with no live cell; the
  bank's B category is 16/18 -> 17/18 on this line, the remaining B zeros (B-ex6-01 `[]` collapse,
  B-ex6-04 bank-defect queue) are not grammar cells.
- Cadence accounting: since cadence-249's four-arm re-run, 0.0.2.51 is the FIRST measured contour
  stamp (2.47/2.48 were measured before it); the next four-arm cadence falls due after the 5th
  measured stamp (four stamps away).
