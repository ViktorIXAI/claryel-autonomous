# ARC-Easy (2376 tasks) — three-arm result

Date: 2026-11-08. Pinned task file `benchmarks/public/arc-easy.tasks.jsonl`, tasks sha16
`cac604a076e8b00a` (source: Hugging Face `allenai/ai2_arc`, ARC-Easy test split, normalised to a
four-option letter prompt; `meta.options = 4` on all 2376 rows, so the random-guess floor is
25 %). Checker contract in force at scoring time: `pub-checkers-v2`
(`scripts/pub_bench_score.py`, self-test 19 cases / 0 failures, `letter` checker: an explicit
`ANSWER: X` line, else the first A–J token). Every arm stored its answer bytes; the percents are
reproducible from them.

## Arms

| arm | model / transport | tasks | strict | wall time | call parameters |
|---|---|---|---|---|---|
| brain-basalt (full set) | `qwen3.8-flash-next-iq3_s-basalt`, IQ3_S on a 24 GB-class GPU, no contour | 2376/2376 | **2261/2376 = 95.2 %** | 2925 s (mean 1.23 s/task), one draw per task | temp 0.7, max_tokens 1200, single seed pass |
| brain-basalt (matched subset) | same | 300/300 | **290/300 = 96.7 %** | first 300 ids of the full leg | temp 0.7, max_tokens 1200 |
| codex | `gpt-6.1-sol`, codex-cli 0.166.0, reasoning xhigh, read-only sandbox, prompt via STDIN | 300/300 | **290/300 = 96.7 %** | 1601 s (5.3 s/task) | sampling parameters not exposed by the transport |
| grok | `grok-4.7`, hermes one-shot, toolsets off, prompt inline | 300/300 | **289/300 = 96.3 %** | 4458 s (14.9 s/task) | sampling parameters not exposed by the transport |

Cross-arm numbers use the **pre-registered matched subset**: the first 300 task ids of the pinned
file in file order, fixed before any arm ran (`--limit 300 --offset 0`). 300/300 ids answered in
all three arms, 0 dropped in the join, 0 empty answers, 0 transport failures (each leg's own
stop-after-3 rule never fired).

Note the honest asymmetry: the local brain's headline (95.2 %) is the full 2376-task set and is
**lower** than its own score on the pre-registered 300-id head of the file (96.7 %). The subset
was frozen before any arm ran and is not re-cut; the gap says the first 300 ids happen to be the
easier part of this file, which is exactly why the full set is the local arm's budget.

## Paired sign tests on the matched 300

Exact two-sided sign test over discordant pairs only (`scripts/pub_bench_compare.py`).

| pair | W/L | diff | p |
|---|---|---|---|
| basalt vs codex | **0W / 0L** | +0.0 pp | 1.000 |
| basalt vs grok | 1W / 0L | +0.3 pp | 1.000 |
| codex vs grok | 1W / 0L | +0.3 pp | 1.000 |

The whole three-arm table turns on **one task id**: `arc-easy-0285` is the only id of 300 where the
three arms do not give the same verdict (basalt and codex correct, grok wrong). 299 of 300 cells
agree across a 24 GB quantized local brain and two cloud brains.

**Verdict: the instrument, not the models, is the limit here.** With zero discordant pairs between
basalt and codex and one discordant pair overall, ARC-Easy at 300 tasks has no power to separate
these brains at all; any claim of an ordering would be noise. The line treats this benchmark as a
plumbing-and-regression yardstick (it caught a dead transport and a stale endpoint alias, and it
pins the local energy baseline) and moves on: ARC-Challenge legs are running now, and the
unsaturated sets (SimpleBench, GPQA-Diamond, MMLU-Pro, LiveCodeBench) are where a difference,
if any exists, can actually be resolved.

## Resources

* Local leg: prompt 267,593 tokens + generated 214,377 tokens = 481,970 tokens for 2376 tasks
  (mean 113 in / 90 out per task), mean 1.23 s per task. GPU sampler at ~2 s (1132 samples,
  window 16:49:10–17:37:02, span 2872 s): mean 127.1 W, GPU busy fraction 0.74, **energy
  101.43 Wh** integrated from `power.draw` (board-level GPU draw, not a wall-outlet reading;
  method and its limits in `../hard/v6-results/ENERGY-METHOD.md`). Per-task energy on the local
  arm: ~43 mWh.
* Cloud legs: wall time only; no local GPU consumed. The grok leg overlapped the ARC-Challenge
  codex leg in wall-clock time — different CLI transports, no shared inference endpoint, so the
  local endpoint stayed exclusive to its own leg and no arm was contended.

