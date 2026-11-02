# P3032 IQ3_S context ladder — 32k on a 2012 Xeon with resident experts (2026-11-02)

First measured series on P3032 (Xeon E3-1270 v2, no AVX2; RTX 3060 12 GB at a
150 W cap; 31.5 GiB DDR3; NVMe data disk at PCIe 3.0 x4). Engine: locally
built strata 0.1.55 (`STRATA_ISA_FLOOR=avx`, sm_86 — build story in
hardware/changes/P3032.md). Model: IQ3_S, ctx 32768, kv int8, spec4+MTP,
**resident experts 16 GiB in RAM (page-locked) + unbuffered file tier**,
memory limit 19 456 MiB, vision off.

## Method

`ladder3.py`: prompt lengths 1k/4k/8k/16k/30k built from unique salted
sentences (calibrated 31.1 tok/sentence), each rung submitted cold (first
time those bytes reach the engine) then byte-identical warm. Generation
instruction forces 700 tokens, temperature 0.7, thinking off. A 3 s hardware
sampler (GPU clocks/power/temp/VRAM, RAM available, swap, disk sector delta)
ran in parallel; 152 samples in the final pass. Raw rates below are from the
engine's own accounting lines.

## Results

| prompt tok | prefill tok/s (cold) | TTFT | decode cold tok/s | decode warm tok/s | drafts accepted* |
|---|---:|---:|---:|---:|---|
| 1 000 | 75.7 | 13.2 s | 39.8 | 43.5 | 275/519 |
| 3 976 | 182.4 | 21.8 s | 38.0 | (n=83, 21.8) | 256/522 |
| 8 231 | 186.1 | 44.2 s | (n=68, 27.8) | 40.2 | 262/503 |
| 16 968 | 187.4 | 90.5 s | 37.1 | (n=60, 21.1) | 268/524 |
| 31 818 | 202.8 | 156.9 s | 41.5 | 39.3 | 256/509 |

\* drafts from the 700-token run of each rung (for 8 231 that was the warm
run; its cold run stopped at 68 tokens, 17/52).

Cold rows with n=68/60 are runs where the model chose `stop` early; they are
kept as-is and not blended into the decode band (band = 700-token runs:
37.1–41.5 cold, 39.3–43.5 warm). Warm rows reuse the engine prompt cache
(99.9 % reused, ~0.3 s to first token).

Hardware envelope during the pass: GPU power median 76 W / peak 148 W under
the 150 W cap, peak 66 °C, SM clock median 1980 MHz; VRAM 11 145 MiB in use
(~1.1 GiB reserve); RAM never below 9.0 GiB available; swap used ≤ 0.5 MiB
(all three passes). NVMe file tier active throughout (sector deltas in raw).

## Verdict

**Decode is good for this class: ~40 tok/s cold / ~40–44 warm — 2.6–2.8×
P3001's mmap-mode numbers (14–15 cold / 19–21 warm) at the same GPU, thanks
to resident experts unlocked by 32 GB RAM. Prefill is the weak point:
~190–203 tok/s plateau (AVX1 128-bit kernels × DDR3), i.e. a 30k-token
prompt costs ~2.6 minutes before the first token. Fine for short/medium
prompts and batch work; not a long-context interactive box.** Draft
acceptance sits ~50 % (vs 85–97 % on AVX2 fleet boxes) — the AVX1 verify
path taxes speculative decoding.

## Failed passes kept as evidence

- Pass 1: shared probe text silently hit the prompt cache — every "cold"
  rung showed full reuse; the pass is only valid as a prompt-cache
  demonstration (warm 16k ≈ 0.2 s prefill). sha256/16 `a0b69e05204c85b3`.
- Pass 2: rung sizing mis-calibrated; the 16k target became ~44k tokens and
  the engine returned **HTTP 400** (over ctx 32768) — honest capacity
  rejection. sha256/16 `a5c8a394e2944529`.
- Pass 3 (authoritative table above): sha256/16 `29ca83244f5f4da2` (sampler),
  run log `ea2d5336679d0596`.

Client-side rows: results/p3032-iq3s-context-ladder.jsonl.
Sanitized serve profile: hardware/configurations/strata-iq3_s-p3032.launch.json.

Safe to publish: contains counts, rates, temperatures, power only.
