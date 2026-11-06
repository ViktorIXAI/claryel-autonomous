# Time and energy accounting, bank v6.1

| arm | tasks | model calls | tokens in/out | wall seconds | GPU energy |
|---|---|---|---|---|---|
| contour 0.0.2.29 rep0 | 77 | 141 | 26298 / 9786 | 545 s | see window note |
| contour 0.0.2.29 reps 1-2 | 154 | 285 | 53151 / 17902 | 294 s | see window note |
| bare basalt reps 1-2 (local GPU, no contour) | 104 | 104 (one shot each) | not reported | 2250 s | sampler window pending |
| ChatGPT (codex CLI) rep1 | 71 | 71 | not reported by the CLI transport | 592 s | not measurable from this machine |
| Grok (hermes CLI) rep1 | 57 | 57 | not reported by the CLI transport | 1654 s | not measurable from this machine |

Reproduce: `scripts/gpu_energy.py` integrates the same trace; the sampler command is in
`ENERGY-METHOD.md`.

Status at 05:12 CET: the bare-basalt and Grok repetitions are still running, so their energy/scale
columns are marked pending rather than filled with estimates. The contour GPU-energy row fills in when
the fourth contour repetition (rep3) runs on an idle serve immediately after the raw legs finish.
