# Basalt 0.2.1 → 0.3.3 on P2005: what the new engine and its new knobs buy

Date: 2026-11-13. Machine: P2005 (RTX 5090L 24 GiB, ~60.5 GiB RAM). Pack: `Qwen3.8-FN-IQ3_S.basalt` (82 GiB).
This continues [brain-16gb-vram-ceiling.md](brain-16gb-vram-ceiling.md); the live regime going in was
`vram-reserve-mib 512` (whole card), `resident-budget-gib 42`, `resident-cpu-experts true`.

## Why

0.2.1 (2026-11-04) was 469 commits behind upstream `v0.3.3`, and the release notes named
exactly the two walls we had hit: long-prompt reading (our p90 prompt is 112 K tokens) and the
RAM-copy ceiling (the engine refused to put more than 43.25 GiB of the model into RAM at our RAM limit).

## Install method (no downtime risk)

* Separate worktree `~/basalt-033` at tag `v0.3.3`; the running `~/basalt` (0.2.1 binary + config) is untouched.
* `cmake -B build -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc && cmake --build build` → `bin/basalt`.
  Without the explicit CUDA compiler the configure step dies at `enable_language(CUDA)`.
* Config: `tools/migrations/config_v1_to_v2.py basalt-config.json` — 0.3.x reads a v2 config where each
  model is an entry (`models: [{model, alias, gpu, kv, max-context}]`); the flat v1 keys still load.
  Note the model path in a v2 config resolves **relative to the config file**, so use an absolute path.
* The 0.2.1 stack is supervised: `bin/basalt serve` starts a Python server which restarts its engine child.
  `pkill basalt` alone therefore brings the old engine back; stop it with `pkill -f '[s]erve.server'` first.
* `keep-up.sh` (cron */2) only restarts when nothing matches `bin/basalt`, so the new engine at
  `~/basalt-033/bin/basalt` is left alone while it runs.

## v8 — the new performance knobs, one at a time (raw: `data/p2005-033-20261113/v8-raw.log`)

Short arm = 7 repeats of 600-token prompt / 1024 requested (engine sees pp=878), then one 20 K-token
prompt (engine sees pp=27553). Whole-box power, whole-box RAM, swap-in/out per second, engine lines.

| Arm | decode median | decode best | cold start | 27.5K read t/s | 27.5K decode | hit | peak RAM | GPU W | CPU W |
|---|---|---|---|---|---|---|---|---|---|
| 0.2.1 control (v7 `vmax_b42`) | 186.7 | 188.7 | 111.9 | 3263 (warm-cache runs 137.0 decode) | 137.0 | 94 % | 38.6 | 122.7 | 94.0 |
| **0.3.3 base** | **185.5** | **201.8** | **126.6** | **3768** | **164.8** | **95.8 %** | **37.1** | 143.2 | 65.3 |
| + `ram-reserve-mib 4096`, budget 50 | 180.6 | 204.4 | 119.5 | 3734 | 154.4 | 96.0 % | 37.0 | 135.6 | 63.5 |
| + `kv k8v4` | 182.7 | 183.9 | 127.8 | 3391 | 153.7 | 96.2 % | 37.0 | 140.7 | 63.8 |
| + `prefill auto:32768` | 180.5 | 204.2 | 131.2 | 3746 | 170.0 | 96.1 % | 37.3 | 133.9 | 64.9 |
| + `prefill-cpu-share 0.2` | 173.8 | 191.4 | 119.3 | 3719 | 156.6 | 96.0 % | 37.1 | 138.8 | 63.6 |
| + `relaxed-drafting 0.5` (**lossy**) | 182.1 | 196.0 | 133.9 | 3710 | 179.5 | 96.3 % | 37.0 | 144.8 | 65.2 |
| + `ple-io ram` | 173.2 | 179.0 | 99.3 | 3712 | 154.8 | 96.2 % | 43.7 + swap | 134.8 | 59.2 |

Readings:

* **The upgrade itself is the win, not the knobs.** Every extra knob is neutral or negative on top of
  plain 0.3.3; the pack and the memory layout stay as they were.
* The **43.25 GiB RAM-copy wall is gone by itself**: at the whole-card VRAM window there is nothing left to
  copy — SSD reads during decode fell to `ssd=0.2–0.4 %`, and raising `resident-budget-gib` to 50 with a
  4 GiB `ram-reserve-mib` changed neither RAM peak (37.0 GiB) nor speed.
* **Long-prompt reading**: 27.5 K cold read 3263 → 3768 t/s (+15 %), TTFT 8.4 → 7.3 s; and decode
  *while* a 27.5 K context is resident improved 137 → 165 t/s.
* **Cold start** (first request after load) 111.9 → 126.6 t/s.
* Expert-cache hit 94 → 96 %, so less SSD traffic and lower CPU burn: 94 → 65 W while GPU rose 123 → 143 W.
* `relaxed-drafting` (the lossy knob) buys nothing here — with a 96 % expert-cache hit the draft is already
  accepted at 68–73 %; we keep exact decoding.

