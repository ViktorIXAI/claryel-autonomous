# Fleet brain (P2005): memory ceilings — 12.11.2026

Owner instruction sequence: cap the main brain at **15.5 GiB of VRAM**, then hold **system RAM use at 30 GiB or
less**, keep everything else as it was, measure what it costs in tokens/s, and publish the running configuration
and the launch command.

Brain box: RTX 5090 Laptop 24 GB, 60 GiB DDR4, model `Qwen3.8-FN-IQ3_S.basalt` (87.6 GiB file), context 262 144,
vision on, `kv int8`. Backups: on the box `~/basalt/basalt-config.json.bak-20261112` (the original engine config),
on the control machine `~/.hermes/config.yaml.bak-brain-switch` (the brain-selection config).

## Final configuration (what runs now)

`~/basalt/basalt-config.json`:

```json
{
  "server": {
    "model": "model/Qwen3.8-FN-IQ3_S.basalt",
    "alias": "qwen3.8-flash-next-iq3_s-basalt",
    "gpu": "0",
    "host": "0.0.0.0",
    "port": 8080
  },
  "engine": {
    "max-context": 262144,
    "kv": "int8",
    "resident-experts": true,
    "expert-cache": "auto",
    "prefill": "auto",
    "vram-reserve-mib": 512,
    "resident-budget-gib": 22,
    "conversation-cache-mib": 6144,
    "conversation-cache-slots": 6,
    "conversation-cache-disk-mib": 20480
  }
}
```

Two keys set the shape (values after the second measurement round, see "What owns the speed" below):

* `vram-reserve-mib 512` — the card is deliberately left essentially full (23.6 GiB of 24.4 GiB in use). Reserving
  8 591 MiB of it, as the first round of this file did, halves decode speed: the expert tier shrinks and the
  expert-cache hit falls from 93 % to 72 %.
* `resident-budget-gib 22` — the ceiling for experts resident in system RAM. This is the knob that meets the
  owner's 30 GiB host target: 28 Gi used, 31 Gi free, swap 1.0 Gi.

Everything else untouched: context, `kv int8`, `resident-experts`, `prefill auto`, conversation cache 6 GiB × 6
slots + 20 GiB disk tier.

## Launch command

`~/basalt/run-serve.sh` (unchanged — `keep-up.sh` runs every 2 minutes and re-launches it whenever the endpoint is
not healthy, plus an `@reboot` line):

```bash
#!/bin/bash
cd $HOME/basalt
K=$(cat $HOME/basalt/basalt.key)
setsid nohup bin/basalt serve --config basalt-config.json --vision 0 --api-key "$K" >> basalt-serve.log 2>&1 &
echo started
```

Manual restart after a config change (≈20–45 s of downtime, the fallback chain covers it):

```bash
pkill -f "[b]in/basalt"; sleep 3; bash ~/basalt/run-serve.sh
for i in $(seq 1 30); do curl -s -m 8 http://127.0.0.1:8080/health | grep -q '"loaded": true' && break; sleep 10; done
```

## Measured state per RAM tier

| RAM tier (`resident-budget-gib`) | RAM used | RAM free | VRAM used | Swap used | Engine's own note at load |
|---|---|---|---|---|---|
| 56 (original) | 50 Gi of 60 | 0.6 Gi | 23 563 MiB (basalt 21 618 + vision 1 850) | **8.0 Gi of 8.0 — full, 6.8 Gi of it was basalt** | fits |
| 25 | 34–35 Gi | 25–26 Gi | 15 487 MiB (13 596 + 1 850) | 0.99 Gi of 8.0 | `14.2 GiB experts on SSD`; 30 % of experts file-only; expert-cache hit 53–71 % |
| **20 (current)** | **26 Gi** | **33 Gi** | **15 517 MiB** | 1.1 Gi of 8.0 | `19.2 GiB experts on SSD`; 41 % of experts file-only; `ram floor 7.8 GiB` |

Those two ceilings held exactly at the time. The 15.5 GiB VRAM half of it was **reverted the same evening** once
the matrix below showed what it was really costing; the RAM half is still in force at tier 22 (28 Gi used).

## Fallback brain check (done before the restarts)

`fallback_providers` chain is `strata-mac → openai-codex → xai-oauth (grok) → anthropic sonnet`. The local
fallback (Mac, same IQ3_S family, 262 144 context) answered the same benchmark: TTFT 2.57 s cold / 0.91 s warm at
~64 SSE chunks/s — a real, usable brain at roughly half the P2005 speed, not a stub. Each restart took the
endpoint down for ~20 s, which is exactly the window the chain covers.

