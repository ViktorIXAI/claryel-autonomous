# hard bank v6: contour 0.0.2.17 full arm (rep0, 77 tasks, 2026-11-05 20:50-21:09 Europe/Rome)

Endpoint: local basalt serve (qwen3.8-flash-next-iq3_s-basalt, 262k ctx), box label B2003,
bank seeds = bank gseed (same plan as 0.0.2.16 full-216). One rep. Not a paired A/B against 2.16:
the serve stack is seeded but not bit-reproducible, so per-category deltas below are re-draws unless marked as pairs.

Plain tasks (71, single-shot): strict **41/71** (58%), content 41/71, mean content 0.679
Loop tasks (6, protocol loop-v2): strict **4/6**, mean content 0.900

| cat | strict | mean content | n |
|---|---|---|---|
| A | 4/9 | 0.444 | 9 |
| B | 5/7 | 0.714 | 7 |
| C | 5/8 | 0.625 | 8 |
| D | 4/9 | 0.733 | 9 |
| E | 10/10 | 1.000 | 10 |
| F | 2/6 | 0.833 | 6 |
| G | 5/6 | 0.900 | 6 |
| H | 1/5 | 0.300 | 5 |
| I | 5/6 | 0.833 | 6 |
| J | 3/7 | 0.446 | 7 |
| K | 1/4 | 0.750 | 4 |

Top failure notes on non-strict: fields_mismatch x7, value x4, avoid x4, read_first_missing x3, final_answer_wrong x3, id_set_mismatch x3, banned_attempted x2, ungrounded_claims x2, set_mismatch got=['C', 'F'] want=['B', 'C', 'F'] x1, set_mismatch got=['A', 'C', 'D'] want=['C'] x1, set_mismatch got=['D'] want=['A', 'D'] x1, claimed_actions x1

**Cells lost to FORMAT only** (content 1.00, format_ok False): 0 (none)

## Verdict vs 0.0.2.16

P0 of 0.0.2.17 confirmed: the keyword-free format repair now runs with CHECKER_INJECT OFF.
- Format-only strict losses: **6 -> 0** (B-ex6-00/01/03 and J-ex6-00/04/05 all strict now).
- Plain strict: 39/71 -> 41/71 (+2 net). Loop unchanged 4/6.
- Strict improved 6 cells, regressed 4 cells vs the 2.16 redraw (A-ex6-05, C-ex6-01, F-ex6-01, H-ex6-02) — seed variance on content, not format.
- Remaining dominant content misses: A fields_mismatch (arithmetic), H ungrounded_claims, K value tokens (true vs required yes), J id_set_mismatch, F avoid, D-p read_first.

## Next stamp candidates (one change each)

- **0.0.2.18**: K boolean flag canonicalize (true/false -> yes/no) + unbundle keyword-free K grounding from CHECKER_INJECT (issue #15 targets scorer-keyword injection, not boolean synonym repair).
- Later: H safety / length trim unbundle; A scaffold-harm probe.
