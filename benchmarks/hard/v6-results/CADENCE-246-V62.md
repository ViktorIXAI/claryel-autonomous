# Cadence-246 — four-arm re-run on bank v6.2 (contour 0.0.2.45 vs bare basalt vs ChatGPT-codex vs Grok)

Owner rule: every 5 measured contour stamps re-run the joint four arms on the **current**
bank. Stamps measured since the last cadence (rep0 four-arm era / cadence-240 at 2.40):
**2.41, 2.42, 2.43, 2.44, 2.45 = 5 — due**. This is the first four-arm run on the corrected
bank **v6.2**, on FRESH matched seeds: reps 16, 17, 18 for every arm, gseeds re-derived from
`(task, rep)` (`scripts/plan_reps.py`, seed protocol sp1), so contour cell (task, rep k) and
raw cell (task, rep k) are seed-matched. Pre-registered before any row was written:
`REVIEW-INBOX.md` 2026-11-07 06:20 CET.

## Measurement stack (names every number below)

| element | value |
|---|---|
| bank | `benchmarks/hard/bank-hard-v6.2.json` sha16 `3c866ea7daae611c` (run-workspace copy `d1e8d11df5840dcc`; 77 tasks field-identical, asserted by `scripts/cadence_score_v62.py`) |
| scorer contract | **v6.2** `c8c0c7dd114dfc32` (modules parb_check_v6 `89437d8cfe1fc6c8`, parb_loop `f5f5b78ab46a0f0c`, e_sandbox `424c04126e9b6c1e`) |
| strict rule | `content == 1.0 and format_ok` |
| seed protocol | sp1 (per-(task,rep) gseed) |
| contour leg stamp | `0.0.2.45` (release 2.45; contour behavior axis reports **2.44**; adopted feature matrix = 2.43, pinned by `gate_v49`; no v244/frozen-band events fired — verified in the published ledgers) |
| harness | built from commit `fdd03f2` (the run records predate release 0.0.2.46, which fixed `harness_git_sha` stamping; the cadence legs ran that tree) |
| endpoint | P2005 Basalt serve, contour arms serial, endpoint idle for each; cloud legs run on subscription CLIs and never touch the serve |
| scoring script | `scripts/cadence_score_v62.py` (all tables below are its output, regenerated — not retyped) |

Common set: **61 single-shot non-E cells** per rep (bank minus 6 loop-D minus 10 E).
E is excluded symmetrically (raw E batteries are not re-executed for new seeds; every
published seed of every arm scores 10/10 on E, so E carries no discriminating cells).
Loop-D is N/A for single-shot brains by protocol (agent-loop scorer needs real trajectories).

## Pre-registered rule (c): contour ledger scores re-derived from stored bytes

Re-scored every contour result answer with the same contract v6.2 and compared cell by
cell against the stored ledger: **0 mismatches across all 3 legs** (165 replayable cells;
30 E cells = docker battery not offline-replayable; 18 loop cells stored no `_loop_rows` —
the published protocol gap of these arms, ledger scores kept as-run). No scorer-routing
bug. Zero blank result answers.

## Per-rep and pooled pairs (61 seed-matched cells per rep)