Deliberate switch onto the fallback, to free the P2005 GPU while measuring:

```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak-brain-switch
sed -i '0,/^  provider: "strata"$/s//  provider: "strata-mac"/' ~/.hermes/config.yaml
sed -i '0,/^  default: "qwen3.8-flash-next-iq3_s-basalt"$/s//  default: "qwen3.8-flash-next-iq3_s"/' ~/.hermes/config.yaml
# back to the main brain:
cp ~/.hermes/config.yaml.bak-brain-switch ~/.hermes/config.yaml
```

Rollback of the engine limits: `cp ~/basalt/basalt-config.json.bak-20261112 ~/basalt/basalt-config.json` and
restart the serve.

## Speed cost

Client-side SSE reference (same script, 600-token prompt, seed 424242, greedy; chunk rate as a proxy) taken while
walking from the original config to the capped one:

| Pass | tier 56 (before caps) | tier 25 + 15.5 GiB VRAM |
|---|---|---|
| run 1 (cold) | TTFT 2.67 s, 81.3 | TTFT 3.48 s, 65.5 |
| run 2 | TTFT 0.53 s, 139.1 | TTFT 1.18 s, 80.2 |
| run 3 | — | TTFT 1.07 s, 92.4 |
| 4 000-token prompt | — | TTFT 4.35 s, 76.3 |

