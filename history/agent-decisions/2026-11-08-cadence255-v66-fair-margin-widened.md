# 2026-11-08 — cadence-255 verdict: bank v6.6 FAIR on fresh seeds; contour margin over all three brains widened

Decision by the autonomous measurement agent under the owner's 2026-11-07 delegation
("decisions are yours, keep improving the tests and the scoring system, version every
element"). Pre-registration: `REVIEW-INBOX.md` 2026-11-08 ~03:0x CET (stage plan, fairness
clause, digest rule frozen before any row), relaunch addendum 04:2x CET. Writeup:
`benchmarks/hard/v6-results/CADENCE-255-V66.md`, artifacts
`benchmarks/hard/v6-results/cadence-255/`.

## What was measured

Four arms on bank v6.6 (`5c86252b2ef2f422`, ws copy `590503cf1701a6ce`), scorer contract
v6.2 (`c8c0c7dd114dfc32`), seed protocol sp1 (audit 231/231), FRESH matched reps 52/53/54:
contour release `0.0.2.55` (behavior axis 2.55 = the adopted line, harness
`5f7c167d63b0`) vs bare basalt vs ChatGPT-codex vs Grok, common set 61 single-shot non-E
cells x 3 reps = 183/arm. Cadence due on both frozen clauses: 5 measured-era stamps since
cadence-249 AND two bank re-words (v6.5 provisional, v6.6 working).

## Verdicts against the frozen rules

1. Rule (a) fairness: v6.6 is FAIR. The fixed cell H-ex6-01 lifted ALL THREE raw arms
   0/3 -> 3/3 on fresh seeds (v6.5 probe had every zero at `ungrounded_claims`); pooled
   raw totals v6.4 -> v6.6: basalt 144 -> 146, codex 131 -> 135, grok 134 -> 134 — no
   regression beyond the noise floor. The bank-re-word fairness clause passed for the
   second bank in a row.
2. Rule (b) margin: contour common 170 -> 177; pooled W/L 37/6 (p=2.0e-06) vs basalt,
   46/4 vs codex, 48/5 vs grok (both p<1e-06). The margin WIDENED vs cadence-249
   (31/5, 43/4, 39/3). Adopted-line gates hold on brand-new seeds: K-ex6-03 3/3,
   A-ex6-03 1/3 -> 3/3 (2.52), C-ex6-02 0/3 -> 3/3 (2.53), D-plain 9/9 with 2.55 live.
3. Rule (c) integrity: 0 ledger-vs-bytes mismatches on 201 replayable contour cells
   (loop rows replay via the pinned adapter mapping); 30 E cells remain offline-N/A.
4. Endpoint health: leg medians 1.27-1.28 s/task, max 12.7 s, no stall/spin; contour
   energy 18.78 Wh / 231 cells = 0.0813 Wh per task, at or below the published band.
5. Grok transport incident handled per the frozen rule: 186 dead rc1 rows purged and the
   leg relaunched (final 213 rows, 0 empty); tooling hardened the same window
   (`err` field, abort after 5 consecutive empty answers, commit `38b20f9`).

## Consequence

Line stays `0.0.2.55`; no contour hypothesis from this cadence until the UNSTABLE-CELLS
map is rebuilt on the 2.55 line (pre-registration). The two B single-cell draws
(`B-ex6-03` r52, `B-ex6-06` r54) and `A-ex6-00`/`F-ex6-00` single draws feed that map.
Next four-arm cadence due after 5 further measured stamps.
