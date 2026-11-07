# RESCORE-V62 — every published arm re-scored under the bank v6.2 golds

Date: 2026-11-07 (host clock). This is step 1 of the queue in
`bank-defect-v62-changelog.md`: pure offline replay of stored answer bytes against the
new references — zero model calls, zero contour.

## Stack identity

| element | value |
|---|---|
| bank v6.1 (old gold) | `9ec86dfca4a6f85f` (bytes verified intact) |
| bank v6.2 (new gold) | `3c866ea7daae611c` |
| scorer (frozen, both sides identical) | `harness/parb_check_v6.py` @ this commit: `check_json_obj`+`deep_eq`(EPS) for A, `check_C_v6` exact-set for C |
| seed protocol | n/a (replay of stored bytes) |
| strict rule | `content==1.0 and format_ok` (published scoreboard rule) |
| method | BOTH sides recomputed from the same stored answer bytes (`scripts/rescore_v62.py`), never stored-score deltas |

## Result

| cell | joined rows | strict under v6.1 gold | strict under v6.2 gold | flips WIN | flips LOSE |
|---|---|---|---|---|---|
| A-ex6-03 | 120 | 0 (0.0 %) | 44 (36.7 %) | 44 | 0 |
| C-ex6-02 | 120 | 0 (0.0 %) | 27 (22.5 %) | 27 | 0 |

Coverage: 106 published arm files — every contour full/pair arm with a stored A-ex6-03 and
C-ex6-02 answer (`full-*`, `pair-230..243`, `cadence-240`), the four-arm rep0 archives
(`four-arm-v61/`, `answers-{contour,codex,grok,basalt}*.jsonl`), and the cadence raw reps
(`raw-reps-v61/answers-*-reps.jsonl`). Probe directories (`j-probe-218`, `k-218`) and
`reps-229` are excluded as subsets, and `pair-244` was not yet committed when this script
ran — it is pure-text replayable with the same command at any time. Blank answers skipped:
0. Per-cell rows: `rescore-v62.csv` (arm, task, rep, both scores, flip, stored-shape flag).

## What this proves

1. **The v6.1 golds were unreachable by construction**: 0/120 across every contour stamp
   AND both external raw brains — no arm configuration ever passed them. The defect queue's
   0/89 tally now covers the full published corpus including fresh-seed cadence reps.
2. **The v6.2 golds are reachable and fair**: 44/120 and 27/120 of the same stored bytes
   become strict passes; every WIN is an answer that executed the prompt's own stated rule
   (A: the printed 9500.0 chain; C: the executed truth table of the shipped snippets).
3. **Zero collateral damage**: 0 LOSE cells in any arm — no answer that passed under v6.1
   fails under v6.2. The bank change strictly removes impossible cells and changes nothing
   else; per the fairness rule, raw-arm improvement (basalt/codex/grok all gain) is the
   bank-fairness check and it holds.
4. Remaining failures are genuine model gaps, not bank blocks: A keeps 76 misses (dominant
   blocks carry real `tax` slips like 1122.9/1103.9 against the faithful 1179.9), C keeps 93
   (mostly missing `B` — the set-order insight — or extra letters).
5. 54 rows carry a stored-score "mismatch" flag — all inside answer archives, which store
   bytes without score fields by shape; results/ledger arms re-score byte-identically to
   their stored scores (0 mismatches), so no scorer-routing bug is implicated.

## Consequences for the scoreboard

Published arm totals quoted in earlier PAIR/CADENCE docs were measured under v6.1 and stay
labelled v6.1 (bank sha16 next to every number, per the identity rule). Comparisons that
cross the v6.2 boundary must be re-run fresh on the v6.2 workspace; a v6.2 workspace build
+ pinning is the next measurement-stack step, and the four-arm cadence (contour `0.0.2.43`
line vs ChatGPT vs Grok vs bare basalt) runs on v6.2 for the fairness re-check.

Reproduce: `python3 scripts/rescore_v62.py` (rewrites `rescore-v62/rescore-v62.csv` and
prints the summary; fail-closes if the v6.1/v6.2 golds for the two cells stop differing).
