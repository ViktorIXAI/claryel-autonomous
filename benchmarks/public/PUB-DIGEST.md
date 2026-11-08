# Public benchmark percent digest

One row per scored arm, newest first, written by `scripts/pub_bench_score.py`. Rows are only comparable when the task-file sha16 and the call parameters match; unscored checkers (pytest, ifeval) are excluded from the denominator and named. Checker contract in force: `pub-checkers-v2` - the scorer refuses to publish while its own self-test fails, and a gold the contract cannot parse is scored as UNSCORED, never guessed. A row re-scored under another contract id is a new row, not an edit.

| bench | model | tasks | tasks sha16 | call | strict |
|---|---|---|---|---|---|
| arc-easy | gpt-6.1-sol | 300 | cac604a076e8b00a | codex codex-cli 0.166.0 CLI (sampling params not exposed by the transport) | 290/300 = **96.7%** |
| arc-challenge | qwen3.8-flash-next-iq3_s-basalt | 1172 | 523af08216f14256 | temp 0.7, max_tokens 1200 | 1129/1172 = **96.3%** |
| arc-easy | qwen3.8-flash-next-iq3_s-basalt | 2376 | cac604a076e8b00a | temp 0.7, max_tokens 1200 | 2261/2376 = **95.2%** |
| gsm8k | grok-4.7 | 300 | 7dd0080ff23b8bc3 | hermes Hermes Agent v0.23.0+860.gf17db36.dirty (2026.9.24) · upstre toolsets off CLI (sampling params not exposed by the transport) | 288/300 = **96.0%** |
| gsm8k | qwen3.8-flash-next-iq3_s-basalt | 1319 | 7dd0080ff23b8bc3 | temp 0.7, max_tokens 1200 | 1284/1319 = **97.3%** |
| gsm8k | gpt-6.1-sol | 300 | 7dd0080ff23b8bc3 | codex codex-cli 0.166.0 CLI (sampling params not exposed by the transport) | 293/300 = **97.7%** |
| gsm8k | qwen3.8-flash-next-iq3_s-basalt | 25 | 7dd0080ff23b8bc3 | temp 0.7 | 24/25 = **96.0%** |
