# P3001 storage A/B — IQ3_S served from NVMe vs the system SATA SSD (2026-11-02)

## Box (identical for both runs)

HP Z420 Workstation. CPU: Intel Xeon E5-2697 v2 (Ivy Bridge EP, 12 cores /
24 threads, 2.70 GHz base; AVX1 only, no AVX2). RAM: 15.5 GiB DDR3-1866 ECC
RDIMM (4×4 GB). GPU pair: NVIDIA Quadro K620 2 GB (display only) + NVIDIA
GeForce RTX 3060 12 GB (compute). NIC: 1 GbE. Drives under test:

| disk | model | interface | role |
|---|---|---|---|
| NVMe | Seagate FireCuda ZP1000GM30063, 1 TB | PCIe 3.0 ×4, ~2.5 GB/s | `/home` (previous IQ3_S home) |
| SATA SSD | Kingston SA400S3, 240 GB | SATA III, ~0.45 GB/s (engine-measured class) | `/` — system disk |
| HDD | WDC WD10EZEX 1 TB | SATA | parked, unused |

## Software stack (identical for both runs)

Ubuntu 24.04.4 LTS; NVIDIA driver 580.196.07 (R580 branch — the last that
still drives Maxwell/K620; chosen over R610, which dropped it); CUDA toolkit
13.4 (`cuda_13.4.r13.4/compiler.38855100_0`). Strata control/terminal 0.2.9
(`strata 0.2.9, build 0.1.55, python 3.12.15`). Engine: official 0.1.55
linux-x86_64-cuda13 **cannot run** on this CPU (AVX2 floor); a local build from
tag `v0.2.9` with `-DSTRATA_ISA_FLOOR=avx -DCMAKE_CUDA_ARCHITECTURES=86`
(`BUILD.json`: `source: local, version: 0.1.55, archs: [86], isa_floor: avx,
vision: none`) is used — it reports `expert kernels run on AVX1 128-bit
(iq_avx1, the older-CPU build)`. Serve is fronted by the OpenAI-compatible
endpoint on :8080; systemd-free operation via `keep-up.sh` (cron every 5 min +
`@reboot`).

Model: Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S (MoE, 128 experts/layer, 256 routed
experts per token across the ladder batches; total expert set 46.8 GiB, native
shards IQ3_S 00001/00002-of-2). Launch config:
`hardware/configurations/strata-iq3_s-p3001.launch.json` — `--pack packs/iq3_s
--spec 4 --spec-min-p 0.5 --mtp mtp/rt --max-context 32768 --kv int8
--mmap-experts --expert-cache auto`.

## What was moved

`rsync -a` (no `--delete`) of `~/Strata` (incl. `engine-avx/`), `~/Strata-data`
(models, pack, MTP) and the terminal `data/` dir from the NVMe to `/srv/strata`
on the Kingston: 144,798,288,745 bytes, avg 54 MB/s. Then the serve profile was
repointed so the engine binary, weights, pack, MTP and expert-profile all read
from SATA; page cache was dropped (`sync; echo 3 > drop_caches`) before each
cold start. NVMe copy untouched.

## Engine's own plan on each disk

NVMe run: drive class ~2.5 GB/s → prefill chunk 2048, page cache keeps part of
the file set.

SATA run (engine log, verbatim): `prefill plan: chunk 8192, ring 96 kept: file
set 45.8 GiB does not fit the page cache 12.2 GiB -> about 196.7 GB read from
the drive per 32768-token prompt (4 chunks); no option does better` …
`46.8 GiB experts, 4.8 GiB in the GPU caches, file tier 42.0 GiB; 12.2 GiB
available for the page cache; PCIe 12.4 GB/s; drive 0.45 GB/s (sda is a
SATA-class SSD (assumed))`. Expert cache identical: 2495 slots / 4.79 GiB VRAM.

## Measured ladder (same script, 128 completion tokens, temperature 0)

| step | NVMe prefill tok/s | SATA prefill tok/s | NVMe decode | SATA decode | NVMe wall | SATA wall |
|---|---|---|---|---|---|---|
| cold 1,568 tok | 41.9 | 12.3 | 14.1 | 3.2 | 46.7 s | 168.4 s |
| cold 6,168 tok | 192.7 | 47.6 | 14.7 | 3.4 | 41.0 s | 166.9 s |
| cold 12,268 tok | 189.3 | 47.0 | 15.0 | 3.4 | 73.6 s | 298.1 s |
| warm 6,168 tok (99.9 % KV hit) | — | — | 20.8 / 19.1 | 7.4 / 8.0 | 11.0 / 7.1 s | 20.6 / 17.1 s |

A 12k-token prompt took **5 minutes** on the SATA SSD vs 74 seconds on NVMe.
Decode with a hot KV cache still runs at 3.4 tok/s cold / 7–8 warm because
every generated token streams routed experts from the file tier — the KV hit
does not help the expert reads.

## Verdict

The SATA SSD is a hard 4–5× multiplier on everything (the box has no other
bottleneck that small: the interface speed shows up directly — 0.45 vs
~2.5 GB/s). IQ3_S **can** run fully off a SATA SSD — placement, serving and
answers all work — but interactive use collapses (≈3 tok/s decode, minutes per
prompt). Fleet rule: MoE models with a file tier need NVMe on the data path;
a SATA SSD is acceptable only as a cold standby copy. Production P3001 was
restored to the NVMe after this test; the `/srv/strata` SATA copy is kept as a
standby so the NVMe can be physically removed if ever needed without
reinstalling.

Reproduce: `~/Strata/ladder_p3001.py`; raw rows on the box as
`ladder-p3001-nvme.jsonl` and `ladder-p3001.jsonl`; engine logs
`strata-iq3_s.log` (NVMe) and `strata-iq3_s-ssd.log` (SATA).
