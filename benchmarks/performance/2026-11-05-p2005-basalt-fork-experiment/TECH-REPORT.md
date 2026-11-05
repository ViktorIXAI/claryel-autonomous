# Basalt on P2005 — detailed technical report

Companion to the short verdict in [README.md](README.md). Everything below was executed
and measured on 2026-11-04/05 on P2005; the engine is now that fleet's primary brain.

## 1. What Basalt is

[Basalt](https://github.com/jesdga95/basalt) is a fork of Strata narrowed to a single
target: NVIDIA Blackwell (sm_120) + one model family (Qwen3.8-Flash-Next). C++/CUDA
engine, Python server with an OpenAI- and Anthropic-compatible API, everything tuned
for that one point in the design space (unified-kernel path, NVFP4/dense tensor-core
decode, tuned self-distilled MTP drafter shipped separately).

## 2. Build (on the box, no cross-compile)

```
git clone .../basalt && git checkout v0.2.1
CUDACXX=/usr/local/cuda/bin/nvcc cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc
cmake --build build -j 28          # 507 targets, ~4 min on 16C/32T
```

Gotchas found:
- non-interactive ssh PATH has no CUDA — CMake needs an explicit `CMAKE_CUDA_COMPILER`;
- the engine binary lands in `bin/basalt` (plus `basalt-probe`, `basalt-bench`,
  `basalt-vision`), not in `build/`;
- CUDA 13.0 (already installed for Strata) is sufficient; sm_120 auto-detected.

## 3. Model pack: converted from OUR GGUF, not downloaded

Rationale: the official `.basalt` packs use a different quant lineage (GSQ-RCO-IQ3_S =
81.6 GiB, NVFP4-DQ6_K = 122.6 GiB). Converting our own 78 GiB GSQ-RCO-IQ3_S shards
keeps the comparison weight-for-weight identical to the tuned Strata run.

```
.venv/bin/python tools/convert/convert.py \
  --gguf .../Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf \
  --mmproj mmproj-Qwen3.8-Flash-Next-BF16.gguf \
  --mtp-source kit/convert/mtp \
  --mtp-dense kit/convert/mtp/rt/dense.bin \
  --draft-vocab kit/convert/mtp/rt/draft_vocab.bin \
  --out model/Qwen3.8-FN-IQ3_S.basalt --workers 16
# -> 81.625 GiB, 18 sections, 194 s
```

- The tuned drafter kit (BF16 MTP tensors ~5 GiB + tuned `rt/dense.bin` + draft vocab)
  comes from the pack repo (`convert/`); `--mtp-source` must point one level ABOVE
  `tensors/` (the manifest lives there).
- Without a drafter a pack is "significantly slower" per the docs — the kit is what
  makes a self-converted pack competitive.
- **Real failure recorded:** one 1.68 GB kit tensor was silently truncated by a resume
  download; the converter crashed at mmap after 45 minutes of packing. Fix: verify
  every kit file against `mtp-manifest.json` sizes and SHA-256 *before* converting.

## 4. Serve configuration (the working config)

`basalt-config.WORKING-20261105.json` on the box, launched with `--vision 0`:

```json
{ "server": { "model": "model/Qwen3.8-FN-IQ3_S.basalt",
              "alias": "qwen3.8-flash-next-iq3_s-basalt", "gpu": "0", "port": 8080 },
  "engine": { "max-context": 262144, "kv": "int8", "resident-experts": true,
              "expert-cache": "auto", "prefill": "auto", "vram-reserve-mib": 512 } }
```

Start-up (cold): dense weights 21.5 GiB → GPU; 29.5 GiB experts → page-locked RAM at
2956 MB/s; `resident=45.0GB`, `pool=15`; elastic KV 4.0 GiB; ctx 262144; total time to
`loaded: true` ≈ 25 s (Strata cold-load on the same pack is noticeably longer).
Engine command (expanded by the server):
`--max-context 262144 --kv int8 --resident-experts --expert-cache auto --prefill auto
--vram-reserve-mib 512 --gpu 0 --grammar on`.
API key is command-line only (`--api-key`, refused in config files); every request must
name the served alias (404 otherwise); vision is opt-in (`--vision 0` → GPU vision).

Memory during load+bench: ~49 GiB used, 12+ GiB RAM available throughout — the 1 GiB
RAM + 0.5 GiB VRAM reservation contract held (VRAM 23.7/24.4 GiB, ~450 MiB spare).

## 5. Measured speed (same quickbench ladder, 64 new tokens/run, as the Strata runs)

| Context | Basalt prefill | Basalt decode | draft accept | Strata 2026-11-04 (same box, same weights, same 512 reserve) |
|---:|---:|---:|---:|---:|
| 512 | 245 (short floor) | 90.6 | 41/66 | ~510 / 60–67 |
| 2 048 | 2 079 | 180.9 | 41/58 | 1 149 / 75–78 |
| 8 192 | 2 990 | 208.5 | 41/54 | 1 852 / 77–83 |
| 16 384 | 3 835 | 202.8 | 43/60 | 1 886 / 82–84 |
| 32 768 | 3 927 | 190.7 | 40/58 | 1 833 / 87–92 |
| 65 536 | 3 821 | 217.8 | 42/53 | 1 859 / 73–88 |
| 131 072 | 3 710 | 162.2 | 38/53 | 1 791 / 71 |

Against Strata's best historical record on this box (warm, 960 reserve, long gens —
see the [retrospective record](../2026-10-23-p2005-strata-historical-record/README.md),
110–118 warm decode): Basalt reaches **1.4–1.9×** that ceiling **under a harsher
protocol** (cold prompts, 64-token generations, 512 reserve). Against the reproducible
tuned Strata run: **decode ×2.3–2.8, prefill ×2.0–2.2**, 131k-prompt wall 22.5 s vs 73 s.

Why: draft accept is essentially the same (~72–76% both engines), so the win is not
speculation luck — it is the Blackwell-only kernel set (unified decode kernel, dense
tensor-core path, 8-bit hyper-connection copies read as-is) and the prefill streaming
pipeline. GPU runs pegged at 100% util, 103–143 W — the box's dynamic power cap is now
the constraint, not the engine.

## 6. Fleet integration (2026-11-05)

Hermes primary brain switched to `qwen3.8-flash-next-iq3_s-basalt` via the existing
`strata` provider entry (same host/port, key byte-identical, verified by hash compare
without printing it). Autostart: box-side keep-up cron `*/2` + `@reboot`
(`~/basalt/keep-up.sh`, log `keep-up.log`). Fallback chain: Mac Studio Strata →
Codex → Grok → Sonnet. Thermal-watch and hardware crons untouched. One behavioral
note for agents: Basalt emits `reasoning_content` and burns token budget on thinking —
keep `max_tokens ≥ 2048` in probes.

## 7. Verdict

On one 24 GB Blackwell card with the same IQ3_S weights, Basalt converts this box from
"comfortable chat node" (~80 tok/s) to "primary agent brain" (160–220 tok/s) at the
same memory reservations. Cost of adoption: a second engine stack to maintain
(self-built binary, pack conversion pipeline, kit verification), model locked to one
alias in requests, and vision is opt-in. For a fleet that serves exactly this model
family on Blackwell, the trade is clearly worth it.