| arm | rep | contour plain /71 | contour loop /6 | contour/61 vs arm/61 | W / L | exact p |
|---|---|---|---|---|---|---|
| basalt | rep16 | 65 | 6/6 | 55 vs 47 | 13 / 5 | 0.09625 |
| basalt | rep17 | 67 | 5/6 | 57 vs 46 | 14 / 3 | 0.01273 |
| basalt | rep18 | 64 | 6/6 | 54 vs 45 | 13 / 4 | 0.04904 |
| **basalt pooled** | r16-18 |  |  | **166 vs 138** | **40 / 12** | **0.000128** |
| codex (gpt-6.1-sol, xhigh) | rep16 | 65 | 6/6 | 55 vs 42 | 16 / 3 | 0.00443 |
| codex | rep17 | 67 | 5/6 | 57 vs 43 | 16 / 2 | 0.00131 |
| codex | rep18 | 64 | 6/6 | 54 vs 43 | 15 / 4 | 0.01921 |
| **codex pooled** | r16-18 |  |  | **166 vs 128** | **47 / 9** | **2.6e-07** |
| grok (grok-4.7) | rep16 | 65 | 6/6 | 55 vs 46 | 12 / 3 | 0.03516 |
| grok | rep17 | 67 | 5/6 | 57 vs 46 | 13 / 2 | 0.00739 |
| grok | rep18 | 64 | 6/6 | 54 vs 45 | 12 / 3 | 0.03516 |
| **grok pooled** | r16-18 |  |  | **166 vs 137** | **37 / 8** | **0.0000154** |

rep16 basalt (p=0.096) is a single-rep draw; the pooled arm margins sit 5-8× above the
~1.4-cell same-seed noise floor measured on this line, so all three pooled verdicts are
arm-level claims and quotable. The contour arm beats **every** external brain on the
corrected bank; the ordering codex < basalt < contour replicates the v6.1 head-to-head
structure on a bank where the two published unreachable golds were fixed.

## Per-category pooled strict (61 cells x 3 reps = 183)

| cat | n | contour | basalt | codex | grok |
|---|---|---|---|---|---|
| A | 27 | 25 | 25 | 24 | 26 |
| B | 21 | 17 | **21** | 18 | 18 |
| C | 24 | 19 | 16 | 16 | 13 |
| D (single-shot) | 9 | 9 | 9 | 9 | 9 |
| F | 18 | **18** | 7 | 1 | 9 |
| G | 18 | 18 | 15 | 15 | 15 |
| H | 15 | **13** | 0 | 0 | 2 |
| I | 18 | 17 | 18 | 18 | 18 |
| J | 21 | 21 | 21 | 21 | 21 |
| K | 12 | 9 | 6 | 6 | 6 |

Same class structure as the v6.1 `CATEGORY-SPLIT-V61.md` finding: the contract-sensitive
categories (F, H, C, K) carry the whole margin; A/C/D/I/J are at parity. **B is the one
category the contour loses (17 vs 21)** — see the defect finding below.

## Corrected-gold fairness check (owner rule: a better-worded bank must lift the RAW arms)

The three v6.1 defect golds, strict per arm over 3 reps:

| cell | contour | basalt | codex | grok |
|---|---|---|---|---|
| A-ex6-03 | 2/3 | 3/3 | 3/3 | 3/3 |
| C-ex6-02 | 0/3 | 1/3 | 1/3 | 0/3 |
| K-ex6-03 | 0/3 | 3/3 | 3/3 | 3/3 |

**The clarification worked: every raw arm now passes A-ex6-03 and K-ex6-03 at 3/3** (under
v6.1 golds those cells were 0/120 for every stamp and every brain — published in
`rescore-v62/RESCORE-V62.md`). C-ex6-02 stays genuinely unstable for everyone. No v6.1
number shares a column with a v6.2 number anywhere.

## B-ex6-04 — root cause established on a previously frozen-negative cell: bank defect, stop contour work

