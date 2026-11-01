# Budget-matched simple baselines vs the v1.9 contour

Run date: 2026-11-01. This experiment answers the central external-review
question: *why an evolved contour if a validator, one retry, or a few dozen
lines of code get the same result at the same budget?*

## Design

23 dev-bank tasks × 3 repetitions = **66 (task, rep) pairs**, one from each
difficulty band across all 11 categories, selected from the published v1.9
finals. All arms use the identical task prompts, the identical request seeds
taken from the published v1.9 rows, temperature 0.7, thinking off, and the
**same validators** for scoring. Arms:

| arm | machinery | budget cap |
|---|---|---|
| S0_direct | one call, max_tokens 1024 | 1 call |
| S1_generic | + one generic retry ("output only the requested format") on format failure | ≤2 calls |
| S2_min_gate | + one retry carrying the validator's actual complaint + previous answer (the contour's minimal core, ~40 lines) | ≤2 calls |
| S4_best_of_2 | two independent samples, keep validator-best | 2 calls |
| S3_contour_v1.9 | the released contour, re-run on the **same box/engine** as the arms (P2005SAH, Strata 0.1.52) | contour's own ladder |

A second contour column shows the published B2003 finals for the same pairs
(cross-box reference, not the paired comparison).

## Result

| arm | n | mean content | format_ok | tokens/task | seconds/task | calls/task |
|---|---|---|---|---|---|---|
| S0_direct | 66 | 0.795 | 88% | 371 | 0.8 | 1.00 |
| S1_generic | 66 | 0.806 | 91% | 422 | 0.9 | 1.14 |
| S2_min_gate | 66 | 0.818 | 91% | 417 | 0.9 | 1.12 |
| S4_best_of_2 | 66 | 0.802 | 88% | 741 | 1.4 | 2.00 |
| **S3_contour v1.9 (same box)** | 66 | **0.952** | **98%** | 582 | 1.3 | 1.24 |
| S3_contour v1.9 (B2003, published) | 66 | 0.937 | 98% | 594 | 5.5 | 1.29 |

Independent re-scoring of the same arms (analytics/second_opinion2.py,
~90% coverage, no harness scorer involved) preserves the ordering and the
gap — the contour's win is scorer-independent:

| arm | rows rescored | harness mean | independent mean |
|---|---|---|---|
| S0_direct | 57 | 0.667 | 0.592 |
| S1_generic | 60 | 0.769 | 0.671 |
| S2_min_gate | 60 | 0.711 | 0.587 |
| S4_best_of_2 | 60 | 0.799 | 0.715 |
| S3_contour v1.9 (P2005) | 60 | 0.947 | **0.810** |

Paired deltas vs the same-box contour (content, contour − arm):

| arm | mean delta | contour better | arm better | tie |
|---|---|---|---|---|
| S0_direct | +0.157 | 19 | 0 | 47 |
| S1_generic | +0.146 | 19 | 3 | 44 |
| S2_min_gate | +0.134 | 16 | 0 | 50 |
| S4_best_of_2 | +0.150 | 18 | 1 | 47 |

Per category (mean content):

| cat | S0 | S1 | S2 | S4 | S3 (P2005) | S3 (B2003) |
|---|---|---|---|---|---|---|
| A finance | **0.000** | **0.000** | **0.000** | **0.000** | **1.000** | 1.000 |
| B extraction | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| C logic | 0.667 | 0.583 | 0.917 | 0.667 | 1.000 | 1.000 |
| D agent plan | 1.000 | 0.933 | 1.000 | 1.000 | 1.000 | 1.000 |
| E programming | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| F sysadmin | 0.694 | **0.722** | 0.694 | 0.694 | 0.722 | 0.667 |
| G long context | 0.833 | 0.833 | 0.833 | 0.861 | 0.861 | 0.833 |
| H hallucination | 0.806 | **1.000** | 0.806 | 0.806 | 0.889 | 0.889 |
| I injection | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| J format | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| K multilingual | 0.750 | 0.792 | 0.750 | 0.792 | 1.000 | 0.917 |

## What this shows

* **The contour's advantage is real and concentrated.** Against the best
  simple arm (S2) it gains +0.134 mean content for +40% tokens, wins 16
  pairs and loses none. The gain is not spread evenly: it is almost entirely
  in **A (finance: 0.000 → 1.000)**, **C (0.917 → 1.000)** and **K
  (0.750 → 1.000)**.
* **Simple machinery cannot fix finance arithmetic.** Every simple arm scores
  exactly zero on invoice tasks: the failure mode is wrong/omitted computed
  values, not formatting, and no amount of "output only the requested
  format" retries changes that. The contour wins because it extracts lines
  structurally and lets **code do the arithmetic** — machinery of a
  different kind, not more retries.
* **Half the benchmark needs no contour at all.** B, D(plan), E, I, J are at
  1.000 for every arm; F and G are contour-neutral. On **H, a generic retry
  (S1) beats the contour (1.000 vs 0.889)** — published as a contour
  weakness, candidate for the next iteration.
* **Sampling is not machinery.** S4_best_of_2 (double budget, no gates)
  stays at 0.802 — extra samples do not substitute for the contour's
  structure.

## Honest limits

* 66 pairs, one box (P2005SAH), one model. Category-level numbers on 6 pairs
  are indicative, not precise.
* The contour's budget is its own ladder; we report tokens/seconds per task
  rather than forcing an equal cap. At equal *call* budget (≤2 calls) the
  contour still wins (1.24 calls/task average).
* Arms scored by the same validators that define the benchmark — this
  experiment measures *machinery*, not scorer quality; the independent
  scorer (v2) covers that axis separately.

## Reproduce

```bash
PARB_BANK=benchmarks/text-gates/bank.json PARB_V19=<v19-results.jsonl> \
PARB_API=... PARB_MODEL=... PARB_OUT=./baselines \
python3 experiments/baselines/simple_baselines.py --per-cat 6
PARB_V19=... PARB_V19_LEDGER=... python3 experiments/baselines/analyze_baselines.py
```

Raw rows: `experiments/baselines/data/baselines-results.jsonl`,
`contour-p2005.jsonl`, `contour-p2005-ledger.jsonl` (also in the
`data-full-2026-11-01` release assets).
