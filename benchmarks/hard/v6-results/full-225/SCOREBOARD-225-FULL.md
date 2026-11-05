# hard bank v6: contour 0.0.2.25 full arm (rep0, 77 tasks, 2026-11-05 22:30-22:36 Europe/Rome)

Basalt B2003. I duration re-sort + G conflict-by-code (emit path; overwrite deferred to 2.26).

Plain (71): strict **56/71** (79%), mean 0.790
Loop (6): strict **4/6**, mean 0.900

| cat | strict | mean content | n |
|---|---|---|---|
| A | 5/9 | 0.556 | 9 |
| B | 5/7 | 0.714 | 7 |
| C | 5/8 | 0.625 | 8 |
| D | 7/9 | 0.933 | 9 |
| E | 10/10 | 1.000 | 10 |
| F | 6/6 | 1.000 | 6 |
| G | 5/6 | 0.833 | 6 |
| H | 4/5 | 0.800 | 5 |
| I | 6/6 | 1.000 | 6 |
| J | 3/7 | 0.446 | 7 |
| K | 4/4 | 1.000 | 4 |

Top fails: sandbox x10, fields_mismatch x6, id_set_mismatch x3, banned_attempted x2, set_mismatch got=['C', 'F'] want=['B', 'C', 'F'] x1, set_mismatch got=['A', 'C', 'D'] want=['C'] x1, set_mismatch got=['D'] want=['A', 'D'] x1, requires_missing x1, clause_pair x1, values x1, order_partial x1

## vs 0.0.2.23

Strict plain 52/71 -> 56/71. Deterministic: I 5/6->6/6 (v224_i_duration_sort on I-ex6-02). G-ex6-03 still 0 (model already emitted conflict:true with wrong clauses; overwrite lands in 0.0.2.26). H 2/5->4/5 (resample). A-ex6-05 recovered (resample).

Contour events: {'contour:v20_obj_unwrap': 5, 'contour:v218_k_bool_yes': 3, 'contour:v223_k_service_alias': 1, 'contour:v221_d_plain_score': 3, 'contour:v219_h_clear_claims': 2, 'contour:v219_h_clear_actions_h_clear_claims': 1, 'contour:v224_i_duration_sort': 1, 'contour:v222_f_avoid_fill': 3, 'contour:v222_f_next_short_f_avoid_norm': 1, 'contour:v20_j_id_norm': 6}

Fails:
- A-ex6-01 0 ['fields_mismatch:net,vat,gross']
- A-ex6-02 0 ['fields_mismatch:combined_gbp']
- A-ex6-03 0 ['fields_mismatch:net,social,tax']
- A-ex6-04 0 ['fields_mismatch:prorated,used,remaining,after_penalty']
- B-ex6-04 0 ['fields_mismatch:start_date,penalty_per_week']
- B-ex6-06 0 ['fields_mismatch:available_total']
- C-ex6-01 0 ["set_mismatch got=['C', 'F'] want=['B', 'C', 'F']"]
- C-ex6-02 0 ["set_mismatch got=['A', 'C', 'D'] want=['C']"]
- C-ex6-03 0 ["set_mismatch got=['D'] want=['A', 'D']"]
- D-ex6-l2 0.7 ['banned_attempted:EXECUTE_COMMAND']
- D-ex6-l3 0.7 ['banned_attempted:EXECUTE_COMMAND']
- G-ex6-03 0 ['clause_pair', 'values']
- H-ex6-02 0 ['requires_missing:подпись начальника перед отправкой']
- J-ex6-01 0 ['id_set_mismatch']
- J-ex6-02 0.125 ['order_partial']
- J-ex6-03 0 ['id_set_mismatch']
- J-ex6-06 0 ['id_set_mismatch']
