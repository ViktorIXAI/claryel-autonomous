# Task set attribution and licenses

* GSM8K — Cobbe et al. 2021, `openai/grade-school-math`, MIT licence; test split, 1319 items,
  final-answer numbers taken from the `answer` field (`####` line).
* ARC — Clark et al. 2018, `allenai/ai2_arc`, CC BY-SA 4.0; ARC-Easy test 2376 and
  ARC-Challenge test 1172 items, answer letters from the `answerKey` field.
* HumanEval — Chen et al. 2021, `openai/human-eval`, MIT licence; 164 items. Scored by the execution
  checker `scripts/pub_bench_exec.py` (contract `pytest-v1`, superseded by `pytest-v2`); the checker
  runs the upstream test block per task in a resource-limited child process.
* IFEval — Zhou et al. 2023, `google-research/google-research/instruction_following_eval`,
  Apache-2.0 (repo `LICENSE` vendored as `vendor/LICENSE.instruction_following_eval`, NOTICE beside
  the code); 541 prompts with 834 instruction checks, pinned to upstream commit
  `e6890f85757dd84e27ca6df2dd30651dafad28e0`. The upstream checker is used as shipped and is not
  edited; the upstream reference-response file is vendored only to self-test the checker.
* SimpleBench — Schmidgall et al. 2024, MIT licence, but the released repository contains a
  10-question demo only; no full public set is fetchable, so the set is closed as unpinnable and no
  SimpleBench number is published anywhere in this repository.

Normalisation is in `scripts/pub_bench_prep.py`; the pinned bytes are identified by the sha16 in
`MANIFEST.json` and repeated in every percent row.
