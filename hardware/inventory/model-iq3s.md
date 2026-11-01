# Model build passport — qwen3.8-flash-next IQ3_S (GGUF, 2 parts)

| field | value |
|---|---|
| model name at endpoint | qwen3.8-flash-next-iq3_s |
| family / architecture | Qwen-3.8-Flash-Next class MoE (per engine launch profile: expert profile + MTP speculators) |
| quantization | IQ3_S (GSQ-RCO recipe build) |
| part 1 | Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf — 54,817,524,224 B |
| part 2 (PLE) | Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00002-of-00002.gguf — 28,800,138,432 B |
| mtime (both machines) | 2026-10-12 18:12 / 18:27 — identical on B2003 and P2005 |
| SHA-256 | part1: `4c1eb2ceb4915e1192f4f386021897bde56a97f40a0bb78bb86465e0f7d2aca3` · part2: `316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113` (computed 2026-11-01 08:2x CET on P2005, ionice; same-size+same-mtime copies live on B2003 — B2003 re-hash deferred to avoid disturbing its running series) |
| vision mmproj | mmproj-Qwen3.8-Flash-Next-BF16.gguf (B2003 vision config) |
| upstream source | base: `Qwen/Qwen3.8-Flash-Next` (Qwen team, Alibaba Group) · GGUF build: `ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF`, IQ3_S directory — filenames and both shard sizes match our files exactly (verified 2026-11-01); their GGUF release Apache-2.0 over the base Qwen community license |
| weights redistribution | not done (license-safe pattern: ids + sizes + hashes only) |
| attribution | full credits in `ACKNOWLEDGMENTS.md` (Qwen team; ISTA-DASLab GSQ+RCO quantization) |

Identical size+mtime across B2003/P2005 makes "same build" a strong claim; the
SHA-256 will convert it to a proven one. Until then treat it as *size-verified*.
