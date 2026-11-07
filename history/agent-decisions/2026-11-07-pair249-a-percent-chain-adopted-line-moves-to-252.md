# 2026-11-07 — pair-249: contour 0.0.2.52 (A percent-chain arithmetic) MEASURED and ADOPTED; line moves 0.0.2.51 -> 0.0.2.52

Decision: adopt `A_PCT_CHAIN` as line behavior (flag stays `>= (2,52)`), move the contour line to
`0.0.2.52`, and close `A-ex6-03` as REPAIRED on the adopted line.

## What was decided and why

The frozen pre-registration rule (REVIEW-INBOX 21:57 CET, before any v* row) was the only basis:
(a) the pair's own control strict-failed A-ex6-03 in 2 of 3 seeds (live target met, matching the
published ~2/3 base rate); (b) BOTH live target cells converted on the candidate side with the
mechanism event on the row at byte-identical ptok/ctok/model_calls; (c) every guard clean — zero
control fires, zero fires outside the 1/77 census cell, zero target P->F, frozen bands silent,
adopted-family census drift only inside adopted paths; (d) the pool delta (218->221/231,
6W/3L p=0.5078) is context only and is not quoted as an effect.

This is the second consecutive pair where a pre-dry-run prediction converted 100% of the live
control failures (pair-248: 1/1; pair-249: 2/2). The arithmetic family (2.27 + four branches) is
now the most predictive contour mechanism in the series: the chain is recomputed from the prompt's
own printed rules, so when the grammar fires, the corrected values are known BEFORE the arm runs.

## Numbers

- Control 0.0.2.51: 73/74/71 strict; candidate 0.0.2.52: 72/74/75; pooled 218/231 -> 221/231.
- Target cell: A pool 24/27 -> 27/27 on bank v6.6; converted answers equal the dry-run gold
  (2090.0 / 1179.9 / 6230.1) computed from the prompt's printed rules.
- Energy 21.66 Wh (control) vs 17.06 Wh (candidate); the delta is control-side wall variance,
  the mechanism is zero-token.

## Stack

bank v6.6 `5c86252b2ef2f422` (ws copy `590503cf1701a6ce`, diff []), scorer contract v6.2
`c8c0c7dd114dfc32`, seeds sp1 reps 37/38/39 (231/231 audited, plans shipped), harness `736b6634`,
P2005 Basalt, serial idle arms. Report: `benchmarks/hard/v6-results/PAIR-249-V66.md`.

## Consequences / next

1. `A-ex6-03` leaves the chronic map; the percent-chain grammar stays live for the future line.
2. The biggest surviving adopted-line loss is `C-ex6-02` 3/3 on BOTH arms (6/6 on the first v6.6
   draws). The v47 set-repair is published-spent on this class, so the next question is bank-side:
   run the versioned derivability audit (v2) over v6.6 C-ex6-02 and only then decide bank
   correction vs contour closure of the cell. No contour stamp may target it before that audit.
3. Cadence counter: 2/5 measured stamps since cadence-249; the four-arm re-run on v6.6 becomes
   due after the 5th.
4. This pair doubles as the first full-bank stability map on v6.6; later pairs re-target from it.
