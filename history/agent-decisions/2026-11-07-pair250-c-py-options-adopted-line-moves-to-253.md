# 2026-11-07 — pair-250: contour 0.0.2.53 (C python-literal options) MEASURED and ADOPTED; line moves 0.0.2.52 -> 0.0.2.53

Decision: adopt `C_PY_GROUND` as line behavior (flag stays `>= (2,53)`), move the contour line to
`0.0.2.53`, and close `C-ex6-02` — the 27/27 chronic loss that survived every contour era — as
REPAIRED on the adopted line.

## What was decided and why

The frozen pre-registration rule (REVIEW-INBOX 22:56 CET, before any v52r4x/v53r4x row) was the
only basis: (a) the pair's own control strict-failed C-ex6-02 in 3/3 seeds (live target met,
matching the published 27/27 base rate); (b) ALL THREE live target cells converted on the
candidate side carrying `contour:v53_c_py_from_prompt`, with the operative zero-extra-work test
strictly satisfied — converted rows have ONE model call against the control's two (the deterministic
ОТВЕТ-line rewrite passes the cell before the adopted v47 set-selector can arm, and the ptok
delta 370−239=131 is exactly the control's second call); (c) every guard clean — zero control
fires, zero fires outside the 1/77 census cell, zero target P->F, frozen bands silent (the 2.41
`C_RULE_GROUND` stays dead at 2.53), adopted-family census drift fully accounted (v47 8->4 = the
three pre-emptions + one C-ex6-03 draw); (d) the pool delta (215->216/231, 7W/6L p=1.0) is
context only and is not quoted as an effect.

**Rule-(b) interpretation (disclosed, not silent):** the frozen text said "at identical
ptok/calls". Read as literal cross-arm equality it would fail every repair that PRE-EMPTS a
control-side retry by construction — the candidate cannot match a cost the fix removed. The
operative test in the same clause ("post-hoc code; any ADDED model call on a converted row
closes the stamp") is what gates attribution, and it is satisfied strictly (candidate calls=1 ≤
control calls=2, no selector/retry event on any converted row). The verdict is rendered on the
operative test. Future pre-registrations must phrase (b) as "no added model call; candidate
calls ≤ control calls". The frozen rule text itself is not edited; the interpretation travels
with this decision record and PAIR-250-V66.md.

## Numbers

- Control 0.0.2.52: 71/71/73 strict; candidate 0.0.2.53: 70/72/74; pooled 215/231 -> 216/231.
- Target cell: C pool 20/24 -> 22/24 on bank v6.6 (+3 target −1 C-ex6-03 selector draw);
  converted ОТВЕТ lines equal the dry-run executed truth table {A,B,C,D} on all three seeds.
- Converted-cell cost: 0.76/0.78/1.26 s and 1 call vs 5.07/1.29/1.50 s and 2 calls; zero model
  tokens added, one call REMOVED per converted cell.
- Energy 19.32 Wh (control) vs 18.30 Wh (candidate); within run-to-run wall variance plus the
  removed retries; no anti-cost claim.

## Stack

bank v6.6 `5c86252b2ef2f422` (ws copy `590503cf1701a6ce` stamped in every run record), scorer
contract v6.2 `c8c0c7dd114dfc32`, seeds sp1 reps 41/42/43 (231/231 audited, plans shipped),
harness `740540e5b836…`, P2005 Basalt, serial idle arms. Report:
`benchmarks/hard/v6-results/PAIR-250-V66.md`; artifacts `pair-250/` (37 files incl. plans +
seed audit + launcher + energy windows).

## Consequences / next

1. `C-ex6-02` leaves the chronic map — the series' biggest single-cell loss (27/27 across every
   published era) closes via executed-snippet grounding, not resampling.
2. Third consecutive pair converting 100% of its pre-dry-run live targets (248: 1/1, 249: 2/2,
   250: 3/3). Prompt-internal grounding is now the proven contour family; remaining losses are
   1/3 partial cells (B-ex6-03, C-ex6-01, I-ex6-01, I-ex6-04) and event-less lottery bands
   (H/A/I single-shot, D-loop) where selection has no proven trigger.
3. Cadence counter: 3/5 measured stamps since cadence-249; the four-arm re-run on the current
   line becomes due after the 5th.
4. Next candidate must come from the pair-249+250 v6.6 stability map: the four 1/3 cells are the
   measurability check — a pair may only target a cell the CURRENT line still strict-fails.
