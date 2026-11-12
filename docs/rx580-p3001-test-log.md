# P3001 / RX 580 2048SP — full test log, 12.11.2026

Chronological record of every pass run on P3001 after the owner pulled the RTX 3050 and put in a
Radeon RX 580 2048SP 8 GB. Each entry: what was run, the exact command shape, what came back, what
failed and why. All timestamps are UTC as printed by the bench scripts. Raw report files for every
pass are archived in `docs/data/rx580-20261112/raw/`; power-cap data in `docs/data/rx580-powcap-20261112/`.

Interpretation and purchase/energy verdicts live in `docs/rx580-campaign-summary.md`; the power-cap
study in `docs/rx580-power-cap-study.md`; the small-model economics in `docs/rx580-cheap-answer-lane.md`;
the engine survey in `docs/amd-gcn4-inference-engines.md`; the bmoe study in `docs/bigmoeonedge-p3001.md`.

## Machine under test

* P3001: Xeon E5-2697 v2 (Ivy Bridge-EP, 12c/24t, **AVX1 only**), 62 GiB DDR3 ECC 1333, Seagate
  FireCuda 530R 1 TB NVMe on `/home`, Ubuntu 24.04.4, kernel 6.8.0-147.
* Card: `1002:6fdf` Polaris 20 XL / gfx803, 8 GiB VRAM, 32 CU, `amdgpu 3.57.0`, Mesa/RADV, Vulkan 1.4.
  Still present as a second device: Quadro K620 (Vulkan1) — every run pinned the AMD card with
  `GGML_VK_VISIBLE_DEVICES=0`.
* Device capability line printed by every Vulkan run: `uma: 0 | rebar: 0 | fp16: 0 | bf16: 0 | fp4: 0 |
  warp size: 64 | shared memory: 65536 | int dot: 0 | matrix cores: none`.
* VBIOS power knobs: `power1_cap = 120 W`, `power1_cap_max = 120 W`, `power1_cap_min = 0 W`.

## 12:05–12:14 — first bench attempt, then the 3B reference

* `report.txt`: first `llama-bench` invocation used `-c 4096` → `error: invalid parameter for argument: -c`
  on both arms. Cause: `llama-bench` has no context-size flag; context is implied by the `-pg "pp,tg"`
  prompt/generate pair. Tooling trap, recorded so nobody re-wastes a pass on it.
* `report2.txt` — Qwen2.5-3B-Instruct Q4_K_M (1.79 GiB, 3.09 B), fully offloaded:

  | arm | pp512 | tg128 | combined |
  |---|---|---|---|
  | `-ngl 99 -fa on` | 402.43 ± 0.53 | 61.08 ± 0.39 | 184.56 |
  | `-ngl 99 -fa off` | 392.63 ± 0.87 | 60.38 ± 0.37 | 181.19 |
  | `-ngl 0` (CPU only) | 298.67 | 14.88 | 66.55 |

  This is the card's reference point: a model that fits in 8 GiB runs at ~60 t/s decode, and the GPU
  is worth 4× over the CPU path on this box.

## 12:28–12:33 — our own model, first contact

* `report3.txt` — `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S` (2 shards, 77.86 GiB, arch `qwen4exp`, class A3B,
  176.94 B params) read **without any conversion** by stock llama.cpp b12318 Vulkan:
  `-ngl 0`: pp512 44.17, tg128 4.09. Then four consecutive arms died with
  `llama_bench: error: failed to create context with model '…'`.
* `report4.txt` — `-ngl 99 -ncmoe 99`: pp512 33.90, tg128 5.85, tiny-context probe `pp8+tg8` 3.81;
  3B `pp2048+tg256` 220.19. Same context failures again on the big model.
  At this point the working hypothesis was "partial offload does not work on gfx803". It was wrong —
  see 13:31.
* `report5.txt` — 3B flag check `-fa off`: pp512 384.99, tg128 61.91, `pp4096+tg256` 245.41.

## 12:39–13:12 — sustained load and thermals

* `report6.txt` — thermal stress arm: 3B fully resident, `-ngl 99 -fa off -pg 8192,1024 -r 8`:
  pp512 392.01, tg128 59.97, combined 160.75 over 8 repetitions (several minutes of continuous load).
* `temps.badloop.csv` — first thermal logger run wrote 27 MB in ~20 min: the loop was logging on every
  iteration without a sleep. Logger fixed, the bad file is deliberately **not** in the archive (it is
  on the machine as an example of the bug).
