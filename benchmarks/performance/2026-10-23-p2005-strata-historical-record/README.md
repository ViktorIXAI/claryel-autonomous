# P2005 Strata historical speed record (2026-10-23) — retrospective publication

**Status of this record:** these measurements were made on 2026-10-23 (and 2026-11-03)
on P2005, *before this GitHub hub existed*. They were never published online at the
time — they lived only in the operator's local bench notes and the box's own logs.
Published here on 2026-11-05 as a dated retroactive record. **The tests were not
re-run** and the exact environment (warm caches, concurrent workloads of that day) is
not reproducible today; treat the numbers as an archival record, not a re-runnable
result. The comparison baseline for reproducible Strata numbers on this box is
[`2026-11-04-p2005-strata-tuned`](../2026-11-04-p2005-strata-tuned/README.md).

## Box (unchanged): P2005

RTX 5090 Laptop 24 GB (GB202, sm_120), Ryzen 9 9955HX, 64 GiB DDR5-5600, Lexar NM1090
PRO Gen5 NVMe; Strata with Qwen3.8-Flash-Next GSQ-RCO-IQ3_S (78 GiB pack), 262 144 ctx,
KV int8, MTP/spec-4.

## A/B tuning ladder, 2026-10-23 (Strata v0.2.2 era, warm quickbench decode)

| Variant | 2K/8K/16K prompt tok/s | warm decode tok/s | verdict |
|---|---|---|---|
| base (P2002 flags, workers 15) | 781 / 1952 / 2097 | **110 / 109 / 115** | baseline |
| +workers 31 + prefill auto:16384 | 420c / 2002 / 2107 | 102–103 | neutral |
| +short-read 0 (with head-alias) | 383 / 517, HTTP 503 | — | regression, reverted |
| +vram-reserve 512 | 1948–2102 | 100–108 | no gain + VRAM-free warning, reverted |
| **workers 31 + explicit --prefill 16384 + STRATA_ADAPT_OVERLAP=1** | 2038–2104 | **113 / 117 / 113** | overlap = keeper |
| +kv-resident 20480 | 2025–2062 | 109–118 | no gain, removed |

Community suite same day: chat decode 83.6 (max 110.3), first token 0.28–0.29 s,
4K prompt 1442, 16K prompt 2125 tok/s, agent-session decode 97.9 (max 125.5),
prompt-cache hit 69.6%. This was the best decode in the fleet at the time
(~55% over P2002), with prefill at parity — expert streaming from RAM, not the GPU,
was the bottleneck.

## Addendum, 2026-11-03 (Strata 0.1.52 → 0.1.56 rolling update)

Engine-log decode bursts **141–160** tok/s after the 0.1.56 update (0.1.52 reference
was ~100–124); prefill 2272–2800. A same-day note recorded that the 512 MiB VRAM
reserve *squeezes decode* on this build (KV grew to 163 840 cells at the expense of
expert-cache slots); with the old 960 MiB reserve, idle decode1024 held ~100–110.

## Conditions attached to the 110–118 figure

warm expert-cache, long generations (decode measured at 1024+ tokens), otherwise idle
endpoint, `vram-reserve 960`, `STRATA_ADAPT_OVERLAP=1`. Short cold-context ladders on
the same box measure materially lower (60–92), which is why the later published runs
look different — different protocol, not a regression.
