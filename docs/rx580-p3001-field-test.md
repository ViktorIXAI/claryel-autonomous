# RX 580 8 GB (gfx803) field test on P3001 — buy or not

Date 2026-11-12, one machine, ~35 min of measured load. Purpose: the owner put a
newly acquired Radeon RX 580 2048 SP into P3001 (replacing a GeForce RTX 3050 8 GB)
and needs a purchase decision within the hour.


## Audit clarification — 2026-11-12 (issue #25; arithmetic and scope)

This is a dated correction to the observations below, not a new measurement or
replacement of the original readings. The second-pass prefill values 52.9–53.9
t/s versus 33.9 t/s imply **+56.0% to +59.0%**, not the **+34%** written below.
The decode values 7.88–8.26 versus 5.85 imply **+34.7% to +41.2%**;
"+41%" describes only the upper end. Also, the earlier paragraph stating
that partial `-ngl` offload "is broken" was superseded by the later offload-depth
retest (4/12/24/48/99 layers loaded). Preserve both dated observations and
attribute the earlier context-creation errors to the reported transient
VRAM-release condition, not a demonstrated architecture limitation. These
calculations use published numbers only; host readings were not independently
reproduced by this documentation audit.

## Test bed
- P3001: Xeon E5-2697 v2 (12c/24t, **no AVX2**), 62 GiB DDR3-1333 ECC, Seagate
  FireCuda 530R 1 TB NVMe (model tier), Ubuntu 24.04.4, kernel 6.8.
- Card: Radeon RX 580 2048 SP, Polaris 20 XL, PCI `1002:6fdf`, `gfx803`, 8 GiB.
  `amdgpu 3.57.0`, Mesa 25.2.8 → RADV Vulkan 1.4. Card is electrically healthy:
  PCIe Gen3 x16 full width/speed, no PCIe or GPU reset errors in dmesg.
- Engine: llama.cpp **b12318**, stock prebuilt `llama-b12318-bin-ubuntu-vulkan-x64`
  (no build step, no ROCm). Device visible out of the box:
  `Vulkan0: AMD Radeon RX 580 2048SP (RADV POLARIS10) (8192 MiB)`; the leftover
  Quadro K620 shows as Vulkan1, so runs were pinned with `GGML_VK_VISIBLE_DEVICES=0`.
- Engine capability line printed for our card:
  `fp16: 0 | bf16: 0 | fp4: 0 | warp size: 64 | shared memory: 65536 | int dot: 0 | matrix cores: none`.
- Strata still refuses this card (`gfx803` is outside its arch list), see
  `docs/amd-gcn4-inference-engines.md`.

## Our fleet model runs on llama.cpp/Vulkan — but slowly
`Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S` GGUF is already on this box
(`~/Strata-data/models/IQ3_S`, 2 shards). llama.cpp reads it natively:
`qwen4exp A3B IQ3_S - 3.4375 bpw | 77.86 GiB | 176.94 B` — no conversion needed.

| config (llama.cpp b12318)                    | pp512 t/s | tg128 t/s |
|----------------------------------------------|----------:|----------:|
| `-ngl 0` (CPU + NVMe mmap)                   | 44.2      | **4.09**  |
| `-ngl 99 -ncmoe 99 -ctk q8_0 -ctv q8_0`      | 33.9      | **5.85**  |
| reference: same model, **Strata on the RTX 3050 8 GB** we removed (16K–256K ladder, 11.11) | 128–188 | **23–31** |

So the GPU is worth only +43 % on decode here, and the whole setup is 4–5× slower
than the Strata + RTX 3050 line it replaced.

Offload-depth curve for our model (`-ncmoe 99`, i.e. all MoE experts on CPU, stock
clocks): `-ngl 4` 4.28 → `-ngl 12` 4.72 → `-ngl 24` 5.50 → `-ngl 48` 7.78 →
`-ngl 99` 7.93 t/s decode. Partial offload is **fine**; the `failed to create
context` errors seen in an earlier sweep were VRAM-release flakiness after a
previous run, not an arch limitation — retry with a few seconds' gap and it loads.

Why: the model is 77.86 GiB and the box has 62 GiB of RAM, so llama.cpp's mmap
streaming misses the page cache on almost every token; A3B activates ~3 B params
per token ≈ 1.3 GB/token, and DDR3-1333 dual channel gives ~20 GB/s. That puts the
decode ceiling for this model on this board near 6–10 t/s regardless of GPU.
Partial layer offload (`-ngl` between 1 and n_layer-1) is broken for this arch in
b12318 — context creation fails; only `-ngl 0` or full `-ngl 99 --n-cpu-moe 99` work.

## What the card is actually good at (fits in 8 GiB)
Qwen2.5-3B-Instruct Q4_K_M (1.79 GiB, fully resident in VRAM, `-ngl 99 -fa off`):

