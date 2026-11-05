# hard bank v6: contour 0.0.2.19 full arm (rep0, 77 tasks, 2026-11-05 21:30-21:36 Europe/Rome)

Endpoint: basalt qwen3.8-flash-next-iq3_s-basalt, box B2003. plan-full.json restored (77) after jprobe overwrite.

Plain (71): strict **47/71** (66%), content 47/71, mean 0.731
Loop (6): strict **4/6**, mean 0.900

| cat | strict | mean content | n |
|---|---|---|---|
| A | 5/9 | 0.556 | 9 |
| B | 5/7 | 0.714 | 7 |
| C | 5/8 | 0.625 | 8 |
| D | 4/9 | 0.733 | 9 |
| E | 10/10 | 1.000 | 10 |
| F | 3/6 | 0.867 | 6 |
| G | 5/6 | 0.833 | 6 |
| H | 4/5 | 0.800 | 5 |
| I | 5/6 | 0.833 | 6 |
| J | 3/7 | 0.429 | 7 |
| K | 2/4 | 0.875 | 4 |

Top failure notes: fields_mismatch x6, read_first_missing x3, final_answer_wrong x3, avoid x3, id_set_mismatch x3, value x2, banned_attempted x2, set_mismatch got=['C', 'F'] want=['B', 'C', 'F'] x1, set_mismatch got=['A', 'C', 'D'] want=['C'] x1, set_mismatch got=['D'] want=['A', 'D'] x1

Format-only: 0 (none)

## vs 0.0.2.18

Strict +4 / -2.
- `+` D-ex6-l2: 0.70->1.00
- `-` D-ex6-l5: 1.00->0.70
- `+` F-ex6-01: 0.80->1.00
- `+` H-ex6-01: 0.00->1.00
- `+` H-ex6-03: 0.00->1.00
- `-` K-ex6-03: 1.00->0.75

H JSON contract: clears fabricated claims/actions_done (keyword-free).
