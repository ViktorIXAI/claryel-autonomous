# BFCL v4 (single-turn, question-only scope) — public set result (ladder item 9)

Pinned set: **1240 tasks**, `benchmarks/public/bfcl.tasks.jsonl`, tasks sha16
`00b74e037240792d` (SHA-256/16, the digest column's convention; SHA-1/16 of the same bytes is
`068d359eb0af79b1`, the hash the repo scanner binds its vendored exception to — both name the
identical 1240 rows). Source: `ShishirPatil/gorilla` at commit
`6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`, `berkeley-function-call-leaderboard/bfcl_eval/data/`.
Pinned scope is the five single-turn non-live categories — `simple_python` 400, `multiple` 200,
`parallel` 200, `parallel_multiple` 200, `irrelevance` 240. The suite renumbered from the "BFCL v3"
label in the ladder line; multi-turn, memory and web-search categories are outside this item's
question-only scope and are **not** pinned. `irrelevance` carries no `possible_answer` file
upstream **by design**: the expected behaviour is to emit no call.

This is the first public set here whose score is **protocol compliance over a structured output**
rather than a final answer match: the verdict is an AST match against the gold call set, so it is
the second set (after IFEval) where a harness has a real validator slot to sit in.

## Arms

| arm | tasks | tasks sha16 | call | strict |
|---|---|---|---|---|
| bare local brain `qwen3.8-flash-next-iq3_s-basalt` (P2005, IQ3_S, 24 GB class) | 1240 (full set) | `00b74e037240792d` | temp 0.7, `max_tokens` 1200, one request per task, no request seed, serve-default thinking; checker `bfcl-ast-v1` | **1116/1240 = 90.0 %** |
| contour 0.0.2.56, matched shape (first rung 1200, no seed, serve-default thinking, validator slot = `bfcl-ast-v1`) | 1240 | `00b74e037240792d` | same shape as the bare arm by the parity shape rule | next leg (staging the `validator=bfcl` workspace) |
| codex `gpt-6.1-sol` (subscription CLI) | 1240 | `00b74e037240792d` | transport does not expose sampling params | not started (the codex slot is on the IFEval leg) |
| grok-4.7 | 1240 | `00b74e037240792d` | — | suspended by owner quota, resumes 2026-11-12 |

Cross-arm standard for this window is three arms (bare local / contour matched shape / ChatGPT
codex): the Grok quota ran dry on the owner side on 2026-11-09 and no Grok percent is produced
before 2026-11-12.

## Bare arm — provenance and cost

* One clean leg, unit `parb-pub-bfcl`, **10:53:33 → 11:44:48 CET**, `finish=ok` on all 1240 rows,
  **0 engine errors, 0 empty answers**, 1240 distinct task ids, no duplicates. No leg restart, no
  quarantined file, so `LEG-INCIDENTS.md` carries no entry for this arm.
* Runner-reported wall: **3075 s** summed request time (2.48 s/task mean, 1.95 s median).
* GPU energy (2 Hz sampler, 1213 samples over 3070 s, `gpu-power-bfcl.csv`): **106.7 Wh**, mean
  125.0 W, max 211 W, mean utilisation 97 %, **peak 23 563 MiB VRAM of a 24 GB card**, peak 69 °C.
  Resource verdict: **tight**, same as every other local leg on this box — the serve owns the card
  for the whole leg.
* Tokens: **482 672 prompt / 227 379 generated**; median prompt 333 tokens (the function docs are
  the prompt cost of this set).
* **Call-budget cost, stated rather than hidden: zero.** `api_finish == "stop"` on all 1240 rows,
  so no answer was cut at the pinned 1200-token budget — unlike IFEval, where 62/541 (11.5 %) hit
  that ceiling on the same endpoint. On this set the budget is not the binding constraint.

## Per-category result and what the failures actually are

| category | strict | failures | dominant failure shape |
|---|---|---|---|
| `simple_python` | 377/400 = 94.2 % | 23 | 22 wrong function name / argument set, 1 call-count |
| `parallel` | 186/200 = 93.0 % | 14 | 9 name/argument, 5 call-count |
| `multiple` | 184/200 = 92.0 % | 16 | 15 name/argument, 1 call-count |
| `parallel_multiple` | 165/200 = 82.5 % | 35 | 32 name/argument, 3 call-count |
| `irrelevance` | 204/240 = 85.0 % | 36 | **36/36 are spurious calls** (`calls=N gold=0`) |

