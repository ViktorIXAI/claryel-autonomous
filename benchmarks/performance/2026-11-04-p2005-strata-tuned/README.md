# Strata speed run — P2005 (RTX 5090 Laptop 24 GiB), tuned memory reserve

Date: 2026-11-04. Box: P2005 (16C/32T mobile CPU, 60.5 GiB RAM, RTX 5090 Laptop 24 GiB,
NVMe). Strata 0.1.56 (commit ffa80d73, tag line v0.2.10 = GitHub latest at run time),
engine f-0291-rc1, CUDA 13 driver stack. Model: Qwen3.8-Flash-Next IQ3_S, 262 144-token
context, KV int8, MTP/spec-4, conversation cache on.

Operator constraint: serve at maximum memory allocation while keeping ~1 GiB RAM free
and ~0.5 GiB VRAM reserved (`--vram-reserve-mib 512`, `--conversation-cache-min-free-mib 1024`).

## A/B tuning ladder (quickbench, 512→131072-token prompts, 64 new tokens)

Marginal prefill is stable ~1.85–1.89k tok/s from 8k up; decode does not collapse with
context until 131k.

| Context | Prefill tok/s | Decode tok/s (spec 4) |
| ---: | ---: | ---: |
| 512 | ~510 (short-prompt floor) | 60–67 |
| 2 048 | ~1 145 | 75–78 |
| 8 192 | ~1 852 | 77–83 |
| 16 384 | ~1 886 | 82–84 |
| 32 768 | ~1 833 | 87–92 |
| 65 536 | ~1 859 | 73–88 |
| 131 072 | ~1 791 | 71 |

Config rounds (same ladder unless noted):
- baseline, `--vram-reserve-mib 960`, pool-workers 15, spec 4 — decode 61–92, 65k: 72.7.
- reserve 512 + conv-cache min-free 1024 — 65k decode 72–88, 32k best 92.2; VRAM idle
  headroom after load: 448 MiB (matches the 0.5 GiB reservation), RAM available stayed >1 GiB.
- pool-workers 24 — 65k decode improved to 87.7; prefill unchanged (GPU-bound). **Kept.**
- spec 6 — strictly worse (decode 64–80 across the ladder, lower accept efficiency). **Rejected**, spec 4 restored.

## Standard suite (harness repo `tools/strata_bench.py`, medians of 3, `--long`)

See `community-report.md` / `results.json` (auto-sanitized: no host names, paths or IPs).
Headline numbers: short chat decode 73.9 (66.7–99.4) tok/s, TTFT 0.34 s; fresh-prompt
prefill 1 396 (4k) / 1 936 (16k) / 1 988 (32k) tok/s; agent session with conversation
cache: 69.1 % prompt-token reuse, decode 80.8 tok/s, TTFT 2.53 s median.

## Verdict

- Version installed is the latest release (v0.2.10 / 0.1.56) — no update needed.
- Tuned config (reserve 512, pool-workers 24, spec 4) meets the reservation without
  measurable speed loss; spec 6 is a regression for this model on this GPU.
- Prefill ~1.9k tok/s is the practical ceiling at every context ≤64k; 26k-token prompt
  ≈ 13–14 s, 131k ≈ 73 s. Decode 71–92 tok/s across the whole ladder.

## Reproduce

`python3 quickbench.py 512 2048 8192 16384 32768 65536 131072` (word-list prompts, engine
usage counters) and `python tools/strata_bench.py --url http://<host>:8080 --long` with
the serve flags listed above. Speed only; no correctness suite was run here — contour
quality is measured by the text-gates series instead.
