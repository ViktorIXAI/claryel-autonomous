# Addendum — max-memory config + idle-endpoint max bench (2026-11-05)

## What changed in the config (frozen as basalt-config.WORKING-20261105.json)

Per operator request the box now runs with essentially zero idle RAM while keeping the
contracted reserves (≈1 GiB RAM free, 512 MiB VRAM free):

| Setting | Before | After | Effect |
|---|---|---|---|
| `resident-budget-gib` | auto (29.5 GiB pinned) | `56` → engine-capped 49.07 (all 36 GiB non-VRAM experts pinned) | no expert is ever read from SSD again |
| `conversation-cache-mib` | 0 | `6144` (6 slots) | idle chats park in RAM, resume without re-reading |
| `conversation-cache-disk-mib` | 0 | `20480` | LRU conversations park on NVMe, survive restarts |

RAM distribution under load (60.4 GiB total): engine RSS ≈ 51.4 GiB (36 pinned experts
+ mapped pack + KV staging + checkpoints), OS ≈ 2 GiB, **0.6–0.9 GiB free**, remainder
is page cache of the pack (the warm tier — reclaimable, not idle). VRAM: 23 563 / 24 463
MiB used, **513 MiB free** (dense 21.5 + GPU vision encoder ~0.9 + elastic KV + graphs).
Safety unchanged: the engine's RAM guard (MemAvailable + PSI) parks conversations to
disk instead of killing requests; hard-critical below 1 GiB free aborts cleanly with an
API error, never a crash.

## Max bench — endpoint fully idle (Hermes brain temporarily moved to Mac Studio)

Protocol: warmup (2×3 conversations, 900 t) → cold ladder ×1 → repeat ladder (resumed
conversations) → long warm decode (1200 t). GPU 145 W, 67 °C, RAM free at the floor.

| Context | cold prefill | cold decode | resumed decode | wall cold → resumed |
|---:|---:|---:|---:|---:|
| 640 | 759 | 72.4 | — | 1.7 s |
| 2 176 | 1 767 | 159.6 | 40.2* | 1.7 → 5.9 s* |
| 8 320 | 2 752 | 188.0 | — | 3.4 s |
| 16 512 | 3 516 | **206.7** | 180.6 | 5.0 → 0.6 s |
| 32 896 | 3 694 | 196.4 | — | 9.2 s |
| 65 664 | 3 645 | 141.3 | 169.3 | 14.0 → 1.9 s |
| 131 200 | 3 410 | 110.5 | **164.2** | 24.6 → **1.5 s** |

*resumed 2K run hit a cold-start slot; not representative.

Long warm decode (900–1200-token generations, warm conversations): **131–168 tok/s**
(peak 167.9). This exceeds the historical Strata record on this box (warm 109–118,
engine-log bursts 141–160 — see the 2026-10-23 retrospective record) on the same GPU
with the same weights.

## Takeaways

- The practical agent win is the conversation cache: a 131k-token session resumes in
  1.5 s instead of 24.6 s of prefill, and resumes decode at ~165 tok/s.
- Peak single-stream decode observed: 206.7 tok/s (16k context, idle endpoint).
- With Hermes traffic sharing the endpoint the same ladder measures ~15% lower —
  benchmarks must state whether the brain was parked; this run had it on the Mac.
- Brains were switched back to Basalt on P2005 immediately after this run.
