# Seed bands per arm on bank v6.1 (repeated-trial protocol: issues #8 and #23)

Generators: `scripts/arm_bands_v61.py` (per-seed strict scores, exact paired sign tests) and
`scripts/margin_bootstrap_v61.py` (seed-averaged per-cell margins with a cell-level bootstrap CI). Both
read published answer bytes and published ledgers, not hand-written scoreboards.

Common single-shot set: 61 cells (category E excluded — E needs docker execution and only the four-arm
repetition has cached E records; the contour's loop-protocol cells are reported separately).

```
common single-shot cell set: 61 cells

| arm | seeds scored | per-seed strict | mean | spread |
|---|---|---|---|---|
| contour | rep0, rep1, rep2, rep3 | 53, 52, 50, 55 | 52.5 | 5 |
| basalt | rep0, rep1, rep2 | 46, 48, 46 | 46.7 | 2 |
| codex | rep0, rep1 | 40, 41 | 40.5 | 1 |
| grok | rep0, rep1 | 44, 45 | 44.5 | 1 |

paired tests on matched cells (contour seed vs arm seed, exact sign test):
  contour rep0 vs basalt  rep0: 53/61 vs 46/61  W11 L04 p=0.11847
  contour rep0 vs basalt  rep1: 53/61 vs 48/61  W09 L04 p=0.26685
  contour rep0 vs basalt  rep2: 53/61 vs 46/61  W11 L04 p=0.11847
  contour rep0 vs codex   rep0: 53/61 vs 40/61  W16 L03 p=0.00443
  contour rep0 vs codex   rep1: 53/61 vs 41/61  W15 L03 p=0.00754
  contour rep0 vs grok    rep0: 53/61 vs 44/61  W12 L03 p=0.03516
  contour rep0 vs grok    rep1: 53/61 vs 45/61  W11 L03 p=0.05737
  contour rep1 vs basalt  rep0: 52/61 vs 46/61  W13 L07 p=0.26318
  contour rep1 vs basalt  rep1: 52/61 vs 48/61  W11 L07 p=0.48068
  contour rep1 vs basalt  rep2: 52/61 vs 46/61  W13 L07 p=0.26318
  contour rep1 vs codex   rep0: 52/61 vs 40/61  W17 L05 p=0.01690
  contour rep1 vs codex   rep1: 52/61 vs 41/61  W16 L05 p=0.02660
  contour rep1 vs grok    rep0: 52/61 vs 44/61  W13 L05 p=0.09625
  contour rep1 vs grok    rep1: 52/61 vs 45/61  W12 L05 p=0.14346
  contour rep2 vs basalt  rep0: 50/61 vs 46/61  W13 L09 p=0.52347
  contour rep2 vs basalt  rep1: 50/61 vs 48/61  W11 L09 p=0.82380
  contour rep2 vs basalt  rep2: 50/61 vs 46/61  W13 L09 p=0.52347
  contour rep2 vs codex   rep0: 50/61 vs 40/61  W17 L07 p=0.06391
  contour rep2 vs codex   rep1: 50/61 vs 41/61  W16 L07 p=0.09314
  contour rep2 vs grok    rep0: 50/61 vs 44/61  W13 L07 p=0.26318
  contour rep2 vs grok    rep1: 50/61 vs 45/61  W12 L07 p=0.35928
  contour rep3 vs basalt  rep0: 55/61 vs 46/61  W13 L04 p=0.04904
  contour rep3 vs basalt  rep1: 55/61 vs 48/61  W11 L04 p=0.11847
  contour rep3 vs basalt  rep2: 55/61 vs 46/61  W13 L04 p=0.04904
  contour rep3 vs codex   rep0: 55/61 vs 40/61  W18 L03 p=0.00149
  contour rep3 vs codex   rep1: 55/61 vs 41/61  W17 L03 p=0.00258
  contour rep3 vs grok    rep0: 55/61 vs 44/61  W14 L03 p=0.01273
  contour rep3 vs grok    rep1: 55/61 vs 45/61  W13 L03 p=0.02127
```

## Margins with confidence intervals

```
common cells: 61
  basalt   mean pass fraction over its seeds: 0.765 (3 seeds)
  codex    mean pass fraction over its seeds: 0.664 (2 seeds)
  grok     mean pass fraction over its seeds: 0.730 (2 seeds)
  contour  mean pass fraction over its seeds: 0.861 (4 seeds)

contour - basalt  = +0.096  95% CI [-0.020, +0.216]  CI excludes 0: no  (+5.8 cells over 61)
contour - codex   = +0.197  95% CI [+0.066, +0.332]  CI excludes 0: yes  (+12.0 cells over 61)
contour - grok    = +0.131  95% CI [+0.025, +0.246]  CI excludes 0: yes  (+8.0 cells over 61)

Method: seeds averaged per cell first, then 10000 bootstrap resamples of the 61 common cells.
```

## What this proves, and what it does not

- **ChatGPT (`gpt-6.1-sol`, xhigh) and Grok 4.7 are beaten by margins whose 95% CIs exclude zero**:
  see the bootstrap block above (seed-averaged per cell, then resampled over cells). The per-seed exact
  sign tests agree in direction on every seed pair.
- **The same-weights control (bare basalt, no contour) is not separated at 95% confidence.** No single
  contour-vs-basalt seed pair reaches p<0.05. Honest wording: the contour's own contribution on this
  bank is a few cells and still needs more repetitions to pin down.
- Repetitions: contour 4 seeds (rep0 `full-229/`, reps1-3 `reps-229/`), ChatGPT 2, Grok 2, bare basalt 3.
  Per-seed spread is 1-3 cells per arm, so any single-seed comparison anywhere in this repo is
  noise-limited — which is exactly what issue #8 was opened for.