| test                | P3001 / RX 580 8 GB |
|---------------------|--------------------:|
| pp512               | 392.0 ± 1.3 t/s     |
| tg128               |  60.0 ± 0.2 t/s     |
| pp8192 + tg1024     | 160.8 ± 3.0 t/s     |

A same-engine RTX 3060 comparison on B2003 is **not usable**: on that laptop
`GGML_VK_VISIBLE_DEVICES=0` selects the Arrow Lake iGPU (`Vulkan0: Intel(R)
Graphics (ARL)`, shared 35 GiB), which is what produced 220.8 pp512 / 11.4 tg128.
The RTX 3060 is `Vulkan1` and had only **823 MiB free** at the time because its
Strata serve holds the card, so no 3060 Vulkan number was taken. Use the Strata +
RTX 3050 reference above instead.

## Thermals and power (5 s hwmon logger, sustained prefill stress ~13 min)
Log: `docs/data/rx580-p3001-temps-load-20261112.csv` (94 samples at `busy>=90 %`).

| state            | GPU edge °C | GPU W | GPU clock MHz | fan        | CPU max °C |
|------------------|------------:|------:|--------------:|------------|-----------:|
| idle             | 27–30       | 14    | 300           | 1780 RPM / 34 % | 34–42 |
| sustained 100 %  | 54–**59**   | 103–**116** | 900–1134 (throttles to ~900) | 1766–1905 RPM / 34–38 % | 42 |

- **Thermally the card is a non-issue**: 59 °C peak edge at full load on the
  reference blower with the fan never above 38 % PWM. No thermal throttling, no
  hotspot runaway, no VRAM over-temp (Polaris exposes only the `edge` sensor).
- Power is hard-capped: `power1_cap = power1_cap_max = 120 W` — this is a
  cut-down (mining/office) VBIOS, a stock 185 W Polaris board would draw more and
  run hotter. Under load the card sits ~110 W and downclocks to ~900 MHz against
  a 1133 MHz boost, i.e. **power-limit throttled, not temperature limited**.
- System: RAM 10.4 GiB used during the small-model stress, swap untouched; the
  big-model runs pushed RAM/swap but never OOMed.

## Power limit: how far it can actually be pushed (second pass, 13:0x–13:3x)
The 120 W ceiling is written in the VBIOS power table: `power1_cap_max = 120 W`,
and `echo 130000000 > power1_cap` (also 150 W, 185 W) is rejected with
`Invalid argument` — the driver will not go above the table, so "remove the limit"
is only possible by flashing a different VBIOS, which we are not doing on
someone's warranty card.

What can be raised without a flash, and what it buys:

| knob                                        | result                                        |
|---------------------------------------------|-----------------------------------------------|
| `power_dpm_force_performance_level = high`  | accepted; memory pinned at max DPM state      |
| `pp_sclk_od = 5`, `pp_mclk_od = 5` (+5 %)   | top sclk state **1348 MHz** (was 1284), mclk **1837 MHz** (was 1750) |
| `pp_dpm_sclk/mclk` mask writes              | `Invalid argument` while level is `high`      |
| `pp_power_profile_mode = COMPUTE`           | silently ignored, stays `3D_FULL_SCREEN`      |

Measured on our model with those settings (same flags as the table above):

| state          | pp512 t/s | tg128 t/s |
|----------------|----------:|----------:|
| stock (auto)   | 33.9      | 5.85      |
| high + OD +5 % | **52.9–53.9** | **7.88–8.26** |

+34 % prefill and +41 % decode — real, but it does not change the ranking:
8.3 t/s is still ~3× under the RTX 3050 + Strata line (23–31 t/s).
Under sustained load the SMU keeps throttling to 850–1086 MHz at 107–112 W, so the
1348 MHz state is only visible at idle; temperature at full load stayed 55 °C.
These tweaks do not survive a reboot (`pp_sclk_od`/`pp_mclk_od` read back 5 but
`power_dpm_force_performance_level` is back to `auto`).

## Verdict
**Do not buy this card for the fleet inference role.**
1. Strata — the engine the whole fleet runs — does not support gfx803 at all.
2. llama.cpp (Vulkan/RADV) does run, and runs *our* GGUF without conversion, but
   on our model it gives 5.9 t/s decode (8.3 t/s with clocks forced high and
   +5 % overdrive) vs 23–31 t/s on the RTX 3050 we just pulled, and 8 GiB VRAM
   cannot hold the KV for the 256 K context we use (q8_0 KV alone is ~36 GB at
   262144).
3. The card is physically fine and cool (59 °C, 110 W, quiet fan), so it is not a
   lemon — it is simply the wrong tool: no fp16, no int8 dot, no matrix cores,
   8 GiB VRAM, and a 120 W VBIOS.
4. Accept only as a cheap spare for small-model duty (≤8 GiB GGUF: 3B at 60 t/s
   decode, whisper.cpp, sd.cpp) if the price is under ~€30–35; for anything that
   must serve our Qwen3.8-Flash-Next line, put the RTX 3050 8 GB back — it is 4–5×
   faster on the same model and is already supported.
