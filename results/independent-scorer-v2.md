# Independent scorer v2 — widened coverage (2026-11-01)

The first independent scorer (`analytics/second_opinion.py`, kept frozen as
published) could re-score ~37% of rows. The second external audit correctly
pointed out that a dissent on 37% coverage is weak evidence in both
directions. `analytics/second_opinion2.py` derives checkable semantics from
each task's ground-truth `ref` for nearly every category (A, B, C, D, F, G,
H, I, J, K; E excluded — it would require executing model code), still with
zero imports of the harness scorer.

## v1.8 → v1.9, B2003 finals (the headline claim)

| measure | harness scorer | independent v2 (90% coverage) |
|---|---|---|
| rows | 3117 → 2127 | 2813 / 1905 rescored |
| mean content | 0.868 → 0.926 | 0.756 → 0.757 |
| matched paired delta | **+0.047** | **−0.006** (n=1905) |
| improved pairs (229) | — | 63 confirmed, 23 reversed, 6 not scoreable |
| regressed pairs (79) | — | 0 confirmed, **45 reversed**, 4 not scoreable |

Reading, stated carefully:

* At 90% coverage the independent scorer **still does not confirm the mean
  gain**. The matched delta is −0.006, i.e. flat.
* It also **reverses most of the harness-reported regressions**: of 79
  "regressed" pairs, 45 score better under the independent scorer and 0
  worse. The contour's fixes do not break content.
* The v1.9 gain is concentrated in category D (order-of-operations gates).
  On the independently scoreable D subset the improvement is confirmed 63 vs
  reversed 23 — a real but partial confirmation.
* The independent scorer is stricter overall (0.757 vs 0.926 mean): it
  demands exact values/sets where the harness gives partial credit. Means
  are not comparable across scorers; only matched deltas are.

Conclusion published, not hidden: **the claim "v1.9 improves mean task
quality by +0.047" is scorer-dependent.** What survives independent
scrutiny: no content regressions, and a confirmed D-category mechanism
gain. Where the contour's advantage is unambiguous under any scorer is the
machinery-vs-baseline comparison (`results/baselines.md`: independent
scorer gives contour 0.810 vs best simple arm 0.715).

## Holdout pilot (mini, v1 bank)

Coverage 87% (62/71 rows): harness mean 0.858, independent mean 0.567.
Note: the v1 holdout bank's G tasks were broken (no document — see
`history/failures/failures.md`), which drags both means; the corrected
pilot is in `results/holdout-mini.md`.

## Reproduce

```bash
python3 analytics/second_opinion2.py benchmarks/text-gates/bank.json \
    <v18-results.jsonl> <v19-results.jsonl>
```

Machine-readable output: `results/independent-scorer-v2.json`,
`results/independent-scorer-v2-holdout.json`.