* `temps.csv` / `temps_load.csv` (mirrored also as `docs/data/rx580-p3001-temps-load-20261112.csv`) —
  1 s samples of AMD hwmon + CPU coretemp + RAM/swap:

  | state | GPU edge | card power | clocks | fan |
  |---|---|---|---|---|
  | idle | 27–30 °C | 14 W | 300 MHz | ~1780 rpm (34 % PWM) |
  | sustained load | 54–59 °C | 110–116 W | 1133 → ~900 MHz | 1766–1905 rpm (34–38 %) |

  CPU during these passes never passed ~42 °C; RAM 53/62 GiB used, swap untouched. Verdict: the card is
  **power-limited, not thermal-limited** — the SMU drops the core clock to hold 120 W.

## 13:0x — B2003 "RTX 3060 baseline" that turned out invalid

llama.cpp Vulkan + Qwen2.5-3B on B2003 reported pp512 220.79 / tg128 11.40. Device mapping check
showed `GGML_VK_VISIBLE_DEVICES=0` had selected the **Intel ARL iGPU**; the RTX 3060 was Vulkan1 with
823 MiB free because its Strata serve holds the card. The numbers are kept in the record as a labelled
invalid arm (commit `9c56e96`), not as a 3060 measurement. Lesson: read the device line printed by the
run, never assume device 0.

## 13:1x–13:2x — can the 120 W ceiling be lifted?

* Writes to `power1_cap` of 130 W / 150 W / 185 W: all rejected with `Invalid argument`. The ceiling is
  in the VBIOS; only a VBIOS flash would move it, which was not done on the owner's card.
* Accepted knobs: `power_dpm_force_performance_level = high`; `pp_sclk_od = 5`, `pp_mclk_od = 5`
  → top sclk 1348 MHz (vs 1284), top mclk 1837 MHz (vs 1750).
* Rejected/ignored: `pp_dpm_sclk` / `pp_mclk` mask writes while level is `high`;
  `pp_power_profile_mode = COMPUTE` (stays `3D_FULL_SCREEN`).
* Later finding (16:0x): writing `0` back to `pp_sclk_od` is also refused, so an overclock offset
  cannot be reset from userspace — a pass that wants a clean baseline must account for leftover offsets.
* All of this is volatile: it does not survive a reboot.

## 13:23 (`report8`) — flag probe on our model at `high` + OD +5 %

| arm | pp512 | tg128 |
|---|---|---|
| `-ngl 99 -ncmoe 99` baseline | 52.86 | 7.88 |
| `-fa off` | 53.15 | 8.25 |
| `-ctk q8_0 -ctv q8_0` | 53.65 | 8.15 |
| `-fa on` | 53.90 | 8.26 |

Against the auto-state measurement (33.90 / 5.85): **+34 % prefill, +41 % decode** from the clock/state
knobs. Against the incumbent RTX 3050 + Strata (128–188 prefill, 23–31 decode): still ~3× slower.

## 13:31 (`report9`) — offload-depth sweep, and the correction of the earlier hypothesis

| `-ngl` (with `-ncmoe 99`) | pp512 | tg128 |
|---|---|---|
| 4 | 46.73 | 4.28 |
| 12 | 47.81 | 4.72 |
| 24 | 47.58 | 5.50 |
| 48 | 53.46 | 7.78 |
| 99 | 51.51 | 7.93 |

Monotone: the GPU does help this model, and the earlier `failed to create context` arms were
**VRAM-release flakiness between consecutive llama-bench runs**, not an architecture limit. Fix used
everywhere after this: wait ≥8–12 s between arms (or a `sleep` in the loop).

## 14:04–14:25 — BigMoeOnEdge (`bmoe` v0.42.0) on GCN4

* `bmoe_report.txt` (14:04): `--auto` (streaming off) and `--auto --moe-stream --io-threads 4` both
  `rc=0`, 3267 tokens, wall 82.1 s and 79.6 s. Engine diagnostics: `llama_moe_cache … hits = 23966,
  misses = 29324, hit rate = 44.97 %, uploaded = 57301.34 MiB`, and the planner line
  `resolve_fused_ops: layer 3 is assigned to device Vulkan0 but fused top-k mask is assigned to device CPU`.
  The `--auto` planner **declined to stream** because the expert set fits resident RAM — it measured
  NVMe uncached 2.3–3.3 GB/s, Vulkan0 104 GiB/s one-token / 292 GiB/s at 128-wide, experts 47.9 GiB
  (936 MiB/token), resident RAM 52.6 GiB.
