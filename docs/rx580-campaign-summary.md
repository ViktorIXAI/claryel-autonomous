# RX 580 2048SP on P3001 — campaign summary (2026-11-12)

One page for the whole experiment: the card the owner bought, what it does well, everything that
failed and why, measured power draw, the limits found, and the energy cost per token. Detailed
runs live in `docs/rx580-p3001-field-test.md`, `docs/amd-gcn4-inference-engines.md` and
`docs/bigmoeonedge-p3001.md`.

Machine: P3001 — Xeon E5-2697 v2 (12c/24t, AVX1 only), 62 GiB DDR3-1333 ECC, FireCuda 530R NVMe,
Radeon RX 580 2048SP (Polaris 20 XL, gfx803, 8 GiB, 32 CU), Quadro K620 still present.
Model of record: our `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S` (79.7 GiB on disk, arch `qwen4exp`).

## Verdict

**Do not buy this card for the fleet.** On our model it is 4–5× slower than the RTX 3050 that was
in the same box and costs ~3.6× more per token. It is healthy and cool, and it is a legitimate
cheap spare **only** for models that fit in 8 GiB — there it is genuinely useful and cheap to run.
Recommendation: put the RTX 3050 back.

## What worked

| Item | Measured |
|---|---|
| Drivers / stack | `amdgpu 3.57.0`, Mesa 25.2.8, Vulkan 1.4, `rocminfo` enumerates gfx803, RADV device name visible |
| llama.cpp prebuilt Vulkan (`b12318`, zero build) | loads our 2-shard IQ3_S GGUF **unmodified**, no conversion |
| Our model, CPU only | pp512 44.2 / 4.09 t/s decode |
| Our model, `-ngl 99 -ncmoe 99 -ctk q8_0` | pp512 33.9 / 5.85 t/s (stock clocks) |
| Same, `high` + OD +5 % | pp512 52.9–53.9 / **8.26 t/s** (+34 % prefill, +41 % decode) |
| Offload depth curve (`-ncmoe 99`) | `-ngl` 4/12/24/48/99 → 4.28/4.72/5.50/7.78/**7.93** t/s — partial offload works |
| 3B Q4_K_M fully resident | 392 pp512 / **60** t/s |
| Nemotron-3-Nano-4B Q4_K_M (2.63 GiB, hybrid Mamba) | 268 pp512 / **40.2** t/s (CPU-only same file: 131 / 10.2) |
| Nemotron-3.5-Bolt-E4B Q4_K_XL (4.70 GiB) | **441** pp512 / **30.4** t/s |
| BigMoeOnEdge 0.42 (Vulkan pack) | runs on the card with no ROCm; reads our shards; its planner correctly declines streaming |

The split is unambiguous: **the card is fine, our model is the problem.** Anything ≤5 GiB runs at
30–60 t/s; our 79.7 GiB MoE does not fit in 62 GiB RAM, so every token pays DDR3-1333 page-cache
misses and the GPU mostly waits.

## What failed, with the cause

| Failure | Cause / evidence |
|---|---|
| Strata on this card | `setup.sh --backend hip --check` → "no AMD GPU Strata can use"; the engine's arch set is gfx906…gfx1201 with **no gfx803**, and Ubuntu 24.04 ships no `rocblas`/`hipblas` at all; rocBLAS Tensile dropped gfx803 in ROCm 5.0 |
| Removing the power limit | `power1_cap_max` = 120 W from the VBIOS; writes of 130/150/185 W → `EINVAL`. Only a VBIOS flash goes higher — not attempted on a warranty card |
| Clock-mask tuning | `echo 0xff > pp_dpm_sclk` / `0x7 > pp_dpm_mclk` → `EINVAL` while `power_dpm_force_performance_level=high`; only `pp_sclk_od`/`pp_mclk_od` (+5 % → 1348/1837 MHz) were accepted, and they do not survive reboot |
| Compute power profile | `pp_power_profile_mode = COMPUTE` is silently ignored, stays `3D_FULL_SCREEN` |
| 262K context on this card | q8_0 KV ≈ 36 GiB, q4_0 ≈ 15 GiB — impossible in 8 GiB VRAM; the tested 8 GiB ceiling for KV+weights is a few tens of thousands of tokens |
| bmoe streaming on this box | 1.77–2.24 t/s vs 3.46 mmap vs 7.93 plain llama.cpp; 295.6 ms/token of **CPU** compute at 8 threads (AVX1) even at 92 % expert-cache hits, so streaming only adds I/O |
| A/B under a RAM cap | `systemd-run --scope -p MemoryMax=30G` → "Interactive authentication required"; no cgroup cap without sudo, so that scenario needs `--cache-mb` + `--dense-weights anon` instead |
| bmoe device-cache arm | `--device-cache-mb` conflicts with `--overlap`, needs `--gpu-layers > 0`; the retry then failed to load the model right after the previous run |
| First RTX 3060 "baseline" on B2003 | invalid: `GGML_VK_VISIBLE_DEVICES=0` selected the Intel ARL iGPU; the 3060 was Vulkan1 with 823 MiB free under its running serve |
| Bench tooling traps | `llama-bench` has no `-c` (use `-pg "pp,tg"`); HF two-shard URL guess 404s; an unbracketed `pkill -f` over SSH kills the SSH session itself |
| **Our own methodology bug** | a bench loop resolved the binary as `$(dirname …)` instead of the file, so four Nemotron rows came out silently empty — an empty row is a missing arm, not a zero; fixed and re-run, numbers above are the re-run |

## Power, thermals, limits (measured, hwmon sampled 1 s)

| State | GPU edge temp | Card power | Clocks | Fan |
|---|---|---|---|---|
| Idle | 27–30 °C | 14 W | 300 MHz | ~1780 rpm / 34 % |
| Sustained Vulkan load (stock) | 54–59 °C | 110–116 W | 1133 → ~900 MHz (SMU throttle) | 1766–1905 rpm / 34–38 % |
| Sustained load with OD +5 % | ~55 °C | 107–112 W | 850–1086 MHz, top states 1348/1837 MHz | same |
| CPU under the same load | max ~42 °C | — | — | RAM ~53/62 GiB, swap untouched |

The card is **power-limited, not thermal-limited**: the SMU pulls the core to ~900 MHz at ~110 W
long before the cooler matters. Hard limit: 120 W VBIOS cap, no driver path above it.

### Energy cost per token (tariff 0.25 €/kWh, card-only watts; box adder ~60 W labelled separately)

| Configuration | t/s | Wh per 1k tokens | € per 1M tokens (card) |
|---|---|---|---|
| RX 580 + our IQ3_S (best config) | 8.26 | 3.77 | 0.94 |
| RX 580 + Nemotron-3-Nano-4B | 40.2 | 0.77 | 0.19 |
| RX 580 + Nemotron-3.5-Bolt-E4B | 30.4 | 1.02 | 0.26 |
| RX 580 + 3B Q4_K_M | 60.0 | 0.54 | 0.13 |
| **RTX 3050 + our IQ3_S (Strata baseline)** | 27.0 | 1.03 | 0.26 |
| RTX 3050 + our IQ3_S, 262K config | 23.5 | 1.18 | 0.30 |

With the ~60 W CPU/board adder the same four RX 580 rows become 5.78 / 1.19 / 1.57 / 0.81 Wh per
1k tokens. Continuous 24/7 the card alone costs 0.34 kWh/day idle (0.084 €) and 2.69 kWh/day under
load (0.672 €). Read as: **for our model this card costs 3.6× more per token than the RTX 3050;
for a ≤5 GiB model it costs less per token than the RTX 3050 does on our model.**

## Bonsai 2 (the model the owner actually asked for)

`prism-ml/Ternary-Bonsai-2-27B-gguf` — ternary compression of Qwen3.8-27B: **5.95 GB (PTQ1_0) /
7.21 GB (PQ2_0) / 7.63 GB (Q2_0)**, 262K context, ~75 % linear attention, vision via a separate
mmproj. Sizes 2B / 4B / 9B / 27B exist. `Q2_0` runs on stock llama.cpp from b11556; `PTQ1_0` and
`PQ2_0` need the PrismML llama.cpp fork, which publishes a **prebuilt Linux Vulkan binary**
(`llama-prism-b12128-d7b2896-bin-ubuntu-vulkan-x64.tar.gz`) — so the GCN4 card needs no build and
no ROCm.

### Bonsai 2 27B measured on the RX 580 (card at `high` + OD +5 %)

| Packing | Engine | pp512 | tg128 | € per 1M tokens (card at ~112 W) |
|---|---|---|---|---|
| **Q2_0 (7.09 GiB)** | **stock llama.cpp b12318 Vulkan** | **44.5** | **9.03** | 0.86 |
| Q2_0 | PrismML fork `prism-b12128` | 42.6–44.4 | 4.81–4.83 | 1.61 |
| PTQ1_0 (5.53 GiB) | PrismML fork | 36.5–37.0 | 3.91–3.93 | 1.98 |
| PTQ1_0, CPU only (`-ngl 0`) | PrismML fork | 29.0 | 1.75 | — |

Offload sweep (fork, PTQ1_0, decode): `-ngl` 8/16/24/40/99 → 2.04 / 2.22 / 2.32 / 3.17 / 3.93 t/s,
so the GPU is doing real work — the fork's CPU path on AVX1 is simply terrible.

Verdict for this family on GCN4: **use the mainline `Q2_0` packing with stock llama.cpp, not the
fork's dense ternary packs.** The fork's `PTQ1_0`/`PQ2_0` kernels are ~2× slower on Polaris, which
reports `fp16: 0 | int dot: 0 | matrix cores: none` — exactly the hardware those kernels were not
written for, and their Vulkan FWHT PR is still a draft upstream. A 27B-class model at 9 t/s inside
7 GiB suits background work, not interactive chat; the card's fast, useful range stays ≤5 GiB
(30–60 t/s). Thermals through these runs: 43–54 °C, 14 W idle, ~42 W settling after load — still
nowhere near a thermal limit.
