# Terminal-Bench 4.0 fast baseline: bare Hermes on P2005

This is an **independent run**, not an official Terminal-Bench 4.0 leaderboard submission. Official leaderboard evaluation uses five attempts per task.

- Run: `tb4-fast5-baseline-20261104-070835`
- Completed: 1 / 5
- Solved: 1
- Failed: 0
- Success rate among completed trials: 100.0%
- Tokens (available trials): input `26044`, output `22351`
- Infrastructure failures: `0` recorded
- Forecast: `3.0 h remaining (low confidence)`
- GPU energy observed: `39.94 Wh active, mean `70.83 W`
- Model: `openai/qwen3.8-flash-next-iq3_s`
- Quantization: `IQ3_S GSQ RCO`
- Inference host label: `P2005`
- Hermes: `v0.22.6`
- Harbor: `0.25.0`
- Strata: `0.2.10 (engine 0.1.56)`
- Claryel Autonomous Harness contour in task solving: not used (explicit)

## Completed tasks

| task | reward | total time | model calls | verifier | report |
|---|---:|---:|---:|---:|---|
| `embedding-drift-monitor` | 1.0 | 633.621694 s | 22 | 11 / 11 | [report](tasks/embedding-drift-monitor__4adgop9/trial.md) |

See `data/cumulative-summary.json` for machine-readable totals.
Raw private paths and network endpoints are redacted. Raw hidden-test stdout is not published.

Prior infrastructure attempts: [notes/prior-infrastructure-attempts.md](notes/prior-infrastructure-attempts.md).

Next experiment plan: [notes/next-brain-plan.md](notes/next-brain-plan.md).
