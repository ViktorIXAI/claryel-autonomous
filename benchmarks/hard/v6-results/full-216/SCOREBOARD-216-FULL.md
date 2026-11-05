# hard bank v6: contour 0.0.2.16 full arm (rep0, 77 tasks, 2026-11-05 20:33-20:46 CET)

Endpoint: local basalt serve (`qwen3.8-flash-next-iq3_s-basalt`, 262k ctx), box label B2003, bank `f52acbd15b3271e7`,
seeds = bank `gseed` (identical to the published 0.0.2.14 contour arm), one rep. Not a paired A/B against 2.14:
the serve stack is seeded but not bit-reproducible, so per-category deltas below are re-draws unless marked as pairs.

Plain tasks (71, single-shot): strict **39/71** (55%), content 45/71, mean content 0.710
Loop tasks (6, protocol loop-v2): strict **4/6**, mean content 0.900

| cat | strict | mean content | n |
|---|---|---|---|
| A | 5/9 | 0.556 | 9 |
| B | 2/7 | 0.714 | 7 |
| C | 6/8 | 0.750 | 8 |
| D | 4/9 | 0.733 | 9 |
| E | 10/10 | 1.000 | 10 |
| F | 3/6 | 0.867 | 6 |
| G | 5/6 | 0.833 | 6 |
| H | 2/5 | 0.400 | 5 |
| I | 5/6 | 0.833 | 6 |
| J | 0/7 | 0.429 | 7 |
| K | 1/4 | 0.750 | 4 |

Top failure notes on plain tasks: sandbox x10, fields_mismatch x6, items_not_bare_ids x6, object_wrapped_in_list x5, value x4, read_first_missing x3, final_answer_wrong x3, avoid x3, id_set_mismatch x3, ungrounded_claims x2

**Cells lost to FORMAT only** (content 1.00, format_ok False): 6 -> B-ex6-00, B-ex6-01, B-ex6-03, J-ex6-00, J-ex6-04, J-ex6-05

Event mix: gate x106, fix x31, ladder x6

## Finding: the 0.0.2.15 format repair never runs in the official configuration

`POST_NORMALIZE = CHECKER_INJECT and contour_at_least(2,0)`, and `CHECKER_INJECT` is OFF by default since 0.0.2.14
(issue #15: no scorer-keyword injection in the official score). The deterministic repairs added in 0.0.2.15
(B/D one-element-list unwrap, J decorated items -> bare ids) live INSIDE `post_normalize_answer`, so the caller's
CHECKER_INJECT gate kills them too. Evidence in this arm: 7/7 J rows still carry `items_not_bare_ids` and 5 rows
`object_wrapped_in_list` while their content is already 1.00; the ledger shows no `contour:v20_j_id_norm` event at all.
Contract test `gate_v36_format_repair_test.py` passed because it calls the function directly and bypasses the pipeline gate.
Repair costs zero model tokens, so this is a pure measurement-validity bug. Six strict cells
in this arm are format-only losses (content already 1.00, format_ok False): B-ex6-00/01/03 and
J-ex6-00/04/05. Fix goes in as contour 0.0.2.17 (deterministic format repair independent of
keyword injection).
