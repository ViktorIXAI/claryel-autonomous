# Contour 0.0.2.31 (plurality vote on C/J): negative result, and the resolution floor of this benchmark

Date: 2026-11-06. Bank hard v6.1 (`9ec86dfca4a6f85f`). Control stamp 0.0.2.29, candidate 0.0.2.31,
three identical seeds each, arms alternating per seed (`pair-231/`).

## Measurement

- control totals 63 / 62 / 60 (mean 61.7), candidate 60 / 59 / 58 (mean 59.0); sign tests 1W/4L, 2W/5L
- unstable cells 9 (control) vs 10 (candidate)
- mechanism fired on every C/J row: 32 unanimous, 4 plurality-equals-original, 1 no-majority, **8 votes
  taken** (7 C, 1 J). It replaced correct answers in `C-ex6-00`, `C-ex6-01`, `C-ex6-03`, `J-ex6-04`
- cost: 458 vs 363 model calls; 13.96 Wh vs 5.54 Wh per 77-task arm (**2.5× energy** for a worse score)

## Why it failed, as a rule

Self-consistency assumes independent noise around a correct answer. On these tasks the model is **biased**:
its samples agree on the wrong option set more often than the right one, so the plurality is the wrong
answer and voting amplifies it. Choosing a mechanism requires knowing which of variance or bias dominates;
the stability map plus a probe of agreement rates answers that cheaply, before writing any gate.

## The number that should have been measured first

The control stamp ran twice over the same seeds in two different pairs (pair-230 control, pair-231 control):
12 of 231 cells (5.2%) change strict pass/fail; mean 60.3 vs 61.7. So a three-seed contour-vs-contour pair
resolves roughly ±1.5–2 cells. Both negative stamps (−1.3, −2.7) sit at that floor. Consequence adopted as
a reporting rule: a contour-vs-contour delta under ~2 cells at three seeds is published as **unresolvable**,
never as a win; either raise the seed count or require a bigger predicted effect.

Arm-level claims stay far above the floor: contour vs ChatGPT +12.0 cells (CI +4.3..+19.8), vs Grok +8.3
(CI +1.8..+15.0) — 4–6× the floor, from six contour seeds against three cloud seeds.

## Next

0.0.2.32 attacks `order_partial` in category J with a deterministic re-sort driven only by the (id, number)
table and the direction phrase already present in the task prompt — zero content invention, zero extra model
calls, so the energy penalty of the vote does not reappear. Measured as a paired arm against 0.0.2.29 on the
same three seeds before any claim is made.
