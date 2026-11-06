# contour 0.0.2.29 full arm on bank v6.1

Bank `bank-hard-v6.json` (v6.1, published sha16 `9ec86dfca4a6f85f`); generated workspace copy
sha16 `f4553aab304f60d7`. One rep, identical gseeds to the 0.0.2.28 v6.1 arm in `../four-arm-v61/`.
Ledger rows: 77; model calls 141; summed task seconds 545.

**plain strict 63/71**, loop strict 5/6.

| cat | strict |
|---|---|
| A | 8/9 |
| B | 5/7 |
| C | 6/8 |
| D | 8/9 |
| E | 10/10 |
| F | 6/6 |
| G | 6/6 |
| H | 4/5 |
| I | 6/6 |
| J | 5/7 |
| K | 4/4 |

Lost plain cells: A-ex6-03, B-ex6-04, B-ex6-06, C-ex6-01, C-ex6-02, H-ex6-01, J-ex6-01, J-ex6-02
Lost loop cells: D-ex6-l3

Contour events in this arm:

- `contour:v229_answer_line_contract` x8
- `contour:v20_j_id_norm` x7
- `contour:v20_obj_unwrap` x5
- `contour:v218_k_bool_yes` x3
- `contour:v229_coverage_from_prompt:5` x3
- `contour:v229_coverage_from_prompt:6` x3
- `contour:v221_d_plain_score` x3
- `contour:v222_f_avoid_fill` x3
- `contour:v229_coverage_from_prompt:4` x2
- `contour:v219_h_clear_claims` x2
- `contour:v227_a_invoice_vat` x1
- `contour:v227_a_fx` x1
- `contour:v227_a_proration` x1
- `contour:v227_a_trimmed_mean` x1
- `contour:v223_k_service_alias` x1
- `contour:v228_h_requires_sig_h_unknown_null` x1
- `contour:v219_h_clear_actions_h_clear_claims` x1
- `contour:v224_i_duration_sort` x1
- `contour:v222_f_next_short_f_avoid_norm` x1
- `contour:v225_g_conflict_code` x1

Paired against the 0.0.2.28 v6.1 arm: `pair-228v61-229.txt` (same bank, same seeds).
