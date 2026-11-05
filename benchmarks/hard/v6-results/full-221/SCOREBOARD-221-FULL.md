# hard bank v6: contour 0.0.2.21 full arm (rep0, 77 tasks, 2026-11-05 21:47-22:03 Europe/Rome)

Basalt B2003. D-plain score routing fix.

Plain (71): strict **50/71** (70%), content 50/71, mean 0.757
Loop (6): strict **5/6**, mean 0.950

| cat | strict | mean content | n |
|---|---|---|---|
| A | 4/9 | 0.444 | 9 |
| B | 5/7 | 0.714 | 7 |
| C | 5/8 | 0.625 | 8 |
| D | 8/9 | 0.967 | 9 |
| E | 10/10 | 1.000 | 10 |
| F | 2/6 | 0.833 | 6 |
| G | 5/6 | 0.833 | 6 |
| H | 5/5 | 1.000 | 5 |
| I | 5/6 | 0.833 | 6 |
| J | 3/7 | 0.429 | 7 |
| K | 3/4 | 0.938 | 4 |

Top fails: fields_mismatch x7, avoid x4, id_set_mismatch x3, value x1, set_mismatch got=['C', 'F'] want=['B', 'C', 'F'] x1, set_mismatch got=['A', 'C', 'D'] want=['C'] x1, set_mismatch got=['D'] want=['A', 'D'] x1, banned_attempted x1, value_mismatch x1, next x1, conflict_flag_missing x1, order_partial x1

Format-only: 0

## vs 0.0.2.20

Strict +5/-3.
- `-` A-ex6-05: 1.00->0.00
- `+` C-ex6-08: 0.00->1.00
- `-` D-ex6-l3: 1.00->0.70
- `+` D-ex6-p0: 0.40->1.00
- `+` D-ex6-p1: 0.40->1.00
- `+` D-ex6-p2: 0.40->1.00
- `-` F-ex6-01: 1.00->0.80
- `+` H-ex6-02: 0.00->1.00

D-p0/p1/p2 all strict 1.00 (were 0.40 under loop scorer).
