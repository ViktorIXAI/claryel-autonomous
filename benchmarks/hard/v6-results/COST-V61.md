# Time and energy accounting, bank v6.1

| arm | tasks | model calls | tokens in/out | wall seconds | GPU energy |
|---|---|---|---|---|---|
| contour 0.0.2.29 rep0 | 77 | 141 | 26298 / 9786 | 545 s | see window note |
| contour 0.0.2.29 reps 1-2 | 154 | 285 | 53151 / 17902 | 294 s | see window note |
| contour 0.0.2.29 rep3 | 77 | 141 | 25641 / 9044 | 151 s | 6.82 Wh measured over 77 tasks (281 s at 87 W mean, busy 0.44) = 0.0886 Wh/task |
| contour 0.0.2.29 reps 4-5 | 154 | 279 | 50998 / 18094 | 265 s | 13.02 Wh measured over 154 tasks (540 s at 87 W mean, busy 0.43) = 0.0845 Wh/task |
| bare basalt reps 1-2 (local GPU, no contour) | 142 | 142 (one shot each) | not reported | 2679 s | 30.45 Wh measured over 65 tasks covered by the sampler (916 s at 120 W, busy 0.90) -> 0.4684 Wh/task -> 33.26 Wh per 71-task arm (scaled from the sampled window) |
| ChatGPT (codex CLI) rep1 | 142 | 142 | not reported by the CLI transport | 1172 s | not measurable from this machine |
| Grok (hermes CLI) rep1 | 95 | 95 | not reported by the CLI transport | 2394 s | not measurable from this machine |

Reproduce: `scripts/gpu_energy.py` integrates the same trace; the sampler command is in
`ENERGY-METHOD.md`.

Windows for the contour energy rows come from the runner's own `*-start.epoch` / `*-end.epoch` files; the
bare-arm window from the run log's mtime and the sampler's first sample. `ENERGY-METHOD.md` states what the
method cannot see. Grok repetition 3 was still running when this was generated, so its row stays at two
seeds in every score table; an unfinished arm is never scored as finished.
