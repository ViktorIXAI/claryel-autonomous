# Time and energy accounting, bank v6.1

| arm | tasks | model calls | tokens in/out | wall seconds | GPU energy |
|---|---|---|---|---|---|
| contour 0.0.2.29 rep0 | 77 | 141 | 26298 / 9786 | 545 s | see window note |
| contour 0.0.2.29 reps 1-2 | 154 | 285 | 53151 / 17902 | 294 s | see window note |
| contour 0.0.2.29 rep3 | 77 | 141 | 25641 / 9044 | 151 s | 6.82 Wh measured (281 s at 87 W mean, busy 0.44) |
| bare basalt reps 1-2 (local GPU, no contour) | 142 | 142 (one shot each) | not reported | 2679 s | 30.45 Wh measured over 65 tasks covered by the sampler (916 s at 120 W, busy 0.90) -> 0.4684 Wh/task -> 33.26 Wh per 71-task arm (scaled from the sampled window) |
| ChatGPT (codex CLI) rep1 | 71 | 71 | not reported by the CLI transport | 592 s | not measurable from this machine |
| Grok (hermes CLI) rep1 | 71 | 71 | not reported by the CLI transport | 1812 s | not measurable from this machine |

Reproduce: `scripts/gpu_energy.py` integrates the same trace; the sampler command is in
`ENERGY-METHOD.md`.
