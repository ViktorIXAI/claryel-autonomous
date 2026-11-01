# Independent quality evaluation (second-opinion scorer)

`analytics/second_opinion.py` re-scores frozen model **answers** (from the
published artifacts) using an implementation written from the task bank's
ground-truth specs only — it imports no harness scorer code. Coverage:

| check | categories | method |
|---|---|---|
| numeric presence | A (invoice/total) | every numeric leaf of `ref` must appear in the answer |
| field containment | B, H | every `ref` value must appear (case-insensitive) |
| agent-plan validity | D (`agent_plan`) | required tools present, forbidden tools absent, relative order respected, `no_sum_before_read` flag |
| strict JSON | format layer | `json.loads` on the extracted block |

Categories C, E, F, G, I, J, K have no oracle that can be re-derived from the
bank alone; they are reported as `not_independently_scoreable`, never guessed.

## Result: contour v1.8 → v1.9 on B2003 (release-2026-11-01 bytes)

Machine-readable copy: `second-opinion-v18-v19-b2003.json` (this directory).

| measure | harness scorer | independent scorer |
|---|---|---|
| v1.8 rescored rows | 3117 | 1152 (37%) |
| v1.9 rescored rows | 2127 | 823 (39%) |
| mean over rescored rows | 0.849 → 0.979 | 0.491 → 0.515 |
| matched pairs both sides | 2127 | 823 |
| matched delta | +0.047 (229↑ 79↓) | **−0.011 (13↑ 22↓)** |
| harness-"improved" pairs confirmed | — | 13 confirmed, 22 reversed, 61 unscoreable |

## Reading (deliberately unflattering)

1. The headline +0.047 of v1.9 is **not fully corroborated** by this
   independent oracle. Within the subset the oracle can score, the delta is
   slightly negative. The v1.9 gain concentrates in D-ha / D-mo / D-sa and
   other multi-constraint agent tasks whose full semantics (tool arguments,
   mock-environment consistency, multi-stage state) the prototype oracle does
   not model — it only checks must/must-not/order over first tool mentions.
2. Absolute means differ between scorers by design: the independent numeric
   check demands **every** ground-truth number while the harness tolerates
   equivalent renderings. Divergence counts (663/396) are metric-semantics
   differences, not evidence either scorer is wrong.
3. What the ledger *does* separate without any oracle: `model_calls` per
   attempt (extra model generation), `gate_fixes` (mechanical post-processing),
   `gate_blocks` (validator refusals) — published per series in
   `results/summary.json`; per-attempt raw pre-fix answers are **not** stored,
   which is a known gap limiting attribution (see docs/limitations.md).

## Next steps (open, not claimed)

* per-category oracles for C/F/J/K (full replay of mock environments from
  the ledger transcripts),
* held-out bank (`benchmarks/holdout/`) scored by both scorers,
* storing pre-fix raw answers in the ledger for post-fix attribution.

Until those exist, treat cross-version deltas as **harness-scorer-measured**,
with this page as the published dissent record.
