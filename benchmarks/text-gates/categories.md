# The 11 task categories (A–K)

Counts from `bank.json` (178 tasks). "Scoring" column names the validator in
`harness/parb_check.py` / `harness/parb_loop.py` that decides `content` 0..1
and `format_ok` 0/1 — expectations are data in the bank (`ref` field), never
LLM-as-judge.

| cat | theme | n | sub-kinds | what the validator checks |
|---|---|---:|---|---|
| A | invoice arithmetic | 16 | invoice, chain_discount, find_error | every required number exact (cents), required line count |
| B | document extraction | 13 | email, csv, orders_text, spec | all matching records extracted, none invented; totals |
| C | constraint satisfaction | 16 | constraints | pick ALL options satisfying ALL conditions; conditions re-derived and evaluated by code |
| D | agent safety & planning | 29 | order_of_ops, loop, read_only, missing_data | read-before-mutate ordering, refusal of mutating plans without confirmation, no invented data; `loop` tasks run inside the mocked tool loop |
| E | Python code-gen | 27 | group_sum, dedup, stats, csv_rows, … | generated code executed against hidden test suites (up to 200 tests in stress tasks) |
| F | sysadmin diagnosis | 10 | service_restart, nvme, oom, diskfull | required structure + named cause + safe step order |
| G | long-context facts | 15 | longctx | facts recovered from long prompts (30k+ tokens), decoy-resistant |
| H | contradiction & confabulation | 13 | contradiction, action_claim, partial | contradiction named explicitly; claimed actions flagged; partial data not silently completed |
| I | prompt-injection resistance | 13 | fake_admin, exfil, price_swap, data_edit | injected instructions refused; data edits verified exact |
| J | strict format compliance | 13 | csv, json | exact CSV/JSON shape: row counts, column names, parseability |
| K | multilingual | 13 | en, it, ru | same validation in non-Russian task languages |

Finance categories are B and C in the version log's shorthand — they are
reported separately, with **cost per actually-correct answer** rather than
raw token cost (lesson from the rejected v1.6).

## How to read a results row

```
task, rep, box, contour_version   → identity (dedup key: task+rep, best kept)
content (0..1), format_ok (0/1)   → the two scores
notes[]                           → machine-readable failure causes
                                  (too_few_safe_steps, no_final_answer,
                                   q5_contradiction_missed, cause_not_named, …)
t_wall, gen, truncated, finish    → timing / decode signals
```

The paired ledger (`gate-ledger-*.jsonl`) carries the cost side per attempt:
`model_calls, gate_fixes, gate_blocks, ladder_steps, ptok, ctok,
useful_tokens, overhead_tokens, seconds` + an `events[]` stream
(`gate:` / `fix:` / `ladder:` / `contour:` — ~40 event kinds).

## Self-tests shipped with the contour

```
python3 harness/gate_fixers_test.py   # 12 cases incl. refusal-to-fix paths
python3 harness/gate_v19_d_test.py    # v1.9 slot normalizer contract
```

Both must pass before any series launch (hard rule in the run protocol).
