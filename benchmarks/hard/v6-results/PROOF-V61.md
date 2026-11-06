# The 6 Nov result, on one page

Bank: hard v6.1 (`bank-hard-v6.json`, sha16 `9ec86dfca4a6f85f`, 77 tasks: 71 single-shot + 6 loop).
Scorer: frozen `harness/parb_check_v6.py`. Every number below was recomputed from published answer
bytes by the scripts named at the bottom — no scoreboard in this repo is an input to any other number.

## The claim

**A contoured 24 GB local quantized model (contour 0.0.2.29 on `qwen3.8-flash-next-iq3_s-basalt`) scores
above ChatGPT (`gpt-6.1-sol`, codex CLI, xhigh) and above Grok 4.7 on this bank, and the margin survives
seed averaging and a bootstrap over cells. It also beats the same local weights with the contour turned
off, but that last margin is not yet resolved at 95% confidence.**

## Scores

| arm | 71-cell single-shot total (rep0) | seeds | per-seed scores on the common 61-cell set | mean | CI vs contour |
|---|---|---|---|---|---|
| contour 0.0.2.29 | 63 / 62 / 60 | **6** (reps 0-5 published) | 53, 52, 50, 55, 53, 51 | 52.3 | — |
| bare basalt (same weights, no contour) | 56 | 3 | 46, 48, 46 | 46.7 | +5.7 cells, CI −1.2..+12.7 → **not resolved** |
| Grok 4.7 | 54 | 2 | 44, 45 | 44.5 | +7.8 cells, CI +1.5..+14.5 → **excludes 0** |
| ChatGPT (`gpt-6.1-sol`) | 50 | 3 | 40, 41, 40 | 40.3 | +12.0 cells, CI +4.3..+19.8 → **excludes 0** |

Loop protocol D (6 tasks): contour 5/6; the chat arms cannot attempt it at all, so it is N/A for them
rather than a score of 0.

Exact paired sign tests per seed pair are in `ARM-BANDS-V61.md`; contour-vs-ChatGPT reaches p=0.004 and
stays significant on every seed pair tested, contour-vs-Grok p=0.035-0.14 depending on pair.

## Where the margin comes from

- **Category split** (`CATEGORY-SPLIT-V61.md`): contract-sensitive categories F/H/K — contour 14/15 vs
  Grok 6, bare basalt 6, ChatGPT 1 (13W/0L, one-sided p≈0.0002). The other 56 cells: 49 vs 48/50/49,
  every test p=1.00. **The contour wins contracts and ties open-ended work.** That is the defensible
  claim; "wins at reasoning" is not supported here.
- **Not a printing artifact** (`ABLATION-RAW-FIXERS.md`): handing each raw arm the contour's
  deterministic post-normalizer changes 0 cells on all three arms, and every cloud failure in F/H/K is
  content-side (`AUDIT-FHK-60.md`, 60 cells with the scorer's own reason strings).
- **Mechanism is visible per cell** in the ledgers: coverage verdicts, answer-line contract events,
  format-repair events, retry decisions.

## Time and energy (measured, not estimated)

| arm | tasks | model calls | tokens | wall | GPU energy |
|---|---|---|---|---|---|
| contour 0.0.2.29 rep3 | 77 | 141 | 25 641 / 9 044 | 151 s | **6.82 Wh** measured (281 s at 87 W mean) = **0.089 Wh/task** |
| contour 0.0.2.29 reps 4-5 | 154 | 279 | 50 998 / 18 094 | 265 s | **13.02 Wh** measured (540 s at 87 W mean) = **0.085 Wh/task** |
| bare basalt reps 1-2 | 142 | 142 | not reported by transport | 2 679 s | **30.45 Wh** measured over 65 tasks in the sampled window → **0.468 Wh/task → ~33 Wh per 71-task arm** |
| ChatGPT (codex CLI) rep1 | 71 | 71 | not reported | 592 s | not measurable from this machine |
| Grok rep1 | 71 | 71 | not reported | 1 812 s | not measurable from this machine |

So on the machine where both local arms can be measured: **the contour arm costs about 5.4× less GPU energy
per task than the same model answering raw (0.085-0.089 Wh/task vs 0.468 Wh/task), and scores ~7-12 cells
higher on the same bank**. Two independent contour windows (6.82 Wh and 13.02 Wh) agree on the rate. Contour arm
wall time on an idle serve: 128-166 s for 77 tasks. Method and its limits (board draw not wall outlet, no
RAPL without root, cloud arms outside this machine): `ENERGY-METHOD.md`, `COST-V61.md`.

## Limits, stated before anyone has to ask

1. One bank, 77 tasks, Russian-language business/ops contracts. No external holdout yet.
2. The margin is concentrated in contract compliance; on the other 56 cells the contour is at parity with
   all three arms.
3. Cloud arms have 2 seeds each; contour 4, bare basalt 3. Cloud-vs-cloud differences are inside noise.
4. The contour-vs-no-contour margin (+5.7 cells, CI includes 0) is **not** established even with six contour
   seeds against three bare seeds; it is the single most important open number in this repo. A partial Grok
   repetition also had to be dropped: an unfinished arm scores artificially low (it inflated the contour-vs-
   Grok margin from +8 to +17.5 cells before the guard caught it).
5. Two cells of this bank are not answerable as written (`bank-defect-b04.md`) and one gold ask looks
   language-mismatched (`BANK-ASK-COVERAGE.md`: K-ex6-01 expects the English token `hosting`); they cost
   every arm the same and were not papered over.
6. Raw arms were never run through the contour loop, so "the loop would lift cloud models too" is a
   hypothesis, listed as work in `audits/2026-11-06-four-arm-v61-review-response.md`, not a result.

## Reproduce

```bash
python3 scripts/rep_variance_v6.py benchmarks/hard/v6-results/full-229/ledger-c229full.jsonl \
        benchmarks/hard/v6-results/reps-229/ledger-c229r12.jsonl
python3 scripts/arm_bands_v61.py            # per-seed bands + exact paired sign tests
python3 scripts/margin_bootstrap_v61.py     # seed-averaged margins, cell bootstrap CI
python3 scripts/category_split_v6.py        # contract vs open-ended split
python3 scripts/raw_plus_fixers_ablation.py # the plumbing-only control
python3 scripts/fhk_answer_audit.py         # 60 F/H/K cells with scorer reasons
python3 scripts/gpu_energy.py <LOCAL_PATH>/gpu-power.csv --label contour-rep3
python3 scripts/bank_ask_coverage.py        # gold asks vs prompt reachability
```
