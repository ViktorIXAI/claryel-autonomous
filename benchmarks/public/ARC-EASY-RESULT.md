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
| contour-0.0.2.56, matched shape (item P0 re-run, 2026-11-08 23:36 CET; row added to this table 2026-11-10 — until now this table carried no contour row at all, so both the superseded escalation percent 290/300 = 96.7 % and the in-force 289/300 were quotable only from the parity section below) | the FROZEN contour runtime `0.0.2.56`, workspace `pub-arc-easy-contour-matched`, request shape equal to the bare arm's (`PARB_SHAPE=bare PARB_LADDER=1200`), first 300 ids, checker `pub-checkers-v2` | 300/300 | **289/300 = 96.3 %** *(in force; the escalation-shape leg, 290/300 = 96.7 %, is superseded as a parity row — 2.0 generated tokens per task made its null delta shape-guaranteed rather than measured. Both of those numbers stay exactly as first published. Dated pointer 2026-11-10)* | 1004.8 s measured engine time (mean 3.35 / median 1.06 s/task), 33.42 Wh sampled (402 samples, 111 mWh/task); leg wall not recorded separately for this leg | temp 0.7, first rung 1200 (single rung, 300 requests, 0 ladder steps), serve-default thinking, no request seed — the bare arm's call shape; 0 contour events, 0 answer edits, 0 truncations |

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

## Matched-shape contour parity (item P0 re-run, 2026-11-08 23:36 CET)

Request shape equal to the bare arm's (`PARB_SHAPE=bare PARB_LADDER=1200`: first rung 1200,
serve-default thinking, temperature 0.7, no request seed), same frozen stamp `0.0.2.56`, same
`pub-checkers-v2`, first 300 ids (tasks sha16 `cac604a076e8b00a`), harness `06def0b`, workspace
`pub-arc-easy-contour-matched`. No contour feature was registered for this leg.

| measure | escalation shape (superseded) | **matched shape (this row)** | bare arm (same 300) |
|---|---|---|---|
| strict | 290/300 = 96.7 % | **289/300 = 96.3 %** | 290/300 = 96.7 % |
| paired vs bare | 0W / 0L, p = 1.000 (shape-guaranteed, see above) | **1W / 0L, p = 1.000** | — |
| endpoint requests | 300 (0 ladder) | **300 (0 ladder steps)** | 300 |
| contour events / edits / truncations | 0 / 0 / 0 | **0 / 0 / 0** | n/a |
| generated tokens (total, mean per task) | 600 (2.0 — thinking off) | **25,894 (86.3)** | 27,720 (92.4) |
| prompt tokens | 21,943 | **33,943** | 33,943 |
| engine time (mean / median per task) | 103.2 s (0.34 / 0.30 s) | **1004.8 s (3.35 / 1.06 s)** | 406.2 s (1.35 / 0.98 s) |
| GPU energy (sampled) | 3.70 Wh = 12.3 mWh/task | **33.42 Wh** (402 samples, mean 118.4 W, busy 0.79) = 111 mWh/task | 126.93 Wh over the whole 2376-task leg = 53 mWh/task |

The single discordant id is `arc-easy-0285`, which the bare arm and the escalation-shape arm both
got and this draw missed.

**Verdict: parity, and this time the parity is measured rather than shape-guaranteed.** With the
request shape matched the arm actually emits reasoning-shaped output (86.3 tokens per task against
the superseded leg's 2.0), still fires no contour machinery, still needs exactly one request per
task, and lands within one task of the bare arm on 300 ids (p = 1.000, 1 discordant id).

**Cost caveat, stated rather than smoothed.** Median per-task engine time is at parity with the
bare arm (1.06 s vs 0.98 s), but this leg's *mean* is 3.35 s because of a slow tail (individual
tasks at 17–27 s), and the sampled per-task energy is therefore 111 mWh against the bare leg's
53 mWh/task. The arm made the same 300 requests as the bare arm and zero ladder retries, so the
tail is endpoint state (this P2005 box had been swapping since the GPQA leg), not harness work.
The escalation leg's 12.3 mWh/task is not cheaper harness work either — it is the price of not
reasoning. Quoted cost comparisons on this box are only valid inside one endpoint window.

## Answer bytes for the ARC-Easy arms are now published (2026-11-10 02:40 CET)

The three ARC-Easy rows in `PUB-DIGEST.md` (bare 2261/2376 = 95.2 %, codex 290/300 = 96.7 %, grok
289/300 = 96.3 %) had no stored answer bytes. Shipped now: `arms/arc-easy-basalt-answers.jsonl`
(2376 rows, `3450700e985bce95`), `arms/arc-easy-codex-answers.jsonl` (300, `b126e410e2d95f91`),
`arms/arc-easy-grok-answers.jsonl` (300, `94295e1012c346b0`). Re-score of the shipped copies under
`pub-checkers-v2` (self-test 22/22, zero model calls) reproduces 2261/2376, 290/300 and 289/300
exactly. Scrub masked nothing — shipped bytes byte-identical to the runner output, zero path/IP/key
hits. The cloud arms keep the matched-300 denominator; no percent and no digest row changed.
