# Cadence-255 — four-arm re-run on bank v6.6 (contour 0.0.2.55 vs bare basalt vs ChatGPT-codex vs Grok)

Owner rule: every 5 measured contour stamps re-run the joint four arms on the **current**
bank, and the raw arms are the standing fairness check whenever the bank has been
re-worded. Since cadence-249 the measured line advanced 2.51 -> 2.52 -> 2.53 ->
2.54 (frozen UNMEASURED) -> 2.55 — five measured-era stamps — and the working bank moved
v6.4 -> v6.5 (provisional) -> v6.6 (working), so this cadence is due on **both** clauses.
FRESH matched seeds: reps 52, 53, 54 for every arm (contour cells via sp1, raw arms paired
by (task,rep) index). Pre-registered before any row was written: `REVIEW-INBOX.md`
2026-11-08 ~03:0x CET, with the frozen stage plan and the fairness clause.

## Measurement stack (names every number below)

| element | value |
|---|---|
| bank | `benchmarks/hard/bank-hard-v6.6.json` sha16 `5c86252b2ef2f422` (run-workspace copy `590503cf1701a6ce`; 77 tasks field-identical, asserted by `scripts/cadence_score_v62.py`; raw-arms copy byte-identical to the workspace copy) |
| bank version label | `v6.6`, resolved from the workspace marker (`bank-version.json`), stamped live into all three run records |
| scorer contract | **v6.2** `c8c0c7dd114dfc32` (modules parb_check_v6 `89437d8cfe1fc6c8`, parb_loop `f5f5b78ab46a0f0c`, e_sandbox `424c04126e9b6c1e`) |
| strict rule | `content == 1.0 and format_ok` |
| seed protocol | sp1 (per-(task,rep) gseed; `seed-protocol.md` in this directory, audit 231/231) |
| contour leg stamp | `0.0.2.55` — release and contour behavior axis both `2.55` = the **adopted line** (adopted after pair-252) |
| harness | built from commit `5f7c167d63b0dd325d2f39e13518dfa1e3ca46e4`; run records stamp `harness_git_sha` live |
| endpoint | P2005 Basalt serve (`qwen3.8-flash-next-iq3_s-basalt`); contour + bare-basalt legs serial on the idle serve; cloud legs on subscription CLIs, never touch the serve |
| scoring script | `scripts/cadence_score_v62.py --bank-pub bank-hard-v6.6.json` (every table below is its output, regenerated — not retyped) |

Common set: **61 single-shot non-E cells** per rep (bank minus 6 loop-D minus 10 E),
identical denominators for every arm. E is excluded symmetrically (raw E batteries are not
re-executed for new seeds; every published seed of every contour arm scores 10/10 on E).
Loop-D is N/A for single-shot brains by protocol.

## Pre-registered rule (c): contour ledger scores re-derived from stored bytes

Re-scored every contour result answer with the same contract v6.2 and compared cell by
cell against the stored ledger: **0 mismatches across all 3 legs** (201 replayable cells:
183 single-shot + 18 loop-D replayed through the pinned adapter mapping; 30 E cells =
docker battery, not offline-replayable). Zero blank result answers. The loop column below
is therefore reproducible from stored bytes.

## Pre-registered rule (a): bank fairness — raw arms must not regress on the corrected bank

Pooled strict on the common 183 cells: cadence-246 (v6.2, reps 16-18) basalt 138 / codex
128 / grok 137 -> cadence-249 (v6.4, reps 25-27) basalt 144 / codex 131 / grok 134 ->
**cadence-255 (v6.6, reps 52-54) basalt 146 / codex 135 / grok 134**. No raw arm
regressed; movement is inside the published same-seed noise floor (5.2% of cells ~ 9.5/183).

The only bank task moved v6.4 -> v6.6 is **H-ex6-01** (v6.5 named the missing audit-log
artifact in the scenario; v6.6 stated the hidden claims contract in the field spec; every
other task byte-identical, gold untouched). Its cells, strict over the 3 fresh reps,
against the v6.5 fairness probe (matched reps 28-30, contour OFF, published in
`v6-results/bank-probe-65/fair-rows.md` and the v6.6 probe):

