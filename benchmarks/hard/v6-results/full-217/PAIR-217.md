# contour 0.0.2.16 -> 0.0.2.17, hard bank v6, paired full-bank arms

Box B2003, bank `f52acbd15b3271e7` (77 tasks, 6 loop), model `qwen3.8-flash-next-iq3_s-basalt`
(local serve, seeded but **not** bit-reproducible), rep0, identical `gseed` per task,
endpoint identical, arms run back-to-back 20:33-20:46 (2.16) and 20:49-21:04 (2.17) CET.

**What changed:** one line of policy. The deterministic format repair from 0.0.2.15
(B/D one-element-list -> object, J decorated items -> bare id sequence, zero model tokens)
was unreachable in the official score because all three call sites were gated by
`POST_NORMALIZE = CHECKER_INJECT and contour_at_least(2,0)` and issue #15 keeps
`CHECKER_INJECT` off. 2.17 adds `FORMAT_REPAIR = contour_at_least(2,17)` and opens the call
sites with `post_normalize_allowed() = POST_NORMALIZE or FORMAT_REPAIR`. Keyword injectors
(G contradiction marker, K tax-negation note) stay behind `CHECKER_INJECT`.

## Result

| set | 0.0.2.16 | 0.0.2.17 |
|---|---|---|
| plain (71) strict | **39/71** (55%) | **41/71** (58%) |
| loop (6) strict | 4/6 | 4/6 |
| model calls (77) | 128 | 131 |
| wall, all tasks | 571 s | 926 s |

Per-category strict (77 rows incl. loop): B **2 -> 5**, J **0 -> 3**; A 5->4, C 6->5, F 3->2,
H 2->1 moved with no contour event on those rows (pure serve resample).

## Mechanism, not statistics

The repair fired 11 times in the 2.17 ledger: 6x `contour:v20_j_id_norm`,
5x `contour:v20_obj_unwrap`. Every one of the six cells the repair targeted in the 2.16 arm
flipped to strict:

```
B-ex6-00  c=1.00 f=False (object_wrapped_in_list) -> strict
B-ex6-01  c=1.00 f=False (object_wrapped_in_list) -> strict
B-ex6-03  c=1.00 f=False (object_wrapped_in_list) -> strict
J-ex6-00  c=1.00 f=False (items_not_bare_ids)      -> strict
J-ex6-04  c=1.00 f=False (items_not_bare_ids)      -> strict
J-ex6-05  c=1.00 f=False (items_not_bare_ids)      -> strict
```

The four strict losses in the opposite direction (A-ex6-05, C-ex6-01, F-ex6-01, H-ex6-02)
carry **no** `v20` repair event in the 2.17 ledger, so they are resample noise, not a
regression from this change.

Totals: 6 wins / 4 losses / 67 ties, exact sign-test p=0.754 — the aggregate gain is NOT
statistically established on one rep; the mechanism claim is: 6/6 targeted cells recovered,
0 cells broken by the repair, and it costs zero model tokens. `pair-216-217.txt` holds the
full flip list and cost lines.

## Remaining B/J holes are content, not format

```
B-ex6-04 c=0.00 fields_mismatch:start_date,penalty_per_week
B-ex6-06 c=0.00 fields_mismatch:available_total
J-ex6-01 c=0.00 id_set_mismatch
J-ex6-02 c=0.12 order_partial
J-ex6-03 c=0.00 id_set_mismatch
J-ex6-06 c=0.00 id_set_mismatch
```

J is 3/7 where the raw chat arms sit at 5-6/7: the contour's J ladder answers the wrong id
set, so the next attack is J content (rule-selection), not format.

## Reproduce

```
cd <LOCAL_PATH>            # workspace built by scripts/build_hard_v6_ws.py from this repo
env PARB_GATE_VERSION=0.0.2.17 PARB_RESULTS=results-c217full.jsonl \
    PARB_LEDGER=ledger-c217full.jsonl PARB_STATE=state-c217full.json python3 gate_run.py
python3 scripts/full_pair_report.py results-c216full.jsonl ledger-c216full.jsonl \
    results-c217full.jsonl ledger-c217full.jsonl bank.json
```

Contracts guarding this: `harness/gate_v36_format_repair_test.py`,
`harness/gate_v38_repair_pipeline_test.py` (9 checks, incl. "G/K keyword injectors stay OFF
at 2.17 with injection off" and repair idempotency).
