# Hardware evaluation queue

Standing list of measured-hardware trials that are armed, running, or blocked on a power button.
Rules: one row per trial, state + the exact next action + the artifact that proves it.

| Trial | Machine | State | Next action |
|---|---|---|---|
| Uncapped GPU A/B (power limit on/off, our IQ3_S through Strata) | P2002 "Bonsai" (RX 9070-class, gfx1201, 16 GiB) | **Blocked: box is off.** Wi-Fi only, wired port down → Wake-on-LAN impossible, needs the physical button. A/B script armed at `~/.hermes/scripts/bonsai_uncap_watch.sh` (reads `power1_cap`/`power1_cap_max`, benches capped vs ceiling, restores default, logs temps) | Owner presses power; then run the script and record the delta |
| Small Nemotron models on the GCN4 card | P3001 (RX 580 8 GiB) | Running (pass 4): `NVIDIA-Nemotron-3-Nano-4B-Q4_K_M` (2.84 GB) and `NVIDIA-Nemotron-3.5-Bolt-E4B-UD-Q4_K_XL` (5.06 GB) through llama.cpp b12318 Vulkan, `-pg 512,128` | Record pp/tg table, compare with the 3B ceiling (392 pp / 60 tg) and with the RTX 3050 baseline |
| bmoe streaming where weights exceed RAM | P3001 (RX 580, 62 GiB RAM) | Queued: `NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF` (~18 GB Q4) is the smallest case where the expert set no longer fits RAM, which is the regime bmoe exists for | Download, run `--auto`, compare streamed decode against the mmap baseline |
| CPU-build battery (17 tasks) | P3032 (HP Z220, no AVX2, Strata CPU build) | **Blocked: box is off**, battery runner and the 17 battery files already staged on it | Owner presses power; then run `scripts/run_battery.sh` and score against `ops/ACCEPT-GATE-BATTERY.md` |
| GPU power limit on the fleet brain | P2005 (RTX 5090 Laptop, 24 GB) | Closed by owner rule: the cap is dynamic via `nvidia-powerd` (142–175 W), `nvidia-smi -pl` is forbidden on this box | No action unless the owner reopens it |

Measurement conventions that apply to every row: `power1_cap_max` is a VBIOS ceiling — writes
above it fail with `EINVAL`, so "remove the limit" means "raise to the ceiling the VBIOS allows"
plus `power_dpm_force_performance_level=high` and `pp_sclk_od`/`pp_mclk_od`; log GPU edge temp,
`power1_input` and clocks every second during the load, not after it.
