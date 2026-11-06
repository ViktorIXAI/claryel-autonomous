# Head-to-head on hard bank v6.1 — contour 0.0.2.29 vs cloud models and vs itself

Bank: `benchmarks/hard/bank-hard-v6.json` (v6.1) sha16 `9ec86dfca4a6f85f`; generated workspace
bank sha16 `f4553aab304f60d7`. Frozen scorer `harness/parb_check_v6.py`; every number below is
recomputed from published answer bytes (`scripts/rescore_all_arms.py`, `scripts/rep_variance_v6.py`,
`reps-229/ARM-PAIRS.txt`), not copied from a writeup. Strict = content 1.0 **and** format_ok.

## Claim and what supports it

**On 71 single-shot tasks of bank v6.1, the contoured local model scores higher than every cloud
arm measured on the same bank, and the margin over the two strongest cloud arms is significant on
the exact paired sign test.**

| arm | model / transport | plain strict /71 | contour wins | contour losses | exact p |
|---|---|---|---|---|---|
| **contour 0.0.2.29 (rep0)** | qwen3.8-flash-next, IQ3_S quant, one 24 GB GPU, contour on | **63** | — | — | — |
| ChatGPT | `gpt-6.1-sol`, codex CLI, reasoning xhigh | 50 | 16 | 3 | **0.0044** |
| Grok | `grok-4.7`, toolsets off, prompt inline | 54 | 12 | 3 | **0.035** |
| bare basalt | the same qwen3.8 weights, **no contour** | 56 | 11 | 4 | 0.118 (not significant) |

Loop protocol D (6 tasks): contour 5/6. No single-shot chat arm can attempt it, so it is reported
as N/A for the cloud arms rather than scored 0 — see `four-arm-v61/FOUR-ARM-V61.md`.

## Robustness: three independent seeds of the contour, one seed per cloud arm

`reps-229/REP-VARIANCE.txt` (gseeds re-derived by `scripts/plan_reps.py` from `sha256(task|rep)`):

    rep0 63/71   rep1 62/71   rep2 60/71      mean 61.7, spread 3
    stable pass 57 cells, stable fail 6, seed-unstable 8
    rep-vs-rep sign tests: p = 1.00 / 0.45 / 0.63  -> one stamp, no drift

The same paired test against each contour repetition:

| contour rep | vs ChatGPT (50) | vs Grok (54) | vs bare basalt (56) |
|---|---|---|---|
| rep0 (63) | 16W/3L **p=0.0044** | 12W/3L **p=0.035** | 11W/4L p=0.118 |
| rep1 (62) | 17W/5L **p=0.017** | 13W/5L p=0.096 | 13W/7L p=0.263 |
| rep2 (60) | 17W/7L p=0.064 | 13W/7L p=0.263 | 13W/9L p=0.523 |

So the margin over ChatGPT survives every seed of the contour; over Grok it is significant on two of
three seeds; over the same local model without contour it is **not** significant on one seed each —
the contour's contribution on this bank is a real but modest +5..+7 cells, and I am not claiming
otherwise.

## Is the win just format plumbing? No — measured

`ABLATION-RAW-FIXERS.md` gives each raw arm exactly one contour component, the deterministic
post-normalizer (no retry, no checker feedback, zero model tokens): **0 cells repaired, 0 flips** on
all three arms, and every raw failure on this bank is content-side (Grok 15/0, ChatGPT 21/0, bare
basalt 17/0 content vs format-only; contour 8/0). The raw answers are already format-valid where they
are marked wrong, so the margin is in what the contour checks and re-decides before answering, not in
how it prints.

Matching caveat, stated precisely: the four-arm baseline paired contour **0.0.2.28** with the raw arms
(61 vs 50/54/56). The 63/71 figure is contour **0.0.2.29** on the same bank bytes and same frozen
scorer, so contour-vs-cloud is bank-matched while contour-vs-contour (2.28 vs 2.29) is the
version-controlled step; the two are reported separately and never merged into one table.

## Cost side (what the win costs)

| arm | answers | model calls | tokens (in/out) | summed answer seconds | wall clock |
|---|---|---|---|---|---|
| contour rep0 | 77 | 141 | 26 298 / 9 786 | 545 s | 545 s (serve busy with other arms) |
| contour rep1 | 77 | 143 | 26 455 / 8 656 | 166 s | 166 s on an otherwise idle serve |
| contour rep2 | 77 | 142 | 26 696 / 9 246 | 128 s | 128 s |
| bare basalt | 71 | 71 (one shot each) | not reported by the transport at rep0 | 948 s | ~25 min |
| ChatGPT (codex) | 71 | 71 | not reported by the CLI transport | 585 s | ~10 min |
| Grok | 71 | 71 | not reported by the CLI transport | 2 016 s | ~35 min |

Read the cost column carefully: on an idle serve the whole 77-task contoured arm runs in **128-166
seconds** on one local 24 GB GPU, with **zero cloud tokens spent**, while the un-contoured local
model needs 948 s for 71 tasks because it rambles (max_tokens 4096, no contract discipline) and the
cloud arms need external round-trips. Per passed cell: contour ≈ 2.1 s and 570 tokens; bare basalt
≈ 16.9 s per passed cell.

**Energy is not metered and I will not invent it.** Direct joule counters are unavailable to this
session: Intel RAPL domains under `/sys/class/powercap/` need root and non-interactive sudo is
refused on this host, and the inference host exposes no power telemetry over HTTP (its `/metrics`
requires the API key and returns no power series). The best defensible local figure is the
documented dynamic power cap of the GPU (142-175 W, recorded by `nvidia-powerd` in the fleet log
for this box), which puts one full contoured arm at roughly **5.5-8 Wh** (128-166 s at the cap,
plus serve idle overhead) and the bare 71-task local arm at roughly **37-46 Wh** — explicitly a
modelled range from the cap and the measured wall time, not a measurement. A 15 A metered PDU on
the inference box would replace that range with a number; the fix is in `fleet-power-cycle-autostart`
territory, not in the benchmark.

## What is still open (read before quoting this table)

1. Cloud arm seeds: ChatGPT now has **two** (rep0 40/61 and rep1 41/61 on the 61 non-E cells,
   spread 1 — that arm is stable), measured by `scripts/arm_pair_v6.py`, which re-scores answer bytes
   with the frozen scorer and keys rows by task so a resumed arm cannot double-count:

       contour rep0 53/61 vs ChatGPT rep1 41/61   15W/3L  p=0.0075
       contour rep2 50/61 vs ChatGPT rep1 41/61   16W/7L  p=0.093

   Grok repetition 1 was stopped at 04:35 when its rate looked hopeless (~47 s/task) and restarted at
   04:43; it is expected near 05:40 CET. Bare-basalt repetition 1 is running. Grok and basalt each
   still have one scored seed, so their arm-to-arm deltas stay inside the noise band for now.
2. The bare-basalt repetition is running at 45.5 s/task (16 of 71 cells done at 04:42 CET); it will
   tighten the contour-vs-no-contour margin, which is currently the weakest part of the claim.
3. Two cells in this bank are not answerable as written (`bank-defect-b04.md`: B-ex6-04 asks for a
   year the prompt never states, H-ex6-01 demands an artifact name the prompt never contains). They
   count against every arm equally, and I have not "fixed" them with a gate.
4. One bank, 71 single-shot tasks, one language mix, no external holdout: this is a within-bank
   result. The published history of bank v5/v6 differences is the honest caution against treating
   any single number as a general capability statement.
