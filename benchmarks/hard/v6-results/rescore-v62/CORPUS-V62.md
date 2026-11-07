# Corpus re-score under the v6.2 measurement stack

Bank **v6.1** `sha16 9ec86dfca4a6f85f` + scorer contract **v6.1** (frozen bytes, hash-pinned by
`harness/gate_scorer_contract.py`) versus bank **v6.2** `sha16 3c866ea7daae611c` + scorer contract
**v6.2** (same frozen checkers, reached by delegation). Strict rule in both stacks:
`content == 1.0 and format_ok`. Every cell was re-scored from the same published answer bytes; nothing here is
a model call, a contour run, or an edited artifact.

| measure | value |
|---|---|
| re-scored cells (replayable) | 8476 |
| contract v6.1 vs v6.2 disagreements on the same bank | **0** |
| cells that changed because of the bank correction | 83 wins / 0 losses |
| strict total, stack A (v6.1 bank + v6.1 contract) | 6912 |
| strict total, stack B (v6.2 bank + v6.2 contract) | 6995 |
| empty answer rows (never scored) | 3 |

Cells that cannot be re-scored offline, counted rather than guessed: `empty_answer` x3, `needs_sandbox` x1380, `trajectory_not_stored` x675.

## What changed, task by task

Bank v6.2 moved the gold of `A-ex6-03`, `C-ex6-02` and the prompt of `K-ex6-03`. Any other task changing
would be a scorer-routing bug, not a correction.

| task | cells re-scored | wins | losses |
|---|---|---|---|
| `A-ex6-03` | 138 | 51 | 0 |
| `C-ex6-02` | 138 | 32 | 0 |

Reconciling with `rescore-v62/RESCORE-V62.md`: that run re-scored only the two
defect cells over the 106 arm files published at the time (120 rows each, 44 and 27
wins). This run covers every answer file in the tree — 127 files, 8476 replayable cells —
so the same two defects show more converted cells (51 and 32): the arms published
after it (`pair-244`, `pair-245`, loop arms) are included. Same arithmetic, wider
coverage; neither table replaces the other and both name this stack.


## Per-arm totals over the replayable set

