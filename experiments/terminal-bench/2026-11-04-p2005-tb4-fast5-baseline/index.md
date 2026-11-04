# Terminal-Bench 4.0 fast baseline: bare Hermes on P2005

This is an **independent run**, not an official Terminal-Bench 4.0 leaderboard submission. Official leaderboard evaluation uses five attempts per task.

- Run: `tb4-fast5-baseline-20261104-070835`
- Completed: 3 / 5
- Solved: 1
- Failed: 2
- Success rate among completed trials: 33.33%
- Tokens (available trials): input `26044`, output `22351`
- Infrastructure failures: `4` recorded
- Attempt exceptions: `2` total, `1` without a reward
- Forecast: `3.0 h remaining (low confidence)`
- GPU energy observed: `184.99 Wh active, mean `70.4 W`
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
| `fin-saccr-rwa` | 0.0 | 4162.160373 s | None | 22 / 24 | [report](tasks/fin-saccr-rwa__xDghuiW/trial.md) |
| `mp-checkpoint-consolidation` | 0.0 | 11018.548148 s | None | 0 / 4 | [report](tasks/mp-checkpoint-consolidation__WdEavAw/trial.md) |
| `risk-scorer-replay` | None | 270.120898 s | None | None / None | [report](tasks/risk-scorer-replay__MVYQn2T/trial.md) |

See `data/cumulative-summary.json` for machine-readable totals.
Raw private paths and network endpoints are redacted. Raw hidden-test stdout is not published.

Prior infrastructure attempts: [notes/prior-infrastructure-attempts.md](notes/prior-infrastructure-attempts.md).

Next experiment plan: [notes/next-brain-plan.md](notes/next-brain-plan.md).