## Honest caveats

1. **Contamination and saturation.** ARC-Easy is a public, static 2021 set, retired for frontier
   comparison in 2026 aggregators (last reported public ARC number 95.3 %, see `PUB-PLAN.md`).
   Our 24 GB quantized local brain scores 95.2 % on the full set — indistinguishable from that
   public frontier number, which is a strong sign memorisation cannot be excluded. This row is
   **not** an intelligence claim.
2. **The harness cannot change this score.** Grading is the final letter only, so contour vs
   no-contour is invisible; per `PUB-PLAN.md` the contour arm joins only benchmarks 4 (IFEval)
   and 9 (BFCL).
3. **One draw per task, temperature 0.7.** No best-of-N, no retry, no seed sweep. On a set this
   saturated one single-draw flip per arm is expected noise, and here the entire three-arm
   disagreement budget is one flip.
4. **Cloud arms hide their sampling parameters**; their rows are labelled by transport instead of
   a fake pin, and they were not run at a matched temperature.
5. **Cloud transports are file/tool capable.** codex runs read-only with STDIN prompt, grok runs
   with toolsets off. Both answer files were grepped before publication for
   `bank|answer_key|expected_|/home/|/Users/|<LAN_IP-prefix>`: **0 matches** in each.
6. **A 4-option MCQ has a 25 % guessing floor.** All three brains sit 71 pp above it, so the
   measured differences are not a floor artifact — they are just too small for this sample.
7. **P0-complete since 2026-11-08 20:43 CET.** The contour-parity row (item P0) ran and is
   published in the section below; the three-arm table above stays the bare-brain comparison.

## Contour parity (item P0): the frozen runtime on the same 300 ids

> **SUPERSEDED 2026-11-08 23:35 CET as a parity row.** The parity rule on this line requires
> the contour leg's request shape to equal the bare arm's (first rung 1200, serve-default
> thinking, no pinned request seed). This arm ran at a 512-token first rung with
> `enable_thinking:false` and a pinned sp1 seed, and it generated **2.0 tokens per task** — it
> never reasoned, which is why the answer-only checker left all 300 verdicts untouched. The
> matched-shape re-run (`PARB_SHAPE=bare PARB_LADDER=1200`, frozen stamp, no new contour
> feature) is running as of this edit and lands as its own row. The bytes of this leg stay
> published unchanged and are shipped under `arms/` for re-scoring.

The frozen contour runtime `0.0.2.56` (tag `stable-hard-0.0.2.56`, harness tree `381dc5b2`-era
modules byte-verbatim via `scripts/pub_bench_contour_ws.py`) ran over the first 300 ids on the
same endpoint, category `P`, public checkers in the validator slot, scored by the same
`pub-checkers-v2` bytes. Note this leg ran **after a serving-engine restart** (the box hit full
swap at ~20:36 and keep-up relaunched the engine; a first 25-row attempt on the sick endpoint was
discarded whole as `dead1/` and contributes nothing).

| measure | value |
|---|---|
| strict on the matched 300 | **290/300 = 96.7 %** — identical to the bare arm |
| paired vs bare arm | **0W / 0L** (p = 1.000): every one of the 300 verdicts is identical |
| contour/repair events fired | **0**; ladder escalations **0**; truncations **0**; stalls **0** |
| model calls / fixes / blocks | 300 / 0 / 0 |
| prompt + generated tokens | 21,943 in + 600 out |
| wall / measured engine time | 115 s / 103.2 s (0.34–0.39 s/task) |
| GPU energy (2 s sampler, 46 samples, 113 s full-leg window) | **3.70 Wh** (~12.3 mWh/task) |

Read as a request-shape result this is informative: on 300 ids the frozen runtime reproduced the
bare arm's verdict on **every task**, fired zero machinery and paid zero ladder retries. What it
did *not* do is answer the parity question: with thinking switched off the arm emitted 2.0 tokens
per task, so the null mechanism census and the null delta are both guaranteed by the request shape
rather than measured. On an answer-only MCQ the checker cannot see reasoning at all, so the
matched-shape leg is expected to land at parity too — and it has to be run to be worth quoting. Unlike ARC-Challenge (same
stamp, 12 discordant ids with the same null mechanism census, attributed there to sampling
shape and the engine restart), this leg shows the variance budget can also land at zero flips;
the ARC-Challenge ±3 pp caveat applies to any use of this row as an instrument.

The honest framing stays: on an answer-only MCQ the contour *cannot* change the score by
construction (category `P` routes away from every hard-bank grammar), so the parity rows exist
to prove that claim mechanically and to bound the harness cost — not to claim a tie on quality.