| arm | v6.5 probe (reps 28-30) | v6.6 cadence (reps 52-54) |
|---|---|---|
| basalt | 0/3 (every zero `ungrounded_claims`) | **3/3** |
| codex | 0/3 (same note family) | **3/3** |
| grok | 0/3 (same note family) | **3/3** |
| contour | 3/3 (via `v219_h_clear_claims` scaffolding) | 3/3 (on v6.6 probe reps the model's own answer already satisfies the contract; the repair fired 0/3 there) |

All three brains that previously failed identically on the contradicting spec now pass on
fresh seeds — the frozen fairness-lift signature (this time all three were the spec-lured
failers, no "guesser" row exists on this cell). **Verdict on rule (a): bank v6.6 is FAIR;
no bank-defect hunt triggered.**

## Pre-registered rule (b): contour margin vs each raw arm (61 seed-matched cells per rep)

| arm | rep | contour plain /71 | loop /6 | contour/61 vs arm/61 | W / L | exact p |
|---|---|---|---|---|---|---|
| basalt | rep52 | 68 | 6/6 | 58 vs 48 | 13 / 3 | 0.02127 |
| basalt | rep53 | 69 | 5/6 | 59 vs 50 | 11 / 2 | 0.02246 |
| basalt | rep54 | 70 | 6/6 | 60 vs 48 | 13 / 1 | 0.00183 |
| **basalt pooled** | r52,53,54 |  |  | **177 vs 146** | **37 / 6** | **2.0e-06** |
| codex (gpt-6.1-sol, xhigh) | rep52 | 68 | 6/6 | 58 vs 44 | 16 / 2 | 0.00131 |
| codex | rep53 | 69 | 5/6 | 59 vs 46 | 14 / 1 | 0.00098 |
| codex | rep54 | 70 | 6/6 | 60 vs 45 | 16 / 1 | 0.00027 |
| **codex pooled** | r52,53,54 |  |  | **177 vs 135** | **46 / 4** | **<1e-06** |
| grok (grok-4.7) | rep52 | 68 | 6/6 | 58 vs 44 | 16 / 2 | 0.00131 |
| grok | rep53 | 69 | 5/6 | 59 vs 46 | 15 / 2 | 0.00235 |
| grok | rep54 | 70 | 6/6 | 60 vs 44 | 17 / 1 | 0.00014 |
| **grok pooled** | r52,53,54 |  |  | **177 vs 134** | **48 / 5** | **<1e-06** |

Contour common total 170 -> **177** vs cadence-249 — the margin **widened** against all
three arms (249 pooled: 31/5, 43/4, 39/3). Attribution, honestly split: +3 H-ex6-01 and
the C gain at C-ex6-02 0/3 -> 3/3 sit partly with the bank fix and the adopted 2.53
C-options gate (contour claims nothing for the bank bytes), K holds 12/12 for the second
cadence in a row on fresh seeds (adopted 2.48 gate), while contour's own seed variance
shows as single-cell draws (below). The raw ranking swapped codex (135) above grok (134);
both inside noise of each other. Every pooled sign test is far above the noise floor.

## per-category pooled strict (3 reps, bank v6.6 `5c86252b`, contract v6.2 `c8c0c7dd`)

| cat | n | contour | basalt | codex | grok | contour vs cadence-249 |
|---|---|---|---|---|---|---|
| A | 27 | 26 | 26 | 24 | 24 | 25 -> 26 |
| B | 21 | 19 | 21 | 21 | 21 | 21 -> 19 |
| C | 24 | 24 | 17 | 15 | 13 | 20 -> 24 |
| D | 9 | 9 | 9 | 9 | 9 | 9 -> 9 |
| F | 18 | 17 | 9 | 2 | 3 | 16 -> 17 |
| G | 18 | 18 | 15 | 15 | 15 | 18 -> 18 |
| H | 15 | 14 | 4 | 4 | 4 | 10 -> 14 |
| I | 18 | 17 | 18 | 18 | 18 | 18 -> 17 |
| J | 21 | 21 | 21 | 21 | 21 | 21 -> 21 |
| K | 12 | 12 | 6 | 6 | 6 | 12 -> 12 |

Contour strict-fail cells across all three legs (7 cells of 231 incl. loop, all single
draws — no cell failed twice except none): `A-ex6-00` r53, `B-ex6-03` r52, `B-ex6-06` r54,
`D-ex6-l0` r53 (loop), `F-ex6-00` r53, `H-ex6-04` r52, `I-ex6-02` r52. The B regressions
(2 cells) are single-rep draws against raw arms passing 3/3 — candidates for the rebuilt
2.55-line stability map, no contour claim either way. Loop pool strict 17/18 (6/5/6).

## corrected-gold fairness check (v6.2-era defect cells, strict over 3 reps)

| A-ex6-03 | contour **3/3** | basalt 3/3 | codex 3/3 | grok 3/3 |
| C-ex6-02 | contour **3/3** | basalt 1/3 | codex 0/3 | grok 0/3 |
| K-ex6-03 | contour 3/3 | basalt 3/3 | codex 3/3 | grok 3/3 |

A-ex6-03 recovered from 1/3 (cadence-249) to 3/3 — the adopted 2.52 percent-chain gate
holds on brand-new seeds. C-ex6-02 recovered from 0/3 to 3/3 — the adopted 2.53 options
gate holds. K-ex6-03 holds 3/3 at its second cadence after the 2.48 adoption (pair-247
reps 22-24, cadence-249 25-27, cadence-255 52-54).

## Pre-registered rule (e): stall guard, wall and energy

Leg medians per task: 1.28 / 1.27 / 1.27 s (pair baseline ~2.3 s — no stall, no spin
degradation; max single task 12.7 s). Sampler `gpu-power-c255.csv` (2 Hz ssh nvidia-smi,
1616 samples) covered all contour and basalt windows and was stopped after them.

| leg | wall | GPU energy | GPU busy |
|---|---|---|---|
| contour q55r52 | 264 s | 6.42 Wh | 0.52 |
| contour q55r53 | 264 s | 6.53 Wh | 0.52 |
| contour q55r54 | 247 s | 5.83 Wh | 0.47 |
| **contour total** | **775 s** | **18.78 Wh** | — |
| bare basalt r52-54 | 1701 s | same serve, outside contour windows | — |
| codex+grok cloud (parallel) | 1905 s wall | cloud CLIs, no local GPU energy | — |
| grok retry leg (see below) | 7547 s | cloud CLI, no local GPU energy | — |

Contour per-task energy 18.78/231 = **0.0813 Wh/task**, at (slightly below) the published
0.085-0.089 Wh/task band; raw basalt stays ~5x higher per task (COST-V61.md).

## Transport incident (disclosed, does not touch the scores)

The Grok leg's first pass died mid-transport: 186/213 calls returned rc=1 with empty
answers at a uniform ~1.2 s (expired xai-oauth access token that self-refreshed near the
G/J block). Per the raw-runner's (task,rep) done-set semantics the dead rows were purged
(backed up as `answers-grok.jsonl.bad-rc1.bak`, kept OUT of this publication) and the leg
was relaunched under its own systemd unit at 04:15 CET; the retry redid 186 rows and kept
the 27 healthy ones. Final published `answers-grok.jsonl`: 213 rows, 0 empty answers,
0 `err` fields, median 14.0 s — consistent with cadence-249's grok windows. Tooling
hardening shipped in the same window (commit `38b20f9`): raw rows now carry transport
`err` text, and `raw_v6.py` aborts after 5 consecutive empty answers so a dead token
cannot burn a leg window again.

## Verdicts

1. **Rule (a):** bank v6.6 is FAIR — the fixed H-ex6-01 lifted all three raw arms 0/3 ->
   3/3 on fresh seeds, no arm regressed on the common pool.
2. **Rule (b):** the contour margin vs every external brain is confirmed and **widened**
   on the v6.6 line: pooled 177 vs 146/135/134, sign tests 37/6, 46/4, 48/5, all p<2e-6.
3. **Rule (c):** 0 ledger-vs-bytes mismatches; all 201 replayable contour cells reproduce.
4. The adopted line 0.0.2.55 (and its gates 2.48 K / 2.52 A / 2.53 C / 2.55 D-plain) holds
   on brand-new seeds; the two B single-cell draws go to the stability map.
5. Next step per pre-registration: rebuild the UNSTABLE-CELLS map on the 2.55 line before
   any new contour hypothesis; next four-arm cadence due after 5 further measured stamps.

**[DONE 2026-11-08 07:17 CET, item 5]:** the current-line map is
[`UNSTABLE-CELLS-V66-255.md`](UNSTABLE-CELLS-V66-255.md) (+ `.csv`), regenerated by
`scripts/unstable_cells_v62.py` from these six-line arms plus pair-252's 2.55 legs — 65/77 cells
strict-pass every arm, zero stable fails, 12 seed-unstable; the 2.53-era map is marked superseded.
The live-target rule is now a script (`scripts/live_target_check.py`). Details in
`REVIEW-INBOX.md` (entry "eval-system work 2026-11-08 07:17 CET").
