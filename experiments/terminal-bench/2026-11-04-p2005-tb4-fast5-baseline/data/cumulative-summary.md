# Cumulative summary

- Run: `tb4-fast5-baseline-20261104-070835`
- Completed: 4 / 5
- Solved: 1
- Failed: 3
- Success rate among completed trials: 25.0%
- Available input tokens: 26044
- Available output tokens: 22351
- Infrastructure failures: 6
- Forecast: 1.8 h remaining (low; early sample and three H100-dependent tasks remain)

| task | reward | total time | agent time | model calls | tool calls | input tokens | output tokens | verifier |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `embedding-drift-monitor` | 1.0 | 633.621694 s | 398.748934 s | 22 | 25 | 26044 | 22351 | 11 / 11 |
| `fin-saccr-rwa` | 0.0 | 4162.160373 s | 3982.376173 s | no data | no data | no data | no data | 22 / 24 |
| `mp-checkpoint-consolidation` | 0.0 | 11018.548148 s | 10817.930726 s | no data | no data | no data | no data | 0 / 4 |
| `risk-scorer-replay` | no data | 270.120898 s | no data s | no data | no data | no data | no data | no data / no data |
| `shadow-relay` | 0.0 | 9669.146872 s | 9494.789342 s | no data | no data | no data | no data | 1 / 8 |

Official leaderboard status: this is an independent one-pass run, not an official Terminal-Bench 4.0 leaderboard run.
