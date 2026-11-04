# Community benchmark on NVIDIA GeForce RTX 5090 Laptop GPU

Measured on 2026-11-04 with `tools/strata_bench.py` (suite 1, 3 runs per test, medians with ranges). Speeds are the engine's own timings; first-token times are measured by the client over HTTP. Speed only: no correctness check was run.

## Hardware and software

- GPU and VRAM: NVIDIA GeForce RTX 5090 Laptop GPU, 24 GiB VRAM
- CPU: AMD Ryzen 9 9955HX 16-Core Processor (16 cores, 32 threads); installed RAM: 60.5 GiB; storage: nvme1n1 Lexar SSD NM1090 PRO 2TB nvme; nvme0n1 MSI M461 2TB             nvme
- OS: Linux 7.0.0-38-generic; GPU driver: 615.71.09; CUDA (driver supports up to): 13.4
- Strata: project 0.1.56, commit ffa80d73; engine 0.1.56
- GPU detail (after the run, near idle): power_limit_w=[N/A], power_draw_w=55.08, pcie=gen4 x8, pstate=P2, temp_c=52
- Background workloads: not recorded (GPU power limit/draw read above)

## Model and configuration

- Model and quantization: qwen3.8-flash-next-iq3_s
- Context: 262144 tokens; parallel slots: 1
- Settings: the install's own configuration, unchanged; thinking off for the suite; temperature 0

## Method

Run by `python tools/strata_bench.py --long` against the HTTP API of a Strata server (already running); model loading is not timed. One warm-up chat and a 1K prompt are discarded first. Every prompt starts with a unique tag, so the conversation cache cannot help the fresh-prompt tests.

- short chat: the three questions of `tools/ab_engine.py`, up to 100 new tokens, 3 runs
- 4K / 16K prompts: generated word lists sized by a calibration request, 24 new tokens, 3 fresh prompts each
- agent session: system prompt and four tools, then 5 turns that each add about 1500 words of a project file and continue from the model's own earlier answers (the way agent clients resend a conversation), 64 new tokens per turn, 3 sessions; the cache numbers come from the answer's usage (`cached_tokens`) and timings (`prompt_n`)
- concurrency (when run): N requests sent at the same moment, total tokens over the wall time of the burst, latency over all requests

## Results

| Configuration | Actual prompt tokens | Reused tokens | Generated tokens | Runs | Prompt tok/s median and range | Decode tok/s median and range | TTFT seconds median and range |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| short chat | 46 (43-51) | 0 | 100 (100-100) | 9 | not measured | 73.9 (66.7-99.4) | 0.34 (0.30-0.39) |
| 4K prompt, fresh | 4019 (4019-4019) | 0 (0-0) | 24 cap | 3 | 1395.8 (1385.6-1401.0) | not measured | 2.90 (2.89-2.92) |
| 16K prompt, fresh | 16058 (16058-16058) | 0 (0-0) | 24 cap | 3 | 1936.3 (1934.3-1960.3) | not measured | 8.32 (8.22-8.33) |
| 32K prompt, fresh | 32049 (32049-32049) | 0 (0-0) | 24 cap | 3 | 1987.7 (1985.2-1987.8) | not measured | 16.16 (16.16-16.18) |
| agent session, follow-up turns | 13128 (13115-13141) at the last turn | see below | up to 64 | 3 | see below | 80.8 (71.5-97.1) | 2.53 (1.71-2.91) |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: 69.1 % (68.9-69.3); earlier-turn tokens read again per session: 74 (2-144) (earlier turns that the cache did not hold; the 12277 (12277-12278) new tokens of the files are read once); first turn (nothing cached) first token: 1.36 s (1.28-1.38).

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 609 | 0 | 609 | 483.0 | 1.284 | 64.3 |
| 1 | 3378 | 623 | 2755 | 1018.2 | 2.735 | 74.0 |
| 2 | 4911 | 3441 | 1470 | 805.3 | 1.85 | 71.5 |
| 3 | 8155 | 4975 | 3180 | 1133.2 | 2.834 | 80.1 |
| 4 | 10383 | 8219 | 2164 | 974.2 | 2.248 | 80.3 |
| 5 | 13141 | 10431 | 2710 | 1038.7 | 2.634 | 93.0 |

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load is not recorded. Total time of the suite: 155 s.
