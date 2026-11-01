# Holdout pilot run (mini) — contour v1.9 on unseen instances

**Run:** 14 holdout tasks × repeats (plan hash `ab0d7168635a9f40`), P2005SAH,
contour **v1.9** (unchanged code), 71 records in 563 s.
Artifacts: [`/logs/samples/holdout-p2005-mini/`](../logs/samples/holdout-p2005-mini/)
(`results-holdout-mini.jsonl`, `gate-ledger-holdout-mini.jsonl`).

Harness-scorer means by category (dedup best `(task,rep)`):

| cat | n | mean content |
|---|---:|---:|
| A | 13 | 1.000 |
| B | 13 | 0.769 |
| C | 13 | 1.000 |
| D | 11 | 0.636 |
| E | 3 | 1.000 |
| F | 3 | 0.667 |
| G | 3 | **0.167** |
| H | 3 | 0.667 |
| I | 3 | 0.889 |
| J | 3 | 0.667 |
| K | 3 | 1.000 |
| **overall** | **71** | **0.819** |

Independent scorer (`second-opinion-holdout-mini.json`): 34/71 rows
independently rescored, independent mean 0.529 vs harness 0.882 on that
subset (stricter coverage metric, same semantics gap as documented for the
dev set in `independent-scorer.md`).

## Reading (no spin)

1. v1.9 carries over to unseen instances of known families (A/C/E/K perfect,
   overall 0.819) — but **not uniformly**: G (very-long-context) collapses
   to 0.167 and D (agent plans) to 0.636 on holdout draws.
2. These are **easy-level** single-rep draws — small n per cell; the pilot
   is a signal, not a leaderboard. A full holdout series (all 206 tasks ×
   standard rep schedule, both boxes) is the next measurement; v2.0
   candidates must beat v1.9 on dev **and** holdout.
3. The G gap is a genuine new finding: dev-bank veryhard G tasks had large
   in-series gains in v1.7 (form repair), but unseen very-long instances
   with different content defeat the contour today. Recorded as a failure
   direction, not hidden by averaging.
