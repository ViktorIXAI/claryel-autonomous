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

## The 48 GiB box simulation: how much of the VRAM loss RAM can buy back

Same 16 GiB VRAM fence (`vram-reserve-mib 8079`), same model, now with the host-RAM envelope the owner set: the
machine is treated as a 48 GiB box with 1 GiB of reserve — **everything on it, system included, must peak under
47 GiB**. Peak RAM below is sampled once a second from `free -b` across the whole bench window, so it is a real
peak, not a snapshot.

| RAM budget | peak host RAM (whole box) | decode cold | decode warm, median | decode warm, best | prefill 878 | GPU W | CPU W | total W | €/1 M tokens |
|---|---|---|---|---|---|---|---|---|---|
| 22 GiB | 29.1 GiB of 47 | 60.1 | 84.7 | 91.2 | 337 | 98.4 | 76.6 | 190 | 0.156 € |
| 30 GiB | 37.2 GiB of 47 | 69.4 | 86.0 | 90.4 | 468 | 106.3 | 80.4 | 202 | 0.163 € |
| 36 GiB | 43.4 GiB of 47 | 70.6 | 97.4 | 103.7 | 537 | 97.1 | 87.4 | 200 | 0.142 € |
| 42 GiB | 46.3 GiB of 47 | 86.1 | 107.8 | 108.9 | 642 | 114.7 | 87.1 | 217 | 0.140 € |

RAM pays for what the card was denied: from a 22 GiB expert tier to 42 GiB, warm decode goes **84.7 → 107.8 t/s**
and cold prefill **337 → 642 t/s**, while cost per million tokens falls 0.156 → 0.140 € — the faster tier is
cheaper, because the watts rise more slowly than the speed. The trade is headroom: 42 GiB leaves 0.7 GiB under
the ceiling, which is not survivable once real sessions with long contexts run on the box.

**Live pick: 36 GiB budget.** Verified after restart, and stress-checked with 16 553- and 41 303-token prompts
(the shapes real agent sessions use):

* peak host RAM **44.0 GiB of 47** (3 GiB margin), GPU **16 085 / 24 463 MiB**, swap 1.0 GiB;
* decode 97–99 t/s warm on short prompts, 86.0 t/s on a 16.5 K prompt, 73.1 t/s on a 41 K prompt (the long
  contexts cost decode, as expected from KV pressure);
* prefill on those long prompts: **3 298 and 3 037 t/s cold** — the strongest prefill number measured on this box;
* expert-cache hit 72–74 %.

If a future real workload pushes the peak past 47 GiB, the step down is `resident-budget-gib: 30` (peak 37.2 GiB,
86 t/s median) rather than touching the VRAM fence.

## Ceiling, stated plainly

With our 82 GiB IQ3_S pack, the 16 GiB VRAM envelope tops out at **≈97 t/s median decode (104 best) when 36 GiB of host RAM is allowed for the expert tier**, and at ≈83 t/s if the box is held to 32 GiB,
against 145 t/s when the card is allowed its full 24 GiB and 187 t/s when RAM is also unbounded. The mechanism is
unchanged from the memory-ceiling study: it is the expert-cache hit rate, 74 % here versus 93 % with a full card.
No engine knob closes that gap — the missing 100 t/s live in the 8 GiB of card and 14 GiB of RAM that the
constraints take away. Getting high decode **and** a 16 GiB card would mean a smaller pack of the same model
(≈2-bit class); that is a build step (disk + time to quantize), not a settings change, and needs an owner go.

Raw logs: `docs/data/p2005-16gb-20261112/v3-raw.log`, `docs/data/p2005-16gb-20261112/v4-raw.log`.
Drivers: `scripts/p2005_v3_ab.sh`, `scripts/p2005_v4_ab.sh`, bench `scripts/brain_bench.py`.
Raw 48 GiB pass: `docs/data/p2005-16gb-20261112/v5-raw.log`, driver `scripts/p2005_v5_ab.sh`.