* `bmoe_report2.txt` (14:08): three arms all `rc=1` — `--moe-stream --overlap --device-cache-mb 1800`
  (flag conflict: device cache needs `--gpu-layers > 0` and is incompatible with `--overlap`),
  `systemd-run --scope -p MemoryMax=30G` (needs polkit/root), and the comparison arm (broken binary path).
* `bmoe_report3.txt` (14:14–14:25): the three flag-valid variants (`s_ov`, `s_dev`, `s_press`) completed;
  decode 1.77–1.91 t/s.
* `pass4_report.txt` (14:36): 8-thread forced streaming: 111 tokens, `0.446 s/token` = **2.242 t/s**,
  prefill 699 tokens in 71.6 s (9.8 t/s), model load 55.0 s, TTFT 126.6 s, `decode cost: 295.6 ms/token
  of compute at 8 thread(s), 92 % cache hits at 26691 MiB`, `2.4955 cpu-s/token`, 25.98 major faults/token.
  The `D8` device-cache arm died with `could not load the model` (transient, same release-flakiness class).
  Verdict: bmoe runs on this card but is a loss against `llama.cpp -ncmoe 99` (7.93 t/s) wherever the
  weights fit RAM; its own floor is the AVX1 CPU matmul, not the disk.

## 14:36–14:47 — Nemotron small models (downloaded 14:36, benched directly)

| model | Vulkan `-ngl 99 -fa off` | CPU only |
|---|---|---|
| NVIDIA-Nemotron-3-Nano-4B Q4_K_M (2.84 GB) | 268 pp512 / 40.2 tg128 | 131 / 10.2 |
| NVIDIA-Nemotron-3.5-Bolt-E4B Q4_K_XL (5.06 GB) | 441 pp512 / 30.4 tg128 | — |

Note: the automated rows inside `pass4_report.txt` came out **empty** because the bench loop resolved a
directory instead of the binary. An empty row is a missing arm, not a zero — the numbers above are the
direct re-run with `find … -name llama-bench -type f`.

## 14:39–15:52 — PrismML Bonsai 2 (ternary Qwen3.8 family)

`bonsai_report.txt` (27B, PrismML fork `prism-b12128`, build 12128, commit d7b289683, card at
`high` + OD +5 %, cap 120 W):

| arm | pp512 | tg128 | combined |
|---|---|---|---|
| PTQ1_0 (5.53 GiB) `-ngl 99 -fa off` | 36.95 | 3.93 | 18.99 |
| PTQ1_0 `-ngl 0` (CPU) | 29.02 | 1.75 | 7.31 |
| PTQ1_0 long probe `-pg 16384,512` | 36.45 | 3.91 | — |
| Q2_0 (7.09 GiB) fork | 42.63 | 4.83 | 23.95 |
| "Q2_0-stock" arm | 42.68 | 4.83 | 23.97 |

The last row is a **labelled script bug**: that arm resolved the same fork binary, so it proves nothing;
the real stock comparison is the pass below. End-of-pass state: card 42 W / 54 °C, RAM 32/62 GiB, swap 0.

`bonsai_report2.txt` (15:26–15:42, same file, two engines and an offload sweep):

| arm | pp512 | tg128 |
|---|---|---|
| fork Q2_0 `-ngl 99` | 44.41 | 4.81 |
| **stock llama.cpp b12318 Q2_0 `-ngl 99`** | 44.48 | **9.03** |
| fork PTQ1_0 `-ngl 8 / 16 / 24 / 40` | — | 2.04 / 2.22 / 2.32 / 3.17 |

`bonsai9_report.txt` (15:42–15:52, 9B sizes):

| arm | pp512 | tg128 |
|---|---|---|
| 9B PTQ1_0 (1.85 GiB) fork `-ngl 99` | 122.26 | 12.38 |
| 9B PTQ1_0 fork `-ngl 0` | 90.24 | 5.13 |
| **9B Q2_0 (2.37 GiB) stock `-ngl 99`** | **170.01** | **27.35** |

