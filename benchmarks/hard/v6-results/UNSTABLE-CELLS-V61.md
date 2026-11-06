# Contour cell stability across 6 seeds (stamp 0.0.2.29, bank v6.1)

Ledgers: ledger-c229full.jsonl, ledger-c229r12.jsonl, ledger-c229r3.jsonl, ledger-c229r45.jsonl. Reason strings are recomputed with the frozen scorer from the answer bytes in the sibling results file; contour events are read from the ledger `events` column.

stable pass 52, stable fail 5, seed-unstable 14 of 71 cells

Stable fails (candidate bank or model ceiling): A-ex6-03, B-ex6-04, B-ex6-06, C-ex6-02, J-ex6-02

| task | cat | passes / seeds | reason in a failing seed | contour events in a failing seed |
|---|---|---|---|---|
| J-ex6-01 | J | 1/6 (...P..) | j content=0.00 format=True ['id_set_mismatch'] | gate:format_gap_json,fix:format_attempt_1,gate:format_gap_json,fix:format_attemp |
| C-ex6-00 | C | 3/6 (P..PP.) | c content=0.00 format=True ["set_mismatch got=['A', 'C'] want=['A', 'C', 'E']"] | gate:logic_parser_gap_0_0,contour:v229_coverage_from_prompt:5,gate:coverage_ok,c |
| C-ex6-01 | C | 4/6 (.PPP.P) | c content=0.00 format=True ["set_mismatch got=['C', 'F'] want=['B', 'C', 'F']"] | gate:logic_parser_gap_0_0,contour:v229_coverage_from_prompt:6,gate:coverage_ok,c |
| F-ex6-00 | F | 4/6 (P..PPP) | f content=0.80 format=True ['avoid'] | gate:sysadmin_structure_gap,fix:sysadmin_attempt_1,gate:sysadmin_structure_gap,f |
| A-ex6-00 | A | 5/6 (PP.PPP) | a content=0.00 format=True ['fields_mismatch:surcharges,total'] | gate:extraction_failed |
| B-ex6-03 | B | 5/6 (PP.PPP) | b content=0.00 format=True ['fields_mismatch:flags,mem,replicas'] | gate:format_gap_json,fix:format_attempt_1,gate:format_ok_json |
| B-ex6-05 | B | 5/6 (PPP.PP) | b content=0.00 format=True ['fields_mismatch:items,n_tags'] | gate:format_gap_json,fix:format_attempt_1,gate:format_gap_json,fix:format_attemp |
| C-ex6-03 | C | 5/6 (PPPPP.) | c content=0.00 format=True ["set_mismatch got=['A'] want=['A', 'D']"] | gate:logic_parser_gap_0_0,contour:v229_coverage_from_prompt:5,gate:coverage_ok,c |
| H-ex6-00 | H | 5/6 (PPPP.P) | h content=0.50 format=True ['unknown_missing'] | gate:quote_not_in_source,fix:quote_attempt_1,gate:quote_not_in_source |
| H-ex6-01 | H | 5/6 (.PPPPP) | h content=0.50 format=True ['requires_missing:аудит-лог operations'] | gate:quote_not_in_source,fix:quote_attempt_1,gate:quote_not_in_source,contour:v2 |
| H-ex6-03 | H | 5/6 (PPPPP.) | h content=0.00 format=True ['unknown_missing'] | gate:quote_not_in_source,fix:quote_attempt_1,gate:quote_not_in_source,contour:v2 |
| J-ex6-03 | J | 5/6 (P.PPPP) | j content=0.00 format=True ['order_partial'] | gate:format_gap_json,fix:format_attempt_1,gate:format_gap_json,fix:format_attemp |
| J-ex6-06 | J | 5/6 (PP.PPP) | j content=0.00 format=True ['order_partial'] | gate:format_gap_json,fix:format_attempt_1,gate:format_gap_json,fix:format_attemp |
| K-ex6-03 | K | 5/6 (PPPPP.) | k content=0.00 format=True ['missing:ITEM', 'missing:QTY', 'missing:LEAD_WEEKS', 'missing:FREE_SHIPPING'] | — |

Reading rule: a cell that flips between seeds is not a scoring mystery, it is the model giving a
different answer under a different seed. Only a mechanism that makes the model re-check that
answer can convert it, and converting it is measurable cell by cell.

## Correction (06:40 CET): the earlier "parse collapse" reading of this table was an artifact

The first version of this script read the answer text from the **ledger** row, which does not carry it: the
answer bytes live in the sibling `results-*.jsonl`. It therefore re-scored an empty string and reported
`no_json` / `no_list` / `no_answer_line` for 12 of the 14 unstable cells. With the answer bytes read from
the right file, **zero** of the 14 cells shows a parse collapse. The table above is the corrected one.

What the coin flips actually are — content-side, not format-side:

| real failure in the losing seed | cells |
|---|---|
| `set_mismatch` / `id_set_mismatch` — the model selects a different option or id set | `C-ex6-00`, `C-ex6-01`, `C-ex6-03`, `J-ex6-01` |
| `order_partial` — right items, wrong order | `J-ex6-03`, `J-ex6-06` |
| `fields_mismatch` / `missing:` — required fields absent or holding different values | `A-ex6-00`, `B-ex6-03`, `B-ex6-05`, `K-ex6-03` |
| `unknown_missing` / `requires_missing` / `avoid` — the answer omits one required component | `H-ex6-00`, `H-ex6-01`, `H-ex6-03`, `F-ex6-00` |

Consequence, stated plainly: **contour 0.0.2.30 was built on a misdiagnosis.** It guarantees the artifact
shape, and in this bank the artifact shape was not the thing that was breaking. The paired arms
(`PAIR-230-V61.md`, same seeds, `0.0.2.29` vs `0.0.2.30`) show no gain; the re-ask does fire (ledger events
`contour:v230_contract_reask_*`) but on cells whose score was already decided by content.

The pass/fail counts in the first version were read from the ledger's own `content`/`format_ok` columns, so
the stability map itself — 52 stable pass, 5 stable fail, 14 coin flips — still stands. Only the cause
column was wrong, and the mechanism built on it did not pay.

Next hypothesis, taken from the corrected table: seed instability here is the model giving a **different
content** under a different seed (different letter sets, different orders, dropped fields). Mechanisms worth
measuring: self-consistency voting over several samples for set/order tasks, and a grounded field-completeness
pass for A/B/K. Neither is implemented yet, and neither will be claimed before a paired arm shows it.
