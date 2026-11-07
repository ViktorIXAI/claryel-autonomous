# 2026-11-07 — pair-243: contour 0.0.2.42 D-loop policy re-ground MEASURED NEGATIVE, frozen; the line stays 0.0.2.40

Decision: `LOOP_POLICY_REGROUND` frozen to `CONTOUR_REVISION == (2, 42)`; `0.0.2.40` remains the
adopted contour line. Published with full detail (negative result): `PAIR-243-V61.md`,
`pair-243/` artifacts (6 arms, 77 rows each), REVIEW-INBOX 2026-11-07 (pre-registration 02:17 +
closure), UNSTABLE-CELLS-V61 addendum.

Why it ran despite the 2026-11-06 bank-ceiling note: that note blocks pairs whose target is the
published bank defects (A-ex6-03/C-ex6-02/K-ex6-03) or the frozen-negative B-ex6-04. Loop-D is
contour-only headroom explicitly kept open by the owner's standing continuation rule; the
relation is stated in the pre-registration, not applied silently.

What was measured (rule text fixed BEFORE any row):
- MEASURED: the fresh control reproduced D-ex6-l3 strict failures at seeds 0+1 (live target).
- Cell attribution held: 2/2 live targets converted, all evented, zero banned attempts in the
  candidate.
- Guard broke: 2 candidate loop cells (D-ex6-l1/l2 seed 1) strict-failed over control passes
  with new banned attempts — the pre-registered ZERO-regression condition failed.
- Pools: loop 16/18 vs 16/18 (2W/2L), single-shot 65.0->65.3 mean, W4/L2 p=0.6875, full pool
  W6/L4 p=0.7539 — no quotable effect. Energy 16.55 vs 18.12 Wh.

Class ruling for the loop pool (published): context nudges re-roll whole trajectories, so
prevention nudges are net-zero there; loop losses must be attacked with SELECTION after a
complete attempt (2.11 best-of-2 family) and the missing trigger (banned-attempt failure notes)
is published as the concrete next-loop-hypothesis, not implemented against this frozen stamp.

Not touched: bank bytes (9ec86dfca4a6f85f published / f4553aab304f60d7 ws re-verified), frozen
scorer, model answer text, frozen flags of earlier stamps. Contract suite 19/19 on the freeze
commit; gate_v56 (27) + gate_v49 (41) pin grammar, wiring and the flag matrix.
