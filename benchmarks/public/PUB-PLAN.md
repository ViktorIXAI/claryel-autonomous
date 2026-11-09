# Public benchmark line (PUB) — plan and first rows

Started 2026-11-08 by owner decision: the hard-bank contour line is **frozen at the measured
stable stamp `0.0.2.56`** (hard-bank development stops at the measured numbers in
`../v6-results/VERSION-LADDER-PERCENT.md`), and the next workstream runs **public benchmarks**
with the same publication discipline: pinned task files, deterministic scorers, stored answer
bytes, one percent row per run.

## Rules of this line

1. A benchmark is one pinned task file: `benchmarks/public/<name>.tasks.jsonl` + `MANIFEST.json`
   (source URL + sha16). A re-fetch that changes bytes is a new version, never an in-place edit.
2. Scorers live in `scripts/pub_bench_score.py` and are deterministic (`number`, `letter`,
   `exact`). Execution checkers (`pytest` for HumanEval, `ifeval` rules) ship as separate
   contracts; until they exist, those tasks are counted as UNSCORED and excluded from the
   denominator — never scored by eyeball.
3. An arm is refused if >5% of answers are missing; partial arms publish nothing.
4. Cross-arm tables use one matched subset with the same task ids and the same call parameters
   (`temperature 0.7`, `max_tokens 1200`, one seed). Cloud arms are expensive, so the matched
   cross-arm set is 300 tasks; the local brain runs the full set. The matched set is the first 300
   ids of the pinned task file in file order, fixed before any arm ran — subsets are never chosen
   after seeing scores.
5. Contamination is stated per benchmark: the classic sets below are public and static, and are
   retired for frontier comparison in 2026 aggregators (last reported GSM8K 92.6%, ARC 95.3%,
   MMLU 90.1%). They are still the right first yardstick for a 24 GB quantized local brain, and
   every row says which model produced it.
6. Energy and wall time are recorded per arm like on the hard bank (GPU sampler for local legs;
   wall time only for cloud legs).

## Benchmark ladder, cheapest first

| # | benchmark | size | what it measures | local arm budget | cross-arm subset |
|---|---|---|---|---|---|
| 1 | GSM8K (test) | 1319 | grade-school arithmetic chains | ~55 min | 300 |
| 2 | ARC-Easy / ARC-Challenge | 2376 / 1172 | school science MCQ | ~40 min each | 300 |
| 3 | HumanEval | 164 | code synthesis, execution-verified | ~20 min (`pytest-v1` execution checker in force) | 164 (full) |
| 4 | IFEval | 541 | verifiable instruction/format compliance | ~25 min (needs `ifeval` checker) | 541 (full) |
| 5 | SimpleBench dev | 2500 → 500 | common-sense trap questions, **not saturated** (best public number 81.9%) | ~30 min on the subset | 500 |
| 6 | GPQA Diamond | 198 | expert science MCQ, noise ±3 pp | ~10 min | 198 (full) |
| 7 | MMLU-Pro | 12k → 500 | 10-option knowledge+reasoning | ~40 min on the subset | 500 |
| 8 | LiveCodeBench (post-cutoff window) | ~200 | contamination-aware code | ~40 min | full window |
| 9 | BFCL v3 | ~1000 | function/tool calling, AST match, multi-turn state | ~1-2 h | 300 |
| later | Terminal-Bench, SWE-bench Verified subset, GAIA-lite | — | agentic work in environments | hours each, only after 1-9 |

Item 4 (IFEval) and item 9 (BFCL) are where a harness can legitimately change the score, because
both score format and protocol compliance; the classic MCQ/math sets are scored on the final
answer, so there the measurement is the model, not the harness — that will be stated in the
result rows, not hidden.

### Source status (2026-11-08)

