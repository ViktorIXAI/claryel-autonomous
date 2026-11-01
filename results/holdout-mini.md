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

## CORRECTION (same day): the G collapse was our own generator bug

The v1 holdout bank shipped G tasks **without their long documents** (the
prep-stage assembly step was skipped in the holdout generator). The model
received only the questions — G=0.167 measured a broken task, not model or
contour behaviour. Root cause, fix and the discovery path are in
`history/failures/failures.md`. The v1 rows above stay published unmodified,
annotated as invalid for G.

Corrected pilot (bank v2, identical ids/refs/seeds, P2005SAH, contour v1.9,
73 records, `logs/samples/holdout-p2005-mini2/`):

| cat | n | mean content |
|---|---|---|
| A | 13 | 1.000 |
| B | 13 | 1.000 |
| C | 13 | 1.000 |
| D | 13 | 1.000 |
| E | 3 | 1.000 |
| F | 3 | 0.667 |
| G | 3 | **0.833** |
| H | 3 | 0.500 |
| I | 3 | 1.000 |
| J | 3 | 1.000 |
| K | 3 | 1.000 |
| **overall** | **73** | **0.959** |

## Reading (corrected, no spin)

1. With the task fixed, v1.9 **does carry over** to unseen instances of the
   known families: overall 0.959, G 0.833 — identical to the dev-bank G
   level. The earlier "transfer failure" claim was an artifact of a broken
   task; we publish the correction, not the comforting version.
2. Run-to-run differences between the v1 and v2 pilots on unchanged tasks
   (B 0.769→1.000, D 0.636→1.000, H 0.667→0.500) despite identical seeds
   reflect engine-level nondeterminism at temperature 0.7 on this stack —
   a known caveat, also visible in the dev-set repeatability category L.
3. Weakest holdout cell now: **H (hallucination/false-premise) 0.500** —
   consistent with the baselines finding that a generic retry beats the
   contour on H. That is the next contour hypothesis, to be tested
   paired on dev and holdout before any adoption.
4. Still easy-level, single box, small n. The full 206-task holdout series
   on both boxes remains the gate for any v2.x adoption.
