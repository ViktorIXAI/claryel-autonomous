# Cadence-240 — four-arm re-run on fresh matched seeds (contour 0.0.2.40 vs bare basalt)

Owner rule: every 5 contour stamps re-run the joint four arms on the **current** bank. The last
joint run was the rep0 four-arm in the 0.0.2.28/2.29 era — overdue by 12 measured stamps
(2.30..2.41). This cadence run uses FRESH matched seeds: reps 6, 7, 8 for every arm, gseeds
re-derived from `sha256(task|rep)` (`scripts/plan_reps.py`), so contour cell (task, rep k) and
raw cell (task, rep k) are seed-matched. Runner: `cadence-240/run-band240.sh`.

Bank identity (verified this session): published `benchmarks/hard/bank-hard-v6.json` sha16
`9ec86dfca4a6f85f`; run workspace bank sha16 `f4553aab304f60d7`. Frozen scorer
`harness/parb_check_v6.py`. Contour stamp of this leg `0.0.2.40` (behavior 2.40 — the adopted
line; run records in `cadence-240/`). Endpoint: P2005, legs serial, no shared-serve contention;
cloud legs run on subscription CLIs and never touch the serve.

This file publishes the two completed legs. Grok and ChatGPT (codex) arms on the same seeds
started 23:40 CET the same evening and are **not scored here** — the four-arm table for reps
6,7,8 regenerates in `ARM-BANDS-V61.md` when those arms land. No bank byte, scorer or contour
file was touched by this run.

## Common set and per-rep result (61 single-shot non-E cells, seed-matched)

E is excluded symmetrically (the raw E batteries were not re-executed for the new seeds; every
published seed of every arm scored 10/10 on E, so E carries no discriminating cells). Loop-D is
N/A for the raw arm by protocol.

| rep | contour plain strict /71 | contour loop /6 | 61-cell pair | contour wins / losses | exact p |
|---|---|---|---|---|---|
| rep6 | 66 | 6/6 | 56/61 vs 46/61 | 11 / 1 | 0.00635 |
| rep7 | 65 | 4/6 | 55/61 vs 44/61 | 13 / 2 | 0.00739 |
| rep8 | 61 | 6/6 | 51/61 vs 45/61 | 9 / 3 | 0.14600 |
| **pooled (183 cells)** | **192/213** | 16/18 | **162/183 vs 135/183** | **33 / 6** | **0.000014** |

Same-stamp noise floor for reference (`scripts/rep_variance_v6.py` over these three ledgers):
plain strict [66, 65, 61], spread 5; rep-to-rep sign tests p = 1.00 / 0.0625 / 0.219. The pooled
arm margin (+9.0 cells/61 per rep on average) sits ~3x above that floor and the pooled
33W/6L is unambiguous — an arm-level claim, quotable. rep8 alone is a low contour draw inside
the same-stamp band; published per-rep, not smoothed.

## Where the win is (pooled per category, strict cells over 3 reps)

| cat | contour | basalt | n |
|---|---|---|---|
| A | 24 | 23 | 27 |
| B | 17 | 20 | 21 |
| C | 17 | 17 | 24 |
| D (single-shot) | 9 | 9 | 9 |
| F | 18 | 7 | 18 |
| G | 18 | 15 | 18 |
| H | 10 | 1 | 15 |
| I | 17 | 18 | 18 |
| J | 20 | 21 | 21 |
| K | 12 | 4 | 12 |

Same structure as the published F/H/K finding (`CATEGORY-SPLIT-V61.md`): contract-sensitive
categories carry the whole margin; A/C/D are ties; B/I/J are at parity or slightly against the
contour (B carries the published defect cell below).

## Discordant cells (all 39)

Contour pass / basalt fail (33): `A-ex6-05`(r6); `C-ex6-03`(r7); `F-ex6-01`(r6,r7,r8);
`F-ex6-02`(r6,r7,r8); `F-ex6-03`(r7,r8); `F-ex6-04`(r7); `F-ex6-05`(r6,r8); `G-ex6-03`(r6,r7,r8);
`H-ex6-00`(r7,r8); `H-ex6-01`(r6); `H-ex6-02`(r6,r7,r8); `H-ex6-03`(r7); `H-ex6-04`(r6,r7);
`K-ex6-00`(r6,r7,r8); `K-ex6-01`(r6,r7,r8); `K-ex6-03`(r6,r7).

Basalt pass / contour fail (6): `B-ex6-04`(r6,r7) — the published bank defect cell
(`bank-defect-b04.md`), not contour-attributable; `B-ex6-05`(r8), `C-ex6-00`(r8), `I-ex6-01`(r7),
`J-ex6-03`(r8) — all four are published seed-unstable/lottery cells
(`UNSTABLE-CELLS-V61.md`; `C-ex6-00` and `J-ex6-03` are group-1 order/set lotteries whose
closed/no-grammar status is recorded in the bank ceiling notes). Zero losses on the 26
contract-sensitive F/H/K cells.

## Cost and energy for the two legs

| leg | answers | model calls | ptok / ctok | answer/wall seconds | serve energy (window) |
|---|---|---|---|---|---|
| contour 0.0.2.40 reps 6+7+8 | 231 | 389 | 71 507 / 26 288 | 585 s wall (342+130+113; first leg includes serve warm-up) | 11.61 + 5.41 + 4.61 = 21.6 Wh |
| bare basalt reps 6+7+8 | 213 (loop D N/A) | 213 | not reported by the raw transport | 1 722 s answering, 1 716 s leg window (28.6 min, gpu busy 0.97) | 66.05 Wh |

Per `scripts/gpu_energy.py` over the sampler windows (`q40r*`, `b678` markers): the contoured arm
answers 8 % more tasks in a third of the wall time on a third of the GPU energy. Raw arms on
subscriptions (the pending legs) do not consume local GPU at all — their cost is cloud quota,
recorded in the run logs.

## Line status

The cadence measures **arms**, not a stamp: no contour behavior changed here. `0.0.2.40` remains
the adopted line; the bank-ceiling decision from pair-242 (no pair-243 without owner bank
clarification) is unchanged.

## Reproduce

    python3 scripts/raw_rep_score_v6.py --raw benchmarks/hard/v6-results/raw-reps-v61/answers-basalt-v61-reps.jsonl \
        --rep 6 --contour benchmarks/hard/v6-results/cadence-240/ledger-q40r6.jsonl --contour-rep 6   # and reps 7, 8
    python3 scripts/rep_variance_v6.py benchmarks/hard/v6-results/cadence-240/ledger-q40r{6,7,8}.jsonl
    python3 scripts/gpu_energy.py <gpu-power.csv> --start <rid>-start.epoch --end <rid>-end.epoch

Artifacts: `cadence-240/` (ledgers, results, logs, run records, per-rep plans, runner script),
raw answer rows in `raw-reps-v61/answers-basalt-v61-reps.jsonl` (reps 1,2,3,4,6,7,8).
