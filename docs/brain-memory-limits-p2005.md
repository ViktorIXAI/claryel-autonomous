# Fleet brain (P2005): memory ceilings A/B — 12.11.2026

Owner instruction: cap the main brain at **15.5 GiB of VRAM** and **25 GiB of system RAM**, then measure what that
costs. Run on the brain box (RTX 5090 Laptop 24 GB, 60 GiB DDR4, model `Qwen3.8-FN-IQ3_S.basalt`, 87.6 GiB file).

## What changed

`~/basalt/basalt-config.json`, engine block. Backup kept as `basalt-config.json.bak-20261112`.

| Key | Before | After |
|---|---|---|
| `resident-budget-gib` | 56 | **25** |
| `vram-reserve-mib` | 512 | **8591** (24 463 − 15 872 → the expert tier may not take more than ~15.5 GiB) |

Everything else untouched: `max-context 262144`, `kv int8`, `resident-experts`, `expert-cache auto`,
`prefill auto`, conversation cache 6 GiB × 6 slots + 20 GiB disk tier. Restarted through `run-serve.sh`
(`keep-up.sh` re-arms every 2 min, so a killed serve comes back by itself).

## State after the restart (measured, not inferred)

| | Before | After |
|---|---|---|
| VRAM used | 23 563 MiB (basalt 21 618 + vision 1 850) | **15 487 MiB** (basalt 13 596 + vision 1 850) — inside the 15.5 GiB ceiling |
| System RAM used | 50 Gi of 60, 0.6 Gi free | 35 Gi of 60, **25 Gi available** |
| Swap | 8.0 Gi of 8.0 Gi used (**100 % full, 6.8 Gi of it was basalt**) | 0.99 Gi of 8.0 Gi — the swap is no longer a parking lot |
| Engine's own verdict | fits | `model 51.1 GiB, free VRAM + RAM 37.0 GiB: the rest is read from the SSD while generating (slow)`; `14.2 GiB experts on SSD`; `30 % of the experts are only in the file` |
| Expert-cache hit | 68–83 % | 53–71 % |

## Speed A/B (same script, same prompt, SSE chunk rate as the speed proxy, 424242 seed, greedy)

| Pass | Before (56 GiB RAM tier) | After (25 GiB RAM tier) |
|---|---|---|
| 600-token prompt, run 1 (cold) | TTFT 2.67 s, 81.3 | TTFT 3.48 s, 65.5 |
| 600-token prompt, run 2 | TTFT 0.53 s, 139.1 | TTFT 1.18 s, 80.2 |
| 600-token prompt, run 3 | — | TTFT 1.07 s, 92.4 |
| 4 000-token prompt | — | TTFT 4.35 s, 76.3 |

Decode cost ≈ **−20…−35 %**, warm TTFT ≈ **×2** (0.5 s → 1.1 s). The loss is explained by the engine's own
line: with 25 GiB of RAM tier, 14.2 GiB of experts (30 % of them) live only in the file and are read from
NVMe during decode; the expert-cache hit rate drops from ~75 % to ~60 %.

## Fallback brain check (done before the restart)

`fallback_providers` chain is `strata-mac → openai-codex → xai-oauth (grok) → anthropic sonnet`. The local
fallback (Mac, same IQ3_S family, 262 144 context) answered the same benchmark: TTFT 2.57 s cold / 0.91 s
warm, 63.7–64.9 chunk rate — i.e. it is a real, usable brain at ~55 % of the P2005 speed, not a stub. During
the restart itself the endpoint was down for ~20 s, which is the window the chain covers.

## Verdict

The caps hold and they buy real headroom: swap went from 100 % full to 1 GiB used, 25 GiB of RAM is free,
VRAM has ~9 GiB spare for anything else on that GPU. The price is one third of the tokens/s and roughly
double the warm time-to-first-token. If the point of the exercise is to free capacity for other work on
P2005, this is the right shape. If the point is speed, the useful middle is **keep the 15.5 GiB VRAM cap and
put the RAM tier at ~40 GiB** — that is where `14.2 GiB experts on SSD` disappears and the SSD reads stop.

Rollback: restore `basalt-config.json.bak-20261112` and restart the serve (a few seconds of downtime, the
fallback chain covers it).

Bench script: `scripts/brain_bench.py` (streams `/v1/chat/completions`, reports TTFT, SSE chunk rate, wall time).
