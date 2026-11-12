# BigMoeOnEdge (bmoe) on P3001 with the RX 580

Date: 2026-11-12. Machine: P3001 (Xeon E5-2697 v2, 62 GiB DDR3-1333, NVMe FireCuda 530R,
Radeon RX 580 2048SP / gfx803). Model under test: our `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S`
(2 shards, 79.7 GiB file, arch `qwen4exp`, 512 experts top-10 over 48 MoE blocks).

Engine: `Helldez/BigMoeOnEdge` v0.42.0, `bmoe-cli-v0.42.0-linux-x86_64.tar.gz` (105 MB unpacked).
It is a llama.cpp fork (llama 0.9.0) that streams only the routed experts per token from flash,
with an LRU expert cache in RAM and an optional expert cache on the compute device.

## Does it run on this card? Yes

- The CLI pack ships its own `libggml-vulkan.so`, so it drives the RX 580 through Mesa RADV;
  **no ROCm and no gfx803 stack is needed**. Verified device line and the hardware planner
  probing `Vulkan0`.
- CPU modules are shipped per instruction-set tier; the host loads `libggml-cpu-ivybridge.so`,
  so the missing AVX2 on this Xeon is not a problem.
- Our sharded GGUF loads unmodified: pass the first shard, the engine finds shard 2 (`shards=2`).
- Trap: without `GGML_VK_VISIBLE_DEVICES=0` the planner spreads layers over `Vulkan1` too,
  which on this box is the Quadro K620 (2 GiB). Always pin the real card.

## What the planner measured on this machine (`--auto --plan`)

```
machine 24 cores, 54774 MiB available of 64226 MiB, 23 GiB/s on this model's matmul
storage uncached: 216 KiB 1 lane 754 MiB/s / 4 lanes 2310 MiB/s; 3466 KiB 4 lanes 3319 MiB/s
Vulkan0: one token 104 GiB/s, 128 wide 292 GiB/s; this model's layer: experts 88.1, dense 110.8 GiB/s
CPU host: one token 23 GiB/s, 128 wide 47 GiB/s; experts 24.2 GiB/s
model qwen4exp: experts 47962 MiB (936 MiB/token, streamable), attention 1456, dense-ffn 259
regime fits — moe-stream off: "the host residual fits: llama.cpp's placement is the whole plan"
declined: "streaming it from flash would only add reads that resident weights do not need"
```

The planner's own arithmetic is the interesting result: it measured NVMe at 2.3–3.3 GB/s,
computed that a token needs 936 MiB of experts, and chose **not** to stream because the expert
set (47.9 GiB) fits inside the 52.6 GiB the process may hold resident.

## Measured runs (same 699-token prompt, 128 generated tokens, `--chatml`)

| Mode | Flags | decode tok/s | prefill tok/s | TTFT |
|---|---|---|---|---|
| bmoe `--auto` (streaming declined, mmap) | `--auto` | 3.458 | 46.0 | 20.4 s |
| bmoe `--auto --moe-stream` (planner kept it off) | same + stream | 3.677 | 46.5 | 20.1 s |
| forced streaming, 4 threads | `--moe-stream --overlap --cache-mb auto` | 1.909 | 4.4 | 223 s |
| forced streaming + dense pinned, 4 threads | `--moe-stream --overlap --dense-weights anon --cache-mb 6000` | 1.769 | 4.4 | 213 s |

Reference points from the same box, same model: llama.cpp b12318 Vulkan `-ngl 99 -ncmoe 99`
= 7.93 tok/s decode (8.26 with the GPU overcoupled), CPU-only 4.09; RTX 3050 + Strata = 23–31.

Flag/behaviour notes recorded the hard way:

- `--device-cache-mb` and `--overlap` are mutually exclusive (device cache computes experts on
  the device, overlap waits for them on the CPU); `--device-cache-mb` also needs `--gpu-layers > 0`.
- `--auto` re-derives `moe-stream` and can leave it off even when the flag was passed.
- `systemd-run --scope -p MemoryMax=` needs polkit auth on this box, so the "weights do not fit
  RAM" scenario cannot be emulated with a cgroup cap as the user; use `--cache-mb` + `--dense-weights anon`
  to apply the same pressure instead.
- Output sanity: the model answered the arithmetic prompt correctly (391 − 207 = 184 parts).

## Verdict for our fleet

bmoe **works with the RX 580** (Vulkan/RADV, zero build) and reads our IQ3_S shards natively, but
on P3001 it is the wrong tool for this model: the experts fit in host RAM, so its streaming path
costs ~2× decode and ~10× prefill versus plain mmap, and mmap placement itself is already
2× slower than `llama.cpp -ncmoe 99`. Where bmoe earns its keep is the regime it was built for —
weights far larger than RAM, e.g. a 30B-A3B MoE on a small-RAM host, where a 2–3 GB/s NVMe is the
bottleneck the engine is designed to hide. That case is still untested on GCN4 and is queued.

Engine version pinned for reproduction: `bmoe-cli 0.42.0`, llama.cpp `b12318` (Vulkan prebuilt).
