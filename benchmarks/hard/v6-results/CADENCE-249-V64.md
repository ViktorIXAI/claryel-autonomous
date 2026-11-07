# Cadence-249 — four-arm re-run on bank v6.4 (contour 0.0.2.49 vs bare basalt vs ChatGPT-codex vs Grok)

Owner rule: every 5 measured contour stamps re-run the joint four arms on the **current**
bank; and when the bank has been re-worded, the raw arms are the standing fairness check.
The bank moved **twice** since cadence-246 (v6.2 -> v6.3 provisional -> v6.4 WORKING), so
this cadence is due on the bank-re-word clause, not the stamp count. FRESH matched seeds:
reps 25, 26, 27 for every arm, gseeds re-derived from `(task, rep)` (seed protocol sp1), so
contour cell (task, rep k) and raw cell (task, rep k) are seed-matched. Pre-registered
before any row was written: `REVIEW-INBOX.md` 2026-11-07 14:26 CET.

## Measurement stack (names every number below)

| element | value |
|---|---|
| bank | `benchmarks/hard/bank-hard-v6.4.json` sha16 `85a0cd0dd6fa1fab` (run-workspace copy `7788cc288922b9a4`; 77 tasks field-identical, asserted by `scripts/cadence_score_v62.py`; raw-arms subset copy byte-identical) |
| bank version label | `v6.4`, resolved **from the workspace marker** (`bank-version.json`, bytes-validated against `benchmarks/hard/BANK-VERSIONS.json`) — first cadence whose run records carry a live non-empty `stack.bank_version` with source `marker` (the queued label gap closed by release 0.0.2.49, proven live) |
| scorer contract | **v6.2** `c8c0c7dd114dfc32` (modules parb_check_v6 `89437d8cfe1fc6c8`, parb_loop `f5f5b78ab46a0f0c`, e_sandbox `424c04126e9b6c1e`) |
| strict rule | `content == 1.0 and format_ok` |
| seed protocol | sp1 (per-(task,rep) gseed) |
| contour leg stamp | `0.0.2.49` (release 2.49 **tooling only**; contour behavior axis reports **2.48** = the adopted line — `gate_v63` proves zero features register at 2.49, so this leg is the adopted contour) |
| harness | built from commit `926afac912bfe253db0fe3ecfc52846502eb2af7`; run records stamp `harness_git_sha` live (release 2.46 wiring) |
| endpoint | P2005 Basalt serve (`qwen3.8-flash-next-iq3_s-basalt`), contour + bare-basalt legs serial on the idle serve; cloud legs run on subscription CLIs and never touch the serve |
| scoring script | `scripts/cadence_score_v62.py --bank-pub bank-hard-v6.4.json` (all tables below are its output, regenerated — not retyped) |

Common set: **61 single-shot non-E cells** per rep (bank minus 6 loop-D minus 10 E),
identical denominators for every arm. E is excluded symmetrically (raw E batteries are not
re-executed for new seeds; every published seed of every arm scores 10/10 on E). Loop-D is
N/A for single-shot brains by protocol.

## Pre-registered rule (c): contour ledger scores re-derived from stored bytes

Re-scored every contour result answer with the same contract v6.2 and compared cell by
cell against the stored ledger: **0 mismatches across all 3 legs** (183 replayable cells;
30 E cells = docker battery not offline-replayable). Zero blank result answers.