Conclusion for this family: on GCN4 the mainline `Q2_0` packing on stock llama.cpp is the fast path;
the vendor fork's dense ternary packs (`PTQ1_0`/`PQ2_0`) are ~2× slower on Polaris, which has no fp16,
no int-dot and no matrix cores. The 9B Q2_0 row (27 t/s in 2.4 GiB) is the only Bonsai configuration
that makes sense on this card. `bonsai_temps.csv` (66 KB of 1 s samples) covers these passes; peak GPU
60.0 °C, peak 123.21 W, peak CPU 75.0 °C since 15:14 (`temps_summary.txt`).

## 15:43–16:08 — GPU power cap vs speed, small models

`powcap_report.txt` + `powcap_power.csv` + `powcap_windows.txt`; caps written to `power1_cap`,
`level=high`, OD left at +5 % (reset refused), 1 s sampler. Full table and analysis:
`docs/rx580-power-cap-study.md`. Headline: **70 W is the cost optimum for VRAM-resident models**
(3B 0.156 → 0.114 €, Nano-4B 0.238 → 0.176 €, Bolt-E4B 0.291 → 0.221 € per 1M tokens), 100 W is free
speed, 50 W already stops paying, 30 W is a dead end (9–20 t/s, +13…18 % cost per token).
Side finding: pinning `level=high` *hurts* resident models (3B 392/60 at `auto` → 372/45 at `high`).
Our 77 GiB MoE arm failed at every cap with `failed to create context` (no spacing between arms).

## 16:11–16:22 — power cap for our 77 GiB MoE, spaced arms

First launch died instantly on a wrong binary path (`…/llama-bench/llama-bench` — the binary sits at
`…/llama-bench`), relaunch at 16:13 with `-ncmoe 99 -fa off -pg 512,128` and **12 s between arms**: it
worked, which closes the `failed to create context` question as release flakiness, not a BAR limit
(`rebar: 0` is real but not the cause here).

| cap | pp512 | tg128 | avg W | peak W | Wh/1k | € / 1M tokens |
|---|---|---|---|---|---|---|
| 120 W | 50.17 | 6.44 | 69.5 | 115 | 3.00 | 0.75 |
| 100 W | 51.53 | 6.74 | 73.6 | 107 | 3.03 | 0.76 |
| 70 W | 44.25 | 6.63 | 62.9 | 80 | 2.64 | 0.66 |
| 50 W | 34.02 | 6.59 | 49.6 | 71 | 2.09 | **0.52** |
| 30 W | 22.23 | 5.03 | 32.1 | 44 | 1.77 | 0.44 |

Decode is essentially cap-independent to 50 W (the experts live in system RAM); the cap is a prefill
and a watts knob. The 100 W row measuring faster than 120 W is run-to-run noise (1 repetition).
The in-script window summary in this pass was degenerate (1 sample per window, because the start/end
epoch was appended to the wrong line); the numbers above come from `aggregate.py` in
`docs/data/rx580-powcap-20261112/`, which pairs window lines and averages the 1 s sampler inside them.

## Machine state at the end of the day

* `power1_cap` restored to 120 W, `power_dpm_force_performance_level` restored to `auto` (verified by
  reading sysfs back). OD offsets remain at +5 % because resetting them is refused — they are volatile
  and a reboot clears them.
* Engines left installed on the box: llama.cpp b12318 Vulkan (`~/llama-vulkan`), bmoe v0.42.0
  (`~/bmoe`), PrismML fork (`~/bonsai/prism`). Models: Nemotron Nano-4B + Bolt-E4B (`~/nemotron`),
  Bonsai 2 27B + 9B (`~/bonsai/models`), our IQ3_S (`~/Strata-data/models/IQ3_S`).
* Thermal record for the whole day: GPU peak 60.0 °C, card peak 123.21 W, CPU peak 75.0 °C, idle
  27 °C / 14 W / 300 MHz. No thermal event, no hang at any cap down to 30 W.

## Open items (not measured, deliberately parked)

* Repetitions of 120 W vs 100 W for the big MoE (1 repetition each — the ordering is noise).
* Sampler clock column: `gpu_clock` is absent on this kernel and the `pp_dpm_sclk` fallback did not
  parse (fixed in `scripts/gpu_powcap_sampler.sh` for the next pass, not re-run).
* A permanent cap policy (udev/boot write of `power1_cap`) — waiting for the owner to pick the number.
* P2002 power-cap A/B: box is off, wired link down, Wi-Fi only, WOL impossible; script armed at
  `~/.hermes/scripts/p2002_uncap_watch.sh`, nothing measured.
