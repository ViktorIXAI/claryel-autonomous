# Public benchmark percent digest

One row per scored arm, newest first, written by `scripts/pub_bench_score.py`. Rows are only comparable when the task-file sha16 and the call parameters match; unscored checkers (pytest, ifeval) are excluded from the denominator and named. Checker contract in force: `pub-checkers-v2` - the scorer refuses to publish while its own self-test fails, and a gold the contract cannot parse is scored as UNSCORED, never guessed. A row re-scored under another contract id is a new row, not an edit.

| bench | model | tasks | tasks sha16 | call | strict |
|---|---|---|---|---|---|
| gsm8k | gpt-6.1-sol | 300 | 7dd0080ff23b8bc3 | codex codex-cli 0.166.0 CLI (sampling params not exposed by the transport) | 293/300 = **97.7%** |
| gsm8k | qwen3.8-flash-next-iq3_s-basalt | 25 | 7dd0080ff23b8bc3 | temp 0.7 | 24/25 = **96.0%** |
