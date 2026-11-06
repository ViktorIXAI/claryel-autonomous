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

## Addendum (13:40 CET): pair233 adds three seeds of 0.0.2.29; the group table stands

`pair-233/` adds seeds 0-2 of the control stamp (`f29r*`): A-ex6-00 and A-ex6-08 passed 3/3 there,
H-ex6-01/H-ex6-04 flipped again — group 3 (`fields_mismatch`/`missing`) and group 4 (`unknown_missing`/
`requires_missing`) remain the live classes. The 2.33 attempt covered group 3 only where the prompt
states a threshold table (1 of 9 A prompts); group 3's B cells are taken by 0.0.2.34 (B field
completeness, `gate_v51_b_fields_test.py`), and K stays open until the bank states its value shapes.
No group's diagnosis changed.

## Addendum (15:25 CET): pair-235 adds three more 0.0.2.29 seeds and three of 0.0.2.35

`pair-235/` control arms (`h29r*`) add seeds 0-2 of the adopted stamp: `B-ex6-06` fails all three
(note `fields_mismatch:available_total`), now 0/9 across both maps — chronic, and the 2.35 grammar
converts it 3/3 with its own event at stamp `0.0.2.35` (see `PAIR-235-V61.md`; the stamp itself is not
adopted because the arm mean stayed at the noise floor). Group 4 stays live: `F-ex6-00` flips again
(1/3 vs 2/3) with the `avoid` note on every failing seed **in both arms**, while H-ex6-00/01/03
stable-passed all six pair-235 seeds — the 6-seed map keeps them at 5/6, so H lottery draws are rarer
than F's. Group 3's A cells flipped again in this pair (`A-ex6-00` 2/3→3/3, `A-ex6-08` 1/3→3/3, both
event-less — pure resampling, no mechanism credited). 0.0.2.36 (group-4 selection) is launched against
`0.0.2.29` on exactly this class.

## Addendum (16:00 CET): pair-236 measures group-4 SELECTION — zero conversions, class closed

`pair-236/` (`i29r*` vs `i36r*`, three matched seeds): the 2.36 lottery fired 6 times (H-ex6-01 in every
candidate seed, H-ex6-03 once, F-ex6-00 twice) and converted **zero** scoreboard cells. The F strict-best
wins raised an already-passing cell; on H, the strict re-sample never beat the first draw — the extra
sample omits the same component. That is class BIAS, not variance: group 4's H cells sit in the 2.31
failure mode (selection can filter variance, it cannot beat a systematic omission), so the selection
doctrine does NOT apply here and group 4 is closed as a contour target. `B-ex6-06` failed again in all
six pair-236 arms (the 2.35 grammar is frozen out of both) — now 0/12 across the two pairs: chronic
confirmed, re-landed at `0.0.2.37` under the pre-registered rule in `PAIR-236-V61.md`. The event-less
flip background of a bank pair (4 of 5 flips here: identical contour path and calls, different bytes)
should be quoted with every arm-mean delta.

## Addendum (16:55 CET): pair-237 adopts 0.0.2.37; group 3 now has live on-target cells and moves to 2.38

`pair-237/` (`j29r*` vs `j37r*`, three matched seeds): the re-landed B table repair passed its
pre-registered all-or-nothing rule exactly (`B-ex6-06` 0/3 -> 3/3, `contour:v235_b_table_total` on
every converted row, no other 2.37-gated event anywhere, arm +2.4 not below control) — **`0.0.2.37`
is ADOPTED as the new control line** (`PAIR-237-V61.md`). B is closed. The group-3 class struck live
this pair: `A-ex6-00` failed seeds 1-2 **in the adopted control line** with
`fields_mismatch:surcharges,total`, and the frozen 2.33 grammar replays over exactly those published
bytes to 1.00 strict with its `v233_a_tariff_table` event (`gate_v50`, 25 checks) — the zero-fire
condition that froze 2.33 at pair-233 is gone, so `0.0.2.38` re-lands it under a pre-registered rule
that treats another zero-fire pair as UNMEASURED, not a pass. Other flips in this pair, all event-less:
`K-ex6-03` lost a seed on `value:FREE_SHIPPING` — again the documented K value-shape bank defect, not a
contour target; `J-ex6-06` flipped on `order_partial` (the 2.32 grammar reproduces 3/7 J tasks but
converted exactly one cell in its own pair — left frozen; a future J grammar must first raise coverage,
not re-measure this one); `F-ex6-00`/`H-ex6-03` kept their group-4 lottery notes — class closed, no
action. Group 1 (`C` set_mismatch, `C-ex6-00` flipped again) stays live but has no deterministic
grammar proven: `set_mismatch` there is the model's per-option verdict flipping, which neither
selection (2.31) nor a form contract can reach; the next group-1 candidate needs a
per-option-grounded mechanism, not another vote.
