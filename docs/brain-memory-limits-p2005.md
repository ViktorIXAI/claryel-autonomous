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
    "vram-reserve-mib": 8591,
    "resident-budget-gib": 20,
    "conversation-cache-mib": 6144,
    "conversation-cache-slots": 6,
    "conversation-cache-disk-mib": 20480
  }
}
```

Two keys did the work:

* `vram-reserve-mib 8591` = 24 463 − 15 872. With `expert-cache auto`, the expert tier only fills what is left on
  the card after the reserve, which pins total GPU use at ≈15.5 GiB.
* `resident-budget-gib 20` = the ceiling for resident experts in system RAM.

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

Both ceilings hold exactly: the 30 GiB RAM target is met with 4 GiB of slack at tier 20, and VRAM sits at 15.5 GiB
with ≈9 GiB of the card free for anything else.

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

Absolute tokens/s per tier (20 / 25 / 56) at the fixed 15.5 GiB VRAM ceiling are taken from basalt's own request
lines (`pp=`, `tg=`, `acc=`, `hit=`) in the follow-up commit to this file.

Bench script: `scripts/brain_bench.py` (streams `/v1/chat/completions`; TTFT, SSE chunk rate, wall time; args:
url, runs, model, prompt tokens, generation tokens). A/B driver: `scripts/p2005_ram_ab.sh`.