| arm | cells | stack A strict | stack B strict | delta |
|---|---|---|---|---|
| `answers-basalt-j-v61.jsonl` | 7 | 7 | 7 | +0 |
| `answers-basalt.jsonl` | 61 | 40 | 41 | +1 |
| `answers-codex.jsonl` | 61 | 39 | 40 | +1 |
| `answers-contour-v61.jsonl` | 67 | 44 | 44 | +0 |
| `answers-contour.jsonl` | 67 | 34 | 34 | +0 |
| `answers-contour215.jsonl` | 67 | 41 | 41 | +0 |
| `answers-contour217.jsonl` | 67 | 38 | 38 | +0 |
| `answers-grok.jsonl` | 61 | 49 | 50 | +1 |
| `cadence-240/results-q40r6.jsonl` | 61 | 56 | 56 | +0 |
| `cadence-240/results-q40r7.jsonl` | 61 | 55 | 55 | +0 |
| `cadence-240/results-q40r8.jsonl` | 61 | 51 | 51 | +0 |
| `four-arm-v61/answers-basalt-v61.jsonl` | 61 | 46 | 47 | +1 |
| `four-arm-v61/answers-codex-v61.jsonl` | 61 | 40 | 41 | +1 |
| `four-arm-v61/answers-grok-v61.jsonl` | 61 | 44 | 45 | +1 |
| `four-arm-v61/results-c228v61.jsonl` | 61 | 51 | 52 | +1 |
| `full-216/results-c216full.jsonl` | 61 | 32 | 32 | +0 |
| `full-217/results-c217full.jsonl` | 61 | 34 | 34 | +0 |
| `full-218/results-c218full.jsonl` | 61 | 38 | 38 | +0 |
| `full-219/results-c219full.jsonl` | 61 | 40 | 40 | +0 |
| `full-220/results-c220full.jsonl` | 61 | 40 | 40 | +0 |
| `full-221/results-c221full.jsonl` | 61 | 40 | 40 | +0 |
| `full-222/results-c222full.jsonl` | 61 | 44 | 44 | +0 |
| `full-223/results-c223full.jsonl` | 61 | 42 | 42 | +0 |
| `full-225/results-c225full.jsonl` | 61 | 46 | 46 | +0 |
| `full-228/results-c228full.jsonl` | 61 | 51 | 51 | +0 |
| `full-229/results-c229full.jsonl` | 61 | 53 | 53 | +0 |
| `j-probe-218/results-jp.jsonl` | 12 | 0 | 0 | +0 |
| `k-218/results-kb00217.jsonl` | 4 | 1 | 1 | +0 |
| `k-218/results-kb00218.jsonl` | 4 | 2 | 2 | +0 |
| `pair-230/results-c29r0.jsonl` | 61 | 52 | 52 | +0 |
| `pair-230/results-c29r1.jsonl` | 61 | 49 | 49 | +0 |
| `pair-230/results-c29r2.jsonl` | 61 | 50 | 52 | +2 |
| `pair-230/results-c30r0.jsonl` | 61 | 51 | 51 | +0 |
| `pair-230/results-c30r1.jsonl` | 61 | 48 | 48 | +0 |
| `pair-230/results-c30r2.jsonl` | 61 | 48 | 49 | +1 |
| `pair-231/results-d29r0.jsonl` | 61 | 53 | 53 | +0 |
| `pair-231/results-d29r1.jsonl` | 61 | 52 | 52 | +0 |
| `pair-231/results-d29r2.jsonl` | 61 | 50 | 52 | +2 |
| `pair-231/results-d31r0.jsonl` | 61 | 50 | 50 | +0 |
| `pair-231/results-d31r1.jsonl` | 61 | 49 | 49 | +0 |
| `pair-231/results-d31r2.jsonl` | 61 | 48 | 48 | +0 |
| `pair-232/results-e29r0.jsonl` | 61 | 51 | 51 | +0 |
| `pair-232/results-e29r1.jsonl` | 61 | 49 | 49 | +0 |
| `pair-232/results-e29r2.jsonl` | 61 | 53 | 55 | +2 |
| `pair-232/results-e32r0.jsonl` | 61 | 53 | 53 | +0 |
| `pair-232/results-e32r1.jsonl` | 61 | 52 | 52 | +0 |
| `pair-232/results-e32r2.jsonl` | 61 | 52 | 54 | +2 |
| `pair-233/results-f29r0.jsonl` | 61 | 50 | 50 | +0 |
| `pair-233/results-f29r1.jsonl` | 61 | 51 | 51 | +0 |
| `pair-233/results-f29r2.jsonl` | 61 | 54 | 56 | +2 |
| `pair-233/results-f33r0.jsonl` | 61 | 53 | 53 | +0 |
| `pair-233/results-f33r1.jsonl` | 61 | 52 | 52 | +0 |
| `pair-233/results-f33r2.jsonl` | 61 | 54 | 56 | +2 |
| `pair-234/results-g29r0.jsonl` | 61 | 53 | 53 | +0 |
| `pair-234/results-g29r1.jsonl` | 61 | 52 | 52 | +0 |
| `pair-234/results-g29r2.jsonl` | 61 | 55 | 57 | +2 |
| `pair-234/results-g34r0.jsonl` | 61 | 52 | 52 | +0 |
| `pair-234/results-g34r1.jsonl` | 61 | 52 | 52 | +0 |
| `pair-234/results-g34r2.jsonl` | 61 | 53 | 54 | +1 |
| `pair-235/results-h29r0.jsonl` | 61 | 51 | 51 | +0 |
| `pair-235/results-h29r1.jsonl` | 61 | 50 | 50 | +0 |
| `pair-235/results-h29r2.jsonl` | 61 | 53 | 54 | +1 |
| `pair-235/results-h35r0.jsonl` | 61 | 53 | 53 | +0 |
| `pair-235/results-h35r1.jsonl` | 61 | 53 | 53 | +0 |
| `pair-235/results-h35r2.jsonl` | 61 | 54 | 56 | +2 |
| `pair-236/results-i29r0.jsonl` | 61 | 52 | 52 | +0 |
| `pair-236/results-i29r1.jsonl` | 61 | 52 | 52 | +0 |
| `pair-236/results-i29r2.jsonl` | 61 | 55 | 57 | +2 |
| `pair-236/results-i36r0.jsonl` | 61 | 52 | 52 | +0 |
| `pair-236/results-i36r1.jsonl` | 61 | 52 | 52 | +0 |
| `pair-236/results-i36r2.jsonl` | 61 | 52 | 54 | +2 |
| `pair-237/results-j29r0.jsonl` | 61 | 52 | 52 | +0 |
| `pair-237/results-j29r1.jsonl` | 61 | 49 | 49 | +0 |
| `pair-237/results-j29r2.jsonl` | 61 | 53 | 55 | +2 |
| `pair-237/results-j37r0.jsonl` | 61 | 52 | 52 | +0 |
| `pair-237/results-j37r1.jsonl` | 61 | 53 | 53 | +0 |
| `pair-237/results-j37r2.jsonl` | 61 | 56 | 58 | +2 |
| `pair-238/results-k37r0.jsonl` | 61 | 52 | 52 | +0 |
| `pair-238/results-k37r1.jsonl` | 61 | 50 | 50 | +0 |
| `pair-238/results-k37r2.jsonl` | 61 | 55 | 57 | +2 |
| `pair-238/results-k38r0.jsonl` | 61 | 52 | 52 | +0 |
| `pair-238/results-k38r1.jsonl` | 61 | 52 | 52 | +0 |
| `pair-238/results-k38r2.jsonl` | 61 | 56 | 58 | +2 |
| `pair-239/results-l37r0.jsonl` | 61 | 52 | 52 | +0 |
| `pair-239/results-l37r1.jsonl` | 61 | 53 | 53 | +0 |
| `pair-239/results-l37r2.jsonl` | 61 | 54 | 56 | +2 |
| `pair-239/results-l39r0.jsonl` | 61 | 54 | 54 | +0 |
| `pair-239/results-l39r1.jsonl` | 61 | 52 | 52 | +0 |
| `pair-239/results-l39r2.jsonl` | 61 | 56 | 58 | +2 |
| `pair-240/results-m39r0.jsonl` | 61 | 53 | 53 | +0 |
| `pair-240/results-m39r1.jsonl` | 61 | 54 | 54 | +0 |
| `pair-240/results-m39r2.jsonl` | 61 | 56 | 58 | +2 |
| `pair-240/results-m40r0.jsonl` | 61 | 55 | 55 | +0 |
| `pair-240/results-m40r1.jsonl` | 61 | 52 | 52 | +0 |
| `pair-240/results-m40r2.jsonl` | 61 | 56 | 58 | +2 |
| `pair-242/results-n40r0.jsonl` | 61 | 55 | 55 | +0 |
| `pair-242/results-n40r1.jsonl` | 61 | 56 | 56 | +0 |
| `pair-242/results-n40r2.jsonl` | 61 | 54 | 56 | +2 |
| `pair-242/results-n41r0.jsonl` | 61 | 57 | 57 | +0 |
| `pair-242/results-n41r1.jsonl` | 61 | 51 | 51 | +0 |
| `pair-242/results-n41r2.jsonl` | 61 | 57 | 59 | +2 |
| `pair-243/results-o40r0.jsonl` | 61 | 55 | 55 | +0 |
| `pair-243/results-o40r1.jsonl` | 61 | 54 | 54 | +0 |
| `pair-243/results-o40r2.jsonl` | 61 | 55 | 56 | +1 |
| `pair-243/results-o42r0.jsonl` | 61 | 56 | 56 | +0 |
| `pair-243/results-o42r1.jsonl` | 61 | 54 | 54 | +0 |
| `pair-243/results-o42r2.jsonl` | 61 | 56 | 58 | +2 |
| `pair-244/results-p40r0.jsonl` | 61 | 57 | 57 | +0 |
| `pair-244/results-p40r1.jsonl` | 61 | 52 | 52 | +0 |
| `pair-244/results-p40r2.jsonl` | 61 | 56 | 58 | +2 |
| `pair-244/results-p43r0.jsonl` | 61 | 55 | 55 | +0 |
| `pair-244/results-p43r1.jsonl` | 61 | 54 | 54 | +0 |
| `pair-244/results-p43r2.jsonl` | 61 | 55 | 57 | +2 |
| `pair-245/results-q43r0.jsonl` | 61 | 55 | 55 | +0 |
| `pair-245/results-q43r1.jsonl` | 61 | 53 | 53 | +0 |
| `pair-245/results-q43r2.jsonl` | 61 | 56 | 58 | +2 |
| `pair-245/results-q44r0.jsonl` | 61 | 57 | 57 | +0 |
| `pair-245/results-q44r1.jsonl` | 61 | 53 | 53 | +0 |
| `pair-245/results-q44r2.jsonl` | 61 | 55 | 57 | +2 |
| `raw-reps-v61/answers-basalt-v61-reps.jsonl` | 427 | 321 | 328 | +7 |
| `raw-reps-v61/answers-codex-v61-reps.jsonl` | 305 | 202 | 208 | +6 |
| `raw-reps-v61/answers-grok-v61-reps.jsonl` | 305 | 219 | 224 | +5 |
| `reps-229/results-c229r12.jsonl` | 122 | 102 | 104 | +2 |
| `reps-229/results-c229r3.jsonl` | 61 | 55 | 55 | +0 |
| `reps-229/results-c229r45.jsonl` | 122 | 104 | 106 | +2 |
| `results-contour-j-v61.jsonl` | 7 | 5 | 5 | +0 |
| `results-contour-v61c.jsonl` | 61 | 39 | 39 | +0 |

## Reading rules

- `comparable = prompt_changed_in_v62` marks cells whose prompt moved with the bank;
  an answer recorded before v6.2 is not a reply to the v6.2 prompt, so those cells are
  reported but never read as a correction (they need a fresh arm on v6.2).
- Category E is scored by executing a battery in a docker sandbox; pass `--include-exec`
  on an idle host (never while an arm is live) to replay it.
- Loop-D cells are replayable only when the arm stored `_loop_rows`; arms that stored prose
  are reported as `trajectory_not_stored`. That is a protocol gap in those old arms, not
  a scoring result, and the axes/typed codes below come from the stored notes instead.
- Published v6.1 tables keep their v6.1 numbers and their bank hash. A v6.1 number and a
  v6.2 number never sit in one column.

Reproduce: `python3 scripts/rescore_corpus_v62.py` (add `--include-exec` on an idle host).
Stack identity for every element: `versions/MEASUREMENT-STACK.md`.
