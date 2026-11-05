# Hard-bank v5 audit (2026-11-05)

Requested by an external reviewer (via Grok bot audit of a not-yet-published
post draft). Scope: full audit at fixed commit `5941690`, all answers
published, totals recomputed from scratch, discrepancies explained.
Until this audit the scoreboard existed only in commit messages:
**those earlier tables are PRELIMINARY and superseded by this file.**

## Reproduce

```
git checkout 5941690   # or any descendant that keeps these files
python3 scripts/audit_hard_v5.py
```

The script asserts completeness (77 unique ids per arm, no empty answers,
exact id-set match with the bank) and prints a per-task table plus totals
under three scoring modes. Pinned inputs (sha256/16):

| input | sha |
|---|---|
| benchmarks/hard/bank-hard.json (bank v5) | 32953591ba2a6c51 |
| harness/parb_check.py | 1c032ef022607d7b |
| harness/parb_loop.py | f5f5b78ab46a0f0c |
| q5-experiment/answers-basalt.jsonl | 1cb5b6ee7189e0e5 |
| q5-experiment/answers-grok.jsonl | d12022d0680bb59c |
| q5-experiment/answers-codex.jsonl | d135e361b033a50c |
| audit-20261105/answers-contour.jsonl | see this commit |

`q5-experiment/answers-*.jsonl` are the complete 77-answer archives of the
raw arms (they predate the q5 experiment naming); contour per-task records
with full answers are in `audit-20261105/answers-contour.jsonl`
(local filesystem paths redacted as `<LOCAL_PATH>`; no answer text changed).

## Arms and run parameters

| arm | exact model id | how run |
|---|---|---|
| basalt (raw) | `qwen3.8-flash-next-iq3_s-basalt`, Basalt v0.2.1 | single HTTP call, temp 0.7, no contour, max_tokens per answer (default serve limit), host P2005: Ryzen 9 9955HX, RTX 5090 Laptop 24 GB, 64 GB RAM |
| contour | same local model, contour `0.0.2.12` | full contour: plan seeds, token ladder 256..8192, fixers, best-of-2; seeds per row in the published JSONL; same P2005 hardware |
| codex | `gpt-6.1-sol`, `model_reasoning_effort=xhigh` (Codex CLI 0.166.0, ChatGPT plan auth) | one `codex exec` call per task, stdin prompt, no tools/contour |
| grok | `grok-4.7` (xAI, via hermes CLI `hermes -z @file`) | one call per task, no tools/contour |

Bank v5 = bank-hard.json regenerated on 2026-11-05: E `valid_price` spec
reworded unambiguous ("чисел (целых или дробных)") — ids unchanged;
4 hard tasks affected (E-ex-01-3, E-ex-03-4, E-ex-04-0, E-ex-05-4).
codex and grok were re-run on exactly those 4 tasks (their published answers
are the post-reword ones). basalt raw answers predate the reword; all four
its answers are range filters (`0 < p <= 10000`) that pass the hidden tests
under both wordings — recorded here instead of re-generating answers.
No answer was ever edited retroactively; the reword is a bank version
change (v-next -> v5), not an answer change.

## Refusal handling (H guard)

`check_H` strips negated action claims (`письмо не отправлено`,
`команда не выполнена`) before the fabricated-action check; affirmative
false claims still fail (contract test `gate_v33_h_negation_test.py`,
14/14). Scored A/B against the pre-guard scorer (`harness/parb_check.py`
at `e58b664`, no `NEG_CLAIM`): **zero score differences on the published
raw answers** (45/54/56 both epochs, plain-D strict). An earlier internal
claim that the guard added "+1/+2 perfect" to codex/grok was a bookkeeping
error made without an A/B rescore; corrected here. The guard matters for
future answers and contour rows (it cleared H rows in the contour 2.12
series), not for these 231 raw rows.

## Scoring modes and the discrepancy table

Same answers, same bank, three defensible scorers:

| mode | basalt | grok | codex | note |
|---|---|---|---|---|
| strict_loop | 43/77 | 52/77 | 56/77 | D judged by the agent-loop scorer (structured tool-call steps required). Single-shot chat text structurally cannot pass D format; this was our provisional table and it UNDERSTATES raw arms by exactly those D cells |
| strict_plain (OFFICIAL for raw arms) | **45/77** | **54/77** | **56/77** | D judged by the plain plan scorer on final text; format required elsewhere |
| content_only (auditor variant) | 45/77 | **58/77** | 56/77 | ignores `format_ok`; reproduces the external recount exactly (58 grok / 45 basalt / 56 codex) |

Where the external numbers came from:
- grok 58 vs our 52: they used plain-D **and** ignored format (4 grok E
  answers with correct code but non-parseable framing: E-ex-02-1, E-ex-02-4,
  E-ex-04-2, E-ex-05-0, plus 2 D cells recovered by plain-D).
- basalt 45 vs our 43: plain-D recovers 2 D plan cells (`D-ex-*`) that the
  loop scorer rejects for missing step structure.
- codex 56 = 56 in all variants.

Our protocol stance: for single-shot arms `strict_plain` is the official
number (the loop scorer's step-shape requirement is a contour-interface
requirement, not a fair one-shot contract); for the contour arm the loop
scorer is correct because its D answers are genuine agent loops. Format
remains part of the contract in both (machine-readable output is required
in production), so `content_only` is reported as the auditor variant, not
the official one.

## Final hard-v5 scoreboard (rep0, one full pass per arm)

| rank | arm | result |
|---|---|---|
| 1 | **contour 0.0.2.12 (local, Basalt)** | **70/77 = 90.9%** |
| 2 | codex gpt-6.1-sol xhigh | 56/77 = 72.7% |
| 3 | grok 4.7 | 54/77 = 70.1% |
| 4 | basalt raw | 45/77 = 58.4% |

Contour residual failures (7): C-ex-00..05 format/missed-options (6) and
F-ex-00-0 (1). Contour day trajectory on this bank family: 73% (pre-fix
bank) -> 78/84/87% (after G-doc fix, bank v-next) -> **90.9%** (bank v5,
audit-confirmed).

Not claimable from this audit: any "beats ChatGPT on q5" statement — the
registered q5 experiment refuted it (gpt-6.1-sol xhigh 18/18, see
`q5-experiment/README.md`). The proven result remains: contour beats its
own bare model (+6/0 cells, exact McNemar p=0.031) and the scoreboard gap
above.
