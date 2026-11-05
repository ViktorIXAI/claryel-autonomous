# Independent re-score of published hard-v6 arms (issue #6)

Every answer byte under `full-2NN/results-*.jsonl` was re-scored with the
published scorer `harness/parb_check_v6.py` and the published bank
`benchmarks/hard/bank-hard-v6.json`. Stored `content`/`format_ok` were used only
as the thing to compare against, never as input. `check` dispatches by category
(A/B/I `check_json_obj`, C, D-plain, F, G, H, J, K); loop-D goes through
`check_D_loop_v6` on the stored trajectory.

Scope of the plain columns: the **text-scored** cells, i.e. 71 single-shot tasks
minus the 10 category-E tasks (E is scored by running a sandbox battery, see the flag
below). Loop-D cells were not replayable from the stored rows (prose without
`_loop_rows`) and are reported as such rather than guessed.

| stamp | plain as-run /61 | plain independent /61 | loop | stored-score disagreements |
|---|---|---|---|---|
| 0.0.2.16 | 29/61 | **32/61** | not replayed | 3 |
| 0.0.2.17 | 31/61 | **34/61** | not replayed | 3 |
| 0.0.2.18 | 35/61 | **38/61** | not replayed | 3 |
| 0.0.2.19 | 37/61 | **40/61** | not replayed | 3 |
| 0.0.2.20 | 37/61 | **40/61** | not replayed | 3 |
| 0.0.2.21 | 40/61 | **40/61** | not replayed | 0 |
| 0.0.2.22 | 44/61 | **44/61** | not replayed | 0 |
| 0.0.2.23 | 42/61 | **42/61** | not replayed | 0 |
| 0.0.2.25 | 46/61 | **46/61** | not replayed | 0 |
| 0.0.2.28 | 51/61 | **51/61** | not replayed | 0 |

## Disagreements between stored scores and independent scoring

- `0.0.2.16`: 3 cell(s)
  - D-ex6-p0 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - D-ex6-p1 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - D-ex6-p2 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - `0.0.2.16`: not re-scored offline: needs_sandbox x10, trajectory_not_stored x6
- `0.0.2.17`: 3 cell(s)
  - D-ex6-p0 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - D-ex6-p1 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - D-ex6-p2 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - `0.0.2.17`: not re-scored offline: needs_sandbox x10, trajectory_not_stored x6
- `0.0.2.18`: 3 cell(s)
  - D-ex6-p0 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - D-ex6-p1 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - D-ex6-p2 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - `0.0.2.18`: not re-scored offline: needs_sandbox x10, trajectory_not_stored x6
- `0.0.2.19`: 3 cell(s)
  - D-ex6-p0 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - D-ex6-p1 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - D-ex6-p2 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - `0.0.2.19`: not re-scored offline: needs_sandbox x10, trajectory_not_stored x6
- `0.0.2.20`: 3 cell(s)
  - D-ex6-p0 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - D-ex6-p1 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - D-ex6-p2 rep0: as-run 0 -> independent 1 (content 1.0, format True, notes -)
  - `0.0.2.20`: not re-scored offline: needs_sandbox x10, trajectory_not_stored x6
  - `0.0.2.21`: not re-scored offline: needs_sandbox x10, trajectory_not_stored x6
  - `0.0.2.22`: not re-scored offline: needs_sandbox x10, trajectory_not_stored x6
  - `0.0.2.23`: not re-scored offline: needs_sandbox x10, trajectory_not_stored x6
  - `0.0.2.25`: not re-scored offline: needs_sandbox x10, trajectory_not_stored x6
  - `0.0.2.28`: not re-scored offline: needs_sandbox x10, trajectory_not_stored x6

## What this shows

- Stored `content`/`format_ok` reproduce under independent scoring for every
  text-scored cell **except** `D-ex6-p0/p1/p2` in arms before 0.0.2.21: those were
  routed through the loop trajectory scorer, recorded 0, and the published checker
  passes them. Same three cells in the same direction across five arms — plumbing,
  not noise.
- Category E (10 cells per arm) still needs a sandbox re-execution on an idle host
  (`--include-exec`); it is flagged rather than silently skipped, and E was 10/10
  as-run in every arm, so it cannot be hiding an ordering change.
- Loop-D (6 cells per arm) stored prose without `_loop_rows`, so trajectory scoring
  cannot be replayed offline from these files; the runner should store the
  trajectory rows with the row, which is a protocol gap for the next arm.
- Cross-check of totals: these corrected totals match `RESCORE-PLAIN-D.json` and the
  external `CROSSCHECK-217.md` rescore of the 0.0.2.17 arm (44/71).

Counters: {"trajectory_not_stored": 60, "cell_mismatch": 15, "needs_sandbox": 100}

Reproduce: `python3 scripts/rescore_all_arms.py` (add `--include-exec` on an idle
host to also re-execute the category-E sandbox battery).
