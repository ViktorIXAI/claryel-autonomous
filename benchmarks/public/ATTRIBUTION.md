# Task set attribution and licenses

* GSM8K — Cobbe et al. 2021, `openai/grade-school-math`, MIT licence; test split, 1319 items,
  final-answer numbers taken from the `answer` field (`####` line).
* ARC — Clark et al. 2018, `allenai/ai2_arc`, CC BY-SA 4.0; ARC-Easy test 2376 and
  ARC-Challenge test 1172 items, answer letters from the `answerKey` field.
* HumanEval — Chen et al. 2021, `openai/human-eval`, MIT licence; 164 items. The execution
  checker is not vendored yet, so these tasks are unscored and excluded from percent rows.

Normalisation is in `scripts/pub_bench_prep.py`; the pinned bytes are identified by the sha16 in
`MANIFEST.json` and repeated in every percent row.
