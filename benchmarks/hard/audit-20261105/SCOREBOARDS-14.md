# Issue #14 scoreboards (frozen answers, hash-pinned inputs)

Pins: bank 32953591ba2a6c51, parb_check 1c032ef022607d7b, parb_loop f5f5b78ab46a0f0c, artifacts 91ccc27a3248b9b5. Contour re-scored from archived answers + D step traces; raw arms re-scored from published answers.


> **WATERMARK (owner retraction 2026-11-05):** these totals are historical outputs of the flawed v5 checkers — **INVALID FOR RANKING** (issue #15 adjudication contract, point 6i). No comparative-superiority claim may be drawn from them.

## 1) Strict contract (77 rows; contour=loop accounting for D, raw arms=strict_plain)

| arm | perfect/77 | pct |
|---|---|---|
| contour | 70/77 | 90.9% |
| basalt | 45/77 | 58.4% |
| grok | 54/77 | 70.1% |
| codex | 56/77 | 72.7% |

Raw arms under strict_loop (empty-step scorer, lower bound): basalt 43/77, grok 52/77, codex 56/77

## 2) Content-only (content==1.0, format ignored)

| arm | content/77 | pct |
|---|---|---|
| contour | 74/77 | 96.1% |
| basalt | 45/77 | 58.4% |
| grok | 58/77 | 75.3% |
| codex | 56/77 | 72.7% |

Format-only failures (content==1, fmt==0): contour 4, basalt 0, grok 4, codex 0

## 3) Sensitivity (byte-identical prompt groups; 48 unique groups)

| arm | cluster score | equal-category score |
|---|---|---|
| contour | 85.4% (41/48 groups full-pass: 41) | 87.9% |
| basalt | 52.1% (25/48 groups full-pass: 25) | 46.3% |
| grok | 70.2% (31/48 groups full-pass: 31) | 66.7% |
| codex | 70.8% (34/48 groups full-pass: 34) | 65.9% |

Duplicate groups: D x3; D x3; D x2; E x5; E x2; E x3; E x4; E x3; E x5; E x4; E x4; H x3

## Pairwise discordant task ids (strict; contour pass/raw fail + contour fail/raw pass)
- contour vs basalt: contour-only 31 ['A-ex-03-0', 'B-ex-00-0', 'B-ex-01-0', 'B-ex-02-0', 'B-ex-03-0', 'D-ex-00-0', 'D-ex-00-1', 'D-ex-00-2', 'D-ex-01-1', 'D-ex-01-2', 'D-ex-02-1', 'D-ex-02-2', 'E-ex-01-3', 'E-ex-03-4', 'E-ex-04-0', 'E-ex-05-4', 'F-ex-01-0', 'F-ex-02-0', 'G-ex-00-0', 'G-ex-01-0', 'G-ex-02-0', 'G-ex-03-0', 'G-ex-04-0', 'G-ex-05-0', 'H-ex-00-0', 'H-ex-01-0', 'H-ex-02-0', 'H-ex-03-0', 'J-ex-00-0', 'J-ex-01-0', 'J-ex-03-0'] | raw-only 6 ['C-ex-00-0', 'C-ex-01-0', 'C-ex-02-0', 'C-ex-03-0', 'C-ex-04-0', 'C-ex-05-0']
- contour vs grok: contour-only 22 ['D-ex-00-1', 'D-ex-00-2', 'D-ex-01-0', 'D-ex-01-1', 'D-ex-01-2', 'D-ex-02-1', 'D-ex-02-2', 'E-ex-02-1', 'E-ex-02-4', 'E-ex-04-2', 'E-ex-05-0', 'F-ex-01-0', 'F-ex-02-0', 'G-ex-00-0', 'G-ex-01-0', 'G-ex-02-0', 'G-ex-03-0', 'G-ex-04-0', 'G-ex-05-0', 'H-ex-00-0', 'H-ex-03-0', 'K-ex-03-0'] | raw-only 6 ['C-ex-00-0', 'C-ex-01-0', 'C-ex-02-0', 'C-ex-03-0', 'C-ex-04-0', 'C-ex-05-0']
- contour vs codex: contour-only 20 ['D-ex-00-0', 'D-ex-00-1', 'D-ex-00-2', 'D-ex-01-0', 'D-ex-01-1', 'D-ex-01-2', 'D-ex-02-0', 'D-ex-02-1', 'D-ex-02-2', 'F-ex-01-0', 'F-ex-02-0', 'G-ex-00-0', 'G-ex-01-0', 'G-ex-02-0', 'G-ex-03-0', 'G-ex-04-0', 'G-ex-05-0', 'H-ex-00-0', 'H-ex-01-0', 'H-ex-03-0'] | raw-only 6 ['C-ex-00-0', 'C-ex-01-0', 'C-ex-02-0', 'C-ex-03-0', 'C-ex-04-0', 'C-ex-05-0']

## 77-row audit verdicts (Hermes): AMBIGUOUS=3, REPEATED_TEMPLATE=41, VALID=33
Machine-readable: audit-77-rows-v14.jsonl (this directory).
