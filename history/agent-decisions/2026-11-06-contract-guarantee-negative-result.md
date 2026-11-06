# Contour 0.0.2.30 (contract guarantee): a negative result, and the analysis bug that produced it

Date: 2026-11-06. Stamp: 0.0.2.30. Bank: hard v6.1 (`9ec86dfca4a6f85f`).

## What was believed and why it was wrong

The first cell-stability analysis (`scripts/unstable_cells_v61.py`) reported that 12 of the 14 seed-unstable
cells died on a parse collapse (`no_json` / `no_list` / `no_answer_line`) with no repair event. The claim was
built on a key mistake: contour ledgers do not carry the answer text and do not use a `contour_events`
column. The answer bytes live in the sibling `results-*.jsonl`, and the event column is `events`. The script
re-scored an empty string, so the scorer said "no artifact" — for every cell, in every seed.

Corrected: **zero** unstable cells show a parse collapse. The real losing-seed reasons are content-side:
different option/id sets (`set_mismatch`, `id_set_mismatch`), wrong order (`order_partial`), wrong or missing
fields (`fields_mismatch`, `missing:`), omitted required components (`unknown_missing`, `requires_missing`,
`avoid`).

## What was built on that belief, and what the measurement says

0.0.2.30 guarantees the artifact shape: one shape-only re-ask, then deterministic salvage of the model's own
text. Paired arms against 0.0.2.29 on three identical seeds (`pair-230/`, `PAIR-230-V61.md`):

- mean 60.3 → 59.0; paired sign tests 0W/1L, 3W/4L, 2W/4L
- unstable cells 8 → 12 (worse)
- the gate fired on 9 of 231 rows, so it is live code, not a no-op
- `A-ex6-07` went 3/3 → 0/3: the shape check demanded a JSON object for a category whose contract is
  `FIELD: value` lines, judged a passing answer "collapsed", replaced it with a fresh sample, and the fresh
  sample had the wrong fields

## Decision

1. 0.0.2.30 is **not** adopted as an improvement. Code and tests stay published; the stamp is recorded as a
   measured negative result. Any retry is a new stamp with the required shape read from the task's own prompt
   (the 0.0.2.29 method) and a hard rule that an answer the frozen scorer can already parse is never replaced.
2. The headline contour number stays 0.0.2.29: six seeds on the common 61-cell set, 53/52/50/55/53/51, mean
   52.3, +12.0 cells vs ChatGPT (CI +4.3..+19.8), +8.3 vs Grok (CI +1.8..+15.0), +5.9 vs bare basalt
   (CI −0.5..+12.5, unresolved).
3. Analysis tools are fail-closed on their own inputs: `unstable_cells_v61.py` now aborts if a sibling
   results file is missing or more than 5% of joined answers are blank. A reason string computed from an
   empty answer is not a measurement, it is a fabrication, and it cost a whole contour stamp.

## Process lessons kept as rules

- Ledger rows score; results rows carry bytes. Any script that re-scores must join ledger → results on
  (task, rep) and assert the join produced text.
- A category heuristic for "required artifact shape" is not a contract. The contract lives in the task text.
- Negative results are published with the same artifacts as positive ones (ledgers, answer rows, logs, run
  records, energy windows), otherwise the repo quietly keeps only the wins.
