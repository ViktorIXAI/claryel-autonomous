# J battery anatomy — contour 0.0.2.18 probe + all published arms (2026-11-05 21:21 CET)

Probe: the 4 J cells the contour lost on the hard-v6 0.0.2.17 full arm, x3 reps (rep 9001-9003,
fresh `sha256(task|rep)` seeds), endpoint idle, stamp 0.0.2.18 (`PGR: release 0.0.2.18, contour
behavior 2.18`).

## 1. All four are CHRONIC, not LOTTERY

| task | strict /3 | content per rep | spread | class |
|---|---|---|---|---|
| J-ex6-01 | 0/3 | 0.00 / 0.00 / 0.00 | 0.00 | CHRONIC |
| J-ex6-02 | 0/3 | 0.00 / 0.00 / 0.00 | 0.00 | CHRONIC |
| J-ex6-03 | 0/3 | 0.00 / 0.00 / 0.00 | 0.00 | CHRONIC |
| J-ex6-06 | 0/3 | 0.00 / 0.00 / 0.00 | 0.00 | CHRONIC |

Zero seed variance: best-of-N / retry logic cannot fix this class (the skill's CHRONIC rule).
The contour is not hurting either — the same cells are lost by the raw arms (below).

## 2. Two of the four are BANK defects — they cost EVERY arm the same cells

Per-category recount of the published four-arm scoreboard (`~/parb-v6-raw/scored-*.csv`):

| arm | J cells lost |
|---|---|
| contour 0.0.2.17 | J01, J02, J03, J06 |
| basalt raw | **J03**, **J06** |
| codex raw | **J03**, **J06** |
| grok raw | **J03** |

- **J-ex6-03 is unanswerable as shipped.** The bank row carries no table: keys are
  `cat, id, kind, level, prompt, ref, seed, stage` (no `doc`/`assembled_doc`) and the whole
  prompt is `Клиенты (id, объём_покупок, дней_с последней): балл = объём*2 + max(0, 100-дней).
  Топ-2 по баллу (убыв., при равенстве id). JSON-список id.` — the rows it ranks are never
  given, gold is `['c1','c3']`. All four arms emit prose/SQL and lose the cell. This is a bank
  generator defect, not a model gap; it must be regenerated (with the tuple table in the prompt)
  or excluded, as a NEW bank version with an A/B rescore of every saved arm (scorer frozen).
- **J-ex6-06 is ambiguous.** Prompt: `Пропустить score>=70, затем отсортировать id по дате
  возрастанию.` «Пропустить» reads as *skip* (→ `['t2']`) or as *let through* (→ gold
  `['t4','t1','t3']`). Contour, basalt and codex all answered `['t2']`, grok answered the gold
  reading. Reword the bank row (e.g. `оставить только score>=70`) or the cell stays a
  luck-of-reading test, not an IQ test.

Bank fix alone moves J for every arm by up to 2 cells — do not quote the J row (contour 3/7 vs
raw 5-6/7) as a reasoning gap until the bank is corrected and re-scored.

## 3. The two genuine model gaps (contour-only losses)

- **J-ex6-01** filter-then-rank: `Топ-2 самых дешёвых среди срок<=10; при равенстве цены —
  меньший срок.` Gold `['skuC','skuA']`; the model answers `['skuC','skuB']` in all 3 reps —
  it drops the `срок<=10` filter for the second slot (skuB has 12 days).
- **J-ex6-02** multi-key tie-break: products `severity*probability`, ties by `severity` desc.
  Three-way tie at 12 (r2, r3, r4) must order `r3, r2, r4`; the model never gets it (3 different
  wrong orders — variance in *which* wrong order, never the right one).

Class: explicit multi-step rule application (filter → multi-key sort → top-N) over a tiny inline
table. The harness already has the winning pattern for the neighbour class: `logic_by_code`
(category C) parses constraints + candidates from the task text and computes the answer itself.
A J analogue (parse the tuple table + the stated keys/order/tie-break, compute the order by code,
emit JSON ids) is the structural hypothesis for the next contour stamp — it needs its own
contract tests and must fail CLOSED (fall back to `ask_ladder`) whenever the parser is not
confident, exactly like `logic_parser_gap` does for C.

## Reproduce

```
cd <LOCAL_PATH>/parb-loopd-216
# plan-jprobe.json = 4 J tasks x rep 9001..9003, gseed = int(sha256("task|rep")[:8],16) % 999983
env PARB_GATE_VERSION=0.0.2.18 PARB_RESULTS=results-jp.jsonl PARB_LEDGER=ledger-jp.jsonl \
    PARB_STATE=state-jp.json PARB_LIMIT=900 python3 gate_run.py
```
Raw-arm J recount: `scored-{contour,basalt,codex,grok}.csv` in the raw results dir, joined to
`bank.json` by task id.
