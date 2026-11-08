# Public benchmark percent digest

One row per scored arm, newest first, written by `scripts/pub_bench_score.py`. Rows are only comparable when the task-file sha16 and the call parameters match; unscored checkers (pytest, ifeval) are excluded from the denominator and named.

| bench | model | tasks | tasks sha16 | call | strict |
|---|---|---|---|---|---|
| gsm8k | qwen3.8-flash-next-iq3_s-basalt | 25 | 7dd0080ff23b8bc3 | temp 0.7 | 24/25 = **96.0%** |