**Finding against rule (c): the `_loop_rows` protocol gap is NOT closed.** The pre-
registered rule required loop-D legs to store `_loop_rows` ("the published protocol gap of
the 2.45-era arms, closed for new runs"), but zero rows in `results-q49r2{5,6,7}.jsonl`
carry `_loop_rows` — the same 18 loop cells (6 tasks x 3 reps) stay ledger-scores-only and
not offline-replayable. The gap is in the loop runner's row storage, not this cadence's
wiring; it is queued as a tooling fix, and every loop score quoted below is an as-run
ledger claim, disclosed as such.

## Pre-registered rule (a): bank fairness — raw arms must not regress on the corrected bank

Pooled strict on the common 183 cells, cadence-246 (bank v6.2, reps 16-18) -> cadence-249
(bank v6.4, reps 25-27): **basalt 138 -> 144, codex 128 -> 131, grok 137 -> 134**. No arm
regressed beyond the published same-seed noise floor (5.2% of cells ~ 9.5/183).

The only bank byte moved v6.2->v6.4 is task `B-ex6-04` (field-identity guard asserted).
Its cells, strict over 3 reps:

| arm | v6.2 (reps 16-18) | v6.4 (reps 25-27) |
|---|---|---|
| basalt | 3/3 (was year-guessing) | 3/3 (holds) |
| codex | 0/3 (refused: year not stated) | **3/3** |
| grok | 0/3 (refused) | **3/3** |
| contour | 0/3 | **3/3** |

That is exactly the frozen fairness-lift signature (refusers flip, the guesser holds) from
the 12:56-CET probe pre-registration, now reproduced on fresh independent seeds. The
residual pool movement sits only in byte-identical categories (basalt F +4/H +3, grok
A -2/F -4, codex nets zero after B-ex6-04) — F is the known raw-chat variance class
(codex F is 0/18 here). **Verdict on rule (a): bank v6.4 is FAIR; no bank-defect hunt
triggered.**

## Pre-registered rule (b): contour margin vs each raw arm (61 seed-matched cells per rep)

| arm | rep | contour plain /71 | loop /6 | contour/61 vs arm/61 | W / L | exact p |
|---|---|---|---|---|---|---|
| basalt | rep25 | 67 | 5/6 | 57 vs 49 | 8 / 0 | 0.00781 |
| basalt | rep26 | 68 | 6/6 | 58 vs 46 | 14 / 2 | 0.00418 |
| basalt | rep27 | 65 | 6/6 | 55 vs 49 | 9 / 3 | 0.14600 |
| **basalt pooled** | r25,26,27 |  |  | **170 vs 144** | **31 / 5** | **0.000013** |
| codex (gpt-6.1-sol, xhigh) | rep25 | 67 | 5/6 | 57 vs 45 | 14 / 2 | 0.00418 |
| codex | rep26 | 68 | 6/6 | 58 vs 43 | 16 / 1 | 0.00027 |
| codex | rep27 | 65 | 6/6 | 55 vs 43 | 13 / 1 | 0.00183 |
| **codex pooled** | r25,26,27 |  |  | **170 vs 131** | **43 / 4** | **2.78e-09** |
| grok (grok-4.7) | rep25 | 67 | 5/6 | 57 vs 45 | 13 / 1 | 0.00183 |
| grok | rep26 | 68 | 6/6 | 58 vs 45 | 14 / 1 | 0.00098 |
| grok | rep27 | 65 | 6/6 | 55 vs 44 | 12 / 1 | 0.00342 |
| **grok pooled** | r25,26,27 |  |  | **170 vs 134** | **39 / 3** | **5.63e-09** |

Contour common total 166 -> 170 vs cadence-246. Attribution, honestly split: +3 B-ex6-04
(bank fix, contour claims nothing there), +3 K (adopted 0.0.2.48 fields-gate: K 9/12 ->
**12/12**, raw arms 6/12 each), offset by contour's own seed variance in the known unstable
classes (F 18 -> 16, H 13 -> 10, C +1, I +1). Every pooled sign test is far above the
noise floor; the contour-vs-cloud ranking is unchanged from cadence-246
(contour > basalt > grok > codex on the common set).

## per-category pooled strict (3 reps, bank v6.4 `85a0cd0d`, contract v6.2 `c8c0c7dd`)

| cat | n | contour | basalt | codex | grok |
|---|---|---|---|---|---|
| A | 27 | 25 | 24 | 24 | 24 |
| B | 21 | 21 | 21 | 21 | 21 |
| C | 24 | 20 | 16 | 16 | 13 |
| D | 9 | 9 | 9 | 9 | 9 |
| F | 18 | 16 | 11 | 0 | 5 |
| G | 18 | 18 | 15 | 15 | 15 |
| H | 15 | 10 | 3 | 1 | 2 |
| I | 18 | 18 | 18 | 18 | 18 |
| J | 21 | 21 | 21 | 21 | 21 |
| K | 12 | 12 | 6 | 6 | 6 |

## corrected-gold fairness check (v6.2-era defect cells, strict over 3 reps)

| A-ex6-03 | contour 1/3 | basalt 3/3 | codex 3/3 | grok 3/3 |
| C-ex6-02 | contour 0/3 | basalt 1/3 | codex 1/3 | grok 0/3 |
| K-ex6-03 | contour 3/3 | basalt 3/3 | codex 3/3 | grok 3/3 |

A-ex6-03: contour underperforms the raw arms on 2 of 3 fresh seeds (the closed arithmetic
near-miss class — watching, no new contour work claimed). K-ex6-03: the adopted 2.48 win
holds on brand-new seeds (contour 3/3; it was 0/9 on the published 2.47 line).

## Pre-registered rule (e): stall guard, wall and energy

Leg medians per task: 1.26 / 1.27 / 1.30 s (pair-247 baseline ~2.3 s — no stall, no spin
degradation; max single task 19.1 s). Sampler `gpu-power-249.csv` (2 s ssh nvidia-smi).

| leg | wall | GPU energy | GPU busy |
|---|---|---|---|
| contour q49r25 | 259 s | 6.34 Wh | 0.48 |
| contour q49r26 | 277 s | 6.70 Wh | 0.55 |
| contour q49r27 | 263 s | 6.59 Wh | 0.47 |
| **contour total** | **799 s** | **19.63 Wh** | — |
| bare basalt r25-27 | 1730 s | same serve, outside contour windows | — |
| codex+grok cloud | 6544 s parallel wall | cloud CLIs, no local GPU energy | — |

## Tooling note found while publishing

`scripts/cadence_score_v62.py` hardcoded the CSV arm label `contour-2.45`; the cadence-249
per-cell CSV initially mislabeled its legs. Fixed in the same commit: the label is now
derived from the legs' own run records (`stack.contour_stamp` -> `contour-2.49`). Scores
are unaffected (label column only); the published CSV carries the corrected label. cadence-246
reproduction keeps its historical label because its run records stamp `contour_stamp 2.45`.

## Artifacts (all sanitized: `<LAN_IP>`, `<LOCAL_PATH>`)

- contour legs: `results-q49r{25,26,27}.jsonl`, `ledger-q49r{25,26,27}.jsonl`,
  `plan-rep2{5,6,7}.json`, `q49r{25,26,27}.log`, `run-record-q49r{25,26,27}.json`
  (stack: bank v6.4/`85a0cd0d`/ws `7788cc28`, contract v6.2/`c8c0c7dd`, sp1, stamp 2.49/behavior 2.48, harness `926afac`)
- raw legs: `answers-{basalt,codex,grok}.jsonl` (213 rows/arm, model+CLI+bank_sha16 per row,
  re-scoreable by outsiders), `band-{basalt,codex,grok}.log`
- orchestration: `band249.log`, `run-cad249.sh`, `run-cad249-cloud.sh`, `gpu-sampler249.sh`,
  `cadence-249-energy.csv`
- cells: `cadence-cells-v62.csv` (780 data rows: 231 contour + 3x183 arm-common; every row
  names bank sha16 + contract)
