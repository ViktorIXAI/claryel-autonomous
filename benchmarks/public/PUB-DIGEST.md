# Public benchmark percent digest

One row per scored arm, newest first, written by `scripts/pub_bench_score.py`. Rows are only comparable when the task-file sha16 and the call parameters match. Deterministic checkers live here; the HumanEval `pytest-v1` execution checker lives in `scripts/pub_bench_exec.py` and names itself in the call column; an unshipped checker keeps its tasks out of the denominator and says so. Checker contract in force: `pub-checkers-v2` - the scorer refuses to publish while its own self-test fails, and a gold the contract cannot parse is scored as UNSCORED, never guessed. A row re-scored under another contract id is a new row, not an edit.

| bench | model | tasks | tasks sha16 | call | strict |
|---|---|---|---|---|---|
| mmlu-pro | gpt-6.1-sol | 500 | c64264aede2498c7 | codex codex-cli 0.166.0 CLI (sampling params not exposed by the transport) | 462/500 = **92.4%** |
| mmlu-pro | qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56 | 500 | c64264aede2498c7 | frozen contour runtime 0.0.2.56 (behavior 2.56): bare-matched: first rung = LADDER[0], no seed, no reasoning_effort, no chat_template_kwargs (serve default thinking), ladder rungs 1200, first rung 1200 | 429/500 = **85.8%** |
| mmlu-pro | qwen3.8-flash-next-iq3_s-basalt | 500 | c64264aede2498c7 | temp 0.7, max_tokens 1200 | 432/500 = **86.4%** |
| humaneval | qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56 | 164 | 971d976289cd9357 | frozen contour runtime 0.0.2.56 (behavior 2.56): bare-matched: first rung = LADDER[0], no seed, no reasoning_effort, no chat_template_kwargs (serve default thinking), ladder rungs 1200, first rung 1200; checker pytest-v1 | 155/164 = **94.5%** |
| gsm8k | qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56 | 300 | 7dd0080ff23b8bc3 | frozen contour runtime 0.0.2.56 (behavior 2.56): bare-matched: first rung = LADDER[0], no seed, no reasoning_effort, no chat_template_kwargs (serve default thinking), ladder rungs 1200, first rung 1200 | 294/300 = **98.0%** |
| arc-easy | qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56 | 300 | cac604a076e8b00a | frozen contour runtime 0.0.2.56 (behavior 2.56): bare-matched: first rung = LADDER[0], no seed, no reasoning_effort, no chat_template_kwargs (serve default thinking), ladder rungs 1200, first rung 1200 | 289/300 = **96.3%** |
| arc-challenge | qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56 | 300 | 523af08216f14256 | frozen contour runtime 0.0.2.56 (behavior 2.56): bare-matched: first rung = LADDER[0], no seed, no reasoning_effort, no chat_template_kwargs (serve default thinking), ladder rungs 1200, first rung 1200 | 291/300 = **97.0%** |
| gpqa-diamond | qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56 | 198 | af73cc064d4d8529 | frozen contour runtime 0.0.2.56 (behavior 2.56): bare-matched: first rung = LADDER[0], no seed, no reasoning_effort, no chat_template_kwargs (serve default thinking), ladder rungs 1200, first rung 1200 | 139/198 = **70.2%** |
| gpqa-diamond | gpt-6.1-sol | 198 | af73cc064d4d8529 | codex codex-cli 0.166.0 CLI (sampling params not exposed by the transport) | 192/198 = **97.0%** |
| gpqa-diamond | qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56 | 198 | af73cc064d4d8529 | frozen contour runtime 0.0.2.56 (behavior 2.56): streamed request, request_seed pinned (sp1), ladder rungs 512,1200, enable_thinking off | 91/198 = **46.0%** |
| arc-challenge | qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56 | 300 | 523af08216f14256 | frozen contour runtime 0.0.2.56 (behavior 2.56): streamed request, request_seed pinned (sp1), ladder rungs 512,1200, enable_thinking off | 283/300 = **94.3%** |
| arc-easy | qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56 | 300 | cac604a076e8b00a | frozen contour runtime 0.0.2.56 (behavior 2.56): streamed request, request_seed pinned (sp1), ladder rungs 512,1200, enable_thinking off | 290/300 = **96.7%** |
| arc-challenge | grok-4.7 | 300 | 523af08216f14256 | hermes Hermes Agent v0.23.0+860.gf17db36.dirty (2026.9.24) · upstre toolsets off CLI (sampling params not exposed by the transport) | 288/300 = **96.0%** |
| gpqa-diamond | qwen3.8-flash-next-iq3_s-basalt | 198 | af73cc064d4d8529 | temp 0.7, max_tokens 1200 | 127/198 = **64.1%** |
| humaneval | gpt-6.1-sol | 164 | 971d976289cd9357 | codex codex-cli 0.166.0 CLI (sampling params not exposed by the transport); checker pytest-v1 | 163/164 = **99.4%** |
| gsm8k | qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56 | 300 | 7dd0080ff23b8bc3 | frozen contour runtime 0.0.2.56 (behavior 2.56): streamed request, request_seed pinned (sp1), ladder rungs 512,1200, enable_thinking off | 290/300 = **96.7%** |
| arc-challenge | gpt-6.1-sol | 300 | 523af08216f14256 | codex codex-cli 0.166.0 CLI (sampling params not exposed by the transport) | 290/300 = **96.7%** |
| humaneval | qwen3.8-flash-next-iq3_s-basalt | 164 | 971d976289cd9357 | temp 0.7, max_tokens 1200; checker pytest-v1 | 158/164 = **96.3%** |
| arc-easy | grok-4.7 | 300 | cac604a076e8b00a | hermes Hermes Agent v0.23.0+860.gf17db36.dirty (2026.9.24) · upstre toolsets off CLI (sampling params not exposed by the transport) | 289/300 = **96.3%** |
| gsm8k | qwen3.8-flash-next-iq3_s-basalt | 1319 | 7dd0080ff23b8bc3 | temp 0.7, max_tokens 1200 | 1284/1319 = **97.3%** |
| arc-easy | gpt-6.1-sol | 300 | cac604a076e8b00a | codex codex-cli 0.166.0 CLI (sampling params not exposed by the transport) | 290/300 = **96.7%** |
| arc-challenge | qwen3.8-flash-next-iq3_s-basalt | 1172 | 523af08216f14256 | temp 0.7, max_tokens 1200 | 1129/1172 = **96.3%** |
| arc-easy | qwen3.8-flash-next-iq3_s-basalt | 2376 | cac604a076e8b00a | temp 0.7, max_tokens 1200 | 2261/2376 = **95.2%** |
| gsm8k | grok-4.7 | 300 | 7dd0080ff23b8bc3 | hermes Hermes Agent v0.23.0+860.gf17db36.dirty (2026.9.24) · upstre toolsets off CLI (sampling params not exposed by the transport) | 288/300 = **96.0%** |
| gsm8k | gpt-6.1-sol | 300 | 7dd0080ff23b8bc3 | codex codex-cli 0.166.0 CLI (sampling params not exposed by the transport) | 293/300 = **97.7%** |
| gsm8k | qwen3.8-flash-next-iq3_s-basalt | 25 | 7dd0080ff23b8bc3 | temp 0.7 | 24/25 = **96.0%** |
