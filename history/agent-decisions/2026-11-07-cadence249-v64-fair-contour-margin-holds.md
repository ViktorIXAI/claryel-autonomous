# 2026-11-07 — cadence-249 verdict: bank v6.4 FAIR on fresh seeds; contour margin holds on v6.4

Decision by the autonomous measurement agent under the owner's 2026-11-07 delegation
("decisions are yours, keep improving the tests and the scoring system, version every
element"). Pre-registration: `REVIEW-INBOX.md` 14:26 CET, rules (a)-(f) frozen before any
row. Writeup: `benchmarks/hard/v6-results/CADENCE-249-V64.md`, artifacts
`benchmarks/hard/v6-results/cadence-249/`.

## What was measured
Four arms on bank v6.4 (`85a0cd0dd6fa1fab`, ws copy `7788cc288922b9a4`), scorer contract
v6.2 (`c8c0c7dd114dfc32`), seed protocol sp1, FRESH matched reps 25/26/27: contour
release `0.0.2.49` (tooling only, contour behavior 2.48 = adopted line, harness
`926afac912bfe`) vs bare basalt vs ChatGPT-codex vs Grok, common set 61 single-shot non-E
cells x 3 reps = 183/arm.

## Verdicts against the frozen rules
1. Rule (c): 0 ledger-vs-bytes mismatches on 183 replayable contour cells. NEGATIVE
   FINDING: the `_loop_rows` storage gap required "for new runs" is NOT closed — 18 loop
   cells again lack stored trajectories; loop numbers stay as-run ledger claims. Queued
   for the next tooling release with a contract test.
2. Rule (a): bank v6.4 is **FAIR** on independent fresh seeds. The B-ex6-04 lift signature
   reproduced exactly (codex/grok/contour 0/3 -> 3/3; basalt's guess 3/3 -> 3/3), no raw
   pool regressed beyond the noise floor, all residual movement sits in byte-identical
   categories (F/H class). No bank-defect hunt triggered; B-ex6-04 stays closed.
3. Rule (b): contour common 170/183 beats basalt 144 (W31/L5, p=1.3e-05), codex 131
   (W43/L4, p=2.8e-09), grok 134 (W39/L3, p=5.6e-09) — all far above the ~9.5-cell noise
   floor. Contour 166->170 vs cadence-246 attributed: +3 bank fix (claimed for the bank,
   not the contour), +3 adopted 2.48 K-fields gate (K 9/12 -> 12/12), offset by contour
   seed variance in F/H. Ranking contour > basalt > grok > codex unchanged on a new bank.
4. Rule (e): no stall/spin (leg medians 1.26-1.30 s vs 2.3 s baseline), contour GPU
   energy 19.63 Wh / 799 s wall for three full 77-task legs.
5. Tooling defect found and fixed while publishing: `cadence_score_v62.py` hardcoded the
   CSV arm label `contour-2.45`, mislabeling the 2.49 legs. Label now derived from the
   legs' run records (`stack.contour_stamp`); scores unaffected; 246 reproduction keeps
   its historical label from its own records.

## Consequences
- Adopted contour line stays `0.0.2.48` (behavior axis) / release 0.0.2.49 tooling; the
  cadence leg confirmed it on v6.4 at fresh seeds.
- Bank v6.4 confirmed as the working bank for the next pairs and the next cadence.
- Next cadence due after 5 more measured contour stamps from 2.49.
- Tooling queue: loop-row trajectory storage (`_loop_rows`) closed for new runs with a
  contract test — every published loop number is currently an as-run claim, which the
  repo states honestly but the rule demanded to close.

## Correction (16:47 CET, same day)
Item 1's NEGATIVE FINDING was WRONG and is retracted. The `_loop_rows` "storage gap" was
a re-scorer lookup-convention error in `scripts/cadence_score_v62.py`: loop trajectories
ARE stored (result-row sibling fields `agent_steps`/`agent_final`), and the generated
pinned adapter `parb_loop.check_D_loop` maps them to the scorer row form. The scorer now
applies that pinned mapping: all 18 loop cells replay offline under contract v6.2 with
0 ledger mismatches (replay strict 17/18 = the published loop column); all other tables
byte-identical. Loop numbers in CADENCE-249-V64.md are reproducible from stored bytes.
Remaining offline gap: category E only (30 cells, docker battery). The tooling queue item
becomes a convenience (store adapter-mapped `_loop_rows` directly) — NOT a protocol gap.
Class lesson (skill's scorer-routing rule, caught minutes after publication this
time): a re-scorer that reports every cell of one category broken must be audited against
the stored-shape convention before the finding is published.
