# hard bank v6: contour 0.0.2.18 full arm (rep0, 77 tasks, 2026-11-05 21:14-21:28 Europe/Rome)

Endpoint: local basalt serve (qwen3.8-flash-next-iq3_s-basalt, 262k ctx), box B2003.
Same plan/seeds family as full-217. One rep. Shared basalt with parallel 0.0.2.15 arm (not killed).

Plain tasks (71): strict **45/71** (63%), content 45/71, mean content 0.708
Loop tasks (6): strict **4/6**, mean content 0.900

| cat | strict | mean content | n |
|---|---|---|---|
| A | 5/9 | 0.556 | 9 |
| B | 5/7 | 0.714 | 7 |
| C | 5/8 | 0.625 | 8 |
| D | 4/9 | 0.767 | 9 |
| E | 10/10 | 1.000 | 10 |
| F | 2/6 | 0.833 | 6 |
| G | 5/6 | 0.833 | 6 |
| H | 2/5 | 0.400 | 5 |
| I | 5/6 | 0.833 | 6 |
| J | 3/7 | 0.429 | 7 |
| K | 3/4 | 0.938 | 4 |

Top failure notes: fields_mismatch x6, avoid x4, final_answer_wrong x3, id_set_mismatch x3, read_first_missing x2, banned_attempted x2, ungrounded_claims x2, value x1, set_mismatch got=['C', 'F'] want=['B', 'C', 'F'] x1, set_mismatch got=['A', 'C', 'D'] want=['C'] x1, set_mismatch got=['D'] want=['A', 'D'] x1, claimed_actions x1

**Format-only losses**: 0 (none)

## vs 0.0.2.17

Strict improved 4, regressed 0.
K boolean canon: K-ex6-00/03 recovered (true->yes); K-ex6-01 still SERVICE value miss.
- `+` A-ex6-05: 0.00 -> 1.00
- `+` H-ex6-04: 0.50 -> 1.00
- `+` K-ex6-00: 0.75 -> 1.00
- `+` K-ex6-03: 0.75 -> 1.00

## Remaining holes (next stamps)

- A arithmetic fields_mismatch
- H ungrounded_claims / claimed_actions (H_SAFETY still behind CHECKER_INJECT)
- J id_set_mismatch / order_partial
- F avoid
- D-p read_first_missing / final_answer_wrong; D-l banned_attempted
- H-trim + K_NEGATION still inject-gated
