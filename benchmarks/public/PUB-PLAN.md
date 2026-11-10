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
| livecodebench | 175 (test6 slice: 112 stdin + 63 functional) | `8da729553c7c5710` | HF `livecodebench/code_generation_lite` (license `cc`) answers 200 unauthenticated; LFS/Xet files `test.jsonl` 1253 MB, `test2` 713, `test3` 623, `test4` 1205, `test5` 558, `test6` 134 MB; the README documents `release_v1..v5` (400 problems May 2023–Mar 2024 up to 880 problems May 2023–Jan 2025) and `version_tag` slices | PROBED 2026-11-09: NOT blocked on access — the set can be pinned without an agreement. Each problem carries public sample tests plus hidden test cases, which is exactly the split item 8 asks for (public tests as validator, hidden tests for scoring). Only the 134 MB `test6` slice fits the local budget; the 0.5–1.3 GB files do not. No arm until the execution checker ships and self-tests. **FETCHED AND PINNED 2026-11-09 13:35 CET**: `test6.jsonl` 134 303 240 B, raw sha256/16 `bb4c364f71921c44`; 175 questions (43 easy / 52 medium / 80 hard), contest dates 2025-01-04 → 2025-04-06, platform split atcoder 112 (`testtype: stdin`) + leetcode 63 (`testtype: functional`, `starter_code` non-empty on all 63); public tests are plain JSON (median 3 per question), the hidden ones are base64 → zlib → **pickle** → JSON (median 40 per question), so the decoder must be a hardened unpickler that refuses every global class and that refusal is a self-test, not a nicety. Size measured on the bytes: normalised slice 289.8 MB (median 54 KB/question, worst single question 32.0 MB), gzip of the raw file 92.7 MB — so the hidden-test payload cannot be a tracked git file; the tracked tasks file will carry ids, prompts, starter code, public tests and per-question hidden-test sha16, and the payload goes to a release asset pinned in `MANIFEST.json`. The 32 MB question is inside the slice, so the validator budget (per-test and per-question byte caps, declared in the contract) is a pre-registration item, not a post-hoc filter. **PINNED + CHECKER SHIPPED 2026-11-09 15:22 CET (no arm yet)**: normalised tasks file `livecodebench.tasks.jsonl`, 175 rows / 425 565 B, SHA-256/16 `8da729553c7c5710` (SHA-1/16 `572c76cf72de552e`) — prompt, starter code, the PUBLIC tests and, per question, `hidden_count` plus the SHA-256/16 of the canonical hidden-test JSON. The hidden battery (6537 tests, 289.5 MB decoded) is an UNTRACKED gzip sidecar (`livecodebench.hidden.jsonl.gz`, 100 111 386 B, SHA-256/16 `86f92ab37602195a`); `score` re-derives each sidecar row's hash and fail-closes on a mismatch, and 175/175 pins verified at build time. Checker contract `lcb-exec-v1` (`scripts/pub_bench_lcb.py`, SHA-256/16 `0430437a774eb39d`): verdict = **every hidden test passes**, stdin regime executed in a rlimit'd child (1 GiB AS, 20 s/test, 600 s/question), pre-registered byte caps set above the measured maxima (max single test input 4.36 MB, max single output 3.44 MB, worst question total 29.9 MB, median 48.7 KB) so no question is excluded by construction, and an over-cap test is a **loss**, never a skip. The pickle decoder refuses **every** global class (`find_globals` raises), proven by a control payload that would otherwise call `os.system`, and all 175 real rows decode under that guard as pure JSON data. Contract self-test **10/10** before any arm (reference passes, wrong completion fails, crash fails, infinite loop -> TLE loss, empty answer fails, payload-pin mismatch -> UNSCORED not guessed, functional regime named unscored, over-byte-cap -> loss, pickler guard). Scope honesty: the 112 AtCoder `stdin` tasks score today; the 63 LeetCode `functional` tasks stay **UNSCORED** (driver from each case's own type list not shipped) and out of the denominator, with the count printed beside every percent. The hidden payload's release-asset upload is a separate owner decision — until then an outsider can verify the per-question pins but cannot re-run the hidden battery. **Bare arm row published 2026-11-09 16:28 CET: 60/112 = 53.6 %** over the 112 `stdin` questions (63 `functional` UNSCORED and named beside the row, not counted as losses): one clean leg 15:25:30→16:23 CET, 175/175 `finish=ok`, 0 empty, 38/175 rows at the 2400-token ceiling — all 22 stdin-scored truncations are losses, so 21 of the 44 hard losses are truncations, not reasoning failures — 129.04 Wh sampled, 3448 s wall, difficulty split easy 26/26, medium 18/26, hard 16/60 (`LIVECODEBENCH-RESULT.md`). The matched-shape contour leg runs from 16:31 CET with the `lcb-exec-v1` slot in the validator position and first rung **2400** (the bare arm's ceiling — the first set where the parity rung is not 1200); no LCB contour percent exists before it completes. **Completed 17:35 CET and published: 54/112 = 48.2 %** — 175/175 rows, 176 model calls, 1 gate fix, 0 ladder steps, 35 truncations, 131.88 Wh (the bare leg spent 129.04 Wh), shape read from the rows (`request_shape bare-matched`, `first_rungs [2400]`). Paired on the 112 scored ids: 8 cells pass only for the bare arm, 2 only for the contour arm, p=0.109 — a **measured null**, not a regression, and 9 of those 10 discordant cells carry no contour event at all; the loss side sits on the 2400-token ceiling (28 truncated stdin rows vs the bare arm's 22, every truncation an automatic loss). Full accounting in `LIVECODEBENCH-RESULT.md`. **codex arm published 20:03 CET: 105/112 = 93.8 %** — the line's first measured non-null cross-arm delta (bare 0W/45L p=5.7e-14, contour 0W/51L p=8.9e-16 on the 112 scored ids), with the transport rollout audit (0 tool calls) and the 2400-token budget confound stated beside the number|
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
  (`BFCL-RESULT.md`). The LiveCodeBench codex leg then ran 16:59:27→19:36:36 CET over all 175 ids
  and is **published: 105/112 = 93.8 %** — the first cross-arm delta on this line that is not a
  null: on the 112 scored ids bare is 0W/45L (p=5.7e-14) and contour is 0W/51L (p=8.9e-16) against
  codex, and codex's 7 losses are cells every local arm also fails. The leg cwd held the local
  arms' answer files, so the rollout logs were audited: 0 tool calls, 0 artifact-path references.
  A
  cloud arm is never launched into an exhausted subscription; when a codex leg stops that way it is
  recorded in `LEG-INCIDENTS.md` like any other leg stop.
* **grok** — `grok-4.7` via the documented CLI transport.
* **contour-0.0.2.56** — the frozen runtime, run as the item P0 parity arm on **every** published
  set (owner request 2026-11-08, which supersedes the earlier plan to restrict it to the
  format/protocol-sensitive sets 4 and 9). On the answer-graded classic sets the parity row is
  expected to show a harness that never fires; the accounting beside the percent is the finding.
  **Status 2026-11-09: item P0 is complete for every set that carried a bare row before
  LiveCodeBench** — gsm8k, arc-easy, arc-challenge, gpqa-diamond, humaneval, mmlu-pro, ifeval and
  bfcl each have a matched-shape contour
  row. LiveCodeBench joined the line at 16:23 CET with its bare row and its matched-shape contour
  leg started at 16:31 (first rung **2400**, the bare arm's ceiling — the first set on this line
  where the parity rung is not 1200), so the set has no contour percent until that leg finishes:
  the validator slot for it (`lcb-exec-v1`) was staged and proven offline against the bare arm's
  stored bytes before the endpoint was reserved (3 stdin rows byte-for-byte identical verdicts,
  the `functional` regime returning UNSCORED rather than zero). Every paired verdict on the line is a measured null: `bare vs contour (matched shape)` gives
  gsm8k 2W/1L p=1.000, arc-easy 1 discordant id p=1.000, arc-challenge 3W/1L p=0.625, gpqa-diamond
  16W/28L (+6.1 pp for the contour leg, the largest delta on the line) p=0.096, humaneval 6W/3L
  p=0.508, mmlu-pro 17W/14L p=0.720, ifeval 16W/21L p=0.511, bfcl 29W/23L p=0.489. The contour event
  census is 0 on every public set, so the frozen harness changes nothing on public tasks by
  construction; what changes a public-set percent on this endpoint is the REQUEST SHAPE (GPQA +24.2 pp,
  ARC-Challenge +2.7 pp between shapes), which is why shape parity, not contour gain, is the finding
  this line owns. LiveCodeBench closed the item on 2026-11-09 at 17:35 CET: matched-shape contour
  54/112 = 48.2 % against bare 60/112 = 53.6 % on the same 112 scored ids, 8 bare-only passes vs
  2 contour-only passes, p=0.109 — the 9th measured null in a row, with the accounting (176 calls
  for 175 rows, 1 gate fix, 0 ladder steps, +2.2 % energy) beside it in `LIVECODEBENCH-RESULT.md`.
  Note that this set is the first where a contour arm could in principle be graded by an execution
  validator rather than an answer matcher, and the gate census is still ~0 per 175 rows.

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

## Deployment hold — issue #43 (2026-11-09 10:10 CET → 2026-11-10 10:10 CET)

The owner mandated a 24-hour architecture deployment freeze (issue #43). This line honors it: no
topology changes, no privilege/network/firewall changes, no container-VM migrations, no system-service
configuration changes, and no restart of another profile's units. Issue #43 itself states the hold is
not a blanket suspension of benchmark work, so benchmark legs keep running under their own existing
policy: a leg unit is a transient user-scoped process this line starts and stops for its own arm, and
it leaves no configuration behind. Anything that would change the architecture waits for the explicit
owner go/no-go after 2026-11-10 10:10 CET; time expiry alone does not authorize it.

## Headroom measurement for a validator-driven repair gate (2026-11-09, from stored bytes)

Why the contour is a null on this line, quantified from verdict sidecars already in `arms/` (no new
arm needed): the gates are triggered by structural/protocol signals, and on public category-P sets the
model already emits a well-formed single-shot answer at the first rung — the parity ledgers show
`model_calls == rows`, 0 gate fixes, 0 blocks, 0 ladder steps on all four parity workspaces
(IFEval 541, BFCL 1244, HumanEval 164, MMLU-Pro 500). On the hard bank the same runtime fires on most
tasks: 77 rows -> 126-145 model calls (1.6-1.9 per task), 30-46 gate fixes, 3-8 blocks, 1-12 ladder
steps. The bank's defect mix is the gate habitat; the public sets are the clean holdout.

Failure anatomy decides whether a repair gate could ever help:
* BFCL (1240 tasks, 124 failing cells): 78 wrong function name/arguments, 34 emitted a call where the
  gold call set is empty, 5 wrong call count, 2 unparseable. Gate-addressable format headroom is
  therefore ~0.16 % of cells; a perfect format repair could not move the percent more than ~0.2 pp.
* IFEval (541 tasks, 74 strict fails): 68 of 74 fail ONLY on surface-verifiable checks
  (`length_constraints:number_words` 14, `keywords:letter_frequency` 11, `combination:repeat_prompt` 10,
  `detectable_format:json_format` 6, `punctuation:no_comma` 6, `length_constraints:number_sentences` 6,
  `change_case:english_capital` 5, `startend:quotation` 4, ...). That is 12.6 % of the set with real
  mechanically checkable headroom, and the contour used none of it, because its validator slot only
  scores the bytes and is not wired into any repair path.

Next candidate, and it is an arm-level experiment, not a contour stamp (the hard line stays frozen at
`0.0.2.56`): `pub-repair-v1` — after the first answer, run the pinned validator; only when it reports a
failed check, re-ask once with the violated check id and its pinned kwargs named, re-check with the same
checker, keep the first answer if the retry scores worse, and publish the retry census, the percent and
the energy next to the untouched 0.0.2.56 rows. Expected ceiling: +12.6 pp on IFEval if every surface
failure were fixable, realistically +3 to +6 pp, ~+0.2 pp on BFCL, zero on the answer-graded sets where
no validator exists. Run it only on the sets with teeth (IFEval, then LiveCodeBench once the exec
checker has a public-test validator slot), and it never replaces the frozen 0.0.2.56 rows.

## `pub-repair-v1` — running now (2026-11-09 18:1x CET)

Contract `pub-repair-v1` (`scripts/pub_bench_repair.py`) is an **arm-level** experiment, not a contour
change: the frozen runtime stays `0.0.2.56` and its stored rows stay byte-for-byte. If a future contour
stamp ever contains a repair gate, that is a new version (`0.0.2.57`) with a new stamp and its own pair,
never a silent edit of these bytes.

Mechanism: read the pinned first-arm answer bytes, run the pinned validator, and for a rejected task
re-ask **once**, naming the violated check ids with their pinned kwargs and showing the rejected attempt.
Two percents are published side by side so the number cannot be cherry-picked: `keep-best` (a retry only
replaces the first answer when it strictly passes) and `retry-only` (what a naive always-take-the-second
harness would score). The scorer refuses a digest row while any re-ask is missing.

Pinned first arm: `benchmarks/public/arms/ifeval-basalt-answers.jsonl`, sha16 `543eb8621087e552`, 541
rows, `temp 0.7 / max_tokens 1200`. The retry inherits that budget, so a retry cut at 1200 tokens is
counted as a failed repair, not excused — the arm is deliberately conservative and reports its own
`api_finish=length` census.

## Next candidate after this: doc-grounding validator (`house-ground-v1`, private set) — **ON HOLD by owner decision 2026-11-09, see issue #44**

The open owner question is whether a harness can beat the bare model or ChatGPT on **personal** data,
for example a new private document. That is a different axis from contour parity: it is not more
computing, it is a verifier over grounding. The only version of it this line can honestly measure is one
where the check is mechanical: every claim, number, name and quote in the answer must be traceable to a
span of the pinned document, the pinned checker decides, and a failed check is what a repair gate would
get to act on.

Rules for that set before any arm exists: the tasks are built from house documents, they stay **local**,
and nothing personal is ever pushed — GitHub gets the task-file sha16, the counts and the percents only.
No arm may run until the grounding checker ships with a self-test over positive and negative examples
(a real span passes; a plausible paraphrase with an invented number fails). Until then the honest answer
to "does a harness make the model smarter about my data" is: **unmeasured**, and the answer-graded public
sets on this line say the effect of the current contour alone is zero.

Status note (2026-11-09 18:45 CET): the owner paused the personal-document line until he names the documents; a reminder fires 2026-11-10 09:00 CET and issue #44 carries the full proposal, the measured basis (`pub-repair-v1` +5.2 pp) and the publication rules. No document is fetched, pinned or scored before his decision.

## Overnight queue 2026-11-09 → 10 (ordered; a tick must pick the first incomplete item, never end idle while one is open)

1. **`lcb-exec-v2` — close the scorer driver gap.** LiveCodeBench left 63 of 175 tasks UNSCORED because
   the runner did not drive some task templates. Fix the driver, re-score the **stored** answer bytes
   offline (zero paid re-runs), publish the corrected rows over the full denominator and mark the
   112-denominator rows `superseded` with dated pointers instead of editing them. Done when: the checker
   self-test is green, the UNSCORED count is reported per arm, and new digest rows exist.
2. **`pub-repair-v2` on IFEval — retry at `max_tokens` 2400.** The v1 census showed 34 of 72 retries cut
   at the inherited 1200-token budget, so v1 is a lower bound. The first arm stays the pinned 1200-byte
   arm; the row must be labelled `pub-repair-v2 (retry@2400)` so nobody reads it as the same request
   shape. Publish census, both percents (`keep-best` and `retry-only`) and sampled energy.
3. **`pub-repair-v1` on LiveCodeBench.** Execution against the hidden tests is a real verifier, and after
   item 1 it covers the whole set: re-ask once per failing task, naming the failing test and the exception,
   keep-best rule, census + energy. This is the strongest prior for a real gain on code.
4. **`pub-repair-v1` on BFCL as a pre-registered negative control.** The headroom analysis says
   gate-addressable failures are 2 of 1240 cells, so the pre-registered expectation is **≤0.5 pp**. Run it
   anyway and publish the expectation next to the result: if it moves more, the headroom analysis was wrong
   and that is the finding.
5. **`pub-repair-v1` on HumanEval.** Only ~5 strict failures, so the ceiling is ~3 %, but it is cheap and
   it tests repair on code generation where the verifier is the same vendored `pytest-v2` execution.
   Small-sample warning must be published: anything under ~2 pp on 164 tasks is not resolvable.
6. **Not queued, on the record:** GPQA-Diamond and MMLU-Pro get no repair arm — they have no verifier, and
   their failures are knowledge errors. Writing this down before the fact is what keeps the later claim
   honest.

Standing limits for every item: no Grok arm before 2026-11-12; issue #43 architecture hold until
2026-11-10 10:10 CET; frozen contour stays `0.0.2.56` with its bytes untouched; a partial arm publishes no
percent; sanitization before push; verdicts and arm bytes shipped so every percent re-scores offline.

**Queue status 2026-11-09 22:10 CET (tick 3):** item 1 **closed** — `lcb-exec-v2`
(checker `68a0a39a6aec46a3`, v1 bytes in `checker_history`) rescored the stored bytes offline;
all three arms now publish over the full 175 (bare 101/175, contour 99/175, codex 168/175 =
96.0 %), every stdin verdict cell identical under v1 and v2, v1 rows superseded by dated
pointers. Item 2 had closed at 19:4 CET with the `pub-repair-v2` rows. Item 3 **closed** —
`pub-repair-lcb-v1`: 67 public-validator-driven re-asks over the full set, keep-best
**108/175 = 61.7 %** vs first arm 101/175 (7W/0L, p = 0.0156), retry-only 107/175, 8 blind
hidden failures published, 59.7 Wh sampled; the print-crash after the measurement is a dated
`LEG-INCIDENTS.md` entry. **Next in force: item 4** (BFCL repair as pre-registered negative
control, pre-registered expectation ≤ 0.5 pp on 1240 — publish the expectation beside the
result), then item 5 (HumanEval repair, small-sample warning mandatory). Codex transport still
healthy as of 19:36; grok stays suspended until 12 Nov.

**Queue status 2026-11-09 23:55 CET (tick 4):** item 4 **closed, expectation refuted** —
`pub-repair-bfcl-v1` ran verdict-only over all 124 first-arm failures (46 call-count class, 78
unmatched-call class; that census came from stored bytes at 23:25, before the first call):
**45 conversions, 0 worse, keep-best = retry-only = 1161/1240 = 93.6 %** vs first arm 90.0 %. The
pre-registered ≤0.5 pp was based on a mis-citation ("2 of 1240" is the checker's count of
*unverifiable gold parameters*, not a failure census) — per the plan's own wording, the wrong
headroom analysis is the finding. Against the redraw control computed from published bytes
(contour-0.0.2.56 matched arm converts 29 of the same 124 = 2.34 pp) the matched sign test is
**23/7, p = 0.0052**: the feedback adds +1.3 pp above a plain second draw. Tooling shipped with it:
the repair digest rows now write the same SHA-256/16 tasks cell as the other rows of the set;
`write_digest` fails closed if its regenerated head drops published prose (the LCB v1→v2
supersession sentence had been eaten by a digest rewrite, restored twice, guard proven with a tamper
control); the infra scanner is green again (0 findings) after 5 byte-pinned exception records for
repair-arm answer bytes, 2 of which were pre-existing gaps on published IFEval files. Leg incidents:
the first BFCL attempt died on a tooling `KeyError` before any endpoint call (zero calls burned,
attempt kept aside), and the 23:26 leg rewrote the digest head with pre-fix code. **Next in force:
item 5** — `pub-repair-v1` on HumanEval (5-ish strict failures, ceiling ~3 %, small-sample warning
mandatory: nothing under ~2 pp on 164 tasks is resolvable), with the redraw control published beside
it the same way. Codex transport healthy; grok suspended until 12 Nov.

**Item 5 pre-registered 2026-11-09 23:58 CET (tick 4b, no repair call made yet).** Headroom census
from stored bytes with `pytest-v2` (self-test asserted first): the bare HumanEval arm fails **5/164**
cells — `humaneval-0032`, `-0132`, `-0134`, `-0145`, `-0147` — and **all five are wrong-value
assertion failures**, no syntax or crash class, so a verdict-only repair ceilings at **5 cells =
3.05 pp**. The redraw control from published bytes (contour-0.0.2.56 bare-matched arm, no feedback)
already converts **2 of those 5** (`-0134`, `-0147`), so 1.22 pp of that ceiling is a plain second
draw. Pre-registered null wording: with 5 discordant cells the best possible exact sign test is 5/0,
**p = 0.0625**, so the arm cannot reach significance even by fixing everything — it is a wiring and
cost measurement on a code set and will be published as such whatever it returns. Re-ask wording is
fixed in advance: class only ("the program returned a wrong value on the hidden tests"), never a test
body, gold value or example pair, because HumanEval ships no public tests and the verifier here is the
scorer. Also closed a gap found while preparing it: the HumanEval **bare** arm's answer bytes had
never been published, so its percent was not externally re-checkable — now
`arms/humaneval-basalt-answers.jsonl` (`4f61b87d5e8d130b`) plus verdict rows
(`6878c8b128c3c05d`); re-scoring the shipped copies reproduces 159/164 (bare) and 157/164 (contour),
matching the digest rows.

**Queue status 2026-11-10 01:05 CET (tick 5):** item 5 **closed** — `pub-repair-humaneval-v1`
published exactly as pre-registered: 5 verdict-only re-asks, it converts **exactly** the 2 cells a
plain redraw already converts (repair-only 0, control-only 0, matched 0/0 p = 1.0),
keep-best = retry-only **161/164 = 98.2 %**, 0 cells made worse, 2 796 + 4 444 tokens, 1.51 Wh.
Provenance: the 00:07–00:11 tick ran the leg and never committed; this tick picked the tree up and
published it only after an independent re-score (shipped merged copy → 161/164 through `pytest-v2`,
all five sha16 sidecars reproduce, `secret_scan --strict` 0 findings, `push_ready.sh` green).
Then the follow-up the v1 row demanded (retry@1200 was published as a lower bound): `pub-repair-humaneval-v2`
(retry@2400) converts **4 of 5** → **163/164 = 99.4 %** (4W/0L p = 0.125, 0 worse), and the new
**matched redraw control** `pub-redraw-humaneval-2400` (bare prompt verbatim, prompt guard + unit
proof, sidecar only, no digest row) converts exactly the same 2 cells as the @1200 control, its verdict
map byte-identical. So on HumanEval: the budget alone moves no verdict, the feedback is worth 2/0
(p = 0.50, directional on 5 cells). Same question asked of the biggest repair claim on the line, at
zero cost: the IFEval repair rows now have a redraw control computed from **published bytes**
(the contour-matched arm is an independent matched-shape draw) — a plain redraw converts 16 of the 74
bare failures, `pub-repair-v1` converts 30 at the same shape, discordance 20/6 p = 0.0094, and
`pub-repair-v2` converts 42 (28/2, p = 8.7e-7). The IFEval repair gain is not a second-draw floor;
raising the retry budget also helps at scale (repair@1200 vs @2400, 2/14, p = 0.004).
**Next in force, pre-registered before any call:**
7. **LiveCodeBench repair rows need the same control, and it is free.** `pub-repair-lcb-v1`
(keep-best 108/175, 7W/0L, p = 0.0156) has no redraw control quoted. The published
`livecodebench-contour-matched` arm (99/175, same 175 ids, same matched shape, retry ceiling 2400) is
an independent second draw, so the join is the same zero-call command as IFEval
(`scripts/pub_bench_verdict_sign.py` over the verdict files, restricted to the 74 first-arm failures).
Reading rule fixed now: if the redraw converts within 2 cells of the repair arm's conversions, the
+7 cells are the redraw floor and the LCB row text gets a dated pointer saying so; if the repair keeps
a ≥6-cell margin, the feedback claim stands on the execution sets as a class (IFEval + HumanEval + LCB).
8. **2026-11-12: Grok resumes.** Queue in this order, resumable by id: gpqa-diamond (59 ids left of
198), humaneval (44 of 164), then the deferred grok legs mmlu-pro 500 and ifeval 541. No percent is
computed from the partial files while they are partial.
9. **Unchanged, on the record:** no repair arm for GPQA-Diamond or MMLU-Pro (no verifier, knowledge
errors). No repair arm for the MCQ sets.
Standing limits unchanged: no Grok arm before 2026-11-12; the issue #43 architecture hold runs to
2026-11-10 10:10 CET and this line changed no topology, service or firewall setting (a leg unit is a
transient user-scoped process); frozen contour stays `0.0.2.56` with its bytes untouched; partial arms
publish no percent; sanitization before every push; every percent re-scores offline from shipped bytes.


**Queue status 2026-11-10 01:50 CET (tick 6):** item 7 **closed, and it cuts against the repair line**
— the free LiveCodeBench redraw control (published bytes, **zero model calls**) converts **10 of the 74
first-arm failures** against the feedback arm's 7; restricted to the 66 cells the arm was allowed to
ask, a blind draw converts 9/66 = 13.6 % versus feedback 7/66 = 10.6 %, discordance 3/5, p = 0.727.
Per the pre-registered reading rule the `pub-repair-lcb-v1` row keeps its bytes, its 61.7 % and its
7W/0L p = 0.0156 against the first arm, and carries a dated pointer: on execution-checked code the
repair gain is **inside the second-draw floor**. The class statement is corrected accordingly —
validator feedback is measured above a matched redraw **only on IFEval** (20/6 p = 0.0094 at 1200,
28/2 p = 8.7e-7 at 2400); it is a null on HumanEval and null-to-negative on LiveCodeBench. The one
thing the repair mechanism demonstrably buys is keep-best adoption (0 regressions in 67 re-asks where a
blind redraw regresses 12), and the public-validator gate itself caps the arm at 66 of 74 failures —
the blind draw converts one of the 8 cells the gate can never ask. Full join, ids and cost contrast in
`LIVECODEBENCH-RESULT.md`.
Item 8 preconditions verified with no model call: the two resumable Grok partials are intact —
`gpqa-diamond` 139 unique ids, 139 `finish=ok`, last id `gpqa-138` (59 to go of 198); `humaneval` 120
unique ids, 120 `finish=ok`, last id `humaneval-0119` (44 to go of 164) — so the 12 Nov resumption
continues by id and still computes no percent while partial.
**The queue is now empty**: items 1–5 and 7 are closed, item 6 stays on the record, item 8 is gated to
2026-11-12 by the owner quota window, item 9 unchanged. Nothing was launched this tick — an unqueued arm
has no pre-registered hypothesis, so it would burn endpoint time and energy for an unframed number. The
issue #43 architecture hold runs to 2026-11-10 10:10 CET and this tick started and stopped no unit and
touched no topology, service or firewall setting.
**Next in force:** item 8, the Grok resumption on 2026-11-12 in the pinned order (gpqa-diamond 59 ids,
humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each arm resumable by id and scored
only when complete. `house-ground-v1` stays the owner's call (issue #44, reminder 2026-11-10 09:00 CET):
no document is fetched, pinned or scored before he names them.

**Queue status 2026-11-10 02:45 CET (tick 7):** nothing launched. The next queue item (8, the Grok
resumption) is gated to 2026-11-12 by the owner quota window, and no unqueued arm has a
pre-registered hypothesis, so the endpoint stayed idle (0 leg units, GPU parked at 0 % util). The
tick went at the standing rule **"every percent re-scores offline from shipped bytes"**, which 14
published rows were violating: the gsm8k / arc-easy / arc-challenge / gpqa-diamond / mmlu-pro **bare**
arms, their **codex** legs, the three **complete grok** legs and the HumanEval **codex** arm had no
answer bytes in `benchmarks/public/arms/`. Shipped 14 answer files + 1 verdict sidecar through
`scripts/publish_pub_bare_arm.py` (`--min-rows` per arm, partial files refused); scrub masked
nothing, all files byte-identical to the runner/scorer output, privacy grep 3 hits (all the English
word "bank" in GSM8K prose), hostname 0 hits. Re-score of the **shipped copies** (self-test 22/22,
zero model calls) reproduces all 14 published percents exactly — 1284/1319, 293/300, 288/300,
2261/2376, 290/300, 289/300, 1129/1172, 290/300, 288/300, 127/198, 192/198, 432/500, 462/500,
163/164 — so no digest row changed and no number was re-measured. The two **partial** grok legs stay
unshipped while partial (139/198, 120/164, resumable by id) and still publish no percent; both files
re-verified intact this tick (139 unique ids / 139 `finish=ok`; 120 / 120). Pins and the reproduction
block are in `arms/README.md`; a dated provenance paragraph landed in `GSM8K-RESULT.md`,
`ARC-EASY-RESULT.md`, `ARC-CHALLENGE-RESULT.md`, `GPQA-RESULT.md`, `MMLU-PRO-RESULT.md` and
`HUMANEVAL-RESULT.md`. **Next in force is unchanged: item 8, the Grok resumption 2026-11-12** in the
pinned order (gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541).
Standing limits unchanged: no Grok arm before 2026-11-12; the issue #43 architecture hold runs to
2026-11-10 10:10 CET and this tick started and stopped no unit and touched no topology, service or
firewall setting; the frozen contour stays `0.0.2.56` with its bytes untouched; sanitization before
every push.
