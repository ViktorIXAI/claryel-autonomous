# hard bank v6: contour 0.0.2.22 full arm (rep0, 77 tasks, 2026-11-05 22:05-22:12 Europe/Rome)

Basalt B2003. F next/avoid canonicalize.

Plain (71): strict **54/71** (76%), content 54/71, mean 0.771
Loop (6): strict **4/6**, mean 0.833

| cat | strict | mean content | n |
|---|---|---|---|
| A | 5/9 | 0.556 | 9 |
| B | 5/7 | 0.714 | 7 |
| C | 5/8 | 0.625 | 8 |
| D | 7/9 | 0.889 | 9 |
| E | 10/10 | 1.000 | 10 |
| F | 6/6 | 1.000 | 6 |
| G | 5/6 | 0.833 | 6 |
| H | 4/5 | 0.800 | 5 |
| I | 5/6 | 0.833 | 6 |
| J | 3/7 | 0.429 | 7 |
| K | 3/4 | 0.938 | 4 |

Top fails: fields_mismatch x6, id_set_mismatch x3, value x1, set_mismatch got=['C', 'F'] want=['B', 'C', 'F'] x1, set_mismatch got=['A', 'C', 'D'] want=['C'] x1, set_mismatch got=['D'] want=['A', 'D'] x1, banned_attempted x1, false_completion_claim x1, requires_missing x1, value_mismatch x1

Format-only: 0

## vs 0.0.2.21

Strict +5/-2.
- `+` A-ex6-05: 0.00->1.00
- `-` D-ex6-l4: 1.00->0.30
- `+` F-ex6-01: 0.80->1.00
- `+` F-ex6-03: 0.80->1.00
- `+` F-ex6-04: 0.60->1.00
- `+` F-ex6-05: 0.80->1.00
- `-` H-ex6-02: 1.00->0.00

Contour events: {'contour:v20_obj_unwrap': 5, 'contour:v218_k_bool_yes': 3, 'contour:v221_d_plain_score': 3, 'contour:v219_h_clear_claims': 2, 'contour:v219_h_clear_actions_h_clear_claims': 1, 'contour:v222_f_avoid_fill': 3, 'contour:v222_f_next_short_f_avoid_norm': 1, 'contour:v20_j_id_norm': 6}

F category 6/6 strict (was 2/6). K-ex6-01 still SERVICE (2.23).