Totals across the 124 failures: **78 name/argument mismatches, 46 call-count mismatches**.

Two readings this table supports, and one it does not:

1. **Abstention fails only in one direction.** Every `irrelevance` failure is the model emitting a
   call it should not have emitted; there is not one failure where it refused on a task that had a
   valid call. The 34 single-extra-call cases and 2 multi-call cases are the whole category loss.
2. **The weakest category is function *selection*, not syntax.** `parallel_multiple` (82.5 %) loses
   32 of 35 cells by choosing a function the gold does not contain, i.e. from several plausible
   candidates in the same prompt, not by formatting the call wrongly.
3. It does **not** support a token-budget or truncation story: nothing was truncated.

## Checker contract

Contract `bfcl-ast-v1` (`scripts/pub_bench_bfcl.py`): AST match over calls extracted from the
answer, order-free multiset equality against `possible_answer`, accepted-value wrappers read as
sets, the upstream `""` optional-parameter marker honoured (624 parameters over 444 entries), a
gold parameter absent from the call's own docs skipped as unverifiable (**2 of 1240 entries**), and
`irrelevance` scored as the **absence** of a call to a provided function. The scorer refuses to
publish unless its own self-test passes, and refuses a >5 %-missing arm.

Gates re-run at scoring time, not only at pinning time: **self-test 22/22**, and the published-bytes
re-score of the shipped arm file reproduced **1116/1240 = 90.0 %** exactly. The two structural
gates recorded when the checker shipped stay in force: gold-as-answer **1240/1240** (the checker
must accept its own gold) and perturbed-gold control **1000/1000 rejected** (it must reject a
mutated gold).

**Checker noise is zero for this set**, which is worth stating next to IFEval's: the AST matcher
uses no stochastic component (IFEval's upstream checker calls `langdetect` and flips ~1 task per
run), so a re-score of identical bytes reproduces the identical verdict vector. No ±0.5 pp band
applies here.

## Reproduce this row

```
python3 scripts/pub_bench_bfcl.py benchmarks/public/bfcl.tasks.jsonl \
        benchmarks/public/arms/bfcl-basalt-answers.jsonl
```

Shipped artifacts (`benchmarks/public/arms/`): `bfcl-basalt-answers.jsonl` (1240 rows, SHA-256/16
`4ac238d09babcb45`) and `bfcl-basalt-verdicts.jsonl` (1240 rows, SHA-256/16 `389aed67b18d0d58`,
byte-identical to the scorer's own output). The answers file is byte-identical to the runner's
output; both are asserted at publish time by `scripts/publish_pub_bare_arm.py`, which refuses
partial arms.

One privacy note that is a byte fact, not an omission: one answer echoes a **fake dataset path
carried by the pinned upstream task bytes themselves** (it is the argument value the gold requires
for `parallel_167`). Masking it would edit scored bytes and break the call syntax, so the token is
kept, proven from the pinned task file by the publisher's `--tasks` proof and reported as
`upstream_pinned_path`, and the scanner suppresses it only under a sha16-bound exception for these
exact bytes.

## Honest caveats

* **Contamination.** The pinned categories are public and widely mirrored; unlike the LiveCodeBench
  post-cutoff window, this set cannot be claimed contamination-free. It measures protocol
  compliance of this brain today, not a held-out capability.
* **Saturation is partial.** 90.0 % overall, but no category is at the ceiling, so headroom is
  measurable here — unlike ARC/GSM8K, where the ceiling hides the contour effect.
* **Resolution floor.** At n=1240 one cell is 0.08 pp, so percent differences of one or two cells
  between the contour and bare arms will be meaningless; the paired sign test over the matched
  (task, id) cells with the discordant ids listed is the instrument for the contour row.
* **Request-shape confound.** Only a matched-shape contour leg (first rung 1200, serve-default
  thinking, temp 0.7, same seed policy) is admissible beside this row; an escalation-shape contour
  row would be a request-shape cost, not a contour effect, and would be marked superseded.
* **The 2 unverifiable entries** (gold params absent from their own docs) are skipped by the
  checker rather than guessed, so they can cost at most 0.16 pp of false negatives and are named
  in the checker.
* **Irrelevance has no gold file upstream.** Its verdict is "no call to a provided function", so
  prose is correct by construction; a model that abstains in prose is never penalised, which is
  the right shape but means the category measures over-calling only.
