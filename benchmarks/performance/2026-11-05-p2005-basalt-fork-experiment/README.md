# Basalt (Strata fork) speed experiment — P2005, same IQ3_S weights

Date: 2026-11-05. Box: P2005 (16C/32T mobile, 60.5 GiB RAM, RTX 5090 Laptop 24 GiB, NVMe).
Engine: [Basalt v0.2.1](https://github.com/jesdga95/basalt) — a Strata fork narrowed to
Blackwell sm_120; built on the box with CUDA 13 (`basalt` 93 MB, build took 4 min).
Model pack: converted **from our own GSQ-RCO-IQ3_S GGUF shards** with the official tuned
MTP drafter kit (`--mtp-source kit/convert/mtp --mtp-dense rt/dense.bin --draft-vocab
rt/draft_vocab.bin`), output 81.625 GiB, 194 s. Serve: `kv int8`, `resident-experts`,
`expert-cache auto`, `prefill auto`, `vram-reserve-mib 512`, ctx 262144 — the same memory
reservations as the tuned Strata run in the parent folder.

Strata baseline (same box, same weights, tuned config, `2026-11-04-p2005-strata-tuned`):
prefill ~1.79–1.99k tok/s, decode 60–92 tok/s.

## Basalt ladder (quickbench, 64 new tokens per run)

| Context | Prefill tok/s | Decode tok/s | Draft acc | Wall |
| ---: | ---: | ---: | ---: | ---: |
| 512 | 245 (short-prompt floor) | 90.6 | 41/66 | 3.2 s |
| 2 048 | 2 079 | 180.9 | 41/58 | 1.4 s |
| 8 192 | 2 990 | 208.5 | 41/54 | 3.1 s |
| 16 384 | 3 835 | 202.8 | 43/60 | 4.6 s |
| 32 768 | 3 927 | 190.7 | 40/58 | 8.7 s |
| 65 536 | 3 821 | 217.8 | 42/53 | 13.2 s |
| 131 072 | 3 710 | 162.2 | 38/53 | 22.5 s |

## Verdict

- **Decode ~2.3–2.8x** Strata on this GPU (162–218 vs 71–92 tok/s across the ladder);
  **prefill ~2x** (3.7–3.9k vs 1.8–2.0k tok/s). 131k-token prompt: 22.5 s vs 73 s.
- Draft accept rate is similar (~72–76%), so the gain is kernels/prefill pipeline, not
  luckier speculation. GPU sat at ~100% util, 103–143 W (the box's dynamic power cap).
- RAM headroom kept: ~12 GiB available during the run, VRAM reservation respected
  (start-up log: `pool=15`, elastic KV, weights 21.5 GiB GPU + 29.5 GiB RAM resident).
- Limitations found: request must name the served model (404 otherwise); vision is off in
  this serve config (`images=off`); a self-converted pack carries the converter warning
  about the official packs, yet it still beat tuned Strata 2x on the same weights.
- Reproducible pitfall: the HF kit downloader (curl -C -) once silently truncated a
  1.68 GB drafter tensor; the converter died at mmap. Fix: verify every kit file against
  `mtp-manifest.json` sizes/SHA-256 before converting.

Experiment left installed at `~/basalt` (not autostarted); Strata remains the fleet's
engine elsewhere and its tuned config is preserved as the working baseline.