This cell has sat on the frozen-negative list since the v6.1 map; the cadence finally names
WHY, and it is the bank, not the model. The prompt states `start_date: "ГГГГ-ММ-ДД"` but
**never states the year** ("подписан 3
марта, старт работ 1 апреля"); the v6.2 gold demands `2026-04-01`. A model can only hit it
by guessing the current year: basalt guessed 2026 three times (3/3 pass), codex correctly
refused the unanswerable year and answered `null` (0/3 strict-fail), the contour draws
guessed 2023/2024 (0/3). A strict verdict on this cell is a luck-of-reading test, not a
capability measurement — it is the published "B carries the defect" pattern re-appearing on
a new id. Ruling: **B-ex6-04 goes to the bank-defect queue for the next bank version
(prompt must state the year); no contour stamp will be aimed at it** (a pair on a defective
cell is UNMEASURED by construction). It explains 3 of the 4 contour B-category losses.

## Loop pool (contour arm only, informational)

17/18 loop draws strict (6/6, 5/6, 6/6) — consistent with the adopted 2.43 line (pair-244:
16/18, pair-245: 17/18). Loop cells of this cadence are the published protocol gap: no
`_loop_rows` stored, so they are ledger-scored only.

## Wall and energy (rule (d))

| leg | wall | GPU energy (P2005 board, `gpu-power-246.csv`) | notes |
|---|---|---|---|
| contour q45r16 | 246 s | 5.98 Wh | busy 0.51 |
| contour q45r17 | 226 s | 5.16 Wh | busy 0.42 |
| contour q45r18 | 228 s | 5.11 Wh | busy 0.44 |
| **contour total (231 calls)** | **700 s** | **16.25 Wh** | 0.070 Wh/call |
| basalt raw (213 calls) | 1821 s | 69.36 Wh | busy 0.95; 0.326 Wh/call — every raw call re-prefills the full prompt without K/V reuse |
| codex leg | 6801 s | n/a (cloud) | parallel with grok |
| grok leg | 6801 s | n/a (cloud) | E-block calls ran 400-670 s each |

The contour arm used **4.3x less GPU energy than the raw arm of the same model** while
scoring +28 strict cells — the contour's repairs and reuses avoid re-prefilling failed
answers; stated as measured, single window per leg.

## Instability map delta (feeds the next pair queue; census in UNSTABLE-CELLS addendum)

Deterministic contour strict-fails on v6.2 (all 3 seeds, live targets):
`B-ex6-04` (bank defect — closed for contour), `C-ex6-02` (real: `set_mismatch`, the model
omits candidate B and the 2.13 C best-of-2 trigger `missed_options` does NOT fire on this
code family — the strongest live target on the v6.2 map), `K-ex6-03` (real: extraction draws
collapse to a meta header line, content class, no contour event — selection/variance class,
not repairable without inventing values). Single-draw flips (noise band): A-ex6-00 r16,
A-ex6-03 r17, B-ex6-05 r18, C-ex6-03 r18, C-ex6-08 r16, H-ex6-01 r16, H-ex6-03 r18,
I-ex6-01 r18.

## Verdict

1. The contour line (adopted 0.0.2.43 matrix, run at tooling release 0.0.2.45) holds on the
   corrected bank: 166/183 vs basalt 138 (p=1.3e-4), codex 128 (p=2.6e-7), grok 137
   (p=1.5e-5). The margin over the same local model without contour **replicates on the
   clarified bank**, and the raw arms rose exactly where the bank was fixed — the owner's
   fairness check for bank edits passes.
2. The long-frozen-negative cell B-ex6-04 has an established root cause (year never stated
   in the prompt, gold demands 2026) — published as a bank defect, contour work on that cell
   stays closed, fix belongs to the next bank version with re-computed gold and changelog.
3. Strongest next live target: C-ex6-02 (3/3 live control fails, no existing trigger).
4. Rule (c): zero scorer-routing disagreements; the v6.2 contract identity chain
   (bank sha16 -> contract sha16 -> run-record stack) held end to end; the run-record
   `harness_git_sha` gap found here was fixed the same day as tooling release 0.0.2.46.

Reproduce: `python3 scripts/cadence_score_v62.py --ws <ws> --raw-ws <raw-ws> --reps 16,17,18
--prefix q45 --arms basalt codex grok --gpu-csv cadence-246/../gpu... ` — artifacts
(dirty-free copies): `results/ledger/run-record/log/plan` for the three contour arms, the
three raw answer files (213 rows each, model + cli + bank_sha16 per row), band logs, launch
scripts, energy windows, and the machine-readable per-cell table
`cadence-cells-v62.csv` (arm, rep, task, cat, strict, bank_sha16, contract).
