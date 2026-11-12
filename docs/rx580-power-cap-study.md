# RX 580 on P3001 — GPU power cap vs speed and cost per token

Owner question: how much speed does the card lose if we cap its power, and where is the cheapest
place to run it? Tariff used throughout: **0.25 €/kWh**.

## Method

`scripts/gpu_powcap_bench.sh` writes `power1_cap` in sysfs for one round, then benches four models
with llama.cpp Vulkan (`-ngl 99 -fa off -pg 512,128`, one repetition), and a 1 s sampler
(`scripts/gpu_powcap_sampler.sh`) records `power1_input` throughout. `power1_cap_min` is 0 W and
`power1_cap_max` is 120 W, so every cap below the VBIOS ceiling is writable — unlike raising it
above 120 W, which the driver rejects. All five caps (120 / 100 / 70 / 50 / 30 W) completed without
the card hanging or dropping off the bus.

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
| | 30 W | 125.5 | 19.50 | −56.5 % | 36.1 | 39 | 0.51 | 0.129 |
| Nemotron-3-Nano-4B Q4_K_M | 120 W | 258.6 | 31.16 | — | 106.6 | 120 | 0.95 | 0.238 |
| | 100 W | 241.1 | 30.68 | −1.5 % | 89.0 | 109 | 0.81 | 0.201 |
| | **70 W** | 179.1 | 26.75 | −14.2 % | 67.8 | 78 | **0.70** | **0.176** |
| | 50 W | 120.2 | 18.55 | −40.5 % | 47.9 | 50 | 0.72 | 0.179 |
| | 30 W | 78.6 | 12.20 | −60.8 % | 33.4 | 45 | 0.76 | 0.190 |
| Nemotron-3.5-Bolt-E4B Q4_K_XL | 120 W | 420.4 | 24.12 | — | 101.0 | 120 | 1.16 | 0.291 |
| | 100 W | 407.6 | 23.82 | −1.2 % | 86.2 | 100 | 1.00 | 0.251 |
| | **70 W** | 266.2 | 20.62 | −14.5 % | 65.5 | 70 | **0.88** | **0.221** |
| | 50 W | 184.4 | 14.02 | −41.9 % | 48.3 | 63 | 0.96 | 0.239 |
| | 30 W | 144.4 | 9.11 | −62.2 % | 34.2 | 41 | 1.04 | 0.261 |

Raw data: `docs/data/rx580-powcap-20261112/` (1 s sampler CSV, bench report, run windows, and the
aggregation script that produced this table).

## Our own 77 GiB MoE (`Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S`, `-ngl 99 -ncmoe 99`)

This model needs 12 s between arms — consecutive bench runs left the VRAM unreleased and the next
context failed to build (so the failures inside the first pass were flakiness, not the missing
resizable BAR).

| cap | pp512 | tg128 | Δ decode vs 120 W | avg W | peak W | Wh / 1k tokens | € / 1M tokens |
|---|---|---|---|---|---|---|---|
| 120 W | 50.2 | 6.44 | — | 69.5 | 115 | 3.00 | 0.75 |
| 100 W | 51.5 | 6.74 | +4.7 % | 73.6 | 107 | 3.03 | 0.76 |
| 70 W | 44.3 | 6.63 | +3.0 % | 62.9 | 80 | 2.64 | 0.66 |
| 50 W | 34.0 | 6.59 | +2.3 % | 49.6 | 71 | 2.09 | **0.52** |
| 30 W | 22.2 | 5.03 | −21.9 % | 32.1 | 44 | 1.77 | 0.44 |

Raw data: `docs/data/rx580-powcap-20261112/powcap_ours_*`.

This inverts the small-model rule. **Decode of the big MoE barely depends on the GPU power cap**
(6.44 → 6.59 t/s from 120 W to 50 W) because its expert weights live in system RAM and the GPU only
assists; what the cap does is cut prefill (50 → 34 → 22 t/s) and the card's draw (70 → 50 → 32 W).
Cost per token therefore keeps falling all the way down: **0.75 € → 0.52 € at 50 W (−30 %), 0.44 € at
30 W (−41 %)**. The 100 W row is noise at the top of the curve (its decode is 4.7 % *above* the 120 W
row), which is also why the model needs repetition before any top-end claim.

## Verdict

* **For models that fit in VRAM, 70 W is the sweet spot.** Cutting the cap from 120 W to 70 W costs
  ~36 % of the power (≈101 → 65 W) and only ~12–15 % of generation speed, so cost per million
  tokens falls **26–28 %** (3B: 0.156 → 0.114 €, Nano-4B: 0.238 → 0.176 €, Bolt-E4B: 0.291 → 0.221 €).
* **For the 77 GiB MoE the cap is a prefill knob, not a decode knob** — decode is flat to 50 W and
  cost per token falls monotonically, so the right cap there is **50 W (−30 % cost, free decode)** and
  30 W only for latency-insensitive batch work.
* **100 W is free speed**: −1 % throughput for −13 W. Worth taking if the box has to stay cool or
  quiet, no reason to leave the card there if the goal is efficiency.
* **50 W is where efficiency turns back up**: decode falls 37–42 % while watts fall only ~52 %, and
  Wh per 1k tokens rises above the 70 W row for all three models. Going below 50 W buys nothing.
* **30 W is a dead end for VRAM-resident models, not for the offloaded MoE**: the small models fall to
  9–20 t/s and their cost per token rises 13–18 % above the 70 W optimum, while the big MoE is still
  getting cheaper per token at 30 W (prefill is what collapses). In both cases the card survives the
  cap — no hang, no reset.
* **Prefill pays for the cap much more than decode** (3B pp512: 372 → 233 at 70 W, −37 %, versus
  −12 % decode). If the workload is long-prompt / RAG-style, keep the card at 100–120 W; if it is
  chat-style generation, run it at 70 W.
* Practical rule for this card in the fleet: **VRAM-resident model → cap 70 W** (chat/background) or
  **100–120 W** (prompt-heavy). **Offloaded big MoE → cap 50 W**, 30 W for batch only. Never cap
  below 30 W — the card still runs, it just stops being useful.

## To finish

* Repetitions at the top of the curve (120 vs 100 W) for the big MoE — the 100 W row measured
  *faster* than 120 W, which is run-to-run noise, not a real gain.
* Clock logging: the sampler's `gpu_clock` fallback did not parse `pp_dpm_sclk` on this kernel, so
  the clock column is empty; fixed in `scripts/gpu_powcap_sampler.sh` for the next pass.
* Applying the caps permanently (a udev rule or a boot script writing `power1_cap`) once the owner
  picks the fleet default.