## v9 — batch slots, single-stream cost (raw: `data/p2005-033-20261113/v9-raw.log`)

`--batch N / --slots N` (2..8) is the 0.3.3 name for what the changelog called `--parallel`.

| Arm | decode median | decode best | hit | ssd | peak RAM | GPU used |
|---|---|---|---|---|---|---|
| batch 1 (default) | 177.6 | 192.1 | 96.2 % | 0.2 % | 37.4 | 23563 MiB |
| batch 4 | 175.4 | 187.2 | 94.2 % | 0.6 % | 42.6 | 23563 MiB |
| batch 8 | 145.9 | 155.1 | 92.5 % | 1.0 % | 47.3 | 23869 MiB |

Each slot carries its own session state, so batching costs VRAM, RAM and expert-cache space: batch 8
gives up 18 % of single-stream decode. (The first concurrency probe was invalid — `brainbench.py`'s
second argument is *sequential repeats*, not parallel streams — so the honest parallel measurement is in v10.)

## v10 — true concurrency (raw: `data/p2005-033-20261113/v10-raw.log`)

Four requests fired at the same moment (600-token prompt, 1024 requested; the pack answers ~155 tokens and stops),
aggregate taken from the engine's own `done` lines over the wall window.

| Config | aggregate tok/s | per-stream decode t/s | TTFT of the four | last stream finishes | peak RAM |
|---|---|---|---|---|---|
| batch 1 (default) | 173.1 | 172.6 / 199.9 / 175.9 / 190.5 | 0.37 / 1.35 / 2.16 / 3.11 s | 3.6 s | 36 GiB |
| batch 4 | 178.8 | 47.2 / 50.2 / 57.5 / 52.8 | 1.35 / 1.70 / 1.84 / 1.97 s | 3.4 s | 42 GiB |
| batch 4 + `prefill-cpu-share 0.3` | 185.2 | 50.9 / 54.0 / 56.5 / 133.5 | 1.63 / 1.71 / 1.71 / 1.79 s | 3.3 s | 42 GiB |

The whole-box throughput is the same no matter how it is scheduled (173–185 tok/s): the limit is the expert path,
not the scheduler. Batching only moves the wait around — batch 1 decodes each request at full ~190 t/s but the
fourth one starts after 3.1 s; batch 4 starts all four at ~1.7 s and each one crawls at 47–57 t/s, while costing
6 GiB more RAM and ~100 MiB more VRAM. Our traffic is one brain call at a time with occasional overlap, where the
queue delay is under a second and every reply stays fast, so **batch 1 stays on**.

## Cost

Whole-box power during decode, 0.25 €/kWh, decode-only window (prefill energy excluded):

| Config | W (GPU+CPU) | median t/s | €/M generated tokens |
|---|---|---|---|
| 0.2.1 whole-card | 122.2 + 94.1 = 216.3 | 186.7 | 0.080 |
| 0.3.3 whole-card (v8 base) | 143.2 + 65.3 = 208.5 | 185.5 | 0.078 |
| 0.3.3 whole-card (v9 base) | 126.5 + 53.1 = 179.6 | 177.6 | 0.070 |

Real agent traffic (971 tokens average, p90 1718) puts us at ~0.07–0.08 €/M generated tokens, i.e. roughly
0.07 €/1000 short requests; a 3000-request day is ~0.25 € of active burn on top of ~0.18 € idle.
The 0.3.3 gain is concentrated where our traffic actually hurts: prompt reading (p90 112 K tokens) and
long-context decode.

## Live now (2026-11-13)

`vram-reserve-mib 512`, `resident-budget-gib 42`, `resident-cpu-experts true`, `kv int8`, `batch 1` —
same memory plan as 0.2.1, new engine. Started by `~/basalt/run-serve.sh` (now points at
`~/basalt-033`, tag **v0.3.3**, `git describe` = `v0.3.3`), so the `keep-up` cron supervises the new stack;
rollback is one command away: `~/basalt/run-serve-021.sh` (0.2.1 binary and config untouched, plus
`basalt-config.json.bak-021-final`).

Vision: `--vision 0` (the 0.3.x server takes a mode/GPU number, a bare `--vision` is a startup error) —
health reports `images: true`. The encoder borrows expert-cache slots, so on the live stack the expert hit
is 93–94 % instead of 96 % and warm decode is **171–177 t/s** rather than the 185 measured without vision;
long-context decode is unchanged (27.5K context: 165.8 t/s). GPU 23 657 / 24 463 MiB at 163 W and 51 °C,
RAM 39 Gi used, swap 1.0 GiB.

Hermes primary brain is back on this box (`model.provider strata`, `model.default qwen3.8-flash-next-iq3_s-basalt`,
fallback chain mac → codex → grok → sonnet), proven with a real one-shot turn that landed in the serve log:
`pp=13159` system prompt read at **3211 t/s** (TTFT 4.1 s cold), decode 133.7 t/s.
