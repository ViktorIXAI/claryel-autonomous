# P1005 post-swap quick contour sweep — `0.0.2.2` on RTX 3060

**Date:** 2026-11-03  
**Box:** P1005, Xeon E5-2690 v4, 31 GiB RAM, NVIDIA RTX 3060 12 GB  
**Engine:** Strata repo v0.2.10, engine 0.1.56, CUDA 12 package  
**Model:** Qwen3.8-Flash-Next IQ3_S, 32 768-token context  
**Contour:** `0.0.2.2` (F diagnostic grounding)  
**Scope:** one run through all 178 bank tasks at repetition 0. This is a
post-hardware-swap health sweep, not the planned 2421-pair paired A/B series.

## Result

| scope | mean answer score | perfect answers |
|---|---:|---:|
| raw, all 178 tasks | **0.9759** | 170 / 178 |
| capacity-valid, 176 tasks | **0.9851** | 170 / 176 |

Two G-ve document-QA tasks require a 113k-character source and exceed the box's
32k context. They are capacity rejects and are excluded from the adjusted score.
The first complete pass after the GPU swap is therefore normal: the contour fix
still works on a different class of machine, while F scores 1.00 on all ten tasks.

| category | n | mean |
|---|---:|---:|
| A | 16 | 1.000 |
| B | 13 | 1.000 |
| C | 16 | 1.000 |
| D | 29 | 0.984 |
| E | 27 | 0.938 |
| F | 10 | 1.000 |
| G | 13 | 1.000 |
| H | 13 | 0.962 |
| I | 13 | 1.000 |
| J | 13 | 1.000 |
| K | 13 | 1.000 |

## Resource envelope

The sampler ran once per minute, not at 1 Hz:

- GPU temperature: 43–66 °C
- GPU power: 22.1–169.1 W
- GPU clock: 210–1995 MHz
- GPU utilization: 0–100 %
- GPU memory: 11 061–11 227 MiB of 12 288 MiB
- Host MemAvailable floor: 549 MB
- swap used: 0 observed in the sampler window

The 549 MB host-memory floor is the main risk. A later full paired attempt started
immediately after a separate baseline and stopped before writing results when the
gate saw about 520 MB available. A follow-up quick run started after the serving
process had reached a lower steady-state footprint; its sampled MemAvailable floor
was 4.1 GB, GPU power reached 182.3 W, and VRAM stayed at 11.2 GiB.

## Failures kept as evidence

The six valid attempts below were not removed:

| task | score | note |
|---|---:|---|
| E-ha-01-1 | 0.88 | generated code failed 6/50 assertions |
| E-ha-03-0 | 0.28 | generated code failed 36/50 assertions |
| E-ha-04-1 | 0.16 | generated code failed 42/50 assertions |
| D-ha-00-1 | 0.80 | missed two client names |
| H-ve-01-0 | 0.50 | content scorer failure, no note recorded |
| D-ve-00-2 | 0.75 | plan contained a dangerous action; gate block correct |

## Verdict

The contour is healthy after the P100 → RTX 3060 swap. E/code-generation is the
weak area in this single pass, while the targeted F contour fix remains fixed.
Before accepting a full cross-box `0.0.2.1 -> 0.0.2.2` claim on P1005, run the
paired full series with a 1 Hz sampler and an idle endpoint; the full A/B3 attempt
must not start while the serving process is at the host-memory boundary.

## Artifacts

Raw artifacts are pinned in [`logs/INDEX.md`](../logs/INDEX.md): result JSONL,
ledger JSONL, telemetry CSV, and runner log.
