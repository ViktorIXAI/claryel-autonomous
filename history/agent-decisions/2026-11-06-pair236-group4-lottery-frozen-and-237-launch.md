# Decision: pair-236 — group-4 lottery selection converts zero cells and is frozen; 2.37 re-lands the B table repair (2026-11-06)

## Context

pair-236 (arms `i29r*` vs `i36r*`, P2005/Basalt, bank v6.1 `f4553aab304f60d7`, three matched seeds,
77/77 rows per arm, 0 empty/engine-error/zero-prompt rows) measured contour `0.0.2.36` — the proven
best-of-2 selection extended to the group-4 component-omission notes (H `unknown_missing` /
`requires_missing:<field>`, F `avoid`) — against the adopted `0.0.2.29`. Pre-registered rule (PAIR-235
report): attribution claim only, expected +0.5..+1.5 by construction; the claim is that every converted
row carries its event.

## Evidence

- Headline: 62/62/62 (62.0) vs 62/62/65 (63.0) = **−1.0 cells**, inside the ~2-cell floor and negative;
  pooled sign test 2W/5L p=0.453.
- Fire census: 6 fires — H-ex6-01 in all three seeds, H-ex6-03 once, F-ex6-00 twice (2 strict-best
  wins). **Converted scoreboard cells: 0.**
- The target cell died: `H-ex6-01` 3/3 -> 0/3. Both arms run the identical ladder prefix on it; in every
  candidate seed the stored answer carries `requires_missing:аудит-лог operations` (0.5) and the strict
  re-sample never beat the first draw — the second sample omits the same component. Class bias, not
  variance: the 2.31 failure mode reproduced on group 4. The drift into the note itself is event-less,
  so no flip is credited to the mechanism — but the mechanism's promise was to recover exactly those
  draws and it recovered none, at +1 call each.
- The two F wins raised an already-3/3-passing cell (cost 445→641 ptok): value invisible on this bank,
  cost measured.
- C/J flips carry no 2.36 event and identical contour calls/ptok per cell in both arms — serve-state
  resampling, the same contention pattern pair-235 quantified.
- Rescore: 30 cell-arm joins, 0 blanks, 0 mismatches — the flip table is real.
- Energy: 4.6–10.1 Wh per arm-window, 76–97 W mean; lottery cost inside noise; no limit tight.

## Decision

**`0.0.2.36` NOT adopted; frozen to `CONTOUR_REVISION == (2, 36)`** — added to `REJECTED_FEATURES` as
`g4_lottery_selection`, flag matrix pinned in `gate_v49_feature_adoption_test.py` (19 checks). Group-4
selection is closed: the H half is refuted by class bias (selection cannot beat a biased draw), and the
F half has no measurable bank value at this sample size. The adopted line stays `0.0.2.29`.

## Next: 0.0.2.37 — re-adoption of the confirmed B table repair, pre-registered before any `j*` row

With group 4 closed, the strongest live target is `B-ex6-06` (chronic 0/12 across the pair-235/236
control seeds — the 2.35 grammar is frozen out of both arms of pair-236, so it failed identically 6/6
there). 2.35's table aggregation is the only mechanism in the series with a deterministic, fully evented
3/3 conversion at zero model tokens; its LINE freeze came from event-less neighbours at the mean floor.
`0.0.2.37` = adopted behaviour + re-landed `B_TABLE_AGGREGATE` (+ the 2.36 freeze; nothing else).
Contracts green before launch: v36/v37/v38/v39/v40/v44/v45/v49(19)/v51(21)/v52(40)/v53(38)/versioning,
fixers 12/12; live smoke `smk37c` at 15:57:58: stamp/behavior line `0.0.2.37 / 2.37`, the
`contour:v235_b_table_total:available_total` event on `B-ex6-06` only (scored 1.00), B-ex6-03/05
untouched. Pre-registered rule (full text in `PAIR-236-V61.md`): adopt 2.37 iff B-ex6-06 flips 0/3 ->
3/3 with its event on every converted row, no other mechanism event appears anywhere, and the arm does
not land >2 cells below control; otherwise the flag freezes again at 2.37. Launch as
`parb-pair237.service` (`run_pair237.sh`, arms `j29r*` vs `j37r*`, GPU sampler `parb-gpu-samp2.service`
active), immediately after this commit is pushed to `main`.
