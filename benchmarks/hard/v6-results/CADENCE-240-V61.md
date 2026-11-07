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

All four legs are now complete and scored. Grok and ChatGPT (codex) arms on the same seeds ran
23:43 CET the same evening and landed 00:11 / 01:32 CET (`cadence-240/run-band240-cloud.sh`,
`band-codex.log`, `band-grok.log`); the four-arm table below and the regenerated
`ARM-BANDS-V61.md` publish them. No bank byte, scorer or contour file was touched by this run.

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

## Cloud closure (2026-11-07): four arms on the same fresh seeds

ChatGPT (codex, `gpt-6.1-sol`, xhigh, prompt via stdin) and Grok (`grok-4.7`, toolsets off,
prompt inline — the S3 transport rule) ran reps 6,7,8 on the same matched seeds, 213 answer
rows each, every row `finish=ok` and non-empty; the raw runner shares the published row format
(byte-identical to the earlier published reps). Transport windows: codex 23:43->00:11 CET
(~28 min), grok 23:43->01:32 CET (~109 min), both parallel to each other and never touching the
P2005 serve — GPU telemetry in that window averages 12.8 W (idle keep-up only), so no local GPU
energy is attributable to the cloud legs; their cost is cloud quota on subscription plans.

Fairness gate (per the raw-arm protocol): the new answer rows contain zero bank/gold/expected
references and zero local paths (grep over the exact shipped rows); every row carries
`bank_sha16 9ec86dfca4a6f85f` (the published bank). Residual disclosure: the codex transport is
stdin-only for the prompt but the CLI runs read-only in the raw workspace, which holds
`bank.json`; the answer text shows no trace of bank reading and its band is flat identical to
the rep0/1/3 seeds (40/41/40 vs 40/41/40), which is what a gold-free run looks like. The grok
transport disables file tools entirely.

Generated by `scripts/cadence240_cloud_v61.py` (regenerates every number below):

common set: 61 single-shot non-E cells; contour reps 6,7,8 = 0.0.2.40 (stamp read from ledger rows); bank sha16 9ec86dfca4a6f85f

| rep | contour | basalt | codex | grok | pair vs codex (W/L, p) | pair vs grok (W/L, p) |
|---|---|---|---|---|---|---|
| rep6 | 56 | 46 | 40 | 42 | 16/0, p=0.00003 | 14/0, p=0.00012 |
| rep7 | 55 | 44 | 41 | 43 | 15/1, p=0.00052 | 13/1, p=0.00183 |
| rep8 | 51 | 45 | 40 | 46 | 14/3, p=0.01273 | 8/3, p=0.22656 |

Pooled over the 183 seed-matched cells: contour 162/183 vs ChatGPT 121/183 (W45 L4, exact
p=8.2e-10) and vs Grok 131/183 (W35 L4, exact p=3.4e-07). The rep8-vs-Grok pair (8/3, p=0.23)
sits inside the disclosed same-stamp noise band (contour rep8 is the low contour draw); the two
pooled arm margins sit far above it, so the arm-level claim holds on fresh seeds as it did at
rep0 — and on these three seeds it is now seed-matched, not rep0-only.

Per-category pooled strict cells over reps 6,7,8 (max 3 per cell):

| cat | contour | basalt | codex | grok | cells |
|---|---|---|---|---|---|
| A | 24 | 23 | 21 | 22 | 27 |
| B | 17 | 20 | 18 | 18 | 21 |
| C | 17 | 17 | 15 | 13 | 24 |
| D | 9 | 9 | 9 | 9 | 9 |
| F | 18 | 7 | 1 | 7 | 18 |
| G | 18 | 15 | 15 | 15 | 18 |
| H | 10 | 1 | 0 | 3 | 15 |
| I | 17 | 18 | 18 | 18 | 18 |
| J | 20 | 21 | 21 | 21 | 21 |
| K | 12 | 4 | 3 | 5 | 12 |

The category structure replicates the rep0 four-arm finding: F/H/K carry the contour margin over
every raw arm — contour 40/45 strict cells on F+H+K vs bare basalt 12/45, ChatGPT 4/45 and Grok
15/45. ChatGPT collapses hardest on contract-sensitive cells (F 1/18, H 0/15), Grok holds B/I/J
at parity with the contour, and A/C/D are near-ties. E stays excluded symmetrically (raw
batteries not re-executed for the new seeds; every published E row of every arm scored 10/10),
loop-D is N/A to all raw arms by protocol.

## Cost and energy for the two local legs

| leg | answers | model calls | ptok / ctok | answer/wall seconds | serve energy (window) |
|---|---|---|---|---|---|
| contour 0.0.2.40 reps 6+7+8 | 231 | 389 | 71 507 / 26 288 | 585 s wall (342+130+113; first leg includes serve warm-up) | 11.61 + 5.41 + 4.61 = 21.6 Wh |
| bare basalt reps 6+7+8 | 213 (loop D N/A) | 213 | not reported by the raw transport | 1 722 s answering, 1 716 s leg window (28.6 min, gpu busy 0.97) | 66.05 Wh |

Per `scripts/gpu_energy.py` over the sampler windows (`q40r*`, `b678` markers): the contoured arm
answers 8 % more tasks in a third of the wall time on a third of the GPU energy. Raw arms on
subscriptions (the closed cloud legs) do not consume local GPU at all — their cost is cloud quota
on subscription plans, recorded in the run logs.

## Line status

The cadence measures **arms**, not a stamp: no contour behavior changed here. `0.0.2.40` remains
the adopted line; the bank-ceiling decision from pair-242 (no pair-243 without owner bank
clarification) is unchanged.

## Reproduce

    python3 scripts/raw_rep_score_v6.py --raw benchmarks/hard/v6-results/raw-reps-v61/answers-basalt-v61-reps.jsonl \
        --rep 6 --contour benchmarks/hard/v6-results/cadence-240/ledger-q40r6.jsonl --contour-rep 6   # and reps 7, 8
    python3 scripts/rep_variance_v6.py benchmarks/hard/v6-results/cadence-240/ledger-q40r{6,7,8}.jsonl
    python3 scripts/cadence240_cloud_v61.py            # four-arm closure tables
    python3 scripts/gpu_energy.py <gpu-power.csv> --start <rid>-start.epoch --end <rid>-end.epoch

Artifacts: `cadence-240/` (ledgers, results, logs, run records, per-rep plans, both runner
scripts, cloud leg logs), raw answer rows in
`raw-reps-v61/answers-{basalt,codex,grok}-v61-reps.jsonl` (basalt reps 1,2,3,4,6,7,8;
codex/grok reps 1,3,6,7,8).
