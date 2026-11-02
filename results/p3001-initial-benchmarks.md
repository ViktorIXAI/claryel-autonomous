# P3001 initial benchmarks — 2026-11-02

Box: hardware/inventory/P3001.md (Ivy-Bridge Xeon, no AVX2; RTX 3060 12 GB;
local `STRATA_ISA_FLOOR=avx` engine 0.1.55 cuda13). Engine cold at ladder
start — the Qwen3.6 swap experiment had just evicted the page cache, i.e. a
worst-case cold start. Model: IQ3_S (hardware/inventory/model-iq3s.md),
launch config hardware/configurations/strata-iq3_s-p3001.launch.json,
`--max-context 32768 --kv int8 --mmap-experts --spec 4 --mtp rt`, 128 completion
tokens per row, temperature 0, fresh conversation per cold row. Requests hit the
box's own OpenAI endpoint; the `prompt_tps`/`decode_tps` columns are the
engine's own reported timings.

## IQ3_S ladder

| tag | prompt tok | cached | prefill tok/s | decode tok/s | wall s |
|---|---|---|---|---|---|
| cold-2k | 1,568 | 0 | 41.9 | 14.1 | 46.7 |
| cold-8k | 6,168 | 0 | 192.7 | 14.7 | 41.0 |
| cold-16k | 12,268 | 0 | 189.3 | 15.0 | 73.6 |
| warm-8k-a | 6,168 | 6,163 | (99.9 % cached; ratio meaningless) | 20.8 | 11.0 |
| warm-8k-b | 6,168 | 6,163 | (99.9 % cached) | 19.1 | 7.1 |

Reading: on this box the file tier is not slow at scale — expert streaming
amortises over 2,048-token prefill chunks and the plateau is ~190 tok/s from
8k up. The pain is short prompts: a 60-token prompt prefills at 10.9–19.8
tok/s because every routed expert costs a fresh NVMe read with nothing to
amortise against. Warm decode with MTP drafting: 19–21 tok/s; cold decode is
hit-rate-limited at 14–15.

## Qwen3.6-35B-A3B UD-Q4_K_XL (negative result, engine built-in benches)

First attempt, no swap: OOM-killed by the kernel during expert placement
(exit 137; dmesg: `anon-rss:14935564kB`). With a 24 GB swapfile on the NVMe
(placement 156.5 s: 36/256 experts per layer in VRAM = 2.64 GiB, 18.75 GiB in
host memory): warm-up 620.9 s, then three bench rounds:

| round | pp256 tok/s | tg128 tok/s |
|---|---|---|
| 0 | 1.3 | 13.7 |
| 1 | 1.5 | 6.4 |
| 2 | 1.4 | 16.9 |

Batch accounting: 41,315 / 122,880 expert rows on GPU (33.6 %), the rest on a
12-thread CPU pool, 1,997 expert-slot replacements; swap 10–13 GiB in use,
iowait 83–87 %. Verdict: the q36 family needs ≥32 GB RAM; on 15 GiB it is
OOM without swap and unusable with it (a 200-token prompt ≈ 2.5 minutes).
Full write-up: history/failures/failures.md.

Reproduce: `~/Strata/ladder_p3001.py` on the box (rows also kept locally as
JSONL); q36 benches via `strata --model <UD-Q4_K_XL.gguf> --max-context 8192
--bench-pp 256 --bench-tg 128`.
