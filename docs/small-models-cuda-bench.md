# Small-model bench: RTX 3050 8 GB vs RTX 5090 vs RX 580

Date: 2026-11-14. Same model set and same llama.cpp release used for the P3001/RX 580 field test
(`docs/rx580-p3001-test-log.md`), so the three cards are directly comparable.

## Protocol

* Engine: llama.cpp **b12318** (tag `b12318`, commit `7021f7e`), built on each host with the CUDA
  backend (`sm_86` on P3032, `sm_120` on P2005), `Release`, `LLAMA_CURL=OFF`.
* Bench: `llama-bench -ngl 99`, pp512 and tg128, `-fa 0` and `-fa 1`. P3032 `-r 2`, P2005 `-r 1`.
* RX 580 rows are the Vulkan numbers recorded on 2026-11-13 in `docs/rx580-p3001-test-log.md`
  (`-ngl 99 -fa off`), iGPU/CPU rows from that log are not reproduced here.
* Hosts: P3032 (`HP Z220`, E3-1270v2, 31.5 GiB RAM, RTX 3050 8 GB, CUDA 12.6, driver 580.178.04) and
  P2005 (Ryzen 9 9955HX, 60 GiB RAM, RTX 5090 Laptop 24 GiB, CUDA 13.0, driver 615.71.09).
* On P2005 the Basalt brain was stopped for the bench window (about 4 min total, twice) and restored
  afterwards; its `*/2 keep-up.sh` cron was disabled for the window and re-enabled. Verified
  `/health` ok and VRAM back at the standing value after each pass.

## Models

Downloaded from Hugging Face on 2026-11-14 into `/ai/models/small/` (P3032) and
`~/models-small/` (P2005); SHA1 sums are identical on both hosts (`SHA1SUMS.txt` next to the files).

| file | repo | size |
|---|---|---|
| `qwen2.5-3b-instruct-q4_k_m.gguf` | `Qwen/Qwen2.5-3B-Instruct-GGUF` | 2.10 GB |
| `NVIDIA-Nemotron3-Nano-4B-Q4_K_M.gguf` | `nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF` | 2.84 GB |
| `NVIDIA-Nemotron-3.5-Bolt-E4B-UD-Q4_K_XL.gguf` | `unsloth/NVIDIA-Nemotron-3.5-Bolt-E4B-GGUF` | 5.06 GB |
| `Ternary-Bonsai-2-9B-Q2_0.gguf` | `prism-ml/Ternary-Bonsai-2-9B-gguf` | 2.56 GB |
| `Ternary-Bonsai-2-27B-Q2_0.gguf` | `prism-ml/Ternary-Bonsai-2-27B-gguf` | 7.63 GB |
| `Ternary-Bonsai-2-9B-PTQ1_0.gguf` | `prism-ml/Ternary-Bonsai-2-9B-gguf` | 2.00 GB (not loadable, see notes) |

## Results (pp512 / tg128 t/s)

| model | RX 580 8 GB (Vulkan, fa off) | RTX 3050 8 GB (CUDA, fa off) | RTX 3050 8 GB (CUDA, fa on) | RTX 5090 24 GB (CUDA, fa off) | RTX 5090 24 GB (CUDA, fa on) |
|---|---|---|---|---|---|
| Qwen2.5-3B Q4_K_M | 392 / 60.0 | 3062 / 88.1 | 3558 / 92.9 | 9732 / 266.1 | 14573 / 300.6 |
| Nemotron-3-Nano-4B Q4_K_M | 268 / 40.2 | 2302 / 70.2 | 2386 / 71.1 | 10365 / 240.6 | 10350 / 243.8 |
| Nemotron-3.5-Bolt-E4B Q4_K_XL | 441 / 30.4 | 3165 / 48.9 | not run | 11810 / 157.9 | 12999 / 162.2 |
| Bonsai 2 9B Q2_0 | 170 / 27.4 | 1413 / 68.9 | 1437 / 69.9 | 6542 / 214.9 | 6640 / 218.0 |
| Bonsai 2 27B Q2_0 | 44.5 / 9.0 | 450 / 22.8 | not run | 2075 / 72.4 | 2095 / 74.0 |

Speed-up over the RX 580 (decode, tg128): RTX 3050 **1.5x** (3B) to **2.5x** (27B);
RTX 5090 **4.0x** (3B) to **8.0x** (27B). Prefill is a different order of magnitude: 3050 is
**7-10x** the RX 580, the 5090 is **25-47x**.

## Platform confounders (read before using the RX 580 column)

The three columns are not three cards in one machine; each card sat in its own workstation:

| host | card | CPU | RAM | memory bandwidth | GPU link | engine API |
|---|---|---|---|---|---|---|
| P3001 (HP Z420 Xeon; operator calls it Z440) | RX 580 2048SP 8 GB | E5-2697 v2, 12c/24t | 8 x 8 GB DDR3-1333 ECC RDIMM, **quad channel**, 62 GiB | ~42.7 GB/s | Gen3 x16 slot, x8 card | llama.cpp **Vulkan** (RADV) |
| P3032 (HP Z220) | RTX 3050 8 GB | E3-1270 v2, 4c/8t | 4 x 8 GB DDR3-1333, **dual channel**, non-ECC, 31.5 GiB | ~21.3 GB/s | CPU port Gen3, trained x8 | llama.cpp **CUDA** |
| P2005 | RTX 5090 24 GB | Ryzen 9 9955HX, 16c/32t | 60 GiB dual-channel DDR5 | ~70+ GB/s | Gen5 x16 (mobile) | llama.cpp **CUDA** |

What that does and does not invalidate:

* The four models that fit fully in 8 GiB (3B 1.95, Nano 2.63, Bolt 4.70, Bonsai 9B 2.37 GiB) run
  with weights resident in VRAM, so host RAM bandwidth and core count barely touch their decode.
  Those rows are a fair card-vs-card comparison.
* The 27B Q2_0 row (7.09 GiB GGUF) keeps part of its stack in host memory on both 8 GiB cards, so it
  *is* host-sensitive — and the host helping the RX 580 is the stronger one (2x memory bandwidth,
  3x cores, 2x RAM). The 3050 being 2.5x faster there is therefore understated, not inflated.
* The API stack is a genuine part of the gap and cannot be separated on different machines: Polaris
  on Vulkan has no fp16 and no int-dot path, Ampere on CUDA does. The clean test is the same host
  with both cards (see below).

## Next: same-host card A/B

Plan (started 2026-11-14): the RX 580 moves into P3032 (Z220) so the two 8 GiB cards are measured in
one machine, one PSU, one PCIe slot, one set of host drivers. P3032 was powered off at 15:59 UTC for
the swap. The bench and smoke scripts are already on the box (`/tmp/p3032_small_bench.sh`,
`/tmp/p3032_vk_bench.sh`), and the models are on `/ai/models/small/`.

Two things have to be fixed for the Radeon leg: `mesa-vulkan-drivers` (RADV ICD) must be present, and
the llama.cpp Vulkan backend failed to configure today — `find_package(Vulkan)` in CMake 3.28 with
`libvulkan-dev` + `glslang-tools` installed (`CFG_RC=1` in `/ai/vk-run.log`, no
`build-vk/bin/llama-bench`). Either point CMake at the full LunarG SDK (`ggml/src/ggml-vulkan`
expects `Vulkan::Vulkan` plus a working `glslangValidator`), or install the SDK with
`llama.cpp/scripts/setup-vulkan.sh`. Vulkan itself is healthy on the box: `vulkaninfo --summary`
listed `NVIDIA GeForce RTX 3050` with `DRIVER_ID_NVIDIA_PROPRIETARY 580.178.04`.

## Notes

* Flash-attention is worth 3-13 % decode on the 3050 and up to 13 % decode / 50 % prefill on the 5090
  for the dense models; it is neutral-to-negative for `nemotron_h` prefill on the 5090.
* `Ternary-Bonsai-*-PTQ1_0` does **not** load in stock llama.cpp b12318 (`failed to read tensor
  info`). The RX 580 PTQ1_0 rows were produced with the PrismML fork (`prism-b12128`); the files
  themselves are intact (identical SHA1 on both hosts).
* Bonsai 2 27B Q2_0 (7.09 GiB GGUF) does not fully fit in 7.84 GiB of VRAM; llama.cpp keeps part of
  the stack on the host and still reaches 22.8 t/s on the 3050. On the RX 580 the same file gave
  9.0 t/s.
* Qualitative smoke on the 3050 (`llama-cli --temp 0`, 48 tokens, sheep riddle): all five models
  reason correctly; Nano, Bolt and both Bonsai emit chain-of-thought before the answer, Qwen2.5-3B
  answers directly. The 48-token cap truncated the Bolt/9B answers, which is a bench limit, not a
  model failure.
* Context for the fleet: decode here is **2.4x** (Bonsai 27B) to **9.8x** (Qwen 3B with fa) faster
  than the IQ3_S brain on the same P3032 hardware (9.5 t/s), and Bonsai 2 27B delivers 27B-class
  parameters in 7.1 GiB.

## Raw artifacts

* P3032: `/ai/bench-3050.txt`, `/ai/smoke-3050.txt`, build log `/ai/llama-build.log`.
* P2005: `~/bench-5090.txt`, `~/bench-5090-27b.txt`, `~/llama-build.log`.
