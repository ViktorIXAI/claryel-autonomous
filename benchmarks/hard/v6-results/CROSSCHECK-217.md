# Independent cross-check of the 0.0.2.17 full arm (c217full, SAH line)

Scored here with the pinned v6-line scorer (`score_v6.py` + `parb_check_v6.py`, same code that
produced every other published cell). Raw converted answers: `answers-contour217.jsonl`
(77 rows incl. 6 loop trajectories with gate markers), per-task table: `scored-contour217.csv`.

| view | 2.14 | 2.15f | 2.17 |
|---|---|---|---|
| single-shot 71 strict | 43 | 46 | 44 |
| loop 6 strict | 1 | 5 | 4 |

- 2.14 -> 2.17: +5/-4, p=1.00; 2.15f -> 2.17: 0/-2 (A-ex6-05, H-ex6-04), p=0.50.
- All three arms sit inside the single-sample noise band (+-2 cells); no arm is currently
  distinguishable from another at rep1. The only mechanically attributed deltas remain:
  B/J format repair (obj_unwrap/j_id_norm events in ledger) and loop markers (structure fix).
- Their separately measured K battery (2.18, K-only arms) is a different protocol slice; do not
  merge its numbers into single-shot tables.
- Cross-check conclusion: the published 2.17 artifacts are internally consistent with our
  independent scoring; totals quoted by both sides agree within noise; superiority claims at
  rep1 are not supportable and we will not make them.
