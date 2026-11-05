# hard bank v6: contour 0.0.2.20 full arm (rep0, 77 tasks, 2026-11-05 21:38-21:46 Europe/Rome)

Basalt B2003. Shared API with foreign noise2 arm (not killed).

Plain (71): strict **47/71** (66%), content 47/71, mean 0.720
Loop (6): strict **6/6**, mean 1.000

| cat | strict | mean content | n |
|---|---|---|---|
| A | 5/9 | 0.556 | 9 |
| B | 5/7 | 0.714 | 7 |
| C | 4/8 | 0.500 | 8 |
| D | 6/9 | 0.800 | 9 |
| E | 10/10 | 1.000 | 10 |
| F | 3/6 | 0.867 | 6 |
| G | 5/6 | 0.833 | 6 |
| H | 4/5 | 0.800 | 5 |
| I | 5/6 | 0.833 | 6 |
| J | 3/7 | 0.429 | 7 |
| K | 3/4 | 0.938 | 4 |

Top fails: fields_mismatch x6, read_first_missing x3, final_answer_wrong x3, avoid x3, id_set_mismatch x3, value x1, set_mismatch got=['C', 'F'] want=['B', 'C', 'F'] x1, set_mismatch got=['A', 'C', 'D'] want=['C'] x1, set_mismatch got=['A'] want=['A', 'D'] x1, set_mismatch got=['B'] want=['B', 'C'] x1

Format-only: 0

## vs 0.0.2.19

Strict +3/-1.
- `-` C-ex6-08: 1.00->0.00
- `+` D-ex6-l3: 0.70->1.00
- `+` D-ex6-l5: 0.70->1.00
- `+` K-ex6-03: 0.75->1.00

K-ex6-03 recovered via Cyrillic bool canon. K-ex6-01 still SERVICE synonym.
