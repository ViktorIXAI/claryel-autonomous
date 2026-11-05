# P2005 machine specification & measurement methodology (for publication)

Companion to [TECH-REPORT.md](TECH-REPORT.md) and [MAX-BENCH-ADDENDUM.md](MAX-BENCH-ADDENDUM.md).
Everything below read directly from the box on 2026-11-05.

## Hardware (as reported by the machine)

| Component | Detail |
|---|---|
| GPU | NVIDIA GeForce RTX 5090 **Laptop**, GB202 / sm_120, 24 463 MiB GDDR7, PCI 0000:01:00.0, max SM clock 3090 MHz |
| GPU power | dynamic cap 175 W max (`power.max_limit`), managed by nvidia-powerd; observed 96–145 W under decode, 67 °C |
| CPU | AMD Ryzen 9 9955HX, 16 cores / 32 threads, 64 MiB L3 (2 instances) |
| RAM | 2 × 32 GiB Kingston DDR5-5600 (1.1 V), dual channel, ~60.4 GiB usable |
| Storage | Lexar NM1090 PRO 2 TB (Gen5, model pack) + MSI M461 2 TB (system) |
| OS | Linux 7.0.0-38-generic, NVIDIA driver 615.71.09, CUDA 13.0 |

## Software stack

Basalt `v0.2.1` (built on-box, ninja/CUDA13), engine binary self-built, model pack
`Qwen3.8-FN-IQ3_S.basalt` 81.6 GiB (self-converted from our GSQ-RCO-IQ3_S GGUF shards
+ official tuned MTP drafter kit). Server: OpenAI-compatible API, alias
`qwen3.8-flash-next-iq3_s-basalt`, grammar on, GPU vision encoder on.

## Engine configuration (frozen `basalt-config.WORKING-20261105.json`)

```json
{ "max-context": 262144, "kv": "int8", "resident-experts": true,
  "expert-cache": "auto", "prefill": "auto", "vram-reserve-mib": 512,
  "resident-budget-gib": 56, "conversation-cache-mib": 6144,
  "conversation-cache-slots": 6, "conversation-cache-disk-mib": 20480 }
```

Memory tiers: VRAM = dense+head 21.5 GiB + vision ~0.9 + elastic KV (0.7→4 GiB) +
adaptive expert slots, 513 MiB kept free. RAM = 36 GiB pinned (every expert the GPU
does not hold — budget 56 is auto-capped to 49.07 by the engine's own headroom rule,
all experts fit), conversation park 6 GiB, page cache holds the pack warm. Free RAM at
peak load measured 0.6–0.9 GiB; engine guard (MemAvailable + PSI) parks conversations
to the 20 GiB disk tier rather than degrading a live request.

## Measurement methodology — why published decode varies

Decode tok/s in these reports is the **average over one generation window**, taken from
the engine's own `timings.predicted_per_second`. The window length is part of the
protocol and changes the number materially:

| Generation window | Decode measured | What it represents |
|---|---|---|
| 64 tokens (quickbench ladder) | 141–207 | burst rate: warm placement, KV still small — matches "instantaneous" engine-log rates |
| 900–1200 tokens (long warm) | 112–168 (typ. 131–150) | **sustained** chat/agent speed: KV growth + adaptive swap rounds settle the rate |

So the 206.7 tok/s headline at 16k is real but describes a ~0.3-second burst; a long
answer runs at ~130–150 tok/s end-to-end. Both numbers are published side by side in
MAX-BENCH-ADDENDUM.md; the honest summary is: *burst 160–220, sustained 130–165, on an
idle endpoint with warm caches and 512 MiB VRAM reserve.* Draft acceptance stayed
68–79% across all windows — the settle comes from KV attention cost and expert churn,
not speculation failure.

## Run-to-run scatter (6× repeated ladder, idle endpoint, same day)

Single-shot ladder rows vary; publishing only one sample understates or overstates the
box. Measured distributions of 64-token decode, same context each time:

| Context | min / median / max, tok/s | draft acc range |
|---:|---|---|
| 16 448 | 175 / 196 / **219** | 0.73–0.82 |
| 32 832 | 178 / 201 / 202 | 0.72–0.78 |
| 65 600 | 56* / 166 / 200 | 0.66–0.81 |

\*first call after a large context jump pays a KV/expert reallocation hitch (56);
subsequent calls at the same context sit at 166–200. The 218.2 tok/s recorded at 64k
in the first published ladder sits at the top of this distribution — it is the
reproducible ceiling band (~200–220 at 16k–64k), not a fluke, and not the typical
value either. Median is the number to quote for "normal speed"; max for "ceiling".

Bench environment for the max run: endpoint fully idle (Hermes brain parked on Mac
Studio), 2 warmup rounds of 3 conversations before the ladder, RAM at contracted floor,
GPU 145 W / 67 °C at measurement time. When the brain shares the endpoint (production
case), expect ~15% below these numbers.

## CPU frequency limit experiment + whole-system thermals (2026-11-05)

The box ships with an OS-level CPU cap: `scaling_max_freq = 4.5 GHz` (hardware max
5.46 GHz), governor performance, boost on, platform profile performance. We tested
whether the cap costs inference speed: uncapped all cores to 5.46 GHz, re-ran the 6×
ladder + a 1200-token generation, then restored 4.5 GHz (verified back).

Result: **no measurable gain** — 16k median 194 (vs 196 capped), 32k 188 (vs 201),
64k 157 (vs 166) — all within run scatter; the long 1200-token run hit **175.9 tok/s**
(best sustained figure of the day) but that tracks drafter luck, not CPU clocks.
Inference here is GPU-bound; CPU mostly feeds the expert stream. Since uncapped CPU
pushed Tctl to 97 °C against a 100 °C ceiling, the 4.5 GHz cap is kept (it buys
thermals for nothing).

Whole-system temperatures logged every ~2 s through the whole test (CPU k10temp Tctl,
both DDR5 DIMMs via spd5118, both NVMe controllers, GPU via NVML):

| Sensor | min | median | max | verdict |
|---|---:|---:|---:|---|
| CPU (Tctl) | 63 °C | 79 °C | **97 °C** | hot under bench bursts, 3 °C from ceiling |
| DIMM1 / DIMM2 (DDR5) | 50 / 46 °C | 51 / 47 °C | 52 / 48 °C | normal (throttle at 85+) |
| NVMe MSI M461 | 39 °C | 39 °C | 39 °C | cool |
| NVMe Lexar NM1090 | 33 °C | 33 °C | 33 °C | cool |
| GPU (RTX 5090 Laptop) | 49 °C | 57 °C | 63 °C | far from limit (87+) |
| GPU power | 26 W | 37 W | 142 W | within the 175 W dynamic envelope |

GPU throttle-event flags during the run: `0x400` HW-power-brake (the chassis'
nvidia-powerd regime — normal on this machine) and `0x4` idle-clocks; **no** HW/SW
thermal slowdown and **no** HW slowdown at any sample. Memory and SSDs never move.
Conclusion: thermal headroom everywhere except the CPU during burst load, and the CPU
is not the speed-limiting subsystem for this workload.
