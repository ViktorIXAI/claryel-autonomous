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
MAX-BENCH-ADDENDUM.md; the honest summary is: *burst 160–210, sustained 130–165, on an
idle endpoint with warm caches and 512 MiB VRAM reserve.* Draft acceptance stayed
68–79% across all windows — the settle comes from KV attention cost and expert churn,
not speculation failure.

Bench environment for the max run: endpoint fully idle (Hermes brain parked on Mac
Studio), 2 warmup rounds of 3 conversations before the ladder, RAM at contracted floor,
GPU 145 W / 67 °C at measurement time. When the brain shares the endpoint (production
case), expect ~15% below these numbers.
