# GCN4 (gfx803 / RX 580 8 GB) inference engines that actually run

Context: P3001 (Xeon E5-2697 v2, 62 GiB DDR3-1333, no AVX2) had its RTX 3050 8 GB
swapped for a Radeon RX 580 2048 SP (Polaris 20 XL, PCI `1002:6fdf`, `gfx803`).
Strata cannot run there: its HIP target list is gfx1030/1031, gfx1100/1101/1102,
gfx1151, gfx1200/1201 (hand-builds reach gfx906 and gfx1010-1012) and gfx803 is
not in the set; Ubuntu 24.04 ships no `rocblas`/`hipblas` at all, and rocBLAS
Tensile has had no gfx803 kernels since ROCm 5.0. Verified 12.11.2026:
`setup.sh --backend hip --check` -> "no AMD GPU Strata can use".

What does run on this card, by effort:

## 1. Vulkan via Mesa RADV — zero build effort, works today
- **llama.cpp Vulkan** — the prebuilt `bin-ubuntu-vulkan-x64` release asset runs
  against RADV out of the box; `llama-cli --list-devices` on P3001 prints
  `Vulkan0: AMD Radeon RX 580 2048SP (RADV POLARIS10) (8192 MiB)`.
  Everything built on llama.cpp inherits this: **Ollama** (Vulkan backend,
  needs the user in group `render` + `setcap cap_perfmon+ep`), **KoboldCpp**
  (`_vulkan_nocuda` builds; on Linux it prefers ROCm when `rocminfo` is present,
  so force Vulkan), LM Studio, GPUStack/llama-box, llama.cpp RPC.
- **whisper.cpp Vulkan** — community report: 106 s of audio transcribed in
  23.6 s on RX 580 (Linux/Mesa), vs CPU.
- **stable-diffusion.cpp** with `SD_VULKAN=ON` — SD1.5 512x512 in ~72-85 s,
  FLUX-schnell in hybrid mode.
- Windows-only trap worth knowing: RADV on Polaris exposes the compute queue in
  a second queue family; llama.cpp needs `GGML_VK_ALLOW_GRAPHICS_QUEUE=1` there.
  On Linux RADV it is not required (measured on P3001).

## 2. ROCm/HIP on gfx803 — rebuild the runtime first
- `NULL0xFF/rocm-gfx803` — ROCm 6.1.5 / 6.3.4 rebuilt with gfx803 targets
  (rebuild rocBLAS, rocSOLVER, rocRAND, **disable lazy loading**). Known bug:
  PyTorch `LayerNorm` returns garbage for normalized sizes >= 320 (~28-48 %
  relative error), which silently corrupts transformers/SD — llama.cpp is fine.
- `Schaka/rocm-gfx803` — patched MIGraphX, ONNX Runtime, PyTorch, Triton and a
  **hard-fork of vLLM** with hand-written gfx803 kernels (no fp16, no
  `dot4_i8`): measured prefill 311 t/s, decode 30.2 t/s on a 2 B model.
- `robertrosenbusch/gfx803_rocm` — Docker path (PyTorch, ComfyUI, WhisperX,
  CTranslate2, Ollama); 1-3 h rebuild, kernel >= 6.8 on Ubuntu 24.04 works.
- `xuhuisheng/rocm-gfx803`, `woodrex83/ROCm-For-RX580` (ROCm 5.4.2 patched,
  needs kernel <= 5.13 — not usable on our 6.8 kernels).

## 3. Will not work
Strata (arch list above), upstream vLLM/SGLang/TensorRT-LLM, ExLlama / any CUDA
stack, ZLUDA (no Polaris target).

## Cost of the architecture (why Vulkan numbers look like that)
Polaris has no fp16 arithmetic, no int8 dot-product instructions and no matrix
cores, so the Vulkan path runs without cooperative matrix: prompt processing is
the weak point, decode is memory-bandwidth bound.
Reported RX 580 llama.cpp Vulkan numbers: Qwen3-1.7B ~66 t/s decode;
Mistral-7B Q4_K_M 17-18 t/s decode; Qwen3.6-35B-A3B Q4_K_M ~16.3 t/s decode at
22.6 t/s prefill with `--n-cpu-moe 30` (CPU offload, ~6.7 GiB VRAM used,
`--cache-type-k q8_0 --cache-type-v q8_0` up to 32 K context).
Old-CPU caveat for our fleet: llama.cpp release binaries assume AVX2 — on
pre-Haswell Xeons build with `-DGGML_AVX2=OFF -DGGML_AVX512=OFF
-DGGML_NATIVE=OFF` or use the AVX1 KoboldCpp build.

Sources: llama.cpp release assets (Ubuntu Vulkan x64) and the Polaris queue-family
patch notes; Ollama GPU docs (Vulkan backend); koboldcpp.com Backends.md;
github.com/Eo33/rx580-llamacpp-vulkan-guide (env var, Windows/RADV limits);
huggingface.co/spaces/DonCallalala/RX580-Whisper.cpp (measured ASR speed);
github.com/{NULL0xFF,Schaka,xuhuisheng,woodrex83,robertrosenbusch}/rocm-gfx803
(and ROCm-For-RX580).
