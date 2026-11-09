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
| contour 0.0.2.56, matched shape (first rung 1200, no seed, serve-default thinking, validator slot = `bfcl-ast-v1`) | 1240 (full set) | `00b74e037240792d` | same shape as the bare arm by the parity shape rule: one 1200-token rung = one request per task, temp 0.7, no request seed | **1122/1240 = 90.5 %** |
| codex `gpt-6.1-sol` (subscription CLI) | **300 of 1240** (cross-arm slice: first 300 ids of the pinned file in file order — that slice is category-pure `simple_python`, see the skew caveat; the tasks sha16 stays the pinned file's, because the scorer slices the pinned file rather than a copied subset) | `00b74e037240792d` | transport does not expose sampling params | **281/300 = 93.7 %** (leg 14:37:16 → 15:07:24 CET, 300/300 `finish=ok`, wall 1807 s at 6.0 s/task, no timeout, no leg restart; section "Cloud arm (codex)" below) |
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
python3 scripts/pub_bench_bfcl.py benchmarks/public/bfcl.tasks.jsonl \
        benchmarks/public/arms/bfcl-contour-matched-answers.jsonl
```

Shipped artifacts (`benchmarks/public/arms/`): bare arm `bfcl-basalt-answers.jsonl` (1240 rows,
SHA-256/16 `4ac238d09babcb45`) and `bfcl-basalt-verdicts.jsonl` (1240 rows, SHA-256/16
`389aed67b18d0d58`, byte-identical to the scorer's own output). The answers file is byte-identical
to the runner's output; both are asserted at publish time by `scripts/publish_pub_bare_arm.py`,
which refuses partial arms.

Contour arm (`bfcl-contour-matched-*`, published by `scripts/publish_pub_arms.py` with the
`--tasks benchmarks/public/bfcl.tasks.jsonl` proof): `answers.jsonl` 1240 rows SHA-256/16
`ed8b58a224521f39`, `verdicts.jsonl` 1240 rows `b6945dd3616dff85`, `results.jsonl` 1240 rows
`ce492b95c4565391` (carries `gen.request_shape` on every row), `ledger.jsonl` 1240 rows
`440433ec40a72e09`, `stats.json` `17a16a334e8c18cc`, `run-record.json` `8681385387e50f51`,
`plan.json` `53d9b22ba9d9a311`, `bank-version.json` `f62925e5dfecc270`, `ws-identity.json`
`5cebff43c0f71fff`. Both reproduce commands were run against the PUBLISHED files: they print
1116/1240 and 1122/1240, and the published contour answers regenerate the shipped verdicts file
byte-for-byte.

One privacy note that is a byte fact, not an omission: one answer echoes a **fake dataset path
carried by the pinned upstream task bytes themselves** (it is the argument value the gold requires
for `parallel_167`). Masking it would edit scored bytes and break the call syntax, so the token is
kept, proven from the pinned task file by the publisher's `--tasks` proof and reported as
`upstream_pinned_path`, and the scanner suppresses it only under a sha16-bound exception for these
exact bytes.

## Contour parity: what the wiring smoke proved (no percent)

Workspace `~/parb-pub-contour/bfcl-matched`, stamp `0.0.2.56`, ws bank sha16 `28dec47661235b11`,
tasks-file sha16 `00b74e037240792d` (identical to the bare arm's task file — the same pinned bytes,
not a re-normalised copy), plan 1240 rows at rep 0 with the sp1 seed formula, validator slot holding
the same `scripts/pub_bench_bfcl.py` bytes that scored the bare row (SHA-256/16 `7e6042ce813a2779`,
recorded in `WS-IDENTITY.json`). The staging builder re-ran the checker's 22-case self-test and
refuses to stage if it fails.

Wiring smoke on 4 task ids (no percent, not a result — three of the four ids were chosen from the
bare arm's failure list on purpose, to see whether the contour path can reach them at all):

```
simple_python_0    c=1.00 f=1 fin=stop calls=1 lad=0  pub:bfcl_ast_match
multiple_7         c=0.00 f=1 fin=stop calls=1 lad=0  pub:bfcl_ast_fail:calls=2 gold=1
parallel_9         c=0.00 f=1 fin=stop calls=1 lad=0  pub:bfcl_ast_fail:calls=1 gold=2
irrelevance_16     c=0.00 f=1 fin=stop calls=1 lad=0  pub:bfcl_ast_fail:calls=1 gold=0
```

What that proves: the frozen runtime runs this public class without a hard-bank-specific assumption
(no refusal), the request shape is the bare arm's (`calls=1`, `lad=0` — one 1200-token rung, one
request per task, no escalation, no request seed), and the verdict comes from the public checker
(the notes carry its own `why` strings, including the `gold=0` shape that means "emitted a call where
none is allowed"). It also shows the contour did **not** repair the three count mismatches in this
sample: at the matched shape the generic ladder does not re-draft a call list, so the parity row is
expected to be near the bare row, and only the paired sign test will say whether it moves at all.

The full 1240-id matched-shape leg ran 11:58:21 → 12:51:42 CET (unit `parb-pub-contour-bfcl-matched`,
GPU sampler `parb-pub-contour-bfcl-matched-samp`), finished by itself with
`PGR finished: records 1240, duration 3201 s, stop reason: none`, and is scored below.

## Contour parity — measured (matched shape, the admissible row)

Run record `pub-bfcl-contour-matched`, stamp `0.0.2.56` / contour behavior `2.56`, ws bank sha16
`28dec47661235b11` (`pub-bfcl-1240`), plan sha16 `d1c794bc40b9ed28`, 1240 plan rows at rep 0 with the
sp1 seed formula, harness git sha `b11e827a725ccc1034d3a167c8c60e0ce089b1d9`, `gen.request_shape` =
`bare-matched: first rung = LADDER[0], no seed, no reasoning_effort, no chat_template_kwargs (serve
default thinking)` on **all 1240 rows**, `first_rung` 1200, ladder `[1200]`.

| quantity | bare arm | contour 0.0.2.56 (matched shape) |
|---|---|---|
| strict (checker `bfcl-ast-v1`) | 1116/1240 = 90.0 % | **1122/1240 = 90.5 %** |
| rows / empty answers / truncations | 1240 / 0 / 0 | 1240 / 0 / 0 |
| requests actually sent | 1240 (one per task) | 1240 (`model_calls` 1240 + `ladder_steps` 0) |
| contour/repair events | n/a | **0** (0 gate fires, 0 fixes, 0 blocks, 0 ladder steps, `rows_with_any_event` = 0) |
| prompt tokens | 482 672 | 482 672 (identical prompt bytes — the parity check on the input side) |
| completion tokens | 227 379 | 224 470 (−1.3 %) |
| summed engine seconds | 3075.1 | 3152.8 (+2.5 %, endpoint state, not harness work) |
| wall window | 10:53:33 → 11:44:48 (3075 s) | 11:58:21 → 12:51:42 (3201 s) |
| sampled GPU energy | 106.7 Wh (1213 samples / 3070 s) | 108.65 Wh (1262 samples / 3194 s, mean 122.5 W, GPU busy 0.88) |

**Paired sign test over the matched ids: 29 contour wins / 23 contour losses, n = 52 discordant
cells, exact two-sided p = 0.489.** 52 of 1240 cells (4.2 %) changed verdict between two arms of the
same brain at the same shape and temperature, so the +6-cell (+0.5 pp) difference sits far inside
this arm-to-arm noise: **the parity verdict on this set is a measured null, not a contour gain.**

Per-category paired deltas (contour − bare): `irrelevance` +4 (208 vs 204), `multiple` +4 (188 vs
184), `parallel_multiple` +3 (168 vs 165), `parallel` +1 (187 vs 186), `simple_python` −6 (371 vs
377) — i.e. the sign of the category deltas is not consistent, which is what a noise-dominated null
looks like.

Discordant ids (W = contour-only pass, L = bare-only pass), with the loser's checker note:

```
W irrelevance_101(calls=12 gold=0)  W irrelevance_126(3/0)  W irrelevance_133(1/0)  W irrelevance_144(1/0)
W irrelevance_164(1/0)  W irrelevance_183(1/0)  W irrelevance_32(1/0)  W irrelevance_99(1/0)
L irrelevance_109(1/0)  L irrelevance_172(1/0)  L irrelevance_222(1/0)  L irrelevance_43(1/0)
W multiple_10  W multiple_136  W multiple_153  W multiple_177  W multiple_52  W multiple_58  W multiple_68
L multiple_164  L multiple_186  L multiple_40(calls=0 gold=1)
W parallel_105  W parallel_119          L parallel_19
W parallel_multiple_145  W parallel_multiple_153  W parallel_multiple_185  W parallel_multiple_31
W parallel_multiple_33  W parallel_multiple_36  W parallel_multiple_43  W parallel_multiple_54
L parallel_multiple_157  L parallel_multiple_177(calls=2 gold=3)  L parallel_multiple_32
L parallel_multiple_53  L parallel_multiple_72(calls=0 gold=4)
W simple_python_158  W simple_python_389  W simple_python_395  W simple_python_58
L simple_python_152  L simple_python_166  L simple_python_177(calls=0 gold=1)  L simple_python_202
L simple_python_235  L simple_python_270  L simple_python_283  L simple_python_285  L simple_python_331
L simple_python_361
```
(For `W` rows the note is the bare arm's failure reason, for `L` rows the contour arm's. Every
`unmatched gold call …` note means the required function name never appeared in the answer; the
`calls=N gold=M` notes are call-count mismatches, and `gold=0` is the irrelevance shape "emitted a
call where none is allowed".)

What this row does and does not show:

* **The harness did nothing, on purpose and verifiably.** Public tasks are category `P`; the contour
  grammars are keyed to hard-bank families A–K, so the only path reachable is the generic token
  ladder, and with the first rung at the bare arm's ceiling the ladder never escalates. Zero events
  over 1240 rows is the census proof, not a claim.
* **The harness cost is therefore near-zero but not zero.** Requests are identical (1240), prompt
  tokens identical, completion tokens 1.3 % lower, sampled energy +1.8 % and summed engine time
  +2.5 % — a second leg on the same box in a different window, so the honest reading is "cost not
  measurable above endpoint-state noise", not "+1.8 % harness overhead".
* **No repair was attempted on the 118 failing cells.** The failures are wrong function names, wrong
  argument values and wrong call counts; at the matched shape nothing in the frozen runtime re-drafts
  a call list against the task's own `functions` docs, so the contour cannot move this class. That is
  the finding a contour round would have to attack (a docs-grounded call-list re-check would be a
  new feature, and the hard-bank line is frozen — so it stays a stated gap, not something built
  here).

## Cloud arm (codex `gpt-6.1-sol`) — measured 2026-11-09, cross-arm slice only

* One clean leg, systemd user unit `parb-pub-bfcl-codex`, **14:37:16 → 15:07:24 CET** (runner
  wall **1807 s**, 6.0 s/task), `finish=ok` on **300/300** rows, 300 distinct ids, **0 empty
  answers**, 0 timeouts at `PUB_CLOUD_TIMEOUT=2400`. No leg restart and no quarantined file, so
  `LEG-INCIDENTS.md` has no entry for this arm. It ran after the IFEval codex leg completed
  (14:41), never in parallel with another cloud leg of the same vendor.
* **Slice skew, stated before the number is read:** the pre-registered cross-arm slice for this
  set is the first 300 ids of the pinned file **in file order**, and this file is ordered by
  category, so the slice is **300/300 `simple_python`** — the easiest category (bare full-set
  94.2 %). The cloud cell therefore ranks the three brains on single-call function naming only;
  `multiple`, `parallel`, `parallel_multiple` and `irrelevance` were never asked of codex, and the
  1240-row numbers of the two local arms stay the set's headline. The slice was fixed before any
  arm ran and is not re-cut here.

| arm (same 300 ids, same checker) | strict |
|---|---|
| bare local brain | 285/300 = 95.0 % |
| contour 0.0.2.56, matched shape | 279/300 = 93.0 % |
| codex `gpt-6.1-sol` | **281/300 = 93.7 %** |

Paired sign tests over the common 300 ids (exact two-sided, generated by
`scripts/pub_bench_verdict_sign.py` from the shipped verdict files):

| pair | W/L | p | discordant ids |
|---|---|---|---|
| bare vs contour | 8W / 2L | 0.109 | bare: `simple_python_152, 166, 177, 202, 235, 270, 283, 285` — contour: `simple_python_58, 158` |
| bare vs codex | 7W / 3L | 0.344 | bare: `simple_python_13, 172, 200, 201, 202, 235, 241` — codex: `simple_python_58, 158, 279` |
| contour vs codex | 5W / 7L | 0.774 | contour: `simple_python_13, 172, 200, 201, 241` — codex: `simple_python_152, 166, 177, 270, 279, 283, 285` |

**Verdict: three arms inside one another's noise on this slice.** The smallest discordant count is
10 cells of 300 (3.3 %), and this set's measured floor is 4.2 % between two arms of the *same*
brain at the same shape, so none of the ±2 pp spreads here is quotable, including the local brain
being ahead of codex. What is quotable is the shape of the failures:

* codex lost **19** cells on the slice: **16 name/argument mismatches** (`unmatched gold call …`)
  and **3 call-count** mismatches — 2 rows where it emitted **no call** where gold required one
  (`calls=0 gold=1`: `simple_python_172`, `simple_python_202`) and 1 where it emitted four
  (`calls=4 gold=1`: `simple_python_234`).
* That is the mirror image of the local brain's `irrelevance` anatomy (all 36 of its losses are
  *spurious* calls, none a wrong refusal). On the one category codex did see, it **under-calls**
  occasionally instead. Abstention behaviour across the five categories stays unmeasured for codex
  because `irrelevance` was never asked of it.
* One byte-audit, because this transport had a defect of exactly that class: a single cluster of
  byte-identical answers across two ids exists in the file (`simple_python_1`,
  `simple_python_97`, both `math.factorial(number=5)`, 24 bytes). Inspected against the task bytes,
  the two are distinct upstream entries with the same gold — "Calculate the factorial of 5 using
  math functions." vs "Calculate the factorial of the number 5" — and their function docs differ.
  This is not the stale-last-message carry closed on the IFEval leg (`pub_bench_cloud.ask()` now
  deletes the output file before every call, see `LEG-INCIDENTS.md`), and both answers are scored
  correct by the checker.

Shipped artifacts: `bfcl-codex-answers.jsonl` (300 rows, SHA-256/16 `08ce765f1f145d7c`) and
`bfcl-codex-verdicts.jsonl` (300 rows, SHA-256/16 `30895bf48007c6e0`), published by
`scripts/publish_pub_bare_arm.py --min-rows 300 --tasks benchmarks/public/bfcl.tasks.jsonl`; the
scrub masked nothing (bytes identical to runner and scorer output — the `--tasks` proof registers
the one upstream-pinned path token that set carries, and this arm's answers turn out not to use it,
so the only scanner hit is an upstream placeholder mailbox pinned at SHA-1/16 `234766f13fea120f`).
Reproduce, against the pinned file and the published answers:

```
python3 scripts/pub_bench_bfcl.py benchmarks/public/bfcl.tasks.jsonl \
        benchmarks/public/arms/bfcl-codex-answers.jsonl --limit 300
# -> simple_python 281/300 = 93.7 %   (re-run on the PUBLISHED copy before this commit: 281/300)
python3 scripts/pub_bench_verdict_sign.py benchmarks/public/bfcl.tasks.jsonl \
        bare=benchmarks/public/arms/bfcl-basalt-verdicts.jsonl \
        contour=benchmarks/public/arms/bfcl-contour-matched-verdicts.jsonl \
        codex=benchmarks/public/arms/bfcl-codex-verdicts.jsonl --limit 300
```

`--limit/--offset/--call-note` are new to `pub_bench_bfcl.py` and are **selection only**: they cut
the pinned file so the digest row keeps the pinned tasks sha16 (a copied subset would mint a second
bench id, the same convention `pub_bench_score.py` already uses). That edit moves the checker's
bytes, so the reproduction was re-run with the new bytes on both published full-set arms before this
row was published: `1116/1240` and `1122/1240`, self-test 22/22, unchanged. The contour arm's
`WS-IDENTITY.json` keeps pinning the checker bytes it was staged with (`7e6042ce813a2779`); the
current file is `02cc555963de7dac` and `MANIFEST.json` now names that with this note.

## Honest caveats

* **Contamination.** The pinned categories are public and widely mirrored; unlike the LiveCodeBench
  post-cutoff window, this set cannot be claimed contamination-free. It measures protocol
  compliance of this brain today, not a held-out capability.
* **Saturation is partial.** 90.0 % overall, but no category is at the ceiling, so headroom is
  measurable here — unlike ARC/GSM8K, where the ceiling hides the contour effect.
* **Resolution floor — now measured, not assumed.** The two matched-shape arms of this brain
  disagree on 52 of 1240 cells (4.2 %): that is this set's single-draw noise floor at temp 0.7, and
  it is 8.7× the +6-cell contour delta. Any BFCL claim smaller than ~1 pp at n=1240 is noise; the
  paired sign test with the discordant ids listed above is the instrument, and the honest verdict on
  this set is a null.
* **Request-shape confound.** Only a matched-shape contour leg (first rung 1200, serve-default
  thinking, temp 0.7, same seed policy) is admissible beside this row; an escalation-shape contour
  row would be a request-shape cost, not a contour effect, and would be marked superseded.
* **The 2 unverifiable entries** (gold params absent from their own docs) are skipped by the
  checker rather than guessed, so they can cost at most 0.16 pp of false negatives and are named
  in the checker.
* **Cross-arm slice skew (new with the cloud arm).** The pre-registered 300-id head slice of this
  task file is category-pure `simple_python`, so the three-arm comparison covers one function-calling
  shape only. It is not a model ranking for the set, and it says nothing about `irrelevance`
  abstention for the cloud arm. A category-balanced cloud slice would be a **new** pre-registered
  subset, declared before scoring, and is not retrofitted to this row.
* **Grok cell for this set:** suspended by owner quota until 2026-11-12 (not a transport failure);
  no Grok number exists or will be inferred for BFCL in this window.
* **Irrelevance has no gold file upstream.** Its verdict is "no call to a provided function", so
  prose is correct by construction; a model that abstains in prose is never penalised, which is
  the right shape but means the category measures over-calling only.
