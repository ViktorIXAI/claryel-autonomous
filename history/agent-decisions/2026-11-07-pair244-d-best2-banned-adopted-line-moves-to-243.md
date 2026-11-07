# 2026-11-07 — pair-244: contour 0.0.2.43 D-loop best-of-2 on the banned-attempt family MEASURED, ADOPTED; the line moves 0.0.2.40 -> 0.0.2.43

Decision: `0.0.2.43` becomes the adopted contour line. `D_BEST2_BANNED = contour_at_least(2, 43)`
inherits forward as line behavior; every frozen negative (2.30/2.31/2.32/2.34/2.36/2.38/2.41/2.42)
stays pinned to its own stamp and is proven event-absent in the candidate arms. Published with full
detail: `PAIR-244-V61.md`, `pair-244/` artifacts (6 arms x 77 rows + sanitized launcher),
REVIEW-INBOX 2026-11-07 (pre-registration 03:05 + closure), UNSTABLE-CELLS-V61 loop addendum.

The verdict was decided ONLY by the rule text fixed before any row (REVIEW-INBOX 03:05 +
run_pair244.sh header): MEASURED (3 live control draws carrying `banned_attempted:<TOOL>` and
strict-failing) + >=1 evented conversion (D-ex6-l3 seed 1: fired+win, adopted trajectory zero
banned attempts, control strict-fail -> candidate strict pass) + all guards clean (zero loop P->F,
zero v243 events outside loop rows, zero frozen-band events — the 2.42 tail proven absent,
2.39/2.40/2.35 parity identical seed by seed) => ADOPT.

Honest accounting published in the same breath: loop pool 13/18 -> 16/18, W3/L0 p=0.25 (n=18,
directional by design); of the three wins exactly ONE is evented/attributable, two are lottery
re-draws the mechanism never touched; single-shot −0.3 cells and full-pool 208->210 (7W/5L p=0.774)
sit under the ~2-cell resolution floor and are never quoted as the reason. One live draw
(D-ex6-l0 seed 2) fired and stayed failed — BOTH draws of the best-of-2 attempted the ban:
selection cannot fix a biased draw, published as a limit of this mechanism.

Cost disclosed: +3 extra loop runs on already-failing cells only (loop pool ptok +7.7%, calls
+12.9%); serve-board arm energy 21.41 vs 17.85 Wh — the −16.6% is single-shot draw length, not
attributed to 2.43.

Next (launched same session, pre-registered before any row): pair-245, control `q43` (the new
adopted line) vs candidate 0.0.2.44 — the third loop best-of-2 trigger: the
`false_completion_claim` note family (the model CLAIMS a banned action was performed; content capped
0.3, zero current triggers match it), same monotone recipe, retry seed +12289. The 2.43 recipe and
its 8117 offset stay byte-frozen; new event names per family.

Not touched: bank bytes (9ec86dfca4a6f85f published / f4553aab304f60d7 ws re-verified), frozen
scorer, model answer text, frozen flags of earlier stamps. Contracts on the adopted tree: gate_v57
(37) + gate_v49 (46) + gate_fixers 12/12 + standing suite 20/20; ws rebuilt + repinned after the
version-file edit, `verify_manifest.py --v6` PASS.
