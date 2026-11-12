# RX 580 on P3001 — GPU power cap vs speed and cost per token

Owner question: how much speed does the card lose if we cap its power, and where is the cheapest
place to run it? Tariff used throughout: **0.25 €/kWh**.

## Method

`scripts/gpu_powcap_bench.sh` writes `power1_cap` in sysfs for one round, then benches four models
with llama.cpp Vulkan (`-ngl 99 -fa off -pg 512,128`, one repetition), and a 1 s sampler
(`scripts/gpu_powcap_sampler.sh`) records `power1_input` throughout. `power1_cap_min` is 0 W and
`power1_cap_max` is 120 W, so every cap below the VBIOS ceiling is writable — unlike raising it
above 120 W, which the driver rejects.

Notes on the setup, recorded because they matter for reading the numbers:

* `power_dpm_force_performance_level` was pinned to `high` for all rounds. That is **not** the
  configuration the earlier field test used, so absolute numbers here are lower for small models
  (3B at `high`: 372/44.8 vs 392/60 at `auto`) — the comparison across caps is what counts.
* Overclock offsets could not be reset: writing `0` to `pp_sclk_od` / `pp_mclk_od` is refused, so
  all rounds ran with the same +5 % offsets. Again consistent across rounds.
* Our own 77 GiB MoE (`-ncmoe 99`) failed to create a context in every round of this pass — the
  known VRAM-release flakiness after the previous bench — so it needs its own spaced pass.

## Result

| Model | cap | pp512 | tg128 | Δ decode vs 120 W | avg W | peak W | Wh / 1k tokens | € / 1M tokens |
|---|---|---|---|---|---|---|---|---|
| Qwen2.5-3B Q4_K_M | 120 W | 372.5 | 44.84 | — | 101.0 | 119 | 0.63 | 0.156 |
| | 100 W | 359.1 | 44.44 | −0.9 % | 88.5 | 100 | 0.55 | 0.138 |
| | **70 W** | 232.9 | 39.50 | −11.9 % | 64.8 | 83 | **0.46** | **0.114** |
| | 50 W | 160.0 | 28.15 | −37.2 % | 48.6 | 54 | 0.48 | 0.120 |
| Nemotron-3-Nano-4B Q4_K_M | 120 W | 258.6 | 31.16 | — | 106.6 | 120 | 0.95 | 0.238 |
| | 100 W | 241.1 | 30.68 | −1.5 % | 89.0 | 109 | 0.81 | 0.201 |
| | **70 W** | 179.1 | 26.75 | −14.2 % | 67.8 | 78 | **0.70** | **0.176** |
| | 50 W | 120.2 | 18.55 | −40.5 % | 47.9 | 50 | 0.72 | 0.179 |
| Nemotron-3.5-Bolt-E4B Q4_K_XL | 120 W | 420.4 | 24.12 | — | 101.0 | 120 | 1.16 | 0.291 |
| | 100 W | 407.6 | 23.82 | −1.2 % | 86.2 | 100 | 1.00 | 0.251 |
| | **70 W** | 266.2 | 20.62 | −14.5 % | 65.5 | 70 | **0.88** | **0.221** |
| | 50 W | 184.4 | 14.02 | −41.9 % | 48.3 | 63 | 0.96 | 0.239 |

Raw data: `docs/data/rx580-powcap-20261112/` (1 s sampler CSV, bench report, run windows, and the
aggregation script that produced this table).

## Verdict

* **70 W is the sweet spot for every model tested.** Cutting the cap from 120 W to 70 W costs
  ~36 % of the power (≈101 → 65 W) and only ~12–15 % of generation speed, so cost per million
  tokens falls **26–28 %** (3B: 0.156 → 0.114 €, Nano-4B: 0.238 → 0.176 €, Bolt-E4B: 0.291 → 0.221 €).
* **100 W is free speed**: −1 % throughput for −13 W. Worth taking if the box has to stay cool or
  quiet, no reason to leave the card there if the goal is efficiency.
* **50 W is where efficiency turns back up**: decode falls 37–42 % while watts fall only ~52 %, and
  Wh per 1k tokens rises above the 70 W row for all three models. Going below 50 W buys nothing.
* **Prefill pays for the cap much more than decode** (3B pp512: 372 → 233 at 70 W, −37 %, versus
  −12 % decode). If the workload is long-prompt / RAG-style, keep the card at 100–120 W; if it is
  chat-style generation, run it at 70 W.
* Practical rule for this card in the fleet: **cap 70 W for background and chat traffic**, 120 W for
  prompt-heavy traffic, never below 50 W.

## To finish

* Cap 30 W round (running while this is written) and a spaced retry pass for our 77 GiB MoE, which
  failed to initialise in this pass.
* Clock logging: the sampler's `gpu_clock` fallback did not parse `pp_dpm_sclk` on this kernel, so
  the clock column is empty; fix in the sampler before the next pass.
