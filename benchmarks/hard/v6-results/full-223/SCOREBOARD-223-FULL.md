# hard bank v6: contour 0.0.2.23 full arm (rep0, 77 tasks, 2026-11-05 22:13-22:23 Europe/Rome)

Basalt B2003. K SERVICE hosting alias.

Plain (71): strict **52/71** (73%), content 52/71, mean 0.739
Loop (6): strict **3/6**, mean 0.783

| cat | strict | mean content | n |
|---|---|---|---|
| A | 4/9 | 0.444 | 9 |
| B | 5/7 | 0.714 | 7 |
| C | 5/8 | 0.625 | 8 |
| D | 6/9 | 0.856 | 9 |
| E | 10/10 | 1.000 | 10 |
| F | 6/6 | 1.000 | 6 |
| G | 5/6 | 0.833 | 6 |
| H | 2/5 | 0.500 | 5 |
| I | 5/6 | 0.833 | 6 |
| J | 3/7 | 0.429 | 7 |
| K | 4/4 | 1.000 | 4 |

Top fails: fields_mismatch x7, id_set_mismatch x3, banned_attempted x2, unknown_missing x2, set_mismatch got=['C', 'F'] want=['B', 'C', 'F'] x1, set_mismatch got=['A', 'C', 'D'] want=['C'] x1, set_mismatch got=['D'] want=['A', 'D'] x1, false_completion_claim x1, requires_missing x1, value_mismatch x1, conflict_flag_missing x1, order_partial x1

## vs 0.0.2.22

Strict +1/-4.
- `-` A-ex6-05: 1.00->0.00
- `-` D-ex6-l2: 1.00->0.70
- `-` H-ex6-03: 1.00->0.00
- `-` H-ex6-04: 1.00->0.50
- `+` K-ex6-01: 0.75->1.00

Contour events: {'contour:v20_obj_unwrap': 5, 'contour:v218_k_bool_yes': 3, 'contour:v223_k_service_alias': 1, 'contour:v221_d_plain_score': 3, 'contour:v219_h_clear_claims': 2, 'contour:v219_h_clear_actions_h_clear_claims': 1, 'contour:v222_f_avoid_fill': 2, 'contour:v222_f_next_short_f_avoid_norm': 1, 'contour:v20_j_id_norm': 6}

## Independent re-check (Hermes, from the published ledgers)

Numbers above reproduce exactly from `ledger-c223full.jsonl` + `results-c223full.jsonl`
(`scripts/ladder_v6.py` recomputes the whole ladder, `scripts/full_pair_report.py` the pair — see
`pair-222-223.txt`). The four losses are NOT damage from this stamp: on each of them the 2.22 and
2.23 arms emitted the SAME contour events with the same `model_calls` — `H-ex6-03`
`contour:v219_h_clear_actions_h_clear_claims` in both, `H-ex6-04` only `fix:quote_attempt_1` in
both, `A-ex6-05` no contour events in either, `D-ex6-l2` `fix:loop_protocol_reask` in both. The
stamp's own event `contour:v223_k_service_alias` appears once, on K-ex6-01, the single strict win.
Verdict: **+1 deterministic cell (K now 4/4), -4 resample cells**; H (5/5 -> 4/5 -> 2/5 across
2.21/2.22/2.23) is the noisiest block and needs 3 reps before any verdict. Answer bytes for
0.0.2.18-0.0.2.22 were backfilled into their directories in the same push.
