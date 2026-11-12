# Fleet brain (P2005): squeezing the 82 GiB model into a 16 GiB VRAM ceiling — 12.11.2026

Owner constraints for this round, both hard: **total GPU memory in use ≤ 16 GiB**, **host RAM including the rest
of the system ≤ 32 GiB**, and **nothing but the benchmark on the box** (the agent was moved to the fallback brain,
so no agent traffic lands on P2005 during a measurement). The model stays our own `Qwen3.8-FN-IQ3_S.basalt`
(82 GiB, context 262 144, `kv int8`) — no downloads, no second GPU.

## How the ceiling is enforced

`vram-reserve-mib: 8079` in the engine block (24 463 − 16 384): the engine may fill everything except 8 GiB of
the card. Every arm below measured **15 989–16 351 MiB of total GPU use**, so the 16 GiB envelope holds by
construction, not by hope. RAM is held by `resident-budget-gib` (the expert tier ceiling in host memory).

## Configuration now live

```json
{"engine": {"max-context": 262144, "kv": "int8", "resident-experts": true, "expert-cache": "auto",
            "prefill": "auto", "vram-reserve-mib": 8079, "resident-budget-gib": 22,
            "resident-cpu-experts": true, "conversation-cache-mib": 6144,
            "conversation-cache-slots": 6, "conversation-cache-disk-mib": 20480}}
```

Verified after restart: **16 057 / 24 463 MiB GPU**, **28 Gi of 60 Gi host RAM** (31 Gi free, swap 1.0 Gi),
decode 60.5 t/s cold / 78–80 t/s warm, prefill 407 t/s, expert-cache hit ≈74 %, endpoint loaded in 27 s.
Rollback of everything measured so far: `cp ~/basalt/basalt-config.json.bak-20261112 ~/basalt/basalt-config.json`
(or `.bak-v4-arms` for the pre-winner state) and restart.

## Matrix — what each knob is worth inside 16 GiB

Six bench passes per arm (600-token prompt, greedy, seed fixed), engine's own accounting; every arm had
`foreign_in_window 0`, i.e. no foreign request contaminated the window. GPU watts are `nvidia-smi power.draw`
(1 s sampling over the bench window), CPU watts are the package through RAPL with the 32-bit energy counter
wrap corrected. Cost at 0.25 €/kWh, per million **generated** tokens, using GPU + CPU + ~15 W of board.

| arm | GPU MiB | host RAM | decode cold | decode warm, median | decode warm, best | prefill | GPU W | CPU W | kWh / 1 M | €/1 M |
|---|---|---|---|---|---|---|---|---|---|---|
| base (engine default spec) | 16 057 | 29 Gi | 61.4 | **82.5** | 83.2 | 412 | 88.4 | 78.1 | 0.611 | 0.153 |
| spec 4 + `resident-cpu-experts` (live) | 16 019 | 28 Gi | 64.7 | 81.8 | **87.1** | 400 | 89.9 | 79.0 | 0.624 | 0.156 |
| spec 4 | 16 019 | 29 Gi | 66.9 | 81.3 | 83.9 | 404 | 94.2 | 82.2 | 0.654 | 0.163 |
| spec 7 | 16 051 | 29 Gi | 67.2 | 79.0 | 83.6 | 402 | 94.0 | 76.1 | 0.651 | 0.163 |
| pinned `expert-cache` 12 000 MiB + spec 4 | 16 351 | 29 Gi | 63.4 | 76.9 | 82.6 | 403 | 95.1 | 77.8 | 0.679 | 0.170 |
| context 65 536 + spec 7 | 16 051 | 28 Gi | 62.6 | 76.2 | 78.7 | 409 | 91.0 | 82.7 | 0.688 | 0.172 |
| spec 2 | 15 989 | 28 Gi | 58.5 | 75.8 | 78.0 | 400 | 96.1 | 76.8 | 0.689 | 0.172 |
| `mtp-max-t 2` | 15 989 | 29 Gi | 60.2 | 72.3 | 74.0 | 399 | 95.4 | 75.6 | 0.715 | 0.179 |

An earlier pass (`v3`, same window) adds: `kv-resident 2048` 69.9 t/s, `vram-elastic` 69.3 t/s, `suffix-draft`
— the engine refuses to start with that key (`unknown argument`), and `resident-budget-gib 28` gave 78.2 t/s but
pushed host RAM to **38 Gi**, so it violates the 32 Gi ceiling and was dropped.

Reading of the table: inside this envelope **nothing buys more than noise**. The engine's own speculation default
is already the best median; forcing spec 2/4/7, pinning the expert cache, shrinking the context or enabling MTP
all sit level or below. `base` and `spec 4 + resident-cpu-experts` are statistically tied (Δ 0.7 t/s against a
run-to-run spread of ±3); the live pick is the second one because it shows the best single run (87.1 t/s) and the
lowest GPU draw of the two, which also leaves the card cooler.

## Profit probes

* **Per million generated tokens:** 0.153 € (base) / 0.156 € (live config). The whole spread across eight arms is
  0.153–0.179 € — tuning the knobs moves cost by ±8 %, nothing like the ±50 % that changing the memory ceilings
  does.
* **Per 1 000 real agent requests** (production-shaped call from the serve log: 141 799 prompt tokens, 99 %
  prompt-cache hit, 1 644 generated, 2.7 s prefill + 19.2 s decode at 85.6 t/s, so 1.12 Wh each): **0.28 €** on the
  16 GiB envelope. The same 1 000 calls on the unconstrained 24 GiB-VRAM tier (145 t/s decode, 0.63 Wh each) cost
  **0.16 €**.
* At ~3 000 such requests a day that is **≈0.84 €/day against ≈0.47 €/day** — the price of the ceiling in money
  rather than percentages.

## Ceiling, stated plainly

With our 82 GiB IQ3_S pack, the 16 GiB VRAM + 32 GiB RAM envelope tops out at **≈83 t/s median decode (87 best)**,
against 145 t/s when the card is allowed its full 24 GiB and 187 t/s when RAM is also unbounded. The mechanism is
unchanged from the memory-ceiling study: it is the expert-cache hit rate, 74 % here versus 93 % with a full card.
No engine knob closes that gap — the missing 100 t/s live in the 8 GiB of card and 14 GiB of RAM that the
constraints take away. Getting high decode **and** a 16 GiB card would mean a smaller pack of the same model
(≈2-bit class); that is a build step (disk + time to quantize), not a settings change, and needs an owner go.

Raw logs: `docs/data/p2005-16gb-20261112/v3-raw.log`, `docs/data/p2005-16gb-20261112/v4-raw.log`.
Drivers: `scripts/p2005_v3_ab.sh`, `scripts/p2005_v4_ab.sh`, bench `scripts/brain_bench.py`.