Decode −20…−35 %, warm TTFT ≈ ×2. The mechanism is the engine's own line: `30 % / 41 % of the experts are only in
the file: decode reads them from the SSD`, and expert-cache hit falls from ~75 % to ~60 %.

## Speed cost — absolute numbers, from basalt's own request lines

Every row has the **same 15.5 GiB VRAM ceiling** (`vram-reserve-mib 8591`); only the RAM tier changes. Driver:
`scripts/p2005_ram_ab.sh` — per tier it restarts the engine, waits for health, then drives 3 × (600-token prompt,
256 generated), 2 × (600/1024) and 1 × (4 000/256). `decode`/`prefill` below are the engine's own `done` lines
(`pp=` prompt read, `tg=` generation, `acc=` speculative drafts accepted 64–73 %); TTFT is client-side SSE.

| RAM tier (`resident-budget-gib`) | host RAM used | decode, cold | decode, warm (best of 4) | prefill, 5 553 tokens cold | expert-cache hit | warm TTFT |
|---|---|---|---|---|---|---|
| 20 — first cap round, later reverted | **26 Gi** | 58.5 t/s | **75.8 t/s** | 1 676 t/s | 64–72 % | ≈1.05 s |
| 25 | 31 Gi | 61.0 t/s | 80.4 t/s | 1 748 t/s | 66–74 % | ≈1.0 s |
| 56 (RAM uncapped) | 46 Gi | 75.4 t/s | **107.9 t/s** | 1 912 t/s | 66–73 % | ≈0.76 s |

Two notes on method. The model stops at ~150 generated tokens on this benchmark prompt (`end=stop`), so the
"1024-token sustained" arm is the same length as the others — no long-generation arm was reachable without
forcing `ignore_eos`. And the cold arm is one request per tier after a fresh load, so it also carries the
first-touch cost.

## Energy and cost (measured on P2005, 12.11)

`scripts/p2005_energy.sh` samples GPU `power.draw` (1 s) and the CPU package through RAPL while one bench runs,
and keeps the engine's own accounting lines for the same window:

```
[server] s1 done  pp=878/0c   1.9s 471t/s  tg=156 60.9t/s acc=69%  ttft=1.9s  end=stop  hit=65.8%
[server] s1 done  pp=878/873c 0.1s         tg=156 73.8t/s acc=70%  ttft=0.1s  end=stop  hit=72.1%
gpu_W_avg 79.8 (max 106.6)   cpu_package_W 76.3   (idle reference: GPU 8 W, CPU 6.7 W)
```

So decode on this box burns **≈80 W of GPU plus ≈76 W of CPU package** — the CPU number is the point: the
RAM-capped tier streams experts from NVMe and runs a third of the expert matmuls on cores, which is why the
box is a ~170 W device rather than a GPU-only one. With ~15 W of board/RAM/NIC overhead:

| arm | decode t/s | kWh per 1 M generated tokens | cost at 0.25 €/kWh |
|---|---|---|---|
| warm (tier 20, current) | 73.8 | 0.64 | **0.16 €** |
| cold (tier 20) | 60.9 | 0.78 | 0.19 € |
| tier 56 (RAM uncapped, power not re-measured) | 107.9 | ≈0.44 | ≈0.11 € |

Brain running 24/7 (mostly idle at ≈50 W plus ~4 M tokens of agent work a day) costs **≈1 € a day**.
The 30 GiB host cap therefore costs about **+0.05…0.08 € per million tokens** compared with leaving RAM
unbounded, and the same cap is what keeps 33 GiB of RAM and 9 GiB of VRAM usable for anything else on the box.
Wall-outlet power is not metered on P2005, so these are component sums, not socket readings.

## What owns the speed: the VRAM ceiling, not the RAM ceiling

A second matrix (`scripts/p2005_v2_ab.sh`, raw log `docs/data/p2005-brain-ab-20261112/ab2-raw.log`) crossed the
two ceilings — same bench, engine's own numbers:

| `vram-reserve-mib` | `resident-budget-gib` | host RAM used | VRAM used | decode cold | decode warm | expert-cache hit | experts on SSD |
|---|---|---|---|---|---|---|---|
| 512 (card full) | 56 | 38 Gi | 23 635 MiB | 114.1 | **187.1** | 94.2 % | — |
| 512 | 32 | 38 Gi | 23 635 MiB | 109.6 | 187.0 | 94.2 % | — |
| **512** | **22 (live)** | **28 Gi** | **23 615 MiB** | 85.9 | **145.0** | **93.2 %** | 9.3 GiB |
| 8591 (15.5 GiB VRAM cap) | 22 | 28 Gi | 15 521 MiB | 49.4 | 75.2 | 72.2 % | 9.3 GiB |
| 8591 | 32 | 38 Gi | 15 541 MiB | 63.8 | 87.1 | 71.7 % | 7.2 GiB |

Across the last three rows: at the **same** RAM budget (22) and the same 9.3 GiB of experts on SSD, giving the card
back to the engine lifts warm decode **75 → 145 t/s (+93 %)** and hit **72 → 93 %**. Down a column with the card
capped: pouring another 10 GiB of RAM at the problem buys almost nothing (75 → 87 t/s, hit unchanged). The earlier
verdict in this file — "the VRAM ceiling is the cheap half" — is **wrong**, and this matrix is what disproves it.

## The same story in four days of real traffic

The serve log carries 57 237 production `done` lines; split by the engine-era markers:

| era | requests | decode p50 | p90 | max | expert-cache hit p50 |
|---|---|---|---|---|---|
| `vram-reserve 512` + budget 56 (before the caps) | 18 331 | 130 | **242** | 353 | 87.2 % |
| same config, later days | 24 648 | 127 | 215 | 327 | 86.1 % |
| same config, longer sessions | 14 177 | 100 | 138 | 236 | 80.7 % |
| `vram-reserve 8591` + budget 20 (capped) | 11 | 62 | 74 | 79 | 58.5 % |

The "200 tokens/s" the owner remembered is real: it is the p90 of the uncapped config at 86–87 % expert-cache hit,
and it vanished when the VRAM reserve pushed experts onto NVMe. It also shows why the synthetic 600/150 bench
understated the damage: −30 % in the bench, −50 % at the production median plus the loss of the whole fast tail.

## Verdict (live config: `vram-reserve 512`, `resident-budget 22`)

* **Both owner constraints hold at once, but only by spending the card, not the RAM**: host RAM 28 Gi used
  (31 Gi free, target ≤30 GiB met) with warm decode 145 t/s, cold 86 t/s, prefill 518 t/s on the 878-token bench,
  expert-cache hit 93 %.
* The 15.5 GiB VRAM cap costs roughly **half of decode** (145 → 75 t/s at equal RAM). Keeping that much of the card
  free only pays if a second GPU service actually needs it on the brain box; at 23.6 / 24.4 GiB there is no
  headroom left.
* Raising RAM does not recover what the VRAM cap took: 22 → 32 GiB is +16 % decode and the hit rate stays at 72 %.
* Energy follows speed: at 145 t/s the same ≈170 W box makes a million tokens in ≈1.93 h (0.48 kWh) → **≈0.12 €/M**
  against 0.16 €/M at the capped tier.
* Fallback brain on the same bench ≈64 SSE chunks/s (~45 t/s equivalent) — about a third of the restored speed.

Rollback of the engine limits: `cp ~/basalt/basalt-config.json.bak-20261112 ~/basalt/basalt-config.json` and
restart the serve.

Bench script: `scripts/brain_bench.py` (streams `/v1/chat/completions`; TTFT, SSE chunk rate, wall time; args:
url, runs, model, prompt tokens, generation tokens). A/B driver: `scripts/p2005_ram_ab.sh`. A/B drivers: `scripts/p2005_ram_ab.sh` (RAM tiers), `scripts/p2005_v2_ab.sh` (VRAM × RAM matrix).
