# P1005 raw-model speed records — Tesla P100 16 GB, Qwen3.8-Flash-Next IQ3_S

All decode/prefill numbers below are the serving engine's own log lines
(`strata serve: … generated in … ms (N tok/s)`), not client-side timing.
Raw model, no harness, thinking off, temperature 0.7, single client, warm
engine unless noted. Engine 0.1.55 linux-x86_64-cuda12, spec4 + MTP,
kv int8, resident experts page-locked in RAM.

| record | value | conditions |
|---|---|---|
| decode peak (burst) | **47.2 tok/s** | 106-token generation, draft acceptance 3/3 |
| decode sustained, structured / agent-style answers | **40.7–43.8 tok/s** | 1.9–2.8 k-token generations, draft acceptance 96–100% |
| decode sustained, free-form prose | **33.9–37.2 tok/s** | 1.0–2.0 k-token generations, draft acceptance 61–66% |
| decode worst case (degenerate repetition prompt) | 31.8–39.4 tok/s | quickbench ladder 2 k / 8 k / 16 k, acceptance 67–75% |
| prefill | **294.0 tok/s** | 16 448-token cold prompt, 0 KV reuse |
| prefill (32 k, client-measured) | 234.3 tok/s | 32 832-token prompt, quickbench after tuning |

## Config behind each row

Prose and worst-case rows: `--resident-budget-gib 25` +
`--memory-limit-mib 28672` + `--vram-reserve-mib 512` +
`STRATA_ROUTE_PRIOR=1.5` + `STRATA_RESIDENT_HEADROOM_GIB=1`
(residency-biased expert routing — the "route only to experts already in
RAM" mode from the 12 GB-card playbook).

Peak and structured-sustained rows: same box, `--resident-budget-gib 20` /
`--vram-reserve-mib 960`, no `ROUTE_PRIOR` (the config the v2.1 quality
series ran on).

`ROUTE_PRIOR=1.5` measured effect on this box: free-form prose decode
20–24 → 33–37 tok/s, degenerate-prompt decode 19–23 → 32–40 tok/s.
It carries the documented quality cost (more repetition, weaker agent
runs — upstream issue #4402); the quality series in this repo was run
without it, so treat speed and quality records as separate configs.

## Evidence (engine log excerpts)

```text
5 generated in 106 ms (47.2 tok/s), drafts accepted 3 of 3
85 generated in 1941 ms (43.8 tok/s), drafts accepted 63 of 63
114 generated in 2711 ms (42.1 tok/s), drafts accepted 84 of 87
102 generated in 2430 ms (42.0 tok/s), drafts accepted 75 of 78
114 generated in 2803 ms (40.7 tok/s), drafts accepted 83 of 90
1500 generated in 40349 ms (37.2 tok/s), drafts accepted 795 of 1297
2048 generated in 55716 ms (36.8 tok/s), drafts accepted 1118 of 1770
982 generated in 28937 ms (33.9 tok/s), drafts accepted 514 of 859
prompt 16448 tokens = 0 reused + 16448 read in 55938 ms (294.0 tok/s)
```

## What is not reachable here

60–70 tok/s decode on sm_60: IQ3_S decode is dequant-bound and Pascal has
no bf16/tensor path; the RTX 3060's 55–72 figure additionally relied on
the gpu-unlock module (GA102–GA106 only). Anything above ~47 sustained
would require a smaller quantization (quality change) or a newer GPU.