| set | tasks | tasks sha16 | source | status |
|---|---|---|---|---|
| gsm8k | 1319 | `7dd0080ff23b8bc3` | openai/grade-school-math test.jsonl | pinned, normalised |
| arc-easy | 2376 | `cac604a076e8b00a` | HF allenai/ai2_arc ARC-Easy test | pinned, normalised |
| arc-challenge | 1172 | `523af08216f14256` | HF allenai/ai2_arc ARC-Challenge test | pinned, normalised |
| gpqa-diamond | 198 | `af73cc064d4d8529` | HF fingertap/GPQA-Diamond (mirror of Idavidrein/gpqa) | pinned, normalised; mirror used because the upstream card is agreement-gated |
| humaneval | 164 | `971d976289cd9357` | openai/human-eval HumanEval.jsonl.gz | pinned; execution checker shipped as contract `pytest-v1` (`scripts/pub_bench_exec.py`, self-test: the reference solution passes and a wrong completion fails), **superseded 2026-11-09 by `pytest-v2`** (monotone prose-wrapped-code extraction, A/B rescore table in `HUMANEVAL-RESULT.md`) |
| mmlu-pro | 500 (of a 12032-row test split) | `c64264aede2498c7` | HF TIGER-Lab/MMLU-Pro test (full split raw sha16 `21420424edfbbbc2`) | pinned 09.11; the 500 rows are the pre-registered stride-24 sample (every 24th row of the split in file order, fixed before any arm ran — a head slice would have been subject-skewed because the split is ordered in 14 contiguous category blocks); 10-option MCQ scored by the same `letter` contract as ARC/GPQA; measured on the bytes: the subset covers all 14 top-level categories within 0.3 pp of the full-split mix (math 11.0 % vs 11.2 %, history 3.0 % vs 3.2 %) and 86 of the 91 source subcategories |
| simplebench | 0 | — | HF `SAGE-Liu/SimpleBench` 401 (agreement-gated); the **official** repo `simple-bench/SimpleBench` ships only a 10-question demo (`simple_bench_public.json` 7247 B, `simple_bench_public_set.csv` 6341 B), and the four open HF mirrors (`crellis/simplebench`, `oliveirabruno01/simple-bench`, `Impulse2000/simple_bench_public-20-12-2024`, `sapiens-technology/simple_bench`) carry those same 10 rows (raw sha16 `c71bf526fc7cb084`) | CLOSED AS UNPINNABLE 2026-11-09: the blocker is not the agreement — the full 2431-question paper set is not published at any fetchable URL, and pinning 10 demo questions would be a fake benchmark. MMLU-Pro runs in its place in the ladder |
| ifeval | 541 | `2c672531577dcc33` | upstream **source**, not the gated card: `google-research/google-research` @ commit `e6890f85757dd84e27ca6df2dd30651dafad28e0`, `instruction_following_eval/data/input_data.jsonl` (raw sha16 `98b6b83558bfc673`) | UNBLOCKED 2026-11-09 without any agreement: the data and its checker are Apache-2.0 in the upstream repo, so the gated HF card was skipped. Pin corrected once within the same hour (`f6fa761e8e85efa9` → `2c672531577dcc33`): the first pin omitted the `bench` field the arm runner reads from every row; no answer bytes exist against the old bytes and no arm ran on them, so the correction touches no measurement. Checker contract `pub-ifeval-v1` (`scripts/pub_bench_ifeval.py`) calls the vendored upstream modules (`benchmarks/public/vendor/instruction_following_eval/`, per-file sha16 pins in `MANIFEST.json`) and refuses to score unless (1) the upstream unit suite runs green within 3 attempts (41 tests; measured 2026-11-09: 2 of 8 suite runs fail on the vendor's own `test_english_capital_checker`, because `CapitalLettersEnglishChecker` calls the stochastic `langdetect` — the retry and the flake rate are recorded on `SUITE_ATTEMPTS` in the scorer; the vendored bytes did not move) and (2) the upstream reference responses score in the recorded band (strict 416/540 = 77.0 %, loose 431/540 = 79.8 %). Measured checker noise over identical bytes: strict 416/417/417, loose 431/430/431 (upstream `langdetect` is stochastic), so IFEval deltas under ~0.5 pp are checker noise; runtime deps pinned (absl 2.5.1, langdetect 1.0.9, immutabledict 4.3.1, NLTK words 236 736 entries) in a user venv, not the system interpreter. Plumbing proof on 3 smoke answers (no percent, not a result): all 3 pass their own instruction checks through the vendored checker. **Bare-arm row published 2026-11-09: 467/541 = 86.3 % strict (481/541 = 88.9 % loose)**, with the 62/541 rows that hit the 1200-token ceiling, the sampled energy and the checker-flake record in `IFEVAL-RESULT.md`; contour matched-shape leg published 10:14 (462/541 = 85.4 % strict); **codex leg completed 14:41 and published: 515/541 = 95.2 % strict (526/541 = 97.2 % loose)**; grok deferred by the owner-quota suspension |
| livecodebench | 0 | — | HF `livecodebench/code_generation_lite` (license `cc`) answers 200 unauthenticated; LFS/Xet files `test.jsonl` 1253 MB, `test2` 713, `test3` 623, `test4` 1205, `test5` 558, `test6` 134 MB; the README documents `release_v1..v5` (400 problems May 2023–Mar 2024 up to 880 problems May 2023–Jan 2025) and `version_tag` slices | PROBED 2026-11-09: NOT blocked on access — the set can be pinned without an agreement. Each problem carries public sample tests plus hidden test cases, which is exactly the split item 8 asks for (public tests as validator, hidden tests for scoring). Only the 134 MB `test6` slice fits the local budget; the 0.5–1.3 GB files do not. No arm until the execution checker ships and self-tests. **FETCHED AND PINNED 2026-11-09 13:35 CET**: `test6.jsonl` 134 303 240 B, raw sha256/16 `bb4c364f71921c44`; 175 questions (43 easy / 52 medium / 80 hard), contest dates 2025-01-04 → 2025-04-06, platform split atcoder 112 (`testtype: stdin`) + leetcode 63 (`testtype: functional`, `starter_code` non-empty on all 63); public tests are plain JSON (median 3 per question), the hidden ones are base64 → zlib → **pickle** → JSON (median 40 per question), so the decoder must be a hardened unpickler that refuses every global class and that refusal is a self-test, not a nicety. Size measured on the bytes: normalised slice 289.8 MB (median 54 KB/question, worst single question 32.0 MB), gzip of the raw file 92.7 MB — so the hidden-test payload cannot be a tracked git file; the tracked tasks file will carry ids, prompts, starter code, public tests and per-question hidden-test sha16, and the payload goes to a release asset pinned in `MANIFEST.json`. The 32 MB question is inside the slice, so the validator budget (per-test and per-question byte caps, declared in the contract) is a pre-registration item, not a post-hoc filter |
| bfcl | 1240 | `00b74e037240792d` | upstream repository tree, **not** the gated HF mirror: `ShishirPatil/gorilla` @ commit `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8` (the standalone `berkeley-nest` repo is gone; the same commit an independent external harness byte-pins as current upstream). Pinned scope: the five single-turn non-live categories - `simple_python` 400, `multiple` 200, `parallel` 200, `parallel_multiple` 200, `irrelevance` 240; gold calls in the sibling `possible_answer/` files; irrelevance carries no gold file BY DESIGN (expected: emit no call) | PINNED 2026-11-09. Naming correction applied: the ladder line says "BFCL v3" while the fetchable files carry the `BFCL_v4_*` prefix (the suite renumbered and added multi-turn / memory / web-search categories that are outside this item's question-only scope; those are NOT pinned). Checker contract `bfcl-ast-v1` (`scripts/pub_bench_bfcl.py`): AST-match over calls extracted from the answer, order-free multiset equality, `possible_answer` value wrappers read as accepted-value sets, upstream `""` optional-parameter marker honoured (624 params over 444 entries), gold params missing from the call's own docs skipped as unverifiable (2 of 1240 entries), irrelevance scores the ABSENCE of a call. Gates before any arm: 22/22 self-test, gold-as-answer 1240/1240 (docs-admissible projection), perturbed-gold control 1000/1000 rejected, repo secret scan green with a sha16-bound metadata exception for upstream placeholder mailboxes/fake paths in the pinned bytes. **Bare arm row published 2026-11-09: 1116/1240 = 90.0 % strict** — one clean leg 10:53:33→11:44:48 CET, 1240/1240 `finish=ok`, 0 empty, **0 truncations** (`api_finish=stop` on every row, unlike IFEval's 11.5 % at the same 1200-token budget), 106.7 Wh sampled, checker self-test re-run green at scoring time and the shipped arm bytes re-scored to the same 1116. Failure anatomy: 78 name/argument mismatches vs 46 call-count mismatches; weakest category `parallel_multiple` 82.5 % (32/35 losses = wrong function chosen); ALL 36 `irrelevance` losses are spurious calls, none is a wrong refusal — see `BFCL-RESULT.md`. Contour matched-shape leg next (needs a `validator=bfcl` slot in `scripts/pub_bench_contour_ws.py`), then codex; Grok deferred by the owner-quota suspension. **Slot shipped 2026-11-09** (`validator=bfcl` in the staging builder, self-test re-run at staging time, the task's own `functions`/`gold` carried into the bank rows because the AST matcher scores against them): a 4-id wiring smoke ran first (matched shape proven by `calls=1 lad=0` on every row, the checker's own `why` strings in the notes), and the full 1240-id matched-shape leg runs from 11:59 CET (ws bank sha16 `28dec47661235b11`, tasks-file sha16 `00b74e037240792d`). **Cloud arm published 2026-11-09: codex `gpt-6.1-sol` 281/300 = 93.7 % on rule 4's cross-arm slice** — one leg 14:37:16→15:07:24 CET, 300/300 `finish=ok`, 0 empty, wall 1807 s. Stated skew: the first 300 ids of this file in file order are **all `simple_python`**, so the three-arm cell covers single-call function naming only. On those ids bare local is 285/300 and contour-matched 279/300; the three exact sign tests (8W/2L p=0.109, 7W/3L p=0.344, 5W/7L p=0.774) are nulls inside the set's measured 4.2 % floor. Failure anatomy differs by brain: codex loses 16 name/argument + 3 call-count cells, 2 of them **no call where gold required one**, the mirror of the local brain's 36 spurious-call losses in `irrelevance` — which codex was never asked. Checker bytes moved by a **selection-only** change (`--limit/--offset/--call-note`, `7e6042ce813a2779` → `02cc555963de7dac`); both full-set arms re-scored under the new bytes to the published 1116/1240 and 1122/1240 before the row landed |

## Item P0 — contour parity (owner request 2026-11-08)

Every published public set must carry two rows: the bare brain and the **frozen contour runtime
`0.0.2.56`** over the same task ids, same temperature and same `max_tokens`, scored by the same
public checker contract. The contour leg publishes its gate-fire count, contour edit count,
truncations, tokens, energy and wall time next to the percent, because a harness that never fires
is a cost, not a gain, and that has to be visible. If the frozen runtime cannot run a public task
class without hard-bank-specific assumptions, that refusal is written into the result doc as the
finding — no contour row is faked. Order: GSM8K first 300 ids, GPQA-Diamond (198), ARC-Easy 300.

**How the parity arm is staged (wiring shipped 2026-11-08).** `scripts/pub_bench_contour_ws.py`
builds the workspace the same way `build_hard_v6_ws.py` stages a hard-bank one: the harness
modules are copied verbatim at the frozen stamp `0.0.2.56`, and the builder checks the frozen
deciding scorer bytes first (the contract guard inside `gate_run` fails closed on drift, so a
staging mistake never burns an endpoint). A public task is category `P`: the contour machinery is
keyed to the hard-bank families A–K, so a `P` task reaches only the generic ladder path and no
family grammar (invoice fields, coverage-choice nudges, plan gates) is grafted onto a public
prompt — the ledger event census is the proof of that, not a claim. The validator slot holds the
public checker contract (`pub-checkers-v2`), the same bytes that decided the bare row, with
`format_ok` fixed to 1 because the public contract has no separate format axis. Call-parameter
differences are stated, not hidden: the frozen runtime streams the request, pins a request seed
(sp1) and starts at the first ladder rung (`512`), escalating to the bare arm's `1200` only on a
real truncation, so the contour row carries its own call label.
`scripts/pub_bench_gate_convert.py` turns the gate artifacts into the public answer format and
publishes the accounting beside the percent: gate-fire events, ladder steps, truncations, tokens,
model calls, engine seconds.

**PARITY SHAPE RULE (added 2026-11-08 after the GPQA finding).** A contour-parity row is
admissible only when the contour leg's REQUEST SHAPE equals the bare leg's: the first token rung
is the bare arm's `max_tokens` (1200, not a 512 escalation start), the same thinking state the
bare arm gets from the serve default (no `chat_template_kwargs`, no `reasoning_effort`), the same
temperature (0.7) and the same seed policy (no request seed). The published GPQA parity row
(46.0 % against 64.1 % bare, 0 gates fired, ladder escalated 188/198 and truncated 122 at the
ceiling) is a **request-shape cost, not a contour effect**, and stays published as such until a
matched-shape leg supersedes it. Measured on the endpoint with the same prompt: with
`enable_thinking` omitted the chain of thought streams in `delta.reasoning_content` and the visible
`content` stays short, while `enable_thinking:false` moves the whole chain into `content`
(144 chars vs 1108 chars of visible text on the same task), so the frozen shape burns the 1200
ceiling on reasoning-heavy sets. `PARB_SHAPE=bare` + `PARB_LADDER=1200` is the matched shape; it
is a call-parameter switch only - it registers no contour feature and changes nothing about the
published escalation-shape arms - pinned by `harness/gate_shape_parity_test.py` (15 checks) and
recorded in every row (`gen.request_shape`) and in the run-record stack. If a matched-shape parity
row cannot be produced for a set, that is written as the finding; no row is published that measures
the wrong thing.

## Arms

* **brain-basalt** — our stable local stack: `qwen3.8-flash-next-iq3_s-basalt` on P2005 (24 GB
  class GPU, IQ3_S quant), no contour (contour gates are keyed to hard-bank task classes).
* **codex** — ChatGPT `gpt-6.1-sol`, xhigh reasoning, via the documented CLI transport. Availability
  measured 2026-11-09 12:39 CET: the subscription hit its usage limit mid-leg (CLI says retry at
  13:32 CET), the IFEval leg stopped at 440/541 rows and stayed resumable by id with no percent.
  The window reopened at 13:34 and the leg **completed 541/541 at 14:41 CET; published
  515/541 = 95.2 % strict (526/541 loose)** — three-arm IFEval comparison in `IFEVAL-RESULT.md`. The
  BFCL codex leg then ran 14:37:16→15:07:24 CET on rule 4's 300-id cross-arm slice and is
  **published: 281/300 = 93.7 %**, with that slice's category skew stated beside the number
  (`BFCL-RESULT.md`). A
  cloud arm is never launched into an exhausted subscription; when a codex leg stops that way it is
  recorded in `LEG-INCIDENTS.md` like any other leg stop.
* **grok** — `grok-4.7` via the documented CLI transport.
* **contour-0.0.2.56** — the frozen runtime, run as the item P0 parity arm on **every** published
  set (owner request 2026-11-08, which supersedes the earlier plan to restrict it to the
  format/protocol-sensitive sets 4 and 9). On the answer-graded classic sets the parity row is
  expected to show a harness that never fires; the accounting beside the percent is the finding.
  **Status 2026-11-09: item P0 is complete for every set that carries a bare row** — gsm8k, arc-easy,
  arc-challenge, gpqa-diamond, humaneval, mmlu-pro, ifeval and bfcl each have a matched-shape contour
  row. Every paired verdict on the line is a measured null: `bare vs contour (matched shape)` gives
  gsm8k 2W/1L p=1.000, arc-easy 1 discordant id p=1.000, arc-challenge 3W/1L p=0.625, gpqa-diamond
  16W/28L (+6.1 pp for the contour leg, the largest delta on the line) p=0.096, humaneval 6W/3L
  p=0.508, mmlu-pro 17W/14L p=0.720, ifeval 16W/21L p=0.511, bfcl 29W/23L p=0.489. The contour event
  census is 0 on every public set, so the frozen harness changes nothing on public tasks by
  construction; what changes a public-set percent on this endpoint is the REQUEST SHAPE (GPQA +24.2 pp,
  ARC-Challenge +2.7 pp between shapes), which is why shape parity, not contour gain, is the finding
  this line owns. Next work is the ladder (LiveCodeBench), not another parity leg.

## First measured row

| bench | model | tasks | tasks sha16 | call | strict |
|---|---|---|---|---|---|
| gsm8k | qwen3.8-flash-next-iq3_s-basalt | 25 (smoke) | `7dd0080ff23b8bc3` | temp 0.7 | **24/25 = 96.0 %** |

The smoke row is plumbing proof (3/3 spot-checked answers end with an explicit `ANSWER:` line and
match gold); the full 1319-task GSM8K arm is running as a systemd user unit and its row lands in
`PUB-DIGEST.md` when it completes.

## What "stop development" freezes

`0.0.2.56` is the last hard-bank contour stamp of this line: `harness/gate_versioning.py` keeps
the stamp, the adopted-line map, the pair verdict docs and the ladder stay published, and no new
contour feature is registered while the PUB line runs. Tooling fixes (scorers, runners, reports)
still ship, because measurement honesty is not model development.

## Arm availability policy — Grok suspension (owner decision, 2026-11-09)

* No Grok arm may be launched between 2026-11-09 and 2026-11-12: the owner-side Grok subscription
  quota is exhausted. Both in-flight Grok legs were stopped at 07:57 CET with `finish=ok` on their
  last rows, so this is an availability window, not a transport defect.
* Partial Grok arms stay on disk and resumable by task id (gpqa-diamond 139/198, humaneval 120/164).
  A partial arm publishes no percent, and no percent computed from it exists in this repository.
* Grok rows completed before the suspension stay in force and comparable, same pinned ids and
  checkers: gsm8k-300 96.0 %, arc-easy-300 96.3 %, arc-challenge-300 96.0 %, hard-bank cadence
  134/183 on bank v6.6.
* Until 2026-11-12 the cross-arm standard on this line is three arms: **bare local brain / contour
  `0.0.2.56` at matched request shape / ChatGPT `gpt-6.1-sol`**. An unavailable Grok cell is always
  written as "suspended by owner quota, resumes 2026-11-12" — never blank, never zero, never called a
  transport failure.
* Scheduling effect: the deferred Grok queue (mmlu-pro 500, ifeval 541) frees the Grok transport and
  removes the serialization constraint on cloud legs; the local endpoint is unaffected, so bare and
  contour legs keep running at full rate during the window.
