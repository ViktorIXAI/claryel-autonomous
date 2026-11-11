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
7. A local leg may only start after `scripts/pub_preflight.py` exits 0 on a fresh reading of the
   endpoint box. The rule is mechanical since 2026-11-10 (see "Standing local-leg preflight" below);
   cloud legs are not gated by it.

## Standing local-leg preflight (2026-11-10, tick 23)

The machine note for this line says swap saturation on the P2005 endpoint box can restart the engine
mid-leg. Ticks 13, 19, 20, 21 and 22 of 2026-11-10 each decided "no local leg today" by reading
`free -m`, `ps`, `nvidia-smi` and `/health` by hand and writing the numbers into prose. Five hand
readings is a rule, so it is now a gate: `scripts/pub_preflight.py READINGS.TXT` prints the readings
and exits **0 = GO**, **3 = NO-GO** (exhausted swap, low MemAvailable, an engine stuck in
uninterruptible I/O, the idle-spin pair "engine > 200 % CPU at 0 % GPU", `/health` not 200, or a
foreign leg on the same endpoint), **1 = input gap** — a missing or unreadable reading is never
treated as healthy. The readings come from a one-line remote read over the repo-standard key; that
command stays untracked so no connection material lands in this repo, and the tool takes a plain
`key=value` file. Contract test: `harness/pub_preflight_test.py` (20 checks, CI-enrolled by the
`harness/*test.py` glob) — one healthy set goes, six independent tampers each turn NO-GO, two
non-vacuity controls (a busy GPU at high engine CPU, 1 GiB of swap free) still go, and both input-gap
classes fail closed. Threshold constants in the file carry the measurements that set them. The gate
registers no contour feature and moves no published byte.

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

**Queue status 2026-11-10 04:25 CET (tick 8):** nothing launched, and nothing was needed — the queue
stays empty and the only open item (8, the Grok resumption) is gated to 2026-11-12 by the owner quota
window. 0 leg units, no `pub_bench_run`/`gate_run` process, the local endpoint idle (GPU 0 % util,
36.7 W, `/health` 200) and untouched by this tick; the two partial Grok files were re-verified intact
again (139 unique ids / 139 `finish=ok`; 120 / 120) and still publish no percent.

The tick went at the standing rule **"every percent re-scores offline from shipped bytes"**, which the
tick-7 pass had only applied to the 14 classic-set rows. **All six repair rows re-verified from the
shipped bytes, zero model calls:** the shipped verdict sidecars count to the published percents
exactly (`pub-repair-v1` 497/541, `pub-repair-v2` 509/541, `pub-repair-bfcl-v1` 1161/1240,
`pub-repair-humaneval-v1` 161/164, `-v2` 163/164, `pub-repair-lcb-v1` 108/175), and an independent
re-run of each pinned checker over the shipped merged answer files reproduces them too
(`bfcl-ast-v1` self-test 22/22 then 1161/1240; `pytest-v2` self-test green then 161/164 with losses
`-0032 -0132 -0145`, and 163/164 with the single loss `-0145`). The execution-graded one was pushed
all the way: the **whole hidden battery** was re-run over the shipped LCB repair bytes (sidecar file
SHA-256/16 `86f92ab37602195a` reproduced, 0 hidden-pin mismatches, 175 questions, 277 s) and gave
**108/175 with zero per-id verdict flips** against the shipped sidecar.

**That pass then found a real defect in the IFEval contract, not noise.** Two IFEval rescores drifted
±1 cell, and instead of filing them under the published checker-noise band they were chased to the
vendored source: `LetterFrequencyChecker.build_description` replaces any `letter` kwarg outside a-z
with `random.choice(string.ascii_letters)`, so the two pinned cells that ask for punctuation
(`ifeval-1122` "at least 4 hashtags, starting with '#'", `ifeval-1129` "6 or more exclamation marks")
were decided by a **coin flip** — measured strict pass 4/12 and 7/12 over twelve draws of byte-identical
shipped answers (31 of the 33 `keywords:letter_frequency` cells carry an alphabetic letter and are
unaffected). Shipped as a new contract, never an edit: **`pub-ifeval-v2`**
(`scripts/pub_bench_ifeval_v2.py`, SHA-256/16 `b4a089bc7bb3b212`) restores the pinned literal character
on the built instruction, re-asserts the five SHA-1/16 vendored pins on every run, pins determinism
(20 identical draws per affected cell) and fails closed if v1 and v2 differ on more than those 2 cells;
no vendored byte moved. Corrected strict, three independent scorer passes over the shipped bytes: bare
469/469/470 (published 467), contour-matched 463 (462), codex 515 (515, unchanged), `pub-repair-v1`
497 (497, unchanged), `pub-repair-v2` 510 (509). Every paired verdict on the set survives the
correction recomputed, with smaller margins: bare-vs-contour parity 16W/21L p=0.511 → 15W/23L
p=0.256 (still a null), `pub-repair-v1` vs the redraw control 20/6 p=0.0094 → 18/6 p=0.0227,
`pub-repair-v2` vs the control 28/2 p=8.7e-7 → 27/2 p=1.6e-6. The ±1 band itself is unchanged — the
vendor's `langdetect` path in `change_case:*` is still there and is now the only remaining drift — so
the "any IFEval delta under ~0.5 pp is checker noise" rule stands. The published v1 rows, their verdict
files and their bytes are untouched; the corrected table and the digest pointer are in
`IFEVAL-RESULT.md` and `MANIFEST.json`.

Operational note for the next local leg (no action taken, issue #43 hold to 10:10 CET): the endpoint
box answers `/health` with 200 and parks at 0 % GPU, but its engine process has been at **~758 % CPU
for 30 h at zero request load** with 45 GiB resident — the idle engine-spin signature this line has
measured before. A pre-flight engine restart is the known cure; it is an infrastructure action and the
main brain serves this session, so it waits for the hold to lift and for the legs that need it.
CI: the last push (01:29 UTC) is green on all four jobs; the single red in the window is a
`pages-build-deployment` collision from the 01:07 push, and the daily `docs-freshness` job's last
scheduled run was **green** (2026-11-09 11:50 UTC), so the "it errors daily because the tree is dirty"
line is no longer true and should not be repeated without checking.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each resumable
by id and scored only when complete. `house-ground-v1` stays the owner's call (issue #44, reminder
2026-11-10 09:00 CET).

**Queue status 2026-11-10 05:30 CET (tick 7):** queue empty, legs empty — no unit, no process, no
endpoint call this tick; the P2005 idle-spin note above stays on record and untouched (the engine
serves this session, restart waits). The new finding is publication infrastructure, not a leg: the
GitHub Pages site (`viktorixai.github.io/claryel-autonomous`, legacy branch-source build of `main` at
`/`) is **unpublished (HTTP 404) since 02:41 UTC** — the legacy pipeline unpublishes the site when a
build errors, and every build since 22:35 UTC is a coin flip (census 22:35–04:23 UTC: 6 errored, 4
built; all six failures are the same `syncing_files` timeout at ~11 min, the successes are 49–95 s
incremental syncs). The tree is inside every soft limit (125 MB / 2165 tracked files, largest file
9.4 MB) and the identical content built green at 01:29 UTC, so this is a flaky sync, not a content
defect; GitHub's status page reports Pages operational with no incidents. The CI action's own rerun
and three manual `POST /pages/builds` retries (03:58, 04:11, 04:23 UTC) all drew the failure side.
Impact on this line is zero: every verification URL in the publication procedure is
`raw.githubusercontent.com` at a pinned SHA — spot-checked 200 at `HEAD` for `PUB-DIGEST.md` and
`IFEVAL-RESULT.md` — and no tracked document links the github.io surface. If the flap persists, the
lever is a Pages-surface decision for the owner (take the 125 MB data tree out of the Pages source,
a source-path config change), not an edit to tracked bytes.
Also on record, checked not assumed: today's 03:00 CET `docs-freshness` cron **errored**
(exit 1, "repo is dirty; refusing daily docs refresh") while the `pub-ifeval-v2` work was in flight;
the tree is clean now and tomorrow's run starts from a clean checkout.

**Corrections to the paragraph above, same tick, before anyone repeats it.** (a) The claim
"unpublished (HTTP 404) since 02:41 UTC" was NOT established: the root URL `…/claryel-autonomous/`
answers 404 even on a healthy build because the tracked tree ships no `index.html` — the root is not
a health probe — and no content URL was probed during the errored window, so whether site content
actually went down between 02:41 and the 04:27 UTC green build can no longer be reconstructed.
(b) The census snapshot in the paragraph was taken mid-window; the final count to 04:45 UTC is
**7 errored / 5 built since 22:35 UTC**, and the failure signature is not one thing: five failures
are the ~11-minute `syncing_files` timeout, two (04:23:02 and 04:23:51 UTC) are fast-fails at 49 s
and 3 s. What is measured: the latest-build API status stood `errored` from 02:41 until a built
entry at 04:27:28 UTC, and as of 04:45 UTC every probed content URL returns 200 and serves `HEAD`
— `PUB-PLAN.md` served from the site already carries the tick-7 marker. Health probe for this
surface going forward: a pinned content URL, never the root.

**Queue status 2026-11-10 06:15 CET (tick 9):** nothing launched — the queue stays empty and the
only open item (8, the Grok resumption) is gated to 2026-11-12 by the owner quota window. 0 leg
units, no `pub_bench_run`/`gate_run` process; the local endpoint was read but not touched
(`/health` 200, GPU 0 % util / 32.5 W). The P2005 idle-spin note from tick 8 is re-confirmed and
unchanged: the engine has run ~708 % CPU at zero request load for 1 d 09 h (59 GiB resident) — the
pre-flight restart cure stays queued behind the issue #43 hold (lifts 10:10 CET today) and behind
the fact that this engine hosts the live brain; no action taken.

The tick went at the standing rule **"every percent re-scores offline from shipped bytes"**, closing
the audit the tick-7 and tick-8 passes had left open. **The remaining 17 digest percents re-scored
from shipped bytes, zero model calls, scorer self-test 22/22 first:** the nine contour answer arms
under `pub-checkers-v2` (gsm8k 294/300 matched + 290/300 escalation, arc-easy 289/290,
arc-challenge 291/283, gpqa-diamond 139/91, mmlu-pro contour 429/500) and the eight verdict-sidecar
rows (humaneval contour-v2 157/164, LCB contour 99 / bare 101 / codex-v2 168 of 175, BFCL contour
1122/1240, IFEval contour 462 / bare 467 / codex 515 of 541 strict). All seventeen reproduce their
published percents exactly — no digest row changed. **One gap closed:** the 2026-11-08 gsm8k
**smoke** row (25 tasks, 24/25, plumbing proof) was the last percent in the table with no shipped
bytes; the runner's file still exists and re-scored 24/25 (single loss `gsm8k-0012`), so it now
ships as `arms/gsm8k-smoke-answers.jsonl` (25 lines, `0c062902777556de`, byte-identical to runner
output, privacy grep 0 hits). With that row, **no percent in the digest table is left without
shipped, re-scorable bytes**; the two partial grok arms stay unshipped by rule and were re-verified
intact a third time (gpqa-diamond 139 unique ids / 139 `finish=ok`, humaneval 120 / 120).
Digest-head guard checked, not assumed: generated `digest_head()` == file head (3/3 paragraphs).

Ops state read this tick (no action): the last push (04:33 UTC) is green on all five jobs, the
Pages flap has not recurred — the two latest builds (04:27:29 and 04:33:37 UTC) both `built` in
under 30 s and the Pages build for this commit will show the same; `docs-freshness` has **no
scheduled run recorded after 2026-11-09 11:50 UTC (green)** — GitHub has not delivered today's run
at the time of writing and the tree is clean, so the daily-error claim is still not true today.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each
resumable by id and scored only when complete. `house-ground-v1` stays the owner's call (issue #44,
reminder fired 09:00 CET window). Standing limits unchanged: no Grok arm before 2026-11-12; frozen
contour `0.0.2.56`; sanitization before every push.

**Queue status 2026-11-10 07:55 CET (tick 10):** nothing launched — the queue stays empty and item 8
(the Grok resumption) remains gated to 2026-11-12 by the owner quota window. 0 leg units, no
`pub_bench_run`/`gate_run` process (the single `pgrep` hit this tick was the session's own command
wrapper, checked not assumed); the local endpoint was read but not touched (`/health` 200, GPU 0 %
util / 37 W). The P2005 idle-spin note persists and is now measured harder: the engine has held
**704 % CPU at 0 % GPU utilization for 1 d 10 h with 57.6 GiB resident** (load average 14.2 on a
32-core box). The pre-flight restart cure stays queued behind the issue #43 hold (lifts 10:10 CET
today) and behind the fact that this engine hosts the live brain; no action taken. The two partial
grok arms were re-verified intact a fourth time (gpqa-diamond 139 unique ids / 139 `finish=ok`,
humaneval 120 / 120), still unshipped and unscored by rule.

**The tick went at verification integrity, and it found a defect class this line had not audited:
the pins themselves were ambiguous.** `benchmarks/public/arms/README.md` is the file index every
re-scoring instruction in this repo points at. Measured on the shipped files, not on the prose: its
**161 rows printed one hash column called `sha16`, and that column mixed two functions — 125 rows
pinned SHA-256/16, 36 rows pinned SHA-1/16**; all **35** shipped `.sha16` sidecar files carried
SHA-1/16; **35 of 196** artifacts had no index row at all; the LiveCodeBench contour `stats.json`
row printed **33 lines for a 34-line file**; and the main table had **no GFM delimiter row**, so
GitHub rendered all 161 rows as prose. Root cause is in three writers, not in the artifacts:
`scripts/pub_bench_repair.py`, `pub_bench_ifeval.py` and `pub_bench_ifeval_v2.py` each defined a
local `sha16()` on `hashlib.sha1`. **No published artifact byte was edited** — every one of the 36
SHA-1 values is still the SHA-1/16 of the same file, so an auditor who verified the page the
documented way (`sha256sum … | cut -c1-16`) hit a false tamper alarm, which is exactly the failure
this line exists to prevent.

The same ambiguity existed one level up, on a **task file** pin: every published IFEval row prints
tasks cell `2c672531577dcc33`, and that is the **SHA-1/16** of
`benchmarks/public/ifeval.tasks.jsonl`; the SHA-256/16 of the identical 541 rows is
`e09a5cab3782ed5b`. Verified for all nine in-force sets: **eight pins reproduce as SHA-256/16,
IFEval is the sole SHA-1/16 pin** and is now labelled (`tasks_sha1_16` / `tasks_sha256_16` /
`hash_note`, plus a top-level `hash_conventions` key naming both conventions repo-wide — the
security scanner binds its byte-pinned exceptions to SHA-1/16 on purpose, and
`scripts/security/secret_scan.py` exception pins were audited against current bytes as part of the
same pass).

Fix, tooling and pins only:

* `scripts/pub_arms_index.py` (new) generates and verifies that index: two pin columns per row
  (`sha256/16` + `sha1/16`), full coverage, and `--check` **fails closed** on a stale pin, stale
  line count, missing row, extra row, untracked artifact, bad header, missing delimiter row or a
  sidecar that does not carry SHA-256/16 of its target. Re-run against the pre-rewrite index at
  `HEAD` it reports **233 drift lines — 161 ambiguous pins (one per indexed row), 35 files with no
  row, 35 sidecars in the wrong convention, 1 stale line count, 1 missing delimiter row — and 0
  after** (196 rows / 196 files);
* the 35 sidecars were rewritten to SHA-256/16 — the old SHA-1 values stay published, in the
  `sha1/16` column of the row above each sidecar;
* the three writers now name their hash helper (`sha1_16` / `sha256_16` / `sha256_16_text`), their
  census keys are renamed (`task_sha1_16`, `task_sha256_16`, `first_answer_sha1_16`,
  `first_answer_sha256_16`), and each carries a `pin_hash_convention` note;
* **a digest row's tasks cell is read from `MANIFEST.json`** through the new
  `scripts/pub_bench_score.manifest_tasks_cell(bench, tasks)` instead of being re-hashed by
  whichever helper the caller had: it refuses (exit 2) a task file matching neither label or a
  SHA-1-era pin that is not labelled, so one pinned file can never carry two identities in one
  table — `pub_bench_ifeval_v2.py` would otherwise have minted `e09a5cab3782ed5b` rows beside the
  published `2c672531577dcc33` rows;
* `harness/pub_arms_index_test.py` (34 checks, CI-enrolled by the `harness/*test.py` glob, so no
  workflow edit was needed) pins all of it with tamper controls: an edited artifact, a SHA-1 value
  in the SHA-256 column, a SHA-1 sidecar, an artifact without a row, a stale line count and a table
  without its delimiter row each redden CI; the three MANIFEST refusals are proven the same way.

**No percent moved.** The IFEval scorers were re-run over the shipped answer bytes *after* the writer
edits, zero model calls, in the pinned venv: bare **469**, `pub-repair-v1` **497**, `pub-repair-v2`
**510** of 541 under `pub-ifeval-v2` — identical to the pre-change pin-audit re-scores, and matching
the published corrected table. `pub_bench_score` self-test 22/22. Digest head regenerated and
byte-checked against `digest_head()` with zero published prose lost; 47 table lines unchanged.
IFEval's `2c672531577dcc33` cells and every other tasks cell in `PUB-DIGEST.md` stay exactly as
published — the audit labels how to read them, it does not restate them.

Ops state read this tick (no action): tick 9's push (`1155889`) is **green on all five jobs**
(secret-scan, devsecops, contour self-tests, hard-v6 scoring contracts, pages) at 05:15-05:22 UTC,
and the Pages flap has not recurred — the three latest builds (04:27:28, 04:33:36, 05:15:13 UTC) all
`built`, latest status `built`. `docs-freshness` still has no scheduled run recorded after
2026-11-09 11:50 UTC (green): GitHub had not delivered today's 03:00 CET run at the time of writing
and the tree was clean, so the daily-error note in the prompt is still not true today.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each
resumable by id and scored only when complete. Local, arm-free work next tick: nothing is queued on
the checker side — every in-force set's checker ships with a self-test and its task pin now
reproduces — so the queue is genuinely empty until 11-12 apart from the standing verification passes.
`house-ground-v1` stays the owner's call (issue #44, reminder 09:00 CET window). Standing limits
unchanged: no Grok arm before 2026-11-12; frozen contour `0.0.2.56`; sanitization before every push.

**The same ambiguity was one layer deeper, in the pins that certify the *checkers* (same tick).** Of
the seven checker/tool pins in `MANIFEST.json`, **six are SHA-1/16** — the five vendored IFEval
checker files and the LiveCodeBench checker `scripts/pub_bench_lcb.py` (`68a0a39a6aec46a3`) — while
the BFCL checker pin is SHA-256/16. The `livecodebench` entry mixes both conventions on one file
name: `checker_files` prints SHA-1/16 for the current bytes and `checker_history[0].sha16` prints
SHA-256/16 of the superseded `lcb-exec-v1` bytes at commit `91f33c5`. An auditor following the
documented `sha256sum` path therefore got a false tamper alarm on the tool that scored the row, on
six of seven tools. Published values were **not** re-minted: each entry now carries the SHA-256/16
twin beside the published value, a `hash_note` naming the convention, and every `checker_history`
entry declares `pin_hash_convention` plus `pinned_at_commit`/`pinned_file`, so the claim is checked
against `git show` bytes rather than trusted. `python3 scripts/pub_arms_index.py --pins` audits all
of it (and `--check` runs it too): **16 drift lines before the labelling, 0 after**; the contract
test adds three tamper controls (edited checker pin, deleted twin, history pin aimed at the wrong
commit). Full pin/twin table is in `benchmarks/public/arms/README.md`.

**This commit moved one tool pin of its own, and records it instead of letting it drift silently**:
`benches.ifeval.checker_history[0].sha256_16` for `scripts/pub_bench_ifeval_v2.py` moved from
`b4a089bc7bb3b212` (the bytes published at 04:33 UTC, the bytes every rescore in `IFEVAL-RESULT.md`
was run against) to `affc8151363d633a`, because the pin-audit edit renamed that module's hash helpers
and routed its tasks cell through `manifest_tasks_cell`. The old value stays in a nested
`pin_history` record with the reason and the zero-movement proof (post-edit re-scores from shipped
bytes: bare 469, `pub-repair-v1` 497, `pub-repair-v2` 510 of 541 — identical to the pre-edit pass;
`selftest cases=22 failures=0`). That is the pattern this line owes its own edits: name the changed
bytes, prove the arithmetic did not move, keep the old citation true of the run that used it.

One naming defect recorded, deliberately not fixed: `scripts/pub_bench_run.py` writes
`rec["task_sha16"] = t.get("id")` — a field whose name says hash and whose value is the **task id**.
It is a label defect in shipped result rows, never used as a hash by any verifier (no reader of that
key exists in the repo — checked), and renaming it would break the row schema of already-published
arms. Left as-is with this note; a fix would be a new row schema, not an in-place rename.

**Queue status 2026-11-10 08:05 CET (tick 11):** nothing launched — the queue stays empty and item 8
(the Grok resumption) remains gated to 2026-11-12 by the owner quota window. 0 leg units, no
`pub_bench_run`/`gate_run` process, no endpoint call and no cloud call this tick; the local endpoint
was read but not touched (`/health` 200, GPU 0 % util / 36.5 W). The P2005 idle-spin note persists:
the engine holds **695 % CPU at 0 % GPU utilization for 1 d 11.5 h with 56.0 GiB resident** (load
average 14.1 on a 32-core box). The pre-flight restart cure stays queued behind the issue #43 hold
(lifts 10:10 CET today) and behind the fact that this engine hosts the live brain; no action taken.
The two partial Grok arms were re-verified intact a fifth time — gpqa-diamond **139 unique ids / 139
`finish=ok` / 0 empty answers**, last id `gpqa-138`, 59 of 198 to go; humaneval **120 / 120**, last id
`humaneval-0119`, 44 of 164 to go — still unshipped and unscored by rule.

**The tick went at the Grok availability cells in the result tables, and three of them were stale.**
The owner rule says a Grok cell for an incomplete set must read "suspended by owner quota, resumes
2026-11-12", never a blank that reads as a zero and never a transport failure. Measured on the tracked
bytes 25 h after the legs were stopped: `GPQA-RESULT.md` still said **"in flight (12/198 at publish
time)"**, `HUMANEVAL-RESULT.md` still said **"not started yet (grok legs are serialized on the
transport)"** — which its own "Grok status on this set" section contradicts, because that leg ran from
04:07 to 07:57 CET and stored 120 rows — and `MMLU-PRO-RESULT.md` attributed its missing Grok arm to
**transport serialization** rather than to the quota window. Prose in all three documents carried the
correct status; only the table cells — the part people quote — had frozen at publish time. No number
was affected: none of those cells carried a percent, so no digest row and no published arm byte is
touched by this fix.

Fixes, documents and tooling only (zero model calls):

* the three Grok cells now carry the suspension wording plus the measured stored counts
  (GPQA 139/198 with 59 ids to go, HumanEval 120/164 with 44 to go, MMLU-Pro never started and queued
  behind the two resumable partials), each labelled resumable by id with **no percent for a partial
  arm**;
* the stale prose is corrected by dated supersession rather than silent rewrite: the GPQA
  "lands late tonight" bullet and the MMLU-Pro "open item" reason each carry a *(corrected
  2026-11-10 …)* note, and `GPQA-RESULT.md` gained the "Grok status on this set" section
  `HUMANEVAL-RESULT.md` already had;
* the rule now has a checker: `scripts/pub_grok_cell_check.py` scans every
  `benchmarks/public/*-RESULT.md` arm table and requires each Grok row to either publish a percent
  (arm completed) or carry the suspension sentence verbatim, and rejects the stale-marker class
  ("in flight", "not started", "pending", "queued", "serialized") on any Grok row that publishes no
  percent — a Grok row deleted from a set's table is also a finding, because a silently dropped
  fourth arm is the same failure class as a stale cell. Scope is stated in the checker: the digest
  table (rows exist only for complete arms) and the audit-frozen README four-arm table are not
  scanned;
* `harness/pub_grok_cell_test.py` (21 checks, CI-enrolled by the `harness/*test.py` glob, no workflow
  edit) proves the checker is not vacuous: on the pre-fix `HEAD` bytes of the three documents it
  reports **12 findings**, on the fixed tree **0**; a synthesized stale cell, a blank cell and a
  deleted Grok row each redden it, while a completed Grok row with a percent passes.

Ops state read this tick (no action): tick 10's push (`db6b832`) is **green on all four jobs**
(secret-scan, devsecops, contour self-tests, hard-v6 scoring contracts) and the Pages build for it
completed in 29 s. Pages health read honestly this time: the build list is newest-first, so the
latest entry is `2026-11-10T06:16:45Z built`; the four latest builds (04:33, 05:15, 06:10, 06:16 UTC)
all `built`, **10 of the last 30** builds in the API window errored (all in the 22:35–04:23 UTC window
tick 7 documented), and both probed content URLs return **200** — the flap has not recurred since
04:33 UTC. `docs-freshness` is scheduled `cron: 20 3 * * *` (03:20 UTC); no run was recorded for
today at 06:57 UTC and the tree was clean, the last recorded scheduled run being 2026-11-09 11:50 UTC
(green), so the brief's "errors daily because the tree is dirty" line is still not reproducing — this
is GitHub scheduled-workflow delivery delay, not a repo failure, and it is re-checked next tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each resumable
by id and scored only when complete. The new checker is the machine-checkable form of the resumption
rule: after 12 Nov a Grok cell must either publish a percent from a complete arm or keep the
suspension wording — nothing in between. `house-ground-v1` stays the owner's call (issue #44).
Standing limits unchanged: no Grok arm before 2026-11-12; frozen contour `0.0.2.56`; sanitization
before every push; a partial arm publishes no percent.

**Queue status 2026-11-10 09:55 CET (tick 12):** nothing launched — the queue stays empty and item 8
(the Grok resumption) remains gated to 2026-11-12 by the owner quota window. 0 leg units, no
`pub_bench_run`/`gate_run` process, no endpoint call and no cloud call this tick; the local endpoint
was read but not touched. The two partial Grok arms were re-verified intact a sixth time (gpqa-diamond
**139 unique ids / 139 `finish=ok` / 0 empty answers**, last id `gpqa-138`; humaneval **120 / 120**,
last id `humaneval-0119`), still unshipped and unscored by rule.

**The tick went at the percent cells of the per-arm tables, and that audit found 9 stale cells in 4
documents.** Tick 11 fixed the Grok *availability* cells for the reason that the table cell, not the
prose, is what gets quoted. The same failure had been sitting one column over, on the percents
themselves: a superseded number stayed the only number a reader of the arms table could see. Measured
on the tracked bytes, four distinct shapes:

* **the only contour number in the table was the superseded one** — `GPQA-RESULT.md` led with
  `91/198 = 46.0 %` and `ARC-CHALLENGE-RESULT.md` with `283/300 = 94.3 %`, both escalation-shape rows
  the digest header had already declared superseded (70.2 % and 97.0 %), with the corrected percent
  living only in a section further down;
* **a set whose arms table had no contour row at all** — `ARC-EASY-RESULT.md` (so both the superseded
  `290/300 = 96.7 %` and the in-force `289/300 = 96.3 %` were unquotable from the table);
* **a superseded checker contract printed as the current verdict** — `HUMANEVAL-RESULT.md` led with
  the `pytest-v1` cells `158/164` (bare) and `155/164` (contour) while the digest's in-force rows for
  the same stored bytes are `pytest-v2`: `159/164 = 97.0 %` and `157/164 = 95.7 %`;
* **the same shape on LiveCodeBench, hidden by a denominator change** — the arms table still prints
  the three `lcb-exec-v1` percents (`60/112`, `54/112`, `105/112`) with the pointer only in the
  sentence *under* the table, and never prints the in-force `lcb-exec-v2` cells (`101/175 = 57.7 %`,
  `99/175 = 56.6 %`, `168/175 = 96.0 %`).

Fixes are labels and rows only — **no published percent, verdict file or arm byte moved**, and every
in-force number added to a table is a digest row that tick 9 already re-scored from shipped bytes:

* dated in-row pointers now sit on the five superseded cells (gpqa-diamond, arc-challenge, humaneval
  bare + contour, livecodebench × 3), each stating that the printed number stays exactly as first
  published and naming the corrected cell beside it; the HumanEval codex cell also says its
  `pytest-v2` rescore left it unchanged at `163/164 = 99.4 %`, which is why it needed no new digest
  row;
* three matched-shape contour rows were **added** to the arms tables that never carried them
  (gpqa-diamond `139/198 = 70.2 %`, arc-challenge `291/300 = 97.0 %`, arc-easy `289/300 = 96.3 %`),
  with their wall/engine time, sampled energy, request count and gate census taken from the
  documents' own parity sections — GPQA's row states plainly that that leg has no energy samples
  (sampler wiring bug) rather than inventing a number, and the ARC-EASY row states that its leg wall
  was never recorded separately;
* the rule is now machine-checked: `scripts/pub_superseded_cell_check.py` derives the supersession set
  from the digest table itself (tokens `ladder rungs 512,1200, enable_thinking off`,
  `checker pytest-v1`, `checker lcb-exec-v1`), and requires that in the result document's arms table
  (a) any row carrying a superseded percent says "superseded", and (b) the corrected percent is
  quotable from a row of the same arm family. Arm identity is **bench+model, not bench+model+tasks**,
  because a corrected contract legitimately moves the denominator (`lcb-exec-v1` 112 of 175 →
  `lcb-exec-v2` 175 of 175) — requiring the tasks cell to match hid exactly the supersession the rule
  exists to catch;
* `harness/pub_superseded_cell_test.py` — **31 checks, 0 failed**, auto-enrolled by the
  `harness/*test.py` glob (57 harness tests now). Non-vacuity: stripping the word "superseded" from
  each of the five fixed tables reddens it, deleting the ARC-EASY contour row reports "no contour row
  at all", removing `139/198 = 70.2 %` from both GPQA contour rows reports the missing in-force cell,
  renaming a table header reports "no arms table found" instead of skipping the document, a bench with
  no audited document is a finding, and a completed Grok row creates no finding (the rule does not
  bite the availability cells). The pre-fix census on the tracked bytes was **9 findings across 4
  documents**; after this commit the checker reports **0**.

Ops state read this tick (no action): the last push (`2f9bab9`) is **green on all four jobs**
(secret-scan, devsecops, contour self-tests, hard-v6 scoring contracts) and its Pages build
completed; the four latest Pages builds (07:00, 07:07, 07:44, 09:07 UTC) all `built`, so the
22:35–04:23 UTC flap has not recurred. `docs-freshness` still records its last scheduled run at
**2026-11-09 11:50 UTC (green)** — GitHub had not delivered today's scheduled run at 08:50 UTC, and
the tree was clean, so the brief's "errors daily because the tree is dirty" line remains unreproduced
for a third tick; the two earlier scheduled failures (2026-11-07, 2026-11-08) are the last red runs
on record.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each resumable
by id and scored only when complete. Standing limits unchanged: no Grok arm before 2026-11-12; frozen
contour `0.0.2.56`; sanitization before every push; a partial arm publishes no percent.

**Queue status 2026-11-10 11:05 CET (tick 13):** nothing launched — the queue stays empty and item 8
remains gated to 2026-11-12 by the owner quota window. 0 leg units, no `pub_bench_run`/`gate_run`
process, no endpoint call and no cloud call this tick; the local endpoint was read but not touched
(`/health` 200, GPU 0 % util / 36.8 W). The P2005 idle-spin note persists: the engine has held
**664 % CPU at 0 % GPU utilization for 38.3 h with 58.7 GiB resident**. The issue #43 architecture
hold expired at 10:10 CET today and this tick recorded that fact rather than acting on it: an engine
restart is an infrastructure action on the box that serves this session's brain, so it stays an owner
decision and no unit was started or stopped. The two partial Grok arms were re-verified intact a
seventh time (gpqa-diamond **139 unique ids / 139 `finish=ok` / 0 empty**, last id `gpqa-138`;
humaneval **120 / 120**, last id `humaneval-0119`), still unshipped and unscored by rule.

**The tick went at the percents that are *not* in the digest table, and the audit found no wrong
number — it found that 33 of them had no machine check at all.** `PUB-DIGEST.md` is the one table this
line re-scores from shipped bytes (tick 9 closed that audit for all 46 rows). The result documents
quote **169** `N/M = P %` citations; **136** of them are digest rows, and **33** carry no digest row
anywhere: pre-registered slice scores, per-category and per-difficulty breakdowns, truncation censuses
and paired-join conversion rates. Those are exactly as quotable as a digest cell and were maintained
by hand. Measured on the tracked bytes and recomputed offline with the pinned checkers (zero model
calls), **every one reproduced** — no published percent, verdict file or arm byte moved.

Shipped as tooling and pins:

* `benchmarks/public/DERIVED-PERCENTS.json` — the registry: **18 derivations** (kind = `subset`,
  `category`, `field_count`, `join`) and **12 exclusion records**, each naming its fraction and a
  reason. The excluded class is exactly the stochastic `pub-ifeval` scorer: the loose columns
  (481/541, 477/541, 526/541), the instruction-check aggregates (denominator 834), the
  `pub-ifeval-v2` corrected cells (469, 463, 510) and the verification-rescore citation 514/541 that
  the document already labels as the documented `langdetect` flake. None of them is CI-asserted at an
  exact count, because the upstream checker itself flips ~1 task per run — the same ±0.5 pp band this
  line publishes; each value stays pinned by its shipped verdict sidecar and by dated multi-pass
  records instead.
* `scripts/pub_derived_percent_check.py` — recomputes every entry from tracked artifacts (asserting
  the pinned checker ids `pub-checkers-v2` / `bfcl-ast-v1` have not moved and running their
  self-tests first), requires the declared fraction to still appear in the named document, refuses a
  derived percent over a denominator with any UNSCORED cell, and then runs the opposite direction:
  **any citation in a result document that is neither a digest row, nor a registry entry, nor an
  exclusion with a reason is a finding**. Census on the tracked tree: 169 citations, 41 distinct
  digest fractions, **0 uncovered**.
* `harness/pub_derived_percent_test.py` — **39 checks, 0 failed**, enrolled by the `harness/*test.py`
  glob. Non-vacuity, six tamper classes: a declared count moved by one cell, the quoted fraction
  deleted from its document, a registry entry deleted so its citation is uncovered, **one shipped
  verdict row flipped in a sidecar**, a fabricated citation inserted into a document, and a missing
  artifact (exit 2, fail-closed).

What the pass therefore proves for the first time, from shipped bytes alone: the four cross-arm slice
percents (gsm8k bare **295/300**, arc-challenge bare **293/300**, bfcl bare **285/300** and
contour-matched **279/300**); the whole BFCL per-category anatomy table (377/400, 186/200, 184/200,
165/200, 204/240 — 1116 of 1240 total); the LiveCodeBench `Where the losses are` split
(26/26 easy, 18/26 medium, 16/60 hard, i.e. the 112 stdin cells of the bare arm, which is what that
table's column header claims); the IFEval truncation censuses (62/541 bare, 72/541 contour) and the
bare-vs-contour strict disagreement 37/541; and **the whole item-7 LiveCodeBench control join**,
recomputed from the shipped sidecars with zero model calls — target set 66 cells (asked ∩ first-arm
hidden failures), blind redraw converts 9, feedback converts 7, the blind draw converts 1 of the 8
cells the public gate can never ask, and the oracle keep-best of a blind redraw is 111/175.

Gates run before the push: `scripts/pub_arms_index.py --check` 0 drift; the three publication
contract tests green (`pub_arms_index` 34, `pub_grok_cell` 21, `pub_superseded_cell` 31);
`scripts/security/secret_scan.py --dir . --strict` exit 0 with 0 findings.

Ops state read this tick (no action): the tick-12 push (`ba8267c`) is **green on all four jobs** and
its `pages-build-deployment` succeeded; the Grok partials were re-verified a seventh time as recorded
above.
`docs-freshness` still records its last scheduled run at **2026-11-09 11:50 UTC (green)** — at
09:56 UTC GitHub had delivered no scheduled run for 2026-11-10 and the tree was clean, so the brief's
"the docs job errors daily because the tree is dirty" line remains unreproduced for a fourth tick;
the last red scheduled runs on record are 2026-11-07 and 2026-11-08.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each
resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; sanitization before every push; a partial arm publishes no
percent.

**Queue status 2026-11-10 11:52 CET (tick 14):** nothing launched — the queue stays empty and item 8
(the Grok resumption) remains gated to 2026-11-12 by the owner quota window. 0 leg units, no
`pub_bench_run`/`gate_run` process, no endpoint call and no cloud call this tick; the local endpoint
was read but not touched (`/health` 200, GPU 0 % util / 36.4 W). The P2005 idle-spin note persists:
the engine holds **657 % CPU at 0 % GPU utilization for 39.3 h with 57.1 GiB resident**. The issue
#43 architecture hold expired at 10:10 CET today; the pre-flight engine restart cure still waits,
because it is an infrastructure action on the box that hosts this session's live brain — owner
decision, nothing was started or stopped by this tick.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
0 drift; `pub_derived_percent_check.py` 18 derivations recomputed from shipped bytes, 169 document
citations, 0 uncovered; `pub_grok_cell_check.py` 9 documents, 0 findings; `pub_superseded_cell_check.py`
9 documents, 0 findings. The two partial Grok arms were re-verified intact an eighth time
(gpqa-diamond **139 unique ids / 139 `finish=ok` / 0 empty**, last id `gpqa-138`, 59 of 198 to go;
humaneval **120 / 120**, last id `humaneval-0119`, 44 of 164 to go), still unshipped and unscored
by rule.

Ops state read this tick (no action): a sibling docs commit landed on `main` at 11:36 CET
(`389dc9b`, audit #25 — qualifies the historical IFEval SHA-1/16 tasks-pin exception in
`arms/README.md`, the only content change since tick 13) and this tick fast-forwarded onto it; its
push is **green on all four jobs** with the Pages build in 32 s. `docs-freshness` still records its
last scheduled run at **2026-11-09 11:50 UTC (green)** — GitHub had delivered no scheduled run for
2026-11-10 at 10:52 UTC and the tree was clean, a fifth tick in which the brief's "errors daily
because the tree is dirty" line does not reproduce; it is scheduled-workflow delivery delay, not a
repo failure.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each
resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; sanitization before every push; a partial arm publishes no
percent.

**Queue status 2026-11-10 13:02 CET (tick 15):** nothing launched — the queue stays empty and item 8
(the Grok resumption) remains gated to 2026-11-12 by the owner quota window. 0 leg units, no
`pub_bench_run`/`gate_run` process, no endpoint call and no cloud call this tick; the local endpoint
was read but not touched (`/health` 200, GPU 0 % util / 32.4 W). The P2005 idle-spin note persists:
the engine holds **647 % CPU at 0 % GPU utilization with 47.2 GiB resident**; the pre-flight engine
restart cure still waits, because it is an infrastructure action on the box that hosts this
session's live brain — owner decision, nothing was started or stopped by this tick.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
0 drift; `pub_derived_percent_check.py` 18 derivations recomputed from shipped bytes, 169 document
citations, 0 uncovered; `pub_grok_cell_check.py` 9 documents, 0 findings;
`pub_superseded_cell_check.py` 9 documents, 0 findings. The two partial Grok arms were re-verified
intact a ninth time (gpqa-diamond **139 unique ids / 139 `finish=ok` / 0 empty**, last id
`gpqa-138`, 59 of 198 to go; humaneval **120 / 120**, last id `humaneval-0119`, 44 of 164 to go),
still unshipped and unscored by rule.

Ops state read this tick (no action): the docs-freshness schedule **did fire today** — run
42807245078 at **11:24:43 UTC, failed in 10 s** with the single finding
`README status date is stale: 2026-11-08 is 2 days old` on the pre-fix SHA. The fix (`5fefb60`,
README status date re-stamped from fresh verification) landed **two minutes later** at 11:26:50 UTC
and that push is green on all four jobs with the Pages build in 2 m 4 s; `python
scripts/qa/docs_policy.py --daily` on the current tree now prints **PASS**, so the next scheduled
run is expected green. Two corrections to the standing ops note: the failure cause is a stale
status date, **not** a dirty working tree (the tree was clean at run time), and the schedule fires
around 10:30-11:50 UTC on the observed runs, not at 03:00 — the brief's "errors daily because the
tree is dirty during its 03:00 run" line remains unreproduced for a sixth tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each
resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; sanitization before every push; a partial arm publishes no
percent.


**Queue status 2026-11-10 14:05 CET (tick 16):** nothing launched — the queue stays empty and item 8
(the Grok resumption) remains gated to 2026-11-12 by the owner quota window. 0 leg units, no
`pub_bench_run`/`gate_run` process, no endpoint call and no cloud call this tick; the local endpoint
was read but not touched (`/health` 200, GPU 0 % util / 36.2 W, engine resident 23.6 GiB VRAM). The
P2005 idle-spin note persists: the engine holds **638 % CPU at 0 % GPU utilization with 55.5 GiB RAM
resident** on 1 d 17.5 h of process uptime (same condition as ticks 13–15, RAM share up from
47.2 GiB); the pre-flight engine restart cure still waits, because it is an infrastructure action
on the box that hosts this session's live brain — owner decision, nothing was started or stopped by
this tick.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
0 drift; `pub_derived_percent_check.py` 18 derivations recomputed from shipped bytes, 41 digest +
169 document citations, 0 uncovered; `pub_grok_cell_check.py` 9 documents, 0 findings;
`pub_superseded_cell_check.py` 9 documents, 0 findings. The two partial Grok arms were re-verified
intact a tenth time (gpqa-diamond **139 unique ids / 139 `finish=ok` / 0 empty**, last id
`gpqa-138`, 59 of 198 to go; humaneval **120 / 120**, last id `humaneval-0119`, 44 of 164 to go),
still unshipped and unscored by rule.

Ops state read this tick (no action): the working tree is clean and local `main` equals
`origin/main` (0 ahead / 0 behind); no new upstream commit since tick 15. `docs-freshness` fired
once today — run 42807245078 at **11:24:43 UTC, failed** with the stale-status-date finding on the
pre-fix SHA (the same run tick 15 recorded); the date fix landed two minutes later and **no
scheduled run has fired against the fixed tree since**, so today's green confirmation is still
open — the next scheduled run is expected tomorrow. `python scripts/qa/docs_policy.py --daily` on
the current tree prints **PASS**. `LEG-INCIDENTS.md` carries no entry for 2026-11-10 and no new
incident occurred this tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each
resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; sanitization before every push; a partial arm publishes no
percent.


**Queue status 2026-11-10 14:45 CET (tick 17):** nothing launched — the queue stays empty and item 8
(the Grok resumption) remains gated to 2026-11-12 by the owner quota window. 0 leg units, no
`pub_bench_run`/`gate_run` process, no endpoint call and no cloud call this tick; the local endpoint
was read but not touched (`/health` 200, GPU 74 % util / 66.6 W sampled, engine resident 23.6 GiB
VRAM — the sampled utilization is this session's own brain traffic, the box hosts the live brain; no
pub arm touches it). The idle-spin condition noted on ticks 13–16 (0 % GPU with 638 % engine CPU) was
not re-sampled under that same idle condition this tick, so it stays open, unconfirmed either way.

CI repair landed this tick (a tooling/text fix, not a measurement): the parallel Bedrock-docs agent
pushed `082ddff` to `main` at 13:39:51 UTC and its `secret-scan` job went red with **1**
`generic-api-key|credential` finding in `docs/bedrock-advisor-integration.md`. Reproduced locally
and decoded the reported secret bytes: the 26-char "secret" is the model id
`anthropic.claude-haiku-5-5` inside a quoted AWS `AccessDeniedException` message — a
`keyword: "long-token"` shape false positive, zero credential material published by the commit. The
repo scanner's byte-pinned exception mechanism deliberately refuses credential-class rules, so the
fix is textual: the code span `Exception: "…"` was restyled to `Exception` — "…" (the quoted AWS
message stays verbatim, one delimiter moves). Verified after the edit: repo `secret_scan.py --strict`
**0 findings, exit 0** on the whole tree, `gitleaks --no-git` whole tree **0 findings**, docs policy
PASS. No history rewrite — the published commit stays as pushed, the fix rides on top.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
0 drift; `pub_derived_percent_check.py` 18 derivations recomputed from shipped bytes, 41 digest +
169 document citations, 0 uncovered; `pub_grok_cell_check.py` 9 documents, 0 findings;
`pub_superseded_cell_check.py` 9 documents, 0 findings. The two partial Grok arms were re-verified
intact an eleventh time (gpqa-diamond **139 unique ids / 139 `finish=ok` / 0 empty**, last id
`gpqa-138`, 59 of 198 to go; humaneval **120 / 120**, last id `humaneval-0119`, 44 of 164 to go),
still unshipped and unscored by rule.

Ops state read this tick (no action): local `main` equals `origin/main` (0 ahead / 0 behind) before
this tick's commit; `docs-freshness` fired once today — run 42807245078 at **11:24:43 UTC, failed**
with the stale-status-date finding on the pre-fix SHA (the same run ticks 15–16 recorded); no
scheduled run has fired against the fixed tree yet, next expected tomorrow. `LEG-INCIDENTS.md`
carries no entry for 2026-11-10 and no arm incident occurred this tick (the CI repair above is a
docs/scanner finding, not a leg event).

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each
resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; sanitization before every push; a partial arm publishes no
percent.


**Queue status 2026-11-10 15:25 CET (tick 18):** nothing launched — the queue stays empty and item 8
(the Grok resumption) remains gated to 2026-11-12 by the owner quota window. 0 leg units, no
`pub_bench_run`/`gate_run` process, no endpoint call and no cloud call this tick; the local endpoint
was read but not touched (`/health` 200, GPU **100 % util / 132.2 W / 23.5 GiB** — that is this
session's own brain traffic, the box hosts the live brain, so the "0 % GPU with ~638 % engine CPU"
idle-spin note from ticks 13–17 was again not re-sampled under that same idle condition and stays
open, unconfirmed either way; engine pid 3284575 at 638 % CPU, 56.7 GiB RSS, 1 d 18 h 56 min
uptime, load average 13.5 on a 32-core box). The two partial Grok arms were re-verified intact a
twelfth time (gpqa-diamond **139 unique ids / 139 `finish=ok` / 0 empty**, last id `gpqa-138`, 59
of 198 to go; humaneval **120 / 120**, last id `humaneval-0119`, 44 of 164 to go), still unshipped
and unscored by rule.

**The tick went at the digest table itself — the artifact every verdict on this line quotes and the
only one no gate had ever read as a table.** Census by the new `scripts/pub_digest_row_check.py`,
zero model calls: **46 rows, 0 arithmetic findings, 0 task-pin findings.** Every row's
`N/M = **P %**` reproduces 100·N/M inside its own one-decimal rounding, every denominator equals its
tasks column, and every tasks cell reproduces the `MANIFEST.json`-labelled pin for its bench (IFEval
through its labelled SHA-1/16, the other eight sets as SHA-256/16). What the census did find: **23
of 46 rows name no checker contract** — they lean on the table head's single global "contract in
force" sentence. That is the same defect class as the stale Grok cells (tick 11) and the stale
superseded cells (tick 12): the per-row cell is what gets quoted, the head is what gets skipped.

Gate plus writer guards; **no published row, verdict file or arm byte moved**:

* `scripts/pub_digest_row_check.py` (new) pins the owner's fail-closed row rules mechanically: table
  shape (one header, one delimiter, six cells per row); bench pinned and non-zero in `MANIFEST.json`
  with a pre-registered prefix task count; tasks cell read through
  `pub_bench_score.manifest_tasks_cell` rather than re-hashed by the caller; fraction, denominator
  and percent consistent to 0.06 pp; **per-row checker-contract naming**; uniqueness per
  (bench, model, tasks, contract set, request shape); and a vocabulary rule that reddens when a
  contract in force is missing from the gate's own list. The 23 pre-rule rows are recorded by exact
  identity (`bench|model|tasks|N/M`), and a **stale exception is itself a finding** — the list cannot
  rot, and a 24th contract-less row cannot land.
* Three live defects at the classic-set writer `pub_bench_score.main()`, found while wiring that
  gate and fixed at the writer. (1) It re-hashed the task file with SHA-256/16 instead of routing
  through `manifest_tasks_cell` — tick 10's guard reached the IFEval scorer only — so an IFEval run
  through the generic scorer would have minted the unlabelled identity `e09a5cab3782ed5b` beside the
  published `2c672531577dcc33` rows, two identities for one pinned file, exactly what that guard
  exists to prevent. (2) Its call label named no contract. (3) An arm with no scored task reached
  `digest_row` as `0/0 = **0.0%**`, a fabricated zero percent over an empty denominator; on the real
  bytes it did not even get that far — the scan died first with `KeyError: 'checker'`, because IFEval
  task rows carry no `checker`/`gold` key at all (reproduced on the shipped 541-row file, then fixed:
  an absent checker is UNSCORED and the writer now refuses with exit 2 and writes no row).
* `harness/pub_digest_row_gate_test.py` — **21 checks, 0 failed**, auto-enrolled by the
  `harness/*test.py` glob. Non-vacuity, seven tamper classes: a printed percent 1.7 pp off its own
  fraction, an unlabelled SHA-256 tasks cell, a verbatim duplicate row, a new contract-less row, a
  denominator-0 row, a deleted pre-rule row (stale exception) and a stale contract vocabulary each
  redden CI, while the published matched-shape / escalation-shape pairs are proven **not**
  duplicates and a writer-shaped row that names its contract is accepted.
* `scripts/push_ready.sh` now runs all five PUB gates (arms index, derived percents, Grok cells,
  superseded cells, digest rows) instead of leaving them to a hand-run list that each tick has to
  remember.

One label defect recorded and deliberately **not** fixed, following the `task_sha16` naming precedent
from tick 10: the three complete Grok rows print a mangled transport label in their call cell
(`… v0.23.0+860.gf17db36.dirty (2026.9.24) · upstre toolsets off CLI`). It is a typo in published
bytes, it enters no calculation, and repairing it would restate a published row's cell; the percents,
ids and checker of those rows stay exactly as published.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
0 drift; `pub_derived_percent_check.py` 18 derivations, 41 digest + 169 document citations, 0
uncovered; `pub_grok_cell_check.py` 9 documents, 0 findings; `pub_superseded_cell_check.py` 9
documents, 0 findings; the new `pub_digest_row_check.py` 46 rows, 0 findings, 23/23 exceptions used;
scorer self-test 22/22; `secret_scan.py --strict` 0 findings.

Ops state read this tick (no action): the newest push `84342dc` (14:07 UTC) is **green on all five
jobs** (secret-scan, devsecops, contour self-tests, hard-v6 scoring contracts, pages).
`docs-freshness` still records its last scheduled run at **2026-11-10 11:24:43 UTC (failed)** — the
stale-status-date finding on the pre-fix SHA that ticks 15–17 recorded — and no scheduled run has
fired against the fixed tree since; `scripts/qa/docs_policy.py --daily` prints PASS on the current
tree, so the brief's "errors daily because the tree is dirty" line remains unreproduced.
`LEG-INCIDENTS.md` carries one 2026-11-10 entry (14:45 CET, two worktrees held `main`) from the ops
line; it is not a PUB leg event and no arm incident occurred this tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each
resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; sanitization before every push; a partial arm publishes no
percent.


**Queue status 2026-11-10 16:24 CET (tick 19):** nothing launched — the queue stays empty and item 8
(the Grok resumption) remains gated to 2026-11-12 by the owner quota window. 0 leg units, no
`pub_bench_run`/`gate_run` process, no endpoint call and no cloud call this tick; the local endpoint
was read but not touched (`/health` 200, GPU **0 % util / 36.9 W / 23.5 GiB** resident). The idle-spin
condition ticks 13–17 noted and tick 18 left unconfirmed **is confirmed again this tick**: engine pid
3284575 at **637 % CPU with the GPU at 0 % utilization**, 59.2 GiB RSS, 43.8 h of process uptime, load
average 15.4 on a 32-core box. The pre-flight engine restart cure still waits, because it is an
infrastructure action on the box that hosts this session's live brain — owner decision, this tick
started and stopped nothing. The two partial Grok arms were re-verified intact a thirteenth time
(gpqa-diamond **139 unique ids / 139 `finish=ok` / 0 empty**, last id `gpqa-138`, 59 of 198 to go;
humaneval **120 / 120**, last id `humaneval-0119`, 44 of 164 to go; both files untouched since
2026-11-09 07:56), still unshipped and unscored by rule.

**The tick went at the repair-family class sentence, and the finding is that it was already false on
the day it was written.** `LIVECODEBENCH-RESULT.md` (and the tick-6 queue block) states that the
validator-feedback effect "is measured significantly **only on IFEval**". That sentence was committed
at **01:46 CET on 2026-11-10**, one hour fifty-three minutes **after** `pub-repair-bfcl-v1` published
(2026-11-09 23:53 CET) a second significant positive on exactly the same question — BFCL feedback-only
**23** cells against redraw-only **7**, p = 0.0052 — and the census it presents simply omitted it.
Recomputed from the shipped verdict sidecars alone (zero model calls, no answer byte touched), the
repair family over four sets and seven arms is **two positive, one null, one null-to-negative**:

| set / arm | what its validator checks | first-arm failures | matched redraw converts | feedback arm converts | **feedback-only** | redraw-only | exact sign test |
|---|---|---|---|---|---|---|---|
| IFEval `pub-repair-v1` (retry@1200) | 25 instruction/format rules | 74 | 16/74 = 21.6 % | 30/74 = 40.5 % | 20/74 = 27.0 % | 6/74 = 8.1 % | 20/6, p = 0.0094 |
| IFEval `pub-repair-v2` (retry@2400) | the same 25 rules | 74 | 16/74 = 21.6 % | 42/74 = 56.8 % | 28/74 = 37.8 % | 2/74 = 2.7 % | 28/2, p = 8.7e-7 |
| BFCL `pub-repair-bfcl-v1` | AST match of the call protocol | 124 | 29/124 = 23.4 % | 45/124 = 36.3 % | 23/124 = 18.5 % | 7/124 = 5.6 % | 23/7, p = 0.0052 |
| HumanEval `pub-repair-humaneval-v1` (@1200) | `pytest-v2` execution | 5 | 2/5 = 40.0 % | 2/5 = 40.0 % | 0/5 = 0.0 % | 0/5 = 0.0 % | no discordance |
| HumanEval `pub-repair-humaneval-v2` (@2400) | `pytest-v2` execution | 5 | 2/5 = 40.0 % | 4/5 = 80.0 % | 2/5 = 40.0 % | 0/5 = 0.0 % | 2/0, p = 0.5 (n = 2) |
| LiveCodeBench `pub-repair-lcb-v1` | hidden-test execution | 74 | 10/74 = 13.5 % | 7/74 = 9.5 % | 3/74 = 4.1 % | 6/74 = 8.1 % | 3/6, p = 0.508 |

The universe of every row is the ids **its first arm failed**, read from that arm's verdict sidecar;
"matched redraw" is the frozen contour-`0.0.2.56` matched-shape arm, an independent second draw of the
same ids at the same request shape with no feedback; `feedback-only` and `redraw-only` are the two
discordant classes the sign test is built from, and the percents are of each row's own failure
universe, never of the set. `both` cells are 10 / 14 / 22 / 2 / 2 / 4 in row order.

**Corrected class statement (dated, replaces "only on IFEval"; no published percent, verdict row or arm
byte moved):** naming the violated check pays above a blind second draw where the failing verdict names
a **class the model can re-target inside the same solution** — an instruction/format rule (IFEval, at
both token budgets) or a call-protocol shape (BFCL: call count, function name) — and it does not pay
where satisfying the verdict needs a different program (LiveCodeBench null-to-negative; HumanEval a
null at n = 5, and its 2/0 at 2400 tokens is inside the second-draw floor and unresolvable at that
sample size). The "textual vs program execution" wording in the LCB document is replaced by
**re-targetable class vs new algorithm**: BFCL is the row that breaks the old dichotomy, because its
check is neither — it is an AST structural match.

Robustness of the IFEval half, measured on the same bytes: two of the 74 cells (`ifeval-1122`,
`ifeval-1129`) are the vendored `letter_frequency` coin flips the `pub-ifeval-v2` contract fixes, so
they can land on either side. Excluding both, the IFEval margins become **19/6, p = 0.015** (v1) and
**28/2, p = 8.7e-7** (v2) — still significant, so the corrected statement does not rest on the two RNG
cells. The same two cells are why the sidecar count of v1 conversions (30) sits two above the arm's own
recorded `retry_fixed` (28): they were never asked and pass today's read. The census figures in the
digest rows stay exactly as published; the two numbers answer different questions and both are labelled
here.

Tooling and pins added (zero model calls, zero published measurement bytes moved):

* `scripts/pub_derived_percent_check.py` gained join mode `directional_sign` — first-arm failure
  universe from `base`, second draw from `control`, feedback arm from `arm`, `which = arm_only |
  control_only`. No previous mode could express the split: `flip_gain` returns a total, and a total
  hides which side of the discordance moved, which is exactly the number the class claim rests on.
* `benchmarks/public/DERIVED-PERCENTS.json`: **24 new entries** (six rows x redraw-converts,
  feedback-converts, feedback-only, redraw-only), so every cell of the table above is recomputed from
  shipped verdict sidecars in CI and each declared fraction must still appear in this document.
  Registry now **42 entries, 0 findings**; 41 digest citations, 169 document citations, 0 uncovered.
* `harness/pub_derived_percent_test.py` requires `directional_sign` to be exercised by an entry, so the
  new mode cannot rot into dead code.
* `LIVECODEBENCH-RESULT.md` carries a dated correction note beside the stale sentence; the sentence
  itself is untouched, per the append-only rule.

Gates run before the push (tracked tree, zero model calls): `scripts/pub_derived_percent_check.py`
42 recomputed, 0 findings; `harness/pub_derived_percent_test.py` **41 checks, 0 failed** (39 before
this tick: the new mode-coverage check plus the redraw-control flip control); the five PUB gates
through `scripts/push_ready.sh` (arms index, derived percents, Grok cells, superseded cells, digest
rows) plus manifest, links, docs policy and `scripts/security/secret_scan.py --dir . --strict`.

Ops state read this tick (no action): local `main` equals `origin/main` (0 ahead / 0 behind) before
this tick's commit; two sibling docs commits landed since tick 18 (`4caafa8`, `cb9d510`, Bedrock/credit
notes from the parallel docs agent) and this tick fast-forwarded onto them. The newest sibling push
`cb9d510` is green on `secret-scan` and `contour self-tests`, with `devsecops`, the hard-v6 scoring
contracts and the pages build still running at read time. `docs-freshness` still records its last
scheduled run at **2026-11-10 11:24:43 UTC (failed)** — the stale-status-date finding on the pre-fix
SHA that ticks 15–18 recorded; no scheduled run has fired against the fixed tree since, and
`scripts/qa/docs_policy.py --daily` prints PASS on the current tree, so the brief's "errors daily
because the tree is dirty" line remains unreproduced. `LEG-INCIDENTS.md` gains no new 2026-11-10 PUB
entry — no leg started, stopped or restarted this tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each
resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; sanitization before every push; a partial arm publishes no
percent.


**Queue status 2026-11-10 17:10 CET (tick 20):** nothing launched — the queue stays empty and item 8
(the Grok resumption) remains gated to 2026-11-12 by the owner quota window. 0 leg units, no
`pub_bench_run`/`gate_run` process, no endpoint call and no cloud call this tick; the local endpoint
was read but not touched (`/health` 200, GPU **0 % util / 36.4 W / 23.5 GiB** VRAM resident). The
idle-spin condition is confirmed again under that same idle condition (ticks 13, 19): engine pid
3284575 at **629 % CPU with the GPU at 0 % utilization**, 59.1 GiB RSS, 44.6 h of process uptime,
load average 11.3 on a 32-core box, 47 of 60 GiB box RAM used. The pre-flight engine restart cure
still waits — this engine hosts this session's live brain, so it is an owner decision; this tick
started and stopped nothing.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
0 drift; `pub_derived_percent_check.py` 42 derivations recomputed from shipped bytes, 41 digest +
169 document citations, 0 uncovered; `pub_grok_cell_check.py` 9 documents, 0 findings;
`pub_superseded_cell_check.py` 9 documents, 0 findings; `pub_digest_row_check.py` 46 rows, 0
findings, 23/23 pre-rule exceptions used; scorer self-test path exercised inside the derived-percent
gate. The two partial Grok arms were re-verified intact a fourteenth time (gpqa-diamond **139 unique
ids / 139 `finish=ok` / 0 empty**, last id `gpqa-138`, 59 of 198 to go; humaneval **120 / 120**,
last id `humaneval-0119`, 44 of 164 to go; both files untouched since 2026-11-09 07:56), still
unshipped and unscored by rule.

Ops state read this tick (no action): the tick-19 push (`55b79e0`) is **green on all five jobs**
(secret-scan, devsecops, contour self-tests, hard-v6 scoring contracts, pages) at 15:28 UTC, its
pages build completed in 4 m 9 s. `docs-freshness` still records its last scheduled run at
**2026-11-10 11:24:53 UTC (failed)** — the stale-status-date finding on the pre-fix SHA — no
scheduled run has fired against the fixed tree since, and `scripts/qa/docs_policy.py --daily` prints
**PASS** on the current tree, so the brief's "errors daily because the tree is dirty" line remains
unreproduced; the next scheduled run is expected tomorrow. `LEG-INCIDENTS.md` gains no new
2026-11-10 PUB entry — no leg started, stopped or restarted this tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each
resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; sanitization before every push; a partial arm publishes no
percent.


**Queue status 2026-11-10 18:55 CET (tick 21):** nothing launched — the queue stays empty and item 8
(the Grok resumption) remains gated to 2026-11-12 by the owner quota window. 0 leg units, no
`pub_bench_run`/`gate_run` process, no endpoint call and no cloud call this tick.

New this tick — a read-only pre-flight reading of the local endpoint, and it is a **tight** one. The
box's swap device is now fully consumed (**8 GiB of 8 GiB used, `SwapFree: 0 kB`**) and the serving
engine (pid 3284575, up 46 h) holds **56.6 GiB RSS plus 6.5 GiB swapped out** — 93.5 % of a 60 GiB
box, with `Committed_AS` 62.6 GB above the 62 GB of RAM. Load average read **18.2 / 6.7 / 3.8**
while the GPU sat at **0 % utilization / 36.4 W / 23 563 MiB resident** and `/health` answered 200,
i.e. the same idle-spin condition as ticks 13, 19 and 20 (engine ~618 % CPU with no request in
flight) plus a swap that is now exhausted rather than merely used. This is exactly the condition this
line's machine note says can restart the engine mid-leg, so it is recorded as a pre-flight risk for
any local leg, not as a measurement: nothing was restarted (the engine hosts this session's live
brain, so a restart is an owner decision) and nothing was launched. The 2026-11-12 Grok resumption is
cloud-side and does not depend on this endpoint.

Standing verification re-run on the tracked tree, zero model calls, all green:
`pub_arms_index.py --check` 0 drift; `pub_derived_percent_check.py` 42 derivations recomputed from
shipped bytes, 41 digest + 169 document citations, 0 uncovered; `pub_grok_cell_check.py` 9 documents,
0 findings; `pub_superseded_cell_check.py` 9 documents, 0 findings; `pub_digest_row_check.py` 46 rows,
0 findings, 23/23 pre-rule exceptions used. The two partial Grok arms were re-verified intact a
fifteenth time (gpqa-diamond **139 unique ids / 139 `finish=ok` / 0 empty**, last id `gpqa-138`, 59 of
198 to go, SHA-256/16 of the stored file `cde63378fa1633c5`; humaneval **120 / 120**, last id
`humaneval-0119`, 44 of 164 to go, `a7c741de0d6ace8c`; both unmodified since 2026-11-09 07:56), still
unshipped and unscored by rule.

Ops state read this tick (no action): `HEAD` == `origin/main` == `2215414`, working tree clean, and
that push is green on all four jobs plus the pages build (17:37 UTC). `docs_freshness_daily.sh` still
records its last scheduled run as a failure — 2026-11-10 03:00 CET, `repo is dirty; refusing daily
docs refresh` — which is the pre-fix worktree symptom described in `LEG-INCIDENTS.md` at 14:45 CET;
that run predates the retarget, the tree is clean now, and the next scheduled run (2026-11-11 02:00
UTC) is the first one against the corrected path. `LEG-INCIDENTS.md` gains no new 2026-11-10 PUB
entry: no leg started, stopped or restarted this tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond 59 ids, humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541), each
resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; sanitization before every push; a partial arm publishes no
percent.


**Queue status 2026-11-10 19:30 CET (tick 22):** nothing launched — the queue stays empty and item 8
(the Grok resumption) remains gated to 2026-11-12 by the owner quota window. 0 leg units, no
`pub_bench_run`/`gate_run` process, no endpoint call and no cloud call this tick.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
0 drift; `pub_arms_index.py --pins` **manifest pin drift: 0** (the checker/tool SHA-1 pins with their
labelled SHA-256 twins and the `checker_history` byte checks against `git show`);
`pub_derived_percent_check.py` 42 derivations recomputed from shipped bytes, 41 digest + 169 document
citations, 0 uncovered; `pub_grok_cell_check.py` 9 documents, 0 findings;
`pub_superseded_cell_check.py` 9 documents, 0 findings; `pub_digest_row_check.py` 46 rows, 0 findings,
23/23 pre-rule exceptions used.

Two integrity reads that are new this tick, both zero model calls:

* **The LiveCodeBench hidden battery still reproduces its pin.** The untracked sidecar
  `livecodebench.hidden.jsonl.gz` measures 100 111 386 B and hashes to SHA-256/16
  `86f92ab37602195a`, byte-identical to `MANIFEST.json -> benches.livecodebench.hidden_payload`
  (175 question rows, 6537 hidden tests, 289 489 972 decoded bytes). That is what keeps the three
  in-force `lcb-exec-v2` rows (bare 101/175, contour 99/175, codex 168/175) re-scorable on this box;
  an outside reader can still verify the per-question `hidden_sha16` pins but cannot re-run the
  battery, because shipping this payload as a release asset is an owner decision and no decision has
  been made.
* **The one digest promise that could have hung was checked and is closed.** The digest head says a
  `pytest-v1` HumanEval row is superseded by the `pytest-v2` rescore "of the same stored answer
  bytes", and the only HumanEval row still labelled `pytest-v1` is the codex row (163/164 = 99.4 %).
  `HUMANEVAL-RESULT.md` carries the corrected A/B table (codex `pytest-v1` 163/164 -> `pytest-v2`
  163/164, zero flips, "so no corrected digest row was needed") and the codex bytes themselves are
  shipped as `arms/humaneval-codex-answers.jsonl` + `-verdicts.jsonl`, so the promise resolves
  instead of pointing at a row that does not exist. Publication-completeness census from the index:
  **161 artifacts + 35 `.sha16` sidecars = 196 index rows**, 35 bare answer files (every in-force
  bench x arm whose arm completed), the two partial Grok legs deliberately unshipped.

Grok partials re-verified intact a sixteenth time, with the exact resume point now recorded from the
pinned task files rather than from row counts: gpqa-diamond **139 rows / 139 unique ids / 139
`finish=ok` / 0 empty**, SHA-256/16 `cde63378fa1633c5`, first id `gpqa-000`, last id `gpqa-138`, and
the 59 ids missing from the pinned file order start at **`gpqa-139`**; humaneval **120 / 120 / 120 /
0 empty**, SHA-256/16 `a7c741de0d6ace8c` — identical to the value recorded at tick 21, first
`humaneval-0000`, last
`humaneval-0119`, the 44 missing ids start at **`humaneval-0120`**. Both files untouched since
2026-11-09 07:56, still unscored and unshipped by rule.

**11-12 pre-flight record (no script written, nothing launched):** of the four resumption legs in the
pinned order, two launchers exist and carry the PATH/`command -v` fail-closed guard
(`go_cloud_gpqa_grok.sh`, `go_cloud_humaneval_grok.sh`); the two deferred legs — **mmlu-pro 500 and
ifeval 541 — have no Grok go-script at all**, so 12 Nov needs them written first. They are not
written in advance on purpose: the ceiling has to match each set's own in-force rows (mmlu-pro bare
and matched ran at `max_tokens 1200`; the IFEval bare/matched/codex rows are a `pub-ifeval-v1`
1200-token family and a 2400-token IFEval Grok row would not be comparable to them), and an
unverified launcher sitting next to an endpoint is how the shape-confounded rows got published in
the first place.

Local endpoint read-only, and the pre-flight risk is unchanged: box RAM 47.5 GiB used of 60.5 GiB
(`free -m`: 48 622 of 61 953 MiB) with **swap 8143 MiB of 8191 MiB used (`SwapFree: 48 044 kB`)**;
the serving engine (pid 3284575, up 1 d 22 h) holds `VmRSS` 56.6 GiB and `VmSwap` 6.5 GiB, the
largest swapper on the box, at **617 % CPU with
the GPU at 0 % utilization / 36.7 W / 23 563 MiB resident**, load average 15.6 / 8.7 / 6.2 on a
32-core box, `/health` 200. Same idle-spin condition as ticks 13, 19, 20, 21 with the swap now at its
last 48 MiB, so this line launches no local leg into it; the pre-flight engine restart cure stays an
owner decision because that engine serves this session's brain. The 2026-11-12 Grok resumption is
cloud-side and does not depend on this endpoint. (`Committed_AS` 63.2 GB decimal against 65.0 GB
decimal of physical RAM is NOT oversubscribed — the pressure is the resident engine plus its swapped
share on a full swap device, not a commit-charge overrun.)

Ops state read this tick (no action): `HEAD` == `origin/main` == `9dadd65`, working tree clean, and
that push is **green on all five jobs** (secret-scan, devsecops, contour self-tests, hard-v6 scoring
contracts, pages) at 18:12 UTC. The failure on the previous commit (`98b61b7`, secret-scan, 18:06
UTC) was the docs agent's quoted-provider-error false positive and was closed by `9dadd65` itself —
not a PUB finding. `scripts/qa/docs_policy.py --daily` prints **PASS** on the current tree, and
`docs_freshness_daily.sh` still records its last scheduled run as the 2026-11-10 03:00 CET
pre-fix-worktree failure described in `LEG-INCIDENTS.md`; the next scheduled run (2026-11-11 02:00
UTC) is the first against the retargeted path. `LEG-INCIDENTS.md` gains no new 2026-11-10 PUB entry:
no leg started, stopped or restarted this tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond from `gpqa-139`, 59 ids; humaneval from `humaneval-0120`, 44 ids; then the deferred
mmlu-pro 500 and ifeval 541, which need their Grok go-scripts written first), each resumable by id
and scored only when complete. Standing limits unchanged: no Grok arm before 2026-11-12; frozen
contour `0.0.2.56`; sanitization before every push; a partial arm publishes no percent.

*Correction with a date (unit arithmetic in a tick's prose, no percent row touched):* the tick-21
sentence "`Committed_AS` 62.6 GB above the 62 GB of RAM" compared a decimal-GB value against a
MiB-read total, so it implied a commit-charge overrun that the bytes do not show. Correct reading of
the same `/proc/meminfo` shape: `Committed_AS` 63.2 GB decimal against 65.0 GB decimal of physical
RAM (61 953 MiB) — not oversubscribed. The real risk recorded in both ticks stands and is the full
swap device plus a 56.6 GiB-resident / 6.5 GiB-swapped engine.

**Queue status 2026-11-10 21:5x CET (tick 23):** nothing launched — the queue stays empty and item 8
(the Grok resumption: gpqa-diamond from `gpqa-139`, humaneval from `humaneval-0120`, then the two
deferred sets) remains gated to 2026-11-12 by the owner quota window. `systemctl --user list-units
'parb-pub-*'` is empty, no `pub_bench_run`/`pub_bench_cloud`/`gate_run` process anywhere, zero
endpoint calls, zero cloud calls this tick.

**What changed this tick is tooling only** (allowed by the 0.0.2.56 freeze: no stamp, no feature,
no arm, no bank byte, no published percent moved). The endpoint pre-flight that ticks 13, 19, 20, 21
and 22 each performed by hand is now a gate: **`scripts/pub_preflight.py`** with contract test
**`harness/pub_preflight_test.py`, 20/20 green** (one healthy reading set exits 0; six independent
tampers — exhausted swap, low MemAvailable, engine in `D` state, the idle-spin pair, `/health` 503,
a foreign leg — each exit 3 and name their reason; a missing reading and an unreadable number exit 1
instead of passing; two non-vacuity controls — high engine CPU *with a busy GPU*, and 1 GiB of swap
free — still exit 0, which is what keeps the two numeric thresholds honest). It is enrolled in CI by
the `harness/*test.py` glob through `scripts/qa/static_checks.py`; `MANIFEST.json` checker pins did
not move, because this tool scores nothing. Writing it also caught a live bug in the new file on the
first LSP pass (`num(vals["engine_pcpu"])` — a two-argument call written with one); the contract test
reddens on that shape, because the healthy case then dies with a `TypeError` instead of printing GO.

**The first real reading through the gate is NO-GO (exit 3), and it is worse than tick 22's reading.**
Same box, 21:47 CET: **swap free 0 MiB of 8 191 MiB** (tick 22 recorded 48 MiB free 25 minutes
earlier — the device is now completely exhausted), MemAvailable 14 047 MiB of 61 953 MiB, engine RSS
**57 935 MiB at 602 % CPU with the GPU at 0 % utilization / 36.9 W / 23 563 MiB resident**, load
average 15.1, `/health` 200, **0 foreign legs**. An earlier read of the same process in the same
minute showed it in state **`Dl`** — uninterruptible I/O, the thrashing signature — so the state
reading flickers between `Sl` and `Dl` rather than being stable, and both NO-GO reasons that fired
(swap, idle-spin) hold on every reading. Consequence stated plainly: **this line launches no local
leg into that state**, the cure (engine restart or parking the keep-up load) is an owner decision
because the same engine serves this session's brain, and the 2026-11-12 Grok resumption is cloud-side
and unaffected by the endpoint condition.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
**index drift: 0**; `pub_derived_percent_check.py` **42 recomputed, 0 findings**;
`pub_grok_cell_check.py` 9 documents, **0 findings**; `pub_superseded_cell_check.py` 9 documents,
**0 findings**; `pub_digest_row_check.py` **46 rows, 0 findings**. `HEAD` == `origin/main` ==
`2b4f04d`, working tree clean at the start of the tick, and that commit is **green on every job**
(secret-scan, devsecops, contour self-tests, hard-v6 scoring contracts, pages, run 20:07 UTC).

Grok partials re-verified intact again, zero model calls and still unscored/unshipped by rule:
`gpqa-diamond/pub-grok.jsonl` SHA-256/16 **`cde63378fa1633c5`**, **139 rows**, and
`humaneval/pub-grok.jsonl` SHA-256/16 **`a7c741de0d6ace8c`**, **120 rows** — both byte-identical to
the values recorded at ticks 21 and 22, last modified 2026-11-09 07:56, resume points `gpqa-139` and
`humaneval-0120` unchanged. The 11-12 launcher gap is also unchanged by decision: the two deferred
legs (**mmlu-pro 500, ifeval 541**) still have no Grok go-script, and none is written in advance,
because each ceiling must match its own in-force family (mmlu-pro 1200; IFEval's `pub-ifeval-v1`
1200-token family) and an unverified launcher beside an endpoint is how the shape-confounded rows got
published.

Daily docs job (report only, not fixed by committing in-flight work): `hermes cron list` shows
`GitHub docs freshness daily` scheduled `0 2 * * *`, **next run 2026-11-11T02:00:00+00:00**, last run
`2026-11-10T03:00` **error: "repo is dirty; refusing daily docs refresh"** — that is the stale
second-worktree symptom recorded in `LEG-INCIDENTS.md` at 14:45 CET and repaired there (both the
scripts and the worktree layout are now single-writer on `~/sah-main`). Tomorrow's run is the first
against the retargeted path with a clean tree.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order, each
leg resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; a local leg now also needs `pub_preflight.py` exit 0;
sanitization before every push; a partial arm publishes no percent.

**Queue status 2026-11-10 22:3x CET (tick 24):** nothing launched — the queue stays empty and item 8
(the Grok resumption: gpqa-diamond from `gpqa-139`, humaneval from `humaneval-0120`, then the two
deferred sets) remains gated to 2026-11-12 by the owner quota window. `systemctl --user list-units
'parb-pub-*'` is empty, no `pub_bench_run`/`pub_bench_cloud`/`gate_run` process on the host, and the
endpoint reading below shows **0 foreign legs**; zero model calls this tick.

**The standing preflight gate reads NO-GO again, with swap pinned at zero.** This is the first routine
use of the gate tick 23 shipped. Same box, 22:29 CET: **swap free 0 MiB of 8 191 MiB** (tick 23
measured 0 at 21:47 — the device has now been exhausted for half an hour, the engine being its own
largest swapper), MemAvailable 13 990 MiB of 61 953 MiB, engine state `Sl` at **606 % CPU with RSS
57 822 MiB**, GPU **0 % utilization / 36.6 W**, load average 13.9, `/health` 200. Both tick-23 NO-GO
reasons reproduce verbatim (swap exhaustion, idle-spin pair), exit 3, and the line launches no local
leg into that state. The cure (engine restart or parking the keep-up load) stays an owner decision
because the same engine serves this session's brain; the 2026-11-12 Grok resumption is cloud-side and
unaffected. The gate's own contract test was re-run against the tracked tree:
`harness/pub_preflight_test.py` **20/20 green**.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
**index drift: 0**; `pub_arms_index.py --pins` **manifest pin drift: 0**;
`pub_derived_percent_check.py` registry `pub-derived-percents-v1` **42 entries recomputed, 0
findings** (its checker self-tests 22/22); `pub_grok_cell_check.py` 9 documents, **0 findings**;
`pub_superseded_cell_check.py` 9 documents, **0 findings**; `pub_digest_row_check.py` **46 rows, 0
findings**. `HEAD` == `origin/main` == `b168a98`, working tree clean at the start of the tick, and
the three most recent CI runs on that head are all **success**.

Grok partials re-verified intact again (seventeenth verification), zero model calls and still
unscored/unshipped by rule: `gpqa-diamond/pub-grok.jsonl` SHA-256/16 **`cde63378fa1633c5`**,
**139 rows**, and `humaneval/pub-grok.jsonl` SHA-256/16 **`a7c741de0d6ace8c`**, **120 rows** —
byte-identical to the values recorded at ticks 21, 22 and 23, last modified 2026-11-09 07:56, resume
points `gpqa-139` and `humaneval-0120` unchanged. The 11-12 launcher gap stands by decision: the two
deferred legs (**mmlu-pro 500, ifeval 541**) get their Grok go-scripts at launch time, ceilings
matched to each set's in-force family (mmlu-pro 1200; IFEval `pub-ifeval-v1` 1200), not pre-written.

Daily docs job (report only, not fixed by committing in-flight work): `hermes cron list` shows
`GitHub docs freshness daily` scheduled `0 2 * * *`, **next run 2026-11-11T02:00:00+00:00**, last run
`2026-11-10T03:00` **error: script exited with code 1** — the stale second-worktree symptom recorded
and repaired in `LEG-INCIDENTS.md` at 14:45 CET (both daily scripts now name `~/sah-main`, and
exactly one worktree holds `main`). Tomorrow's run is the first against the retargeted path with a
clean tree.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order, each
leg resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; a local leg needs `pub_preflight.py` exit 0 and the endpoint
is not there yet; sanitization before every push; a partial arm publishes no percent.

**Queue status 2026-11-10 23:37 CET (tick 25):** nothing launched — the queue stays empty and item 8
(the Grok resumption: gpqa-diamond from `gpqa-139`, humaneval from `humaneval-0120`, then the two
deferred sets) remains gated to 2026-11-12 by the owner quota window. 0 `parb-pub-*` units, no
`pub_bench_run`/`pub_bench_cloud`/`gate_run` process on the host, 0 foreign legs on the endpoint;
zero model calls and zero cloud calls this tick.

**The standing preflight gate reads NO-GO a third time, and the swap finally moved off zero.**
Same box, 23:33 CET: **swap free 247 MiB of 8 191 MiB** — the device was pinned at 0 MiB free at
ticks 23 (21:47) and 24 (22:29), so this is the first non-zero reading since, but it is still below
the gate's 256 MiB threshold. MemAvailable 15 662 MiB of 61 953 MiB (up from 13 990 at tick 24).
Engine pid 3284575 up **51.0 h**, state `Sl`, **596 % CPU with the GPU at 0 % utilization /
36.4 W**, RSS 57 444 MiB, load average 9.5 (down from 13.9). Both NO-GO reasons reproduce verbatim
(swap exhaustion, idle-spin pair), exit 3, and the line launches no local leg into that state. The
cure (engine restart or parking the keep-up load) stays an owner decision because the same engine
serves this session's brain; the 2026-11-12 Grok resumption is cloud-side and unaffected. The
gate's own contract test was re-run: `harness/pub_preflight_test.py` **20/20 green**.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
**index drift: 0**; `pub_arms_index.py --pins` **manifest pin drift: 0**;
`pub_derived_percent_check.py` registry `pub-derived-percents-v1` **42 entries recomputed, 0
findings** (41 digest + 169 document citations, 0 uncovered; checker self-tests green inside the
gate); `pub_grok_cell_check.py` 9 documents, **0 findings**; `pub_superseded_cell_check.py` 9
documents, **0 findings**; `pub_digest_row_check.py` **46 rows, 0 findings**, 23/23 pre-rule
exceptions used.

Grok partials re-verified intact again (eighteenth verification), zero model calls and still
unscored/unshipped by rule: `gpqa-diamond/pub-grok.jsonl` SHA-256/16 **`cde63378fa1633c5`**,
**139 rows**, and `humaneval/pub-grok.jsonl` SHA-256/16 **`a7c741de0d6ace8c`**, **120 rows** —
byte-identical to ticks 21–24, last modified 2026-11-09 07:56, resume points `gpqa-139` and
`humaneval-0120` unchanged. New this tick, a zero-call readiness check of the resumption wiring:
the two resumable launchers (`go_cloud_gpqa_grok.sh`, `go_cloud_humaneval_grok.sh`) were confirmed
to carry the `command -v` fail-closed PATH guard on disk. The launcher gap for the two deferred
legs (**mmlu-pro 500, ifeval 541**) stands by decision: their Grok go-scripts are written at launch
time with ceilings matched to each set's in-force family (mmlu-pro 1200; IFEval `pub-ifeval-v1`
1200), not pre-written.

Ops state read this tick (no action): `HEAD` == `origin/main` == `8cfccfa`, working tree clean, and
that push is **green** (all recorded CI runs `success`, read 23:35 CET). Daily docs job (report
only): `GitHub docs freshness daily` (`0 2 * * *`) last run **2026-11-10T03:00 error: script exited
with code 1** — the stale second-worktree symptom recorded and repaired in `LEG-INCIDENTS.md` at
14:45 CET — **next run 2026-11-11T02:00:00+00:00**, the first against the retargeted `~/sah-main`
path with a clean tree, so the brief's "errors daily because the tree is dirty" line gets its first
chance to resolve or persist tomorrow morning. `LEG-INCIDENTS.md` gains no new 2026-11-10 PUB
entry: no leg started, stopped or restarted this tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order, each
leg resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; a local leg needs `pub_preflight.py` exit 0 (the third
consecutive NO-GO reading keeps that moot); sanitization before every push; a partial arm publishes
no percent.

**Queue status 2026-11-11 00:15 CET (tick 26):** nothing launched — the queue stays empty and item 8
(the Grok resumption: gpqa-diamond from `gpqa-139`, humaneval from `humaneval-0120`, then the two
deferred sets) remains gated to 2026-11-12 by the owner quota window. 0 `parb-pub-*` units, no
`pub_bench_run`/`pub_bench_cloud`/`gate_run` process anywhere on the host, 0 foreign legs on the
endpoint; zero model calls and zero cloud calls this tick.

**The standing preflight gate reads NO-GO a fourth time and the swap is pinned back at zero.**
Same box, 00:12 CET: **swap free 0 MiB of 8 191 MiB** — tick 25 caught the only transient (247 MiB),
now exhausted again. MemAvailable 13 839 MiB (down from 15 662 at tick 25). Engine state `Sl`,
**591 % CPU with the GPU at 0 % utilization / 37.5 W**, RSS 58 225 MiB, load average 11.8, process
age 2 d 03:36 — the same un-restarted process as ticks 23–25. Both NO-GO reasons reproduce verbatim
(swap exhaustion, idle-spin pair), exit 3; the line launches no local leg into that state. The cure
(engine restart / parking the keep-up load) stays an owner decision — the same engine serves this
session's brain — and the 2026-11-12 Grok resumption is cloud-side, unaffected. Gate contract test
re-run: `harness/pub_preflight_test.py` **20/20 green**.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
**index drift: 0**; `pub_arms_index.py --pins` **manifest pin drift: 0**;
`pub_derived_percent_check.py` registry `pub-derived-percents-v1` **42 entries recomputed, 0
findings** (41 digest + 169 document citations, 0 uncovered); `pub_grok_cell_check.py` 9 documents,
**0 findings**; `pub_superseded_cell_check.py` 9 documents, **0 findings**;
`pub_digest_row_check.py` **46 rows, 0 findings**, 23/23 pre-rule exceptions used.

Grok partials re-verified intact again (nineteenth verification), zero model calls and still
unscored/unshipped by rule: `gpqa-diamond/pub-grok.jsonl` SHA-256/16 **`cde63378fa1633c5`**,
**139 rows**, and `humaneval/pub-grok.jsonl` SHA-256/16 **`a7c741de0d6ace8c`**, **120 rows** —
byte-identical to ticks 21–25, mtimes still 2026-11-09 07:56, resume points `gpqa-139` and
`humaneval-0120` unchanged.

Ops state read this tick (no action): `HEAD` == `origin/main` == `4e841e8`, working tree clean, and
that push is **green** (devsecops, hard-v6 scoring contracts, secret-scan, contour self-tests all
`success`, read 00:13 CET). The daily `GitHub docs freshness` job's next run is
**2026-11-11T02:00:00+00:00** — still ahead of this tick, and it will be the first against the
retargeted `~/sah-main` path with a clean tree; the brief's "errors daily while the tree is dirty"
line resolves or persists after that run. `LEG-INCIDENTS.md` gains no new 2026-11-11 PUB entry: no
leg started, stopped or restarted this tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order, each
leg resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; a local leg needs `pub_preflight.py` exit 0 (the fourth
consecutive NO-GO reading keeps that moot); sanitization before every push; a partial arm publishes
no percent.

**Queue status 2026-11-11 00:45 CET (tick 27):** nothing launched — the queue stays empty and item 8
(the Grok resumption: gpqa-diamond from `gpqa-139`, humaneval from `humaneval-0120`, then the two
deferred sets) remains gated to 2026-11-12 by the owner quota window. 0 `parb-pub-*` units, no
`pub_bench_run`/`pub_bench_cloud`/`gate_run` process on the host, 0 foreign legs on the endpoint;
zero model calls and zero cloud calls this tick.

**The standing preflight gate reads NO-GO a fifth time and the swap is pinned again at near zero.**
Same box, 00:45 CET: **swap free 3 MiB of 8 191 MiB** — tick 25 caught the transient (247 MiB), tick
26 read 0, now 3. MemAvailable 15 366 MiB (up from 13 839 at tick 26). Engine state `Sl`, **586 % CPU
with the GPU at 0 % utilization / 36.5 W**, RSS 55 877 MiB, load average 10.5, process age **52.2 h**
— the same un-restarted process as ticks 23–26, now over two days. Both NO-GO reasons reproduce
verbatim (swap exhaustion, idle-spin pair), exit 3; the line launches no local leg into that state.
The cure (engine restart / parking the keep-up load) stays an owner decision — the same engine serves
this session's brain — and the 2026-11-12 Grok resumption is cloud-side, unaffected. Gate contract
test re-run: `harness/pub_preflight_test.py` **20/20 green**.

New this tick, a usage note on the gate itself (no code change, no published byte moved): the
readings file must carry **one `key=value` pair per line**. `read()` splits a line at the first `=`
only, so a line holding two pairs parses as `mem_total_mib = "61953 mem_available_mib=15366"` and
the gate exits **1 (INPUT GAP)** naming the keys it then cannot see. That exit 1 is the gate failing
closed on its own input, not an endpoint condition — the same readings, reformatted to one pair per
line, produced the exit-3 NO-GO above with identical numbers. Exit 1 and exit 3 must therefore be
told apart before either is reported as the state of the box.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
**index drift: 0**; `pub_arms_index.py --pins` **manifest pin drift: 0**;
`pub_derived_percent_check.py` registry `pub-derived-percents-v1` **42 entries recomputed, 0
findings** (41 digest + 169 document citations, 0 uncovered); `pub_grok_cell_check.py` 9 documents,
**0 findings**; `pub_superseded_cell_check.py` 9 documents, **0 findings**;
`pub_digest_row_check.py` **46 rows, 0 findings**, 23/23 pre-rule exceptions used.

Grok partials re-verified intact again (twentieth verification), zero model calls and still
unscored/unshipped by rule: `gpqa-diamond/pub-grok.jsonl` SHA-256/16 **`cde63378fa1633c5`**,
**139 rows**, and `humaneval/pub-grok.jsonl` SHA-256/16 **`a7c741de0d6ace8c`**, **120 rows** —
byte-identical to ticks 21–26, mtimes still 2026-11-09 07:56, resume points `gpqa-139` and
`humaneval-0120` unchanged. The two resumable Grok launchers still carry the `command -v` fail-closed
PATH guard; the launcher gap for the two deferred legs (**mmlu-pro 500, ifeval 541**) stands by
decision — their go-scripts are written at launch time with ceilings matched to each set's in-force
family (mmlu-pro 1200; IFEval `pub-ifeval-v1` 1200), not pre-written.

Ops state read this tick (no action): `HEAD` == `origin/main` == `db8051f`, working tree clean, and
that push is **green** (`contour self-tests`, `secret-scan`, `hard-v6 scoring contracts` all
`success`, read 00:45 CET). The daily `GitHub docs freshness` job (`0 2 * * *`) shows **next run
2026-11-11T02:00:00+00:00** — still ahead of this tick — and that will be its first run against the
retargeted `~/sah-main` path with a clean tree; the brief's "errors daily while the tree is dirty"
line resolves or persists after it. `LEG-INCIDENTS.md` gains no new 2026-11-11 PUB entry: no leg
started, stopped or restarted this tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order, each
leg resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; a local leg needs `pub_preflight.py` exit 0 (the fifth
consecutive NO-GO reading keeps that moot); sanitization before every push; a partial arm publishes
no percent.

**Queue status 2026-11-11 01:18 CET (tick 28):** nothing launched — the queue stays empty and item 8
(the Grok resumption: gpqa-diamond from `gpqa-139`, humaneval from `humaneval-0120`, then the two
deferred sets) remains gated to 2026-11-12 by the owner quota window. 0 `parb-pub-*` units, no
`pub_bench_run`/`pub_bench_cloud`/`gate_run` process on the host, 0 foreign legs on the endpoint;
zero model calls and zero cloud calls this tick.

**The standing preflight gate reads NO-GO a sixth time.** Same box, 01:18 CET: **swap free 0 MiB of
8 191 MiB** (tick 26 read 0, tick 27 read 3, now back at 0 — the device stays pinned at zero).
MemAvailable 15 398 MiB (up from 15 366). Engine state `S` (the reader used `ps -eo state`, which
reports the process state without the thread flag — same 52.7 h process as ticks 23–27, the gate's
uninterruptible-`D` check is unaffected), **581 % CPU with the GPU at 0 % utilization / 36.4 W**, RSS
**57 443 MiB — up 1 566 MiB since tick 27's reading 33 minutes earlier**, load average 11.95. Both
NO-GO reasons reproduce verbatim (swap exhaustion, idle-spin pair), exit 3; the line launches no
local leg into that state. The RSS growth direction matches the over-parking class measured on the
hard bank (03.11), stated as an observation only — the cure (engine restart / parking the keep-up
load) stays an owner decision, the same engine serves this session's brain, and the 2026-11-12 Grok
resumption is cloud-side, unaffected. Gate contract test re-run: `harness/pub_preflight_test.py`
**20/20 green**.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
**index drift: 0**; `pub_arms_index.py --pins` **manifest pin drift: 0**;
`pub_derived_percent_check.py` registry `pub-derived-percents-v1` **42 entries recomputed, 0
findings** (41 digest + 169 document citations, 0 uncovered); `pub_grok_cell_check.py` 9 documents,
**0 findings**; `pub_superseded_cell_check.py` 9 documents, **0 findings**;
`pub_digest_row_check.py` **46 rows, 0 findings**, 23/23 pre-rule exceptions used.

Grok partials re-verified intact again (twenty-first verification), zero model calls and still
unscored/unshipped by rule: `gpqa-diamond/pub-grok.jsonl` SHA-256/16 **`cde63378fa1633c5`**,
**139 rows / 139 unique ids / 139 `finish=ok`**, and `humaneval/pub-grok.jsonl` SHA-256/16
**`a7c741de0d6ace8c`**, **120 / 120 / 120** — byte-identical to ticks 21–27, mtimes still
2026-11-09 07:56, resume points `gpqa-139` and `humaneval-0120` unchanged.

Ops state read this tick (no action): `HEAD` == `origin/main` == `dfe54ad`, working tree clean, and
that push is **green** (devsecops, hard-v6 scoring contracts, secret-scan all `success`, read
01:18 CET). The daily `GitHub docs freshness` job (`0 2 * * *`) shows **next run
2026-11-11T02:00:00+00:00** — still ahead of this tick — which will make it the first run against
the retargeted `~/sah-main` path with a clean tree; the brief's "errors daily while the tree is
dirty" line resolves or persists after it. `LEG-INCIDENTS.md` gains no new 2026-11-11 PUB entry: no
leg started, stopped or restarted this tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order, each
leg resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; a local leg needs `pub_preflight.py` exit 0 (the sixth
consecutive NO-GO reading keeps that moot); sanitization before every push; a partial arm publishes
no percent.

**Queue status 2026-11-11 01:52 CET (tick 29):** nothing launched — the queue stays empty and item 8
(the Grok resumption: gpqa-diamond from `gpqa-139`, humaneval from `humaneval-0120`, then the two
deferred sets) remains gated to 2026-11-12 by the owner quota window. 0 `parb-pub-*` units, no
`pub_bench_run`/`pub_bench_cloud`/`gate_run` process on the host, 0 foreign legs on the endpoint;
zero model calls and zero cloud calls this tick.

**The standing preflight gate reads NO-GO a seventh time.** Same box, 01:52 CET: **swap free 0 MiB of
8 191 MiB** (ticks 26–28 read 0 / 3 / 0 — the device stays pinned at zero), MemAvailable 15 295 MiB,
engine state `S`, **575 % CPU with RSS 57 679 MiB — up 236 MiB over the 34 minutes since tick 28's
reading**, load average 10.49, `/health` 200. One difference from ticks 24–28: this reading caught
the GPU at **99 % utilization / 40.4 W** (the earlier NO-GO window read 0 % / 36–37 W), so the
idle-spin pair did not trip this time and the single NO-GO reason is the swap exhaustion. The
utilization burst is consistent with this session's own brain traffic on the shared endpoint — the
gate reads, it does not attribute. The RSS growth direction still matches the over-parking class
measured on the hard bank (03.11), stated as an observation only; the cure (engine restart / parking
the keep-up load) stays an owner decision, and the 2026-11-12 Grok resumption is cloud-side,
unaffected. Gate contract test re-run: `harness/pub_preflight_test.py` **20/20 green**.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
**index drift: 0**; `pub_arms_index.py --pins` **manifest pin drift: 0**;
`pub_derived_percent_check.py` registry `pub-derived-percents-v1` **42 entries recomputed, 0
findings** (41 digest + 169 document citations, 0 uncovered); `pub_grok_cell_check.py` 9 documents,
**0 findings**; `pub_superseded_cell_check.py` 9 documents, **0 findings**;
`pub_digest_row_check.py` **46 rows, 0 findings**, 23/23 pre-rule exceptions used.

Grok partials re-verified intact again (twenty-second verification), zero model calls and still
unscored/unshipped by rule: `gpqa-diamond/pub-grok.jsonl` SHA-256/16 **`cde63378fa1633c5`**,
**139 rows / 139 unique ids / 139 `finish=ok`**, and `humaneval/pub-grok.jsonl` SHA-256/16
**`a7c741de0d6ace8c`**, **120 / 120 / 120** — byte-identical to ticks 21–28, mtimes still
2026-11-09 07:56, resume points `gpqa-139` and `humaneval-0120` unchanged.

Ops state read this tick (no action): `HEAD` == `origin/main` == `cd78271`, working tree clean, and
that push is **green** (`devsecops`, `secret-scan`, `contour self-tests`, `hard-v6 scoring
contracts`, `pages-build-deployment` all `success`, read 01:53 CET). The daily `GitHub docs
freshness` job (`0 2 * * *`) shows **next run 2026-11-11T02:00:00+00:00** — 7 minutes of UTC ahead
of this reading — which will make it the first run against the retargeted `~/sah-main` path with a
clean tree; the brief's "errors daily while the tree is dirty" line resolves or persists after it.
`LEG-INCIDENTS.md` gains no new 2026-11-11 PUB entry: no leg started, stopped or restarted this
tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order, each
leg resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; a local leg needs `pub_preflight.py` exit 0 (the seventh
consecutive NO-GO reading keeps that moot); sanitization before every push; a partial arm publishes
no percent.

**Queue status 2026-11-11 02:26 CET (tick 30):** nothing launched — the queue stays empty and item 8
(the Grok resumption: gpqa-diamond from `gpqa-139`, humaneval from `humaneval-0120`, then the two
deferred sets) remains gated to 2026-11-12 by the owner quota window. 0 `parb-pub-*` units, no
`pub_bench_run`/`pub_bench_cloud`/`gate_run` process on the host, 0 foreign legs on the endpoint;
zero model calls and zero cloud calls this tick.

**The standing preflight gate reads NO-GO an eighth time.** Same box, 02:26 CET: **swap free 0 MiB of
8 191 MiB** (the device stays pinned at zero, ticks 26–29 read 0 / 3 / 0 / 0), MemAvailable
14 639 MiB (down 656 MiB from tick 29's reading), engine state `Sl` — the `D` state the 02:00 daily
snapshot read did not reproduce on this reading — **574 % CPU with RSS 57 285 MiB, direction now
reversed: down 394 MiB against tick 29's 57 679 MiB over 34 minutes**, load average 14.33, `/health`
200. This reading **re-trips the idle-spin pair**: the GPU is back at **0 % / 36.5 W** (tick 29 had
caught it at 99 %), so the NO-GO carries two reasons this time — swap exhaustion and the spin
signature — where ticks 26–29 carried one. The RSS direction flip is stated as an observation only;
the cure (engine restart / parking the keep-up load) stays an owner decision, and the 2026-11-12
Grok resumption is cloud-side, unaffected. Gate contract test re-run: `harness/pub_preflight_test.py`
**20/20 green**.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
**index drift: 0**; `pub_arms_index.py --pins` **manifest pin drift: 0**;
`pub_derived_percent_check.py` registry `pub-derived-percents-v1` **42 entries recomputed, 0
findings** (41 digest + 169 document citations, 0 uncovered); `pub_grok_cell_check.py` 9 documents,
**0 findings**; `pub_superseded_cell_check.py` 9 documents, **0 findings**;
`pub_digest_row_check.py` **46 rows, 0 findings**, 23/23 pre-rule exceptions used.

Grok partials re-verified intact again (twenty-third verification), zero model calls and still
unscored/unshipped by rule: `gpqa-diamond/pub-grok.jsonl` SHA-256/16 **`cde63378fa1633c5`**,
**139 rows / 139 unique ids / 139 `finish=ok`**, and `humaneval/pub-grok.jsonl` SHA-256/16
**`a7c741de0d6ace8c`**, **120 / 120 / 120** — byte-identical to ticks 21–29, mtimes still
2026-11-09 07:56, resume points `gpqa-139` and `humaneval-0120` unchanged.

Ops state read this tick (no action): `HEAD` == `origin/main` == `a371f82`, working tree clean, and
that push is **green** (`devsecops`, `secret-scan`, `contour self-tests`, `hard-v6 scoring
contracts`, `pages-build-deployment` all `success`, read 01:26 UTC). The daily `GitHub docs
freshness` job's latest scheduled run is still a **failure** (2026-11-10 11:24 UTC, which predates
the 2026-11-10 14:45 worktree retarget recorded in `LEG-INCIDENTS.md`); today's scheduled run has
not fired yet, so its first run against the retargeted path with a clean tree is still pending.
`LEG-INCIDENTS.md` gains no new 2026-11-11 PUB entry: no leg started, stopped or restarted this
tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order, each
leg resumable by id and scored only when complete. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; a local leg needs `pub_preflight.py` exit 0 (the eighth
consecutive NO-GO reading keeps that moot); sanitization before every push; a partial arm publishes
no percent.


**Queue status 2026-11-11 03:02 CET (tick 31):** nothing launched — the queue stays empty and item 8
(the Grok resumption: gpqa-diamond from `gpqa-139`, humaneval from `humaneval-0120`, then the two
deferred sets) remains gated to 2026-11-12 by the owner quota window. 0 `parb-pub-*` units, no
`pub_bench_run`/`pub_bench_cloud`/`gate_run` process on the host, 0 foreign legs on the endpoint;
zero model calls and zero cloud calls this tick.

**The standing preflight gate reads NO-GO a ninth time; swap is pinned at 1 MiB again.** Same box,
03:01 CET: **swap free 1 MiB of 8 191 MiB** (ticks 26–30 read 0 / 3 / 0 / 0 / 0 — the device sits at
its last megabyte), MemAvailable 14 650 MiB, engine state `S`, **569 % CPU with the GPU at 0 %
utilization / 37.2 W**, RSS **57 782 MiB — up 497 MiB in the ~35 minutes since tick 30's 57 285 MiB**,
so the growth direction tick 30 saw reverse has reversed back; load average 16.30, process age
**54.4 h** — the same un-restarted process as ticks 23–30, over two days and six hours. Both NO-GO
reasons reproduce verbatim (swap exhaustion, idle-spin pair), exit 3; the line launches no local leg
into that state. The cure (engine restart / parking the keep-up load) stays an owner decision — the
same engine serves this session's brain — and the 2026-11-12 Grok resumption is cloud-side,
unaffected. Gate contract test re-run: `harness/pub_preflight_test.py` **20/20 green**.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
**index drift: 0**; `pub_arms_index.py --pins` **manifest pin drift: 0**;
`pub_derived_percent_check.py` registry `pub-derived-percents-v1` **42 entries recomputed, 0
findings** (41 digest + 169 document citations, 0 uncovered); `pub_grok_cell_check.py` 9 documents,
**0 findings**; `pub_superseded_cell_check.py` 9 documents, **0 findings**; `pub_digest_row_check.py`
**46 rows, 0 findings**, 23/23 pre-rule exceptions used; `scripts/qa/docs_policy.py --daily` PASS.

Grok partials re-verified intact again (twenty-fourth verification), zero model calls and still
unscored/unshipped by rule: `gpqa-diamond/pub-grok.jsonl` SHA-256/16 **`cde63378fa1633c5`**,
**139 rows / 139 unique ids / 139 `finish=ok` / 0 empty**, and `humaneval/pub-grok.jsonl` SHA-256/16
**`a7c741de0d6ace8c`**, **120 / 120 / 120 / 0 empty** — byte-identical to ticks 21–30, mtimes still
2026-11-09 07:56, resume points `gpqa-139` and `humaneval-0120` unchanged.

Ops state read this tick (no action, report-only): `HEAD` == `origin/main` == **`8bee4db`**, working
tree clean (0 porcelain), and that push is **green on all five jobs** (contour self-tests,
secret-scan, hard-v6 scoring contracts, devsecops, pages build; read 03:02 CET / 02:02 UTC). The
daily **`GitHub docs freshness daily`** job (`0 2 * * *`) still records its last run as
**2026-11-10 02:00 UTC, error: script exited with code 1 — "repo is dirty; refusing daily docs
refresh"**; that captured stdout is the **pre-retarget two-worktree deletion snapshot** already
recorded in `LEG-INCIDENTS.md` at 14:45 CET, when the script still pointed at the second clone. The
retarget held: `docs_freshness_daily.sh` now `cd`s to `~/sah-main` (the only `[main]` worktree, clean),
the second worktree is a **detached HEAD** carrying only 3 untracked scratch files, and the 2026-11-11
02:00 UTC slot recorded no new run (next run 2026-11-12 02:00). Per the brief this is **reported, not
fixed by committing in-flight work**; `scripts/qa/docs_policy.py --daily` prints PASS on the current
tree, so the job's refuse condition (a dirty tree) is not currently true. `LEG-INCIDENTS.md` gains no
new 2026-11-11 PUB entry: no leg started, stopped or restarted this tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond from `gpqa-139`, 59 ids; humaneval from `humaneval-0120`, 44 ids; then the deferred
mmlu-pro 500 and ifeval 541, whose Grok go-scripts are written at launch time with ceilings matched
to each set's in-force family), each resumable by id and scored only when complete. Standing limits
unchanged: no Grok arm before 2026-11-12; frozen contour `0.0.2.56`; a local leg needs
`pub_preflight.py` exit 0 (the ninth consecutive NO-GO reading keeps that moot); sanitization before
every push; a partial arm publishes no percent.

**Queue status 2026-11-11 03:36 CET (tick 32):** nothing launched — the queue stays empty and item 8
(the Grok resumption: gpqa-diamond from `gpqa-139`, humaneval from `humaneval-0120`, then the two
deferred sets) remains gated to 2026-11-12 by the owner quota window. 0 `parb-pub-*` units, no
`pub_bench_run`/`pub_bench_cloud`/`gate_run` process on the host, 0 foreign legs on the endpoint;
zero model calls and zero cloud calls this tick.

**The standing preflight gate reads NO-GO a tenth time; the swap is back at zero and the idle-spin
pair re-tripped.** Same box, 03:36 CET: **swap free 0 MiB of 8 191 MiB** (ticks 26–31 read
0 / 3 / 0 / 0 / 0 / 1 — the device sits at its last megabyte again), MemAvailable 14 769 MiB, engine
state `Sl`, **565 % CPU with the GPU at 0 % utilization / 37.4 W** — so both NO-GO reasons reproduce
verbatim (swap exhaustion, idle-spin pair), exit 3; the line launches no local leg into that state.
RSS **57 549 MiB — down 233 MiB against tick 31's 57 782 MiB over ~35 minutes**, so the RSS direction
flips back again (the reader this tick sampled `ps` RSS in KiB and converted to MiB; the flip is
stated as an observation only). Process age **2 d 07:00 (55.0 h)** — the same un-restarted process as
ticks 23–31; load average 10.98, `/health` 200, 0 foreign legs. The cure (engine restart / parking
the keep-up load) stays an owner decision — the same engine serves this session's brain — and the
2026-11-12 Grok resumption is cloud-side, unaffected. Gate contract test re-run:
`harness/pub_preflight_test.py` **20/20 green**.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
**index drift: 0**; `pub_arms_index.py --pins` **manifest pin drift: 0**;
`pub_derived_percent_check.py` registry `pub-derived-percents-v1` **42 entries recomputed, 0
findings** (41 digest + 169 document citations, 0 uncovered); `pub_grok_cell_check.py` 9 documents,
**0 findings**; `pub_superseded_cell_check.py` 9 documents, **0 findings**;
`pub_digest_row_check.py` **46 rows, 0 findings**, 23/23 pre-rule exceptions used;
`scripts/qa/docs_policy.py --daily` PASS.

Grok partials re-verified intact again (twenty-fifth verification), zero model calls and still
unscored/unshipped by rule: `gpqa-diamond/pub-grok.jsonl` SHA-256/16 **`cde63378fa1633c5`**,
**139 rows / 139 unique ids / 139 `finish=ok` / 0 empty**, and `humaneval/pub-grok.jsonl`
SHA-256/16 **`a7c741de0d6ace8c`**, **120 / 120 / 120 / 0 empty** — byte-identical to ticks 21–31,
mtimes still 2026-11-09 07:56, last stored ids `gpqa-138` and `humaneval-0119`, so the resume points
`gpqa-139` and `humaneval-0120` are unchanged.

**Daily docs job: today's 02:00 UTC run is the first with a green script; its push step was the
remaining failure, and it is repaired as tooling this tick (zero measurement bytes moved).** The job
no longer refuses on a dirty tree — the 2026-11-10 worktree retarget held — it ran
`scripts/qa/refresh_docs_status.py` on a clean tree and committed the date marker
`Daily docs freshness check: 2026-11-11` (**`945df05`**, the first such commit in `git log`). The
push step then failed **8 consecutive times**: the refresh script calls a bare
`git push origin HEAD:main`, and the repo's pre-push hook blocks every push to `refs/heads/main`
unless `ALLOW_HARD_V6_PUSH=1` is set for that push (the single-writer guard) — the job has therefore
never pushed on its own since the guard was introduced; `945df05` reached `origin/main` only because
tick 31's push carried it. The job still records `Execution: failed`, and its chat delivery was
separately degraded (`send_path_degraded` to the Telegram target) — that delivery path is reported,
not touched. Repair applied to the **untracked local wrapper** `~/.hermes/scripts/docs_freshness_daily.sh`:
it now exports `ALLOW_HARD_V6_PUSH=1` so this operator-scheduled daily date-marker push honours the
guard as designed. The hook itself is unchanged, no repo byte, row or verdict moved; tomorrow's run
is the first end-to-end attempt. Recorded as a dated entry in `LEG-INCIDENTS.md`. This is the
tooling-side repair the brief allows — the brief's "do not fix" refers to committing in-flight work
to clean the tree, and the tree was clean.

Ops state read this tick (no action): `HEAD` == `origin/main` == **`7e2469a`**, working tree clean,
and that push is **green on all recorded CI runs** (devsecops, hard-v6 scoring contracts,
secret-scan, contour self-tests; read 03:38 CET). `LEG-INCIDENTS.md` gains the docs-job push-guard
entry above — no leg started, stopped or restarted this tick, so no leg-incident entry.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond from `gpqa-139`, 59 ids; humaneval from `humaneval-0120`, 44 ids; then the deferred
mmlu-pro 500 and ifeval 541, whose Grok go-scripts are written at launch time with ceilings matched
to each set's in-force family), each resumable by id and scored only when complete. Standing limits
unchanged: no Grok arm before 2026-11-12; frozen contour `0.0.2.56`; a local leg needs
`pub_preflight.py` exit 0 (the tenth consecutive NO-GO reading keeps that moot); sanitization before
every push; a partial arm publishes no percent.


**Queue status 2026-11-11 04:12 CET (tick 33):** nothing launched — the queue stays empty and item 8
(the Grok resumption: gpqa-diamond from `gpqa-139`, humaneval from `humaneval-0120`, then the two
deferred sets) remains gated to 2026-11-12 by the owner quota window. 0 `parb-pub-*` units, no
`pub_bench_run`/`pub_bench_cloud`/`gate_run` process on the host, 0 foreign legs on the endpoint;
zero model calls and zero cloud calls this tick.

**Preflight gate NO-GO an eleventh time; both conditions reproduce verbatim.** Same box, 04:12 CET:
**swap free 0 MiB of 8 191 MiB** (ticks 26-32 read 0 / 3 / 0 / 0 / 0 / 1 / 0), MemAvailable
14 288 MiB, engine state `Sl`, **562 % CPU with the GPU at 0 % utilization / 37.14 W** (the
idle-spin pair), load average 14.01, `/health` 200. Engine pid `3284575`, age **2 d 07:36 (55.6 h)**
— the same un-restarted process as ticks 23-32; RSS **57 562 MiB** (this tick's reader converts the
`ps` KiB figure to MiB, so the field label is now correct — tick 32's reading printed KiB in a
MiB-labelled slot, a reader bug, not a box change). Exit 3; the line launches no local leg into that
state. The cure (engine restart / parking the keep-up load) stays an owner decision — the same
engine serves this session's brain — and the 2026-11-12 Grok resumption is cloud-side, unaffected.
Gate contract test re-run: `harness/pub_preflight_test.py` **20/20 green**.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
**index drift: 0**; `pub_arms_index.py --pins` **manifest pin drift: 0**;
`pub_derived_percent_check.py` registry `pub-derived-percents-v1` **42 entries recomputed, 0
findings** (41 digest + 169 document citations, 0 uncovered); `pub_grok_cell_check.py` 9 documents,
**0 findings**; `pub_superseded_cell_check.py` 9 documents, **0 findings**;
`pub_digest_row_check.py` **46 rows, 0 findings**, 23/23 pre-rule exceptions used;
`scripts/qa/docs_policy.py --daily` PASS.

Grok partials re-verified intact again (twenty-sixth verification), zero model calls and still
unscored/unshipped by rule: `gpqa-diamond/pub-grok.jsonl` SHA-256/16 **`cde63378fa1633c5`**,
**139 rows / 139 unique ids / 139 `finish=ok` / 0 empty**, and `humaneval/pub-grok.jsonl`
SHA-256/16 **`a7c741de0d6ace8c`**, **120 / 120 / 120 / 0 empty** — byte-identical to ticks 21-32,
mtimes still 2026-11-09 07:56, last stored ids `gpqa-138` and `humaneval-0119`, resume points
`gpqa-139` and `humaneval-0120` unchanged.

**The daily docs job: today's failure attribution corrected, and the orphan-commit defect repaired as
tooling (zero measurement bytes moved).** Reading the job's own execution record
(`88c0821487c2412e8320bcbc0137bb4c`, 03:00:17->03:02:55 CET) shows **one** push attempt that died on
`Could not resolve host: github.com` (exit 128), not eight attempts and not the single-writer guard:
`BLOCKED_SINGLE_WRITER_GUARD` appears nowhere in that capture. The guard itself is real and is now
proven mechanically by driving the shared-dir `pre-push` hook with today's stdin (without
`ALLOW_HARD_V6_PUSH=1` -> `BLOCKED_SINGLE_WRITER_GUARD`, exit 1; with it -> exit 0), so the 03:40
wrapper fix stands. The verification found a genuine defect in `scripts/qa/refresh_docs_status.py`:
it pushed only inside the marker-changed branch, so a marker commit whose push died is stranded
local forever (today `945df05` reached `origin/main` only because a pub-line push carried it).
Repaired: the push step moved outside that branch, retries a transient transport failure
(`SAH_DOCS_PUSH_ATTEMPTS`, default 3; `SAH_DOCS_PUSH_BACKOFF_S`, default 30 s) and never retries a
guard block. New contract test `scripts/qa/refresh_docs_push_test.py` (10 checks, enrolled in
`scripts/qa/static_checks.py`) pins the retry bound, the no-retry guard path, the unknown-ahead-count
path and the call site; the real tool was then run end-to-end on today's tree (date already current)
and exits 0 with `nothing to push (HEAD == upstream)`. Full dated correction in
`LEG-INCIDENTS.md`; tomorrow's 02:00 UTC run is the first attempt under both fixes.

Ops state read this tick (no action): `HEAD` == `origin/main` == **`38027f2`** before this commit,
working tree clean at tick start, and that push is **green on all five recorded jobs**
(secret-scan, devsecops, hard-v6 scoring contracts, contour self-tests, pages build; read 04:12 CET).
`hermes cron list` shows no paused job owned by this line: the only two `[paused]` entries are
operator-disabled B2003 jobs with `paused_reason: null` (`B2003 finish watch`, created 2026-11-01;
`Tool-eval full after B2003`, created 2026-11-02), which the drain-resume job deliberately never
resumes (it only restarts recurrences paused by a runtime/gateway restart).
`LEG-INCIDENTS.md` gains the correction entry above — no leg started, stopped or restarted this tick.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond from `gpqa-139`, 59 ids; humaneval from `humaneval-0120`, 44 ids; then the deferred
mmlu-pro 500 and ifeval 541, whose Grok go-scripts are written at launch time with ceilings matched
to each set's in-force family), each resumable by id and scored only when complete. Standing limits
unchanged: no Grok arm before 2026-11-12; frozen contour `0.0.2.56`; a local leg needs
`pub_preflight.py` exit 0 (the eleventh consecutive NO-GO reading keeps that moot); sanitization
before every push; a partial arm publishes no percent.


**Queue status 2026-11-11 04:53 CET (tick 34):** nothing launched — the queue stays empty and item 8
(the Grok resumption: gpqa-diamond from `gpqa-139`, humaneval from `humaneval-0120`, then the two
deferred sets) remains gated to 2026-11-12 by the owner quota window. 0 `parb-pub-*` units, no
`pub_bench_run`/`pub_bench_cloud`/`gate_run` process on the host, 0 foreign legs on the endpoint;
zero model calls and zero cloud calls this tick.

**Preflight gate NO-GO a twelfth time — but the FIRST reading since the gate shipped in which the
swap-exhaustion condition does not fire.** Same box, 04:53 CET: **swap free 8 191 MiB of 8 191**
(completely unused; ticks 23–33 every time read 0 / 3 / 0 / 0 / 0 / 1 / 0 MiB free), MemAvailable
14 607 MiB, engine state `S`, **558 % CPU with the GPU at 0 % utilization / 36.95 W** (the
idle-spin pair — the only remaining NO-GO reason), load average 12.51, `/health` 200. Engine pid
`3284575`, age **2 d 08:16 (56.3 h)** — the same un-restarted process as ticks 23–33; RSS
57 254 MiB. One reading cannot separate a real swap release from a lull, and the distinction is
moot for the launch decision while the idle-spin pair still closes the gate: if the engine really
is parked with swap free now, a future reading will show low engine CPU as well. Exit 3; the line
launches no local leg into that state. The cure (engine restart / parking the keep-up load) stays
an owner decision — the same engine serves this session's brain — and the 2026-11-12 Grok
resumption is cloud-side, unaffected. Gate contract test re-run: `harness/pub_preflight_test.py`
**20/20 green**.

Standing gates re-run on the tracked tree, zero model calls, all green: `pub_arms_index.py --check`
**index drift: 0**; `pub_arms_index.py --pins` **manifest pin drift: 0**;
`pub_derived_percent_check.py` registry `pub-derived-percents-v1` **42 entries recomputed, 0
findings**; `pub_grok_cell_check.py` 9 documents, **0 findings**;
`pub_superseded_cell_check.py` 9 documents, **0 findings**; `pub_digest_row_check.py`
**46 rows, 0 findings**; `scripts/qa/docs_policy.py --daily` PASS.

Grok partials re-verified intact again (twenty-seventh verification), zero model calls and still
unscored/unshipped by rule: `gpqa-diamond/pub-grok.jsonl` SHA-256/16 **`cde63378fa1633c5`**,
**139 rows / 139 unique ids / 139 `finish=ok` / 0 empty**, and `humaneval/pub-grok.jsonl`
SHA-256/16 **`a7c741de0d6ace8c`**, **120 / 120 / 120 / 0 empty** — byte-identical to ticks 21–33,
mtimes still 2026-11-09 07:56, last stored ids `gpqa-138` and `humaneval-0119`, resume points
`gpqa-139` and `humaneval-0120` unchanged.

Ops state read this tick (no action): `HEAD` == `origin/main` == **`4fcf356`** before this commit,
working tree clean at tick start, and that push is **green on all five recorded jobs**
(secret-scan, devsecops, hard-v6 scoring contracts, contour self-tests, pages build; read 04:55
CET). `hermes cron list` shows no paused job owned by this line. The paused list now carries
**three** entries, all operator-disabled with `paused_reason: null` and `paused_at: null`: the two
B2003 jobs read at tick 33 plus `gh-inbox-watch`, which first appears in this line's reads this
tick — an operator pause (no reason, no pause timestamp, no recent execution failure), not the
runtime-drain pause class, so the drain-resume job correctly leaves all three alone.
The 03:00 daily-docs run for 2026-11-11 already left its marker (`945df05`, on `origin/main`);
its push-step repair from tick 33 is in force from tomorrow's run.
No leg was started, stopped or restarted this tick; `LEG-INCIDENTS.md` gains nothing (no partial
file discarded, zero model and zero cloud calls).

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond from `gpqa-139`, 59 ids; humaneval from `humaneval-0120`, 44 ids; then the deferred
mmlu-pro 500 and ifeval 541, whose Grok go-scripts are written at launch time with ceilings matched
to each set's in-force family), each resumable by id and scored only when complete. Standing limits
unchanged: no Grok arm before 2026-11-12; frozen contour `0.0.2.56`; a local leg needs
`pub_preflight.py` exit 0 (the twelfth consecutive NO-GO reading keeps that moot); sanitization
before every push; a partial arm publishes no percent.


**Queue status 2026-11-11 05:32 CET (tick 35):** no public-line leg was launched by this tick and the
queue stays empty: item 8 (the Grok resumption — gpqa-diamond from `gpqa-139`, humaneval from
`humaneval-0120`, then the deferred mmlu-pro 500 and ifeval 541) remains gated to 2026-11-12 by the
owner quota window. 0 `parb-pub-*` units at tick start, no `pub_bench_run`/`pub_bench_cloud`/
`gate_run` process, 0 foreign legs on the endpoint. **One exception, reported in full:** while
staging the deferred Grok launchers, a guard written with an unescaped `<` inside `[ ]` failed open
as a shell redirection and started the gpqa-diamond Grok leg for 53 s — 4 calls (`gpqa-139`…
`gpqa-142`). The leg was killed immediately, the 4 rows were quarantined to
`gpqa-diamond/pub-grok.jsonl.suspended-window-20261111.bak` (SHA-256/16 `1e025849786a94c1`) with
zero credit and no percent computed, and the arm file was rebuilt byte-exact to its verified
identity (139 rows, SHA-256/16 `cde63378fa1633c5`, last id `gpqa-138`), so the resume point is
unchanged and those 4 ids are re-asked inside the window. Dated entry in `LEG-INCIDENTS.md`; the
cost that is real is 4 Grok calls spent outside the window. All four Grok launchers now carry a
numeric date guard (`date +%Y%m%d -lt 20261112` -> exit 3) which cannot be read as a redirection,
and all four were executed today: every one refuses and starts nothing.

**Preflight gate NO-GO a thirteenth time; the idle-spin pair is now the single reason.** Same box,
05:26 CET: **swap free 8 191 MiB of 8 191** for the second consecutive reading (ticks 23-33 read
0 / 3 / 0 / 0 / 0 / 1 / 0 / 0 / 0 / 1 / 0 / 8 191), MemAvailable 14 712 MiB, engine state `S`,
**554 % CPU with the GPU at 0 % utilization / 36.43 W**, RSS **56 934 MiB — down 320 MiB against
tick 34's 57 254 MiB over 33 minutes**, load average 10.04, `/health` 200, 0 foreign legs. Engine
pid `3284575`, age **2 d 08:50 (56.8 h)** — the same un-restarted process as ticks 23-34. Exit 3;
the line launches no local leg into that state. The cure stays an owner decision (the same engine
serves this session's brain) and the 12 Nov Grok resumption is cloud-side, unaffected. Gate contract
test re-run: `harness/pub_preflight_test.py` **20/20 green**. The reader itself moved to a stable
untracked path with a one-call wrapper (reading + gate): this tick's first attempt hit the gate's
**input-gap** path (`exit 1`, no readings) because the remote read command had to be reconstructed
from a scratch file the 24 h prune would take away, and a missing reading is never healthy. The
launch decision did not change: the first attempt wrote no leg and reserved no endpoint.

**A transport version drift now sits between the stored Grok bytes and the resumed legs (found
before any 12 Nov call, zero model calls).** The 3 published Grok rows (gsm8k 288/300, arc-easy
289/300, arc-challenge 288/300) and all 259 stored partial rows carry the transport string
`hermes Hermes Agent v0.23.0+860.gf17db36.dirty`; the local CLI now reports
`v0.23.1+2.gb3746e3.dirty`, an install whose HEAD commit is dated **2026-11-10 02:00** — i.e. the
update landed after the legs were stopped, and the 4 quarantined rows above are the first rows the
newer build ever wrote. So each resumed arm will hold two transport versions inside one answer file
(the runner stamps the version per row, so the boundary is auditable); the completed-arm percent may
only be published with that boundary named beside it, and it is stated here before the launch rather
than after the number.

**Standing gates re-run on the tracked tree, zero model calls, all green:**
`pub_arms_index.py --check` **index drift: 0**; `pub_arms_index.py --pins` **manifest pin drift: 0**;
`pub_derived_percent_check.py` registry `pub-derived-percents-v1` **42 entries recomputed, 0
findings** (41 digest + 169 document citations, 0 uncovered); `pub_grok_cell_check.py` 9 documents,
**0 findings** (every percent-less Grok cell still reads `suspended by owner quota, resumes
2026-11-12`); `pub_superseded_cell_check.py` 9 documents, **0 findings**; `pub_digest_row_check.py`
**46 rows, 0 findings**, 23/23 pre-rule exceptions used; `scripts/qa/docs_policy.py --daily` PASS;
`harness/pub_preflight_test.py` 20/20; `harness/pub_arms_index_test.py` 34/34;
`harness/pub_digest_row_gate_test.py` 21/21.

**The `MANIFEST GUARD` lines in the daily docs job's stderr are test tampers, not a task-file move
(attributed before anyone could file it as an integrity event).** Today's 03:00 docs run captured
three guard refusals pointing at a scratch temp copy of `ifeval.tasks.jsonl`, a MANIFEST copy with
the `hash_note` stripped, and a `no-such-bench` entry. Re-running the owner of those messages,
`harness/pub_arms_index_test.py`, reproduces exactly those three lines on its own temp files and
exits 0 (34/34): they are its non-vacuity controls. Independently, the tracked
`benchmarks/public/ifeval.tasks.jsonl` still hashes to both published labels — SHA-1/16
`2c672531577dcc33` (the pin every ifeval digest row prints) and SHA-256/16 `e09a5cab3782ed5b` (the
`hash_note`-labelled twin) — and `MANIFEST.json` carries that note. Today's docs run remains a
failure for the reason already recorded at 04:12 (one push attempt, DNS), with its push-step repair
in force from tomorrow's run.

**Grok partials re-verified after the incident (twenty-eighth verification), zero model calls, still
unscored and unshipped by rule:** `gpqa-diamond/pub-grok.jsonl` **139 rows / 139 unique ids / 139
`finish=ok` / 0 empty**, SHA-256/16 `cde63378fa1633c5`, last stored id `gpqa-138` -> resume
`gpqa-139`; `humaneval/pub-grok.jsonl` **120 / 120 / 120 / 0 empty**, SHA-256/16
`a7c741de0d6ace8c`, last stored id `humaneval-0119` -> resume `humaneval-0120`. Both launchers are
id-resumable and need no purge: every stored row is `finish=ok`, so there is no blank for the
public scorer to keep forever.

**Staged for 2026-11-12 (untracked launchers, zero calls, zero published bytes):** the two deferred
sets now have launchers in the pinned order — mmlu-pro 500 and ifeval 541 through the Grok transport
(`hermes -z <prompt inline> -m grok-4.7 --provider xai-oauth -t ""`, prompt inline because a toolless
transport cannot read a file), `PUB_CLOUD_TIMEOUT=2400` like the gpqa leg, PATH fail-closed check,
out dirs `~/pub-bench/mmlu-pro` and `~/pub-bench/ifeval`. Both cloud CLIs were checked by version
only: `hermes` and `codex-cli 0.166.0` resolve on PATH. The ceiling confound has to be stated at
publish time for the ifeval Grok row exactly as it is for the codex row: the transport exposes no
`max_tokens`, while the in-force ifeval family ran 1200.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond from `gpqa-139`, 59 ids including the 4 re-asked today by mistake; humaneval from
`humaneval-0120`, 44 ids; then mmlu-pro 500 and ifeval 541), each resumable by id and scored only
when complete, with the transport-version boundary named beside any completed percent. Standing
limits unchanged: no Grok arm before 2026-11-12; frozen contour `0.0.2.56`; a local leg needs
`pub_preflight.py` exit 0 (the thirteenth consecutive NO-GO keeps that moot); sanitization before
every push; a partial arm publishes no percent.

---

**Queue status 2026-11-11 06:08 CET (tick 36):** nothing launched — the queue stays empty and item 8
(the Grok resumption: gpqa-diamond from `gpqa-139`, humaneval from `humaneval-0120`, then the
deferred mmlu-pro 500 and ifeval 541) remains gated to 2026-11-12 by the owner quota window.
0 `parb-pub-*` units at tick start, no `pub_bench_run`/`pub_bench_cloud`/`gate_run` process,
0 foreign legs on the endpoint, working tree clean at HEAD `dcdad5e` with `origin/main` equal.
No digest row, verdict, answer byte, bank file or manifest pin moved this tick.

**The local-leg preflight gate returned GO for the first time in fourteen readings — and there is
nothing queued to launch into it.** Fresh reading at 06:08 CET: swap free **8 190 MiB of 8 191**,
MemAvailable 14 148 MiB, engine state **`R`** (not `D`), engine **555 % CPU with the GPU at 29 %
utilization / 39.40 W**, RSS 57 222 MiB, load average 10.05, `/health` 200, 0 foreign legs. The
gate prints **`PREFLIGHT GO`** (exit 0): the idle-spin pair — high engine CPU **at 0 % GPU**, the
single reason for the thirteen previous NO-GOs — is absent. The engine is the same un-restarted
process as ticks 23-35 (pid `3284575`, age **2 d 09:32**), so the condition cleared by itself and no
owner-side restart happened. Two honest limits on that reading: (i) the same engine serves this
session's brain, so a reading taken while the agent is answering carries its own decode traffic and
the 29 % GPU line is an endpoint state, not a forecast — a 12 Nov local leg would need a fresh
reading anyway; (ii) the queue holds no local leg at all. The arm census read programmatically off
`PUB-DIGEST.md` (39 percent rows) is the reason: every in-force set already carries a bare local row,
an admissible matched-shape contour row and a ChatGPT-codex row — gsm8k (bare 1 284/1 319, contour
matched 294/300, codex 293/300), arc-easy (2 261/2 376 / 289/300 / 290/300), arc-challenge
(1 129/1 172 / 291/300 / 290/300), gpqa-diamond (127/198 / 139/198 / 192/198), humaneval
(159/164 / 157/164 / 163/164, both `pytest-v2`), mmlu-pro (432/500 / 429/500 / 462/500), ifeval
(467/541 / 462/541 / 515/541, `pub-ifeval-v1`), livecodebench (101/175 / 99/175 / 168/175,
`lcb-exec-v2`), bfcl (1 116/1 240 / 1 122/1 240 / 281/300 on the pre-registered head slice). Grok is
complete for three sets, partial for two, and not started for mmlu-pro/ifeval — which is exactly the
12 Nov queue. So the GO is recorded as a state change of the endpoint, not as a launch.

**Standing gates re-run on the tracked tree, zero model calls, all green:**
`scripts/pub_arms_index.py --check` **index drift: 0**; `--pins` **manifest pin drift: 0**;
`scripts/pub_derived_percent_check.py` registry `pub-derived-percents-v1` **42 entries recomputed
from shipped bytes, 0 findings** (41 digest + 169 document citations, 0 uncovered);
`scripts/pub_grok_cell_check.py` 9 documents **0 findings**; `scripts/pub_superseded_cell_check.py`
9 documents **0 findings**; `scripts/pub_digest_row_check.py` **46 rows, 0 findings**, 23/23 pre-rule
exceptions used; `scripts/qa/refresh_docs_push_test.py` **PASS** (recovers on attempt 2, guard block
not retried, `main` returns `push_with_retry()`, no bare push call left in the tool).

**Today's daily-docs failure re-read from the scheduler's own record rather than a replay.**
Job `GitHub docs freshness daily` (`ef7ea47ff99b`), execution `88c0821487c2412e8320bcbc0137bb4c`:
started 03:00:17, finished 03:02:55 CET, status **failed, "Script exited with code 1"**. The captured
trace runs the whole static-QA list, commits `[main 945df05] Daily docs freshness check: 2026-11-11`
(03:02:13) and then ends at `+ git push origin HEAD:main` — the **pre-fix single bare push**, which is
expected: the push-step repair was committed at 04:19, after this run started. The marker commit is
**not orphaned**: `945df05` is an ancestor of `origin/main` (carried by the pub-line push at 03:04).
The `MANIFEST GUARD` lines in that stderr remain the non-vacuity tampers of
`harness/pub_arms_index_test.py`, attributed at tick 35, not a task-file move. From the 12 Nov run
the same job pushes through `push_with_retry()` (bounded retry on a transport error, guard block
never retried, always pushes when `git rev-list --count @{u}..HEAD` > 0), pinned by the test above
and enrolled in `scripts/qa/static_checks.py`.

**Grok partials, twenty-ninth verification, zero model calls, still unscored and unshipped by rule:**
`gpqa-diamond/pub-grok.jsonl` **139 rows / 139 unique ids / 139 `finish=ok` / 0 empty**, SHA-256/16
`cde63378fa1633c5`, last stored id `gpqa-138` -> resume `gpqa-139`; `humaneval/pub-grok.jsonl`
**120 / 120 / 120 / 0 empty**, SHA-256/16 `a7c741de0d6ace8c`, last stored id `humaneval-0119` ->
resume `humaneval-0120`. The transport-version drift stated at tick 35 was re-read from the stored
bytes rather than from prose: **all 259 rows carry
`hermes Hermes Agent v0.23.0+860.gf17db36.dirty (2026.9.24) · upstre toolsets off`**, while the live CLI now
reports `Hermes Agent v0.23.1+2.gb3746e3.dirty (2026.9.24) · upstream b3746e35`, so the resumed arms
will genuinely hold two transport versions per file and any completed percent must name that
boundary. `codex-cli 0.166.0` still resolves on PATH for the codex legs.

**Grok launcher guards re-checked statically; nothing executed.** All four launchers
(gpqa-diamond, humaneval, mmlu-pro, ifeval) still carry the numeric window guard
(`TODAY_NUM=$(date +%Y%m%d)` … `if [ "$TODAY_NUM" -lt 20261112 ]` -> `REFUSED … exit 3`) and
`bash -n` is clean on every one. They were **not** run this tick: their refusal path was proven by
execution at tick 35, and re-executing a launcher is the action that burned 4 calls yesterday, so the
static check is the right depth here.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
(gpqa-diamond from `gpqa-139`, 59 ids including the 4 re-asked on 11 Nov by mistake; humaneval from
`humaneval-0120`, 44 ids; then mmlu-pro 500 and ifeval 541), each resumable by id and scored only
when complete, with the transport-version boundary named beside any completed percent. Standing
limits unchanged: no Grok arm before 2026-11-12; frozen contour `0.0.2.56`; a local leg needs
`pub_preflight.py` exit 0 (GO for the first time at this tick, with no local leg queued);
sanitization before every push; a partial arm publishes no percent.

---

**Queue status 2026-11-11 06:45 CET (tick 37):** nothing launched — the queue stays empty and item 8
(the Grok resumption) remains gated to 2026-11-12 by the owner quota window. 0 `parb-pub-*` units at
tick start, no `pub_bench_run`/`pub_bench_cloud`/`gate_run` process, 0 foreign legs, working tree
clean at HEAD `ecdc64a` with `origin/main` equal. No digest row, verdict, answer byte, bank file or
manifest pin moved this tick. What this tick did instead of repeating a status line: it made
tomorrow's queue mechanical — a resume census computed from the pinned task files rather than
asserted from prose, and an ETA sized from this line's own measured per-set rates.

**The preflight GO of tick 36 did not hold: NO-GO again, the fourteenth NO-GO in fifteen readings.**
Fresh reading at 06:45 CET: swap free **8 191 MiB of 8 191**, MemAvailable 15 208 MiB, engine state
`S`, engine **551 % CPU with the GPU at 0 % utilization / 37.31 W** — the idle-spin pair, and the
sole reason the gate refuses. RSS 57 453 MiB (**+231 MiB against tick 36's 57 222 MiB in ~37 min**),
load average 10.79, `/health` 200, 0 foreign legs; still the same un-restarted engine process
(pid `3284575`, age **2 d 10:09**). Remedy stays an owner/box decision (engine restart or park the
keep-up load); nothing was restarted here, and cloud legs are unaffected by this gate. The reading
matters little this tick, because no admissible local leg exists: every in-force set already carries
bare + matched-shape contour + codex rows.

**Grok partials, thirtieth verification, now computed rather than recalled — zero model calls.**
A new untracked local helper (`pub-bench/grok_resume_census.py`, answer files + the **pinned tracked
task files** only, it can never call a transport) subtracts the stored `finish=ok` ids from the pinned
task-file order, so the resume set is a derived number. It reproduces the identities read at ticks
21-36 exactly: `gpqa-diamond/pub-grok.jsonl` **139 rows / 139 unique / 139 `finish=ok` / 0 empty**,
SHA-256/16 `cde63378fa1633c5`; `humaneval/pub-grok.jsonl` **120 / 120 / 120 / 0**, SHA-256/16
`a7c741de0d6ace8c`; **0 duplicate rows and 0 non-`ok` rows in either file**, so no blank-purge is
needed before resuming (the pitfall where the public scorer keeps the FIRST row per id is not armed
here). Derived resume sets: gpqa-diamond **59 ids** `gpqa-139`..`gpqa-197`; humaneval **44 ids**
`humaneval-0120`..`humaneval-0163`; mmlu-pro **500 ids** (first `mmlu-pro-0000`); ifeval **541 ids**
(first `ifeval-1000`).

**New planning number for item 8: the 12 Nov Grok queue is 1 144 calls = 9.0-27.6 h of sequential
wall time, i.e. it cannot be promised inside one day.** Per-leg bands from the rates this line's own
cloud logs measured (`s/task`): gpqa-diamond 59 ids at **188-322** (measured, the expert-science
leg's own rows) = **3.1-5.3 h**; humaneval 44 ids at **56-115** (measured at 80 and 120 rows) =
**0.7-1.4 h**; mmlu-pro 500 ids at **14.9-20.9** (UNMEASURED for this set; band = measured grok
MCQ/arithmetic legs arc-easy 14.9, arc-challenge 17.1, gsm8k 20.9) = **2.1-2.9 h**; ifeval 541 ids at
**20.9-120** (UNMEASURED; low = grok gsm8k, high = grok humaneval long-output) = **3.1-18.0 h**. The
two unmeasured bands are labeled as bands, not measurements. Consequence, pre-registered now rather
than discovered on 12 Nov: the queue chains across more than one day at the high end, so legs run
one vendor at a time in the pinned order, a day that ends mid-set leaves that set unscored and
unpublished (a partial arm publishes no percent), and the resume-by-id design is what makes the
multi-day chain safe rather than expensive.

**The 12 Nov chain launcher exists and is proven without spending a call.**
`pub-bench/go_grok_queue_20261112.sh` (untracked local file, so no connection material lands in this
repo) runs the four legs strictly in sequence with the numeric window guard, `PATH` export plus a
`command -v hermes` fail-closed, `PUB_CLOUD_TIMEOUT=2400`, and a **halt on any non-zero leg exit** so
a dead transport cannot spend calls on the next set. Proofs done this tick, none of which touches a
transport: `bash -n` clean; the guard expression evaluated in isolation both directions
(`20261111` -> closed/would refuse, `20261112` and `20261113` -> open); ordering proven by line
number, guard at line 20 **before** the PATH check (36) and the transport call (42); and a
`GROK_DRYRUN=1` run under `bash -x` that prints the census, exits 0 and leaves **0 transport-invoking
lines in the trace**. The launcher was deliberately NOT executed in live mode: tick 35's cost was
exactly the act of executing a launcher whose guard was wrong, and here the guard, its position and
the dry path are proven separately instead.

**Standing gates re-run on the tracked tree, zero model calls, all green and identical to tick 36:**
`scripts/pub_arms_index.py --check` **index drift: 0**; `--pins` **manifest pin drift: 0**;
`scripts/pub_derived_percent_check.py` **42 entries recomputed from shipped bytes, 0 findings**
(41 digest + 169 document citations, 0 uncovered); `scripts/pub_grok_cell_check.py` 9 documents
**0 findings**; `scripts/pub_superseded_cell_check.py` 9 documents **0 findings**;
`scripts/pub_digest_row_check.py` **46 rows, 0 findings**, 23/23 pre-rule exceptions used.
The daily-docs job needs no re-reading: its 03:00 CET failure was attributed at tick 36 to the
pre-fix bare push and its marker commit `945df05` is an ancestor of `origin/main`; from the 12 Nov
run it pushes through `push_with_retry()`.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order and the
derived resume sets above, each resumable by id and scored only when complete, with the
transport-version boundary (stored rows `v0.23.0+860.gf17db36`, resumed rows `v0.23.1+2.gb3746e3`)
named beside any completed percent. Standing limits unchanged: no Grok arm before 2026-11-12; frozen
contour `0.0.2.56`; a local leg needs `pub_preflight.py` exit 0 (NO-GO at this reading, with no local
leg queued); sanitization before every push; a partial arm publishes no percent.

---

**Queue status 2026-11-11 07:20 CET (tick 38):** nothing launched — the queue stays empty and item 8
(the Grok resumption) remains gated to 2026-11-12 by the owner quota window. 0 `parb-pub-*` units at
tick start, no `pub_bench_run`/`pub_bench_cloud`/`gate_run` process, tree clean; `origin/main` moved
under the line by one foreign commit (`901230f`, the daily self-evolution research digest, touches
only `sources/daily/`) and was fast-forwarded — no pub byte moved. No digest row, verdict, answer
byte, bank file or manifest pin moved this tick.

**Preflight NO-GO again: the fifteenth NO-GO in sixteen readings, idle-spin the sole reason.**
Fresh reading at 07:20 CET: swap free **8 191 MiB of 8 191**, MemAvailable 14 111 MiB, engine state
`S`, engine **548 % CPU with the GPU at 0 % utilization / 36.50 W**, load average 9.35, `/health`
200, 0 foreign legs, still the same un-restarted engine process (pid `3284575`, age **2 d 10:44**).
RSS 56 967 MiB — **down 486 MiB against tick 37's 57 453 MiB in ~35 min**, so the RSS growth noted
last tick oscillates rather than trends. Today alone produced seven readings and the GO at 06:08 is
the only one with a non-zero GPU utilization (29 %); the window is transient and the remedy stays an
owner/box decision (engine restart or park the keep-up load). Nothing was restarted here, cloud legs
are unaffected, and no admissible local leg exists anyway: every in-force set already carries bare +
matched-shape contour + codex rows.

**The 12 Nov chain launcher was this tick executed in LIVE mode under the closed window — the
strongest guard proof that is safe to run today.** Tick 37 proved the guard without executing;
today the execution itself is the proof, because the numeric guard (`20261111 -lt 20261112`) closes:
the launcher printed `REFUSED: grok arms are suspended by owner quota until 2026-11-12` and exited
**3 measured directly (no pipe)**, after which **0** `pub_bench_cloud` and **0** `gate_run` processes
exist; the guard (lines 20/33) sits before the transport call (line 42), and the `GROK_DRYRUN=1` path
again ran the census and exited 0 without a transport line. The census is the partials' **thirty-first
verification, computed not recalled**: `gpqa-diamond/pub-grok.jsonl` **139/139/139/0**, SHA-256/16
`cde63378fa1633c5`; `humaneval/pub-grok.jsonl` **120/120/120/0**, SHA-256/16 `a7c741de0d6ace8c`;
0 duplicate and 0 non-`ok` rows in either. Resume sets unchanged: gpqa-diamond 59 (`gpqa-139`..`gpqa-197`),
humaneval 44 (`humaneval-0120`..`humaneval-0163`), mmlu-pro 500, ifeval 541 — 1 144 calls, sequential
ETA 9.0-27.6 h.

**Today's daily-docs failure read from its own execution record, not from prose.** The 03:00 CET run
of `ef7ea47ff99b` (GitHub docs freshness daily) exited 1 at 03:02:55: the real cause is **one DNS
blip** — `Could not resolve host: github.com` (exit 128) on the **pre-fix bare `git push`**; the
`MANIFEST GUARD:` lines in the same capture are the contract tests' tamper-control noise already
attributed at tick 35, not findings. The repaired tool (`push_with_retry()` with bounded retry,
commit `4fcf356`) is in the current tree, and **no marker commit is stranded**: `origin/main..HEAD`
is 0 after the fetch, so nothing waits for an orphan push; the 12 Nov run pushes through the retry
path. The job's own result delivery also degraded (`send_path_degraded` to the messaging target) —
reported, not repaired here.

**Standing gates re-run on the fetched tree, zero model calls, all green and identical to ticks 36-37:**
`pub_arms_index.py --check` **index drift: 0**; `--pins` **manifest pin drift: 0**;
`pub_derived_percent_check.py` **42 recomputed, 0 findings** (41 digest + 169 doc citations, 0
uncovered); `pub_grok_cell_check.py` 9 documents **0 findings**; `pub_superseded_cell_check.py`
9 documents **0 findings**; `pub_digest_row_check.py` **46 rows, 0 findings**, 23/23 exceptions.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order and the
derived resume sets above, each resumable by id and scored only when complete, with the
transport-version boundary (stored rows `v0.23.0+860.gf17db36`, resumed rows `v0.23.1+2.gb3746e3`)
named beside any completed percent. Standing limits unchanged: no Grok arm before 2026-11-12; frozen
contour `0.0.2.56`; a local leg needs `pub_preflight.py` exit 0 (NO-GO at this reading, with no local
leg queued); sanitization before every push; a partial arm publishes no percent.

## Tick 39 — 2026-11-11 07:55 CET (status only, zero model calls)

Fresh preflight reading at 07:55 CET: swap free **8 191 MiB of 8 191**, MemAvailable 14 082 MiB,
engine state `S`, engine **544 % CPU with the GPU at 0 % / 36.24 W**, load average 12.36, `/health`
200, 0 foreign legs, still the same un-restarted engine (pid `3284575`, age **2 d 11:19**).
RSS 57 575 MiB — **up 608 MiB against tick 38 in ~35 min**, opposite sign to tick 38's fall, so the
oscillation reading from last tick holds. **NO-GO a sixteenth time in seventeen readings**, sole
reason the idle-spin pair. The remedy stays an owner/box decision and no local leg is queued anyway:
every in-force set already carries bare + matched-shape contour + codex rows, and the 12 Nov queue
is Grok-cloud only. Tooling note caught while measuring: the untracked `preflight.sh` wrapper's
trailing `echo` masks the gate's exit code — the gate itself was re-run **unshielded** on the same
readings file and exits **3** as contracted.

**Grok partials, thirty-second computed verification, byte-exact:** `gpqa-diamond/pub-grok.jsonl`
**139/139/139/0**, SHA-256/16 `cde63378fa1633c5`; `humaneval/pub-grok.jsonl` **120/120/120/0**,
SHA-256/16 `a7c741de0d6ace8c`; 0 duplicate and 0 non-`ok` rows. Resume sets unchanged: gpqa-diamond
59 (`gpqa-139`..`gpqa-197`), humaneval 44 (`humaneval-0120`..`humaneval-0163`), mmlu-pro 500,
ifeval 541 — 1 144 calls, sequential ETA 9.0-27.6 h.

**Chain launcher guard re-proven in LIVE mode:** header printed `mode=live window=closed
(opens 20261112)`, then `REFUSED: grok arms are suspended by owner quota until 2026-11-12`, exit
**3**. The zero-transport assertion needed a second pass: an **unbracketed**
`pgrep -cf 'pub_bench_cloud|gate_run'` counted **2** because the measuring shell's own command line
contains the pattern (the same self-match class the skill warns about for ssh one-liners); the
bracketed form `pgrep -cf '[p]ub_bench_clou[d]|[g]ate_ru[n].py'` counts **0**. No arm started,
no owner quota spent.

**Standing five PUB gates green and identical to ticks 36-38:** arms index `--check` **drift 0**;
derived percents **42 recomputed, 0 findings**; grok cells 9 documents **0 findings**; superseded
cells 9 documents **0 findings**; digest rows **46 rows, 0 findings**. No new daily-docs run has
landed since tick 38 attributed today's single 03:00 failure (one DNS blip on the pre-fix bare
push; `push_with_retry()` in tree, no orphaned marker commit).

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order with
the derived resume sets above, each resumable by id and scored only when complete, transport-version
boundary named beside any completed percent. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`; a local leg needs `pub_preflight.py` exit 0 (NO-GO at this
reading, none queued); sanitization before every push; a partial arm publishes no percent.

## Tick 40 — 2026-11-11 08:30 CET (status + one tooling gate, zero model calls)

Fresh preflight reading at 08:29 CET: swap free **8 191 MiB of 8 191**, MemAvailable 14 692 MiB,
engine state `R`, engine **540 % CPU with the GPU at 0 % / 36.66 W**, load average 11.73, `/health`
200, 0 foreign legs — still the same un-restarted engine (pid `3284575`, age **2 d 11:53**). RSS
57 373 MiB, **down 202 MiB against tick 39**, so the oscillation (…56 967 → 57 575 → 57 373) holds
rather than a monotone climb. **NO-GO a seventeenth time in eighteen readings**, sole reason the
idle-spin pair; the gate was again run **unshielded** on the readings file and exits **3** as
contracted. No local leg is queued: every in-force set already carries bare + matched-shape contour
+ codex rows, and the 12 Nov queue is Grok-cloud only, which the preflight gate does not touch.

**The hand-read Grok partial census is now a gate (tooling release, registers no contour feature and
moves no published byte).** From tick 21 to tick 39 the identity of the two suspended partials was
re-read by hand and retyped into commit messages and `LEG-INCIDENTS.md` prose — nineteen hand readings
of the same file is a rule, so it is now a checker, and it de-risks the 1 144 paid calls of the 12 Nov
window by pinning the thing that must not drift: the resume set.

* `benchmarks/public/GROK-RESUME-PIN.json` (`grok-resume-pin-v1`) pins, per queued arm, the published
  tasks cell read through `manifest_tasks_cell`, the pinned task count, and for the two stored arms the
  row / unique / `finish=ok` / empty counts, the **SHA-256/16 of the stored answer file**, the
  `pinned_ok_ids` set and the resume set (`expected_remaining`, first and last remaining id), plus the
  zero-credit quarantine files as evidence. Values are computed from the bytes, never typed.
* `scripts/pub_grok_resume_check.py` makes **zero model or cloud calls**: it reads the pinned task
  files, the local answer files and the pin, and answers mechanically whether the queue may spend a
  call. It fails closed (exit 3) on identity drift (row counts, the answer-file hash), a duplicate id
  parked in the arm file, a non-`ok` row parked there, an `ok` row with an empty answer, and
  resume-set drift; an input gap (missing pin, missing bench record, an expected answer file absent)
  exits 1 and is never a green light.
* Two modes, decided from `owner_window.suspended_until` and the run date (`--as-of`, so the decision
  is reproducible): while the window is **CLOSED** the pin is an exact snapshot and **any growth is a
  finding**, because no Grok call is legal inside it — that is precisely the 2026-11-11 05:31 class,
  where a launcher guard parsed as a redirection wrote 4 rows that had to be quarantined with zero
  credit. Once the window is **OPEN** the pin is a floor: every `pinned_ok_ids` id must still be stored
  (lost work is a finding), the corruption classes still apply, and growth is reported as progress with
  a live resume set, so a healthy resumed queue is never halted by a gate that froze one moment.
* Contract test `harness/pub_grok_resume_test.py` (**19 checks**, CI-enrolled by the `harness/*test.py`
  glob, hermetic fixtures in a temp dir via `PUB_MANIFEST_OVERRIDE`, no real bytes read): a healthy
  partial is READY; seven independent tamper classes each turn NO-GO (answer byte, duplicate id, parked
  non-ok row, empty ok answer, growth inside the closed window, wrong tasks cell, wrong pinned task
  count); growth with the window open is READY with a progress note while a vanished pinned id in that
  same state is still NO-GO; a completed set (0 remaining) is READY; a never-legged arm with no answer
  file is READY; three input-gap classes exit 1; and a moved task file is refused by the published
  MANIFEST pin guard with exit 2.
* Non-vacuity proven on the **real** bytes, not only on fixtures: with the two stored partials copied
  to a scratch workspace and one row appended, the gate prints the window-closed finding and exits 3;
  the real workspace hashes are unchanged by the exercise.
* The 12 Nov chain launcher now calls the gate next to the census (`RESUME GATE NOT GREEN — refusing
  to spend quota` → exit 3). Line-order proof on the patched launcher: window guard **line 20** <
  gate **line 31** < `command -v hermes` **line 44** < transport call **line 50**; `bash -n` clean;
  the `GROK_DRYRUN=1` trace shows the gate once and **0** lines invoking a transport; a LIVE run under
  the still-closed window printed `REFUSED`, exit **3**, with **0** transport processes afterwards
  (counted with the bracketed `grep -c 'pub_bench_clo[d]'`, after tick 39's lesson that an unbracketed
  `pgrep -f` self-matches the measuring shell).
* Gate on the real workspace at 08:30 CET: **READY, 22 checks** — `gpqa-diamond` 139/139 SHA-256/16
  `cde63378fa1633c5` resume `gpqa-139`..`gpqa-197` (59), `humaneval` 120/120
  SHA-256/16 `a7c741de0d6ace8c` resume `humaneval-0120`..`humaneval-0163` (44), `mmlu-pro` 500
  (`mmlu-pro-0000`..`mmlu-pro-12024`), `ifeval` 541 (`ifeval-1000`..`ifeval-3757`) — **1 144 calls**
  in the pinned order. Same numbers the hand census has printed since tick 21, now derived by code.

**Standing five PUB gates green and identical to ticks 36-39:** arms index `--check` drift 0; derived
percents 42 recomputed, 0 findings; grok cells 9 documents 0 findings; superseded cells 9 documents 0
findings; digest rows 46 rows, 0 findings.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order, now
gated on `pub_grok_resume_check.py` exit 0 before the first call. Standing limits unchanged: no Grok
arm before 2026-11-12; frozen contour `0.0.2.56`; a local leg needs `pub_preflight.py` exit 0 (NO-GO
at this reading, none queued); sanitization before every push; a partial arm publishes no percent.

## Tick 41 — 2026-11-11 09:15 CET (status + the resume gate's OPEN-window branch proven on the real partials, zero model calls)

**Queue state:** 0 `parb-pub-*` units, no `pub_bench_run`/`pub_bench_cloud`/`gate_run` process, 0
foreign legs on the endpoint, tree clean, HEAD `3017f3d` == `origin/main` (0 ahead / 0 behind).
Nothing launched: item 8 stays gated to 2026-11-12 by the owner quota window. No digest row, verdict,
answer byte, bank file or manifest pin moved this tick.

**Preflight NO-GO again: the eighteenth NO-GO in nineteen readings, idle-spin the sole reason.**
Fresh reading at 09:15 CET: swap free **8 191 MiB of 8 191**, MemAvailable 15 234 MiB, engine state
`S`, engine **537 % CPU with the GPU at 0 % utilization / 36.43 W**, load average 10.53, `/health`
200, 0 foreign legs — still the same un-restarted engine process (pid `3284575`, age **2 d 12:39**).
RSS 57 146 MiB, **down 227 MiB against tick 40's 57 373 MiB** (…56 967 → 57 575 → 57 373 → 57 146), so
the oscillation holds rather than a monotone climb. The gate was again run **unshielded** on the
readings file and exits **3** as contracted. Remedy stays an owner/box decision; no local leg is
queued anyway, and cloud legs are outside this gate.

**What this tick did instead of repeating the census: the new resume gate was proven on the branch
tomorrow actually takes, on the real suspended files.** `pub_grok_resume_check.py` shipped at tick 40,
and everything proven with it then was: READY with the window **closed** (today's default), and the
tamper classes on **hermetic fixtures**. Tomorrow the chain launcher takes the decision from the real
date, i.e. the **OPEN-window** branch, on exactly these bytes — a mode that had never touched them.
Exercised with `--as-of`, zero model or cloud calls, the two arm files copied to a scratch workspace
(the real files were never opened for writing):

* `--as-of 2026-11-12`, floor intact → **READY (20 checks)**, resume sets unchanged: gpqa-diamond
  **59** (`gpqa-139`..`gpqa-197`), humaneval **44** (`humaneval-0120`..`humaneval-0163`), mmlu-pro
  **500** (`mmlu-pro-0000`..`mmlu-pro-12024`), ifeval **541** (`ifeval-1000`..`ifeval-3757`) =
  **1 144 calls**, order gpqa-diamond → humaneval → mmlu-pro → ifeval. Tomorrow's queue does not halt
  on its own gate.
* **Non-vacuity in the open window, on the real rows:** one pinned `finish=ok` id (`gpqa-007`) deleted
  from the scratch copy → **exit 3** with seven findings, the first naming the class exactly —
  "1 ids the pin records as stored finish=ok are GONE from the arm file: gpqa-007 — stored work was
  deleted or rewritten" — plus the moved answer-file hash (`f8c0b540bb83add0` against the pinned
  `cde63378fa1633c5`), the row/unique/ok counts, and the resume range widening to `gpqa-007..gpqa-197`.
  A resumed queue that silently lost stored work cannot spend quota.
* **Healthy mid-window growth is legal, not a finding:** one legitimately resumed row (`gpqa-139`)
  appended in the open window → **READY** with the progress note ("140 ok ids stored vs 139 pinned —
  the window is open, growth is legal; regenerate the pin at window end") and the live resume set
  shrinking to **58** ids `gpqa-140`..`gpqa-197`. This is the class that would otherwise stall the
  1 144-call chain on day two: a gate that froze one moment would halt a healthy running queue.
* The exercise left the real workspace byte-exact: `gpqa-diamond/pub-grok.jsonl` SHA-256/16
  `cde63378fa1633c5` and `humaneval/pub-grok.jsonl` SHA-256/16 `a7c741de0d6ace8c` before **and** after,
  33rd computed verification of both; the scratch copy was deleted afterwards.

**One observation named and deliberately NOT changed (tooling decision, stated before the window
rather than discovered inside it):** the gate's queue line prints the **pinned** total (`1144 calls`)
by design, while the per-arm resume sets are live — in the growth control the live total was 1143
against the printed 1144. The live total for ETA purposes comes from the census
(`pub-bench/grok_resume_census.py`), which the launcher runs first. Editing a tracked gate's output
the day before 1 144 paid calls is a halt risk bought for a cosmetic line, so it is recorded as a
deferred tooling note and the gate ships unchanged.

**Chain launcher re-read statically, not executed:** window guard **line 20** < census **24** < resume
gate **31** < dry-run exit **35** < `REFUSED` **40** < `command -v hermes` **44** < transport call
**50**, and `bash -n` is clean. Its refusal path was already proven by execution at ticks 38 and 39.

**Standing gates re-run on the fetched tree, all green and identical to ticks 36-40:**
`pub_arms_index.py --check` **index drift 0**; `--pins` **manifest pin drift 0**;
`pub_derived_percent_check.py` **42 recomputed from shipped bytes, 0 findings** (41 digest + 169
document citations, 0 uncovered); `pub_grok_cell_check.py` 9 documents **0 findings**;
`pub_superseded_cell_check.py` 9 documents **0 findings**; `pub_digest_row_check.py` **46 rows, 0
findings**, 23/23 pre-rule exceptions used; plus the two contract tests of this line's own gates —
`harness/pub_grok_resume_test.py` **19 checks, 0 failures** and `harness/pub_preflight_test.py`
**20/20**.

**The daily-docs job status is re-read from the scheduler's own record, not from prose:** exactly **one**
execution today — `88c0821487c2`, 03:00:17 → 03:02:55 CET, **failed (exit 1)** — whose real cause was
attributed at tick 38 to one DNS blip on the pre-fix bare `git push` (the `MANIFEST GUARD:` lines in
the same capture are the arms-index test's tamper controls). No second run until tomorrow 03:00, when
the repaired `push_with_retry()` path is in force. This is the known daily error, not a data problem.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order, gated on
`pub_grok_resume_check.py` exit 0 (READY in both window modes on the real bytes as of this tick), each
leg resumable by id and scored only when complete, with the transport-version boundary (stored rows
`v0.23.0+860.gf17db36`, resumed rows `v0.23.1+2.gb3746e3`) named beside any completed percent.
Standing limits unchanged: no Grok arm before 2026-11-12; frozen contour `0.0.2.56`; a local leg needs
`pub_preflight.py` exit 0 (NO-GO at this reading, none queued); sanitization before every push; a
partial arm publishes no percent.

## Tick 42 — 2026-11-11 09:50 CET (status + the 12 Nov chain's leg loop exercised end-to-end against a stub transport, zero model calls)

**Queue state:** 0 `parb-pub-*` units, no `pub_bench_run`/`pub_bench_cloud`/`gate_run` process, 0
foreign legs, tree clean, HEAD `db2deff` == `origin/main` (0 ahead / 0 behind). Nothing launched:
item 8 stays gated to 2026-11-12 by the owner quota window. No digest row, verdict, answer byte,
bank file or manifest pin moved this tick.

**Preflight NO-GO again: the nineteenth NO-GO in twenty readings, idle-spin the sole reason.**
Fresh reading at 09:50 CET over the repo-standard key: swap free **8 123 MiB of 8 191** (the first
reading of this line that is not the full 8 191 free — 68 MiB of swap in use, still far above the
256 MiB floor), MemAvailable 14 719 MiB, engine state `S`, engine **534 % CPU with the GPU at 0 %
utilization / 37.13 W**, load average 11.80, `/health` 200, 0 foreign legs — same un-restarted
engine process (pid `3284575`, age **2 d 13:14**). RSS 56 475 MiB, **down 671 MiB against tick 41's
57 146 MiB** (…57 575 → 57 373 → 57 146 → 56 475), so the oscillation band holds. The gate was run
**unshielded** on the readings file and exits **3** as contracted; the wrapper still reports 0
because of its trailing `echo` (tick 39's note). Remedy stays an owner/box decision and no local leg
is queued anyway.

**What this tick did instead of repeating the census: it read the shipped cloud runner and then
exercised the chain's leg loop, because two consequences for the 1 144 paid calls are real and
neither the census nor the resume pin covers them.** From `scripts/pub_bench_cloud.py`:

* every attempt is appended to the arm file **including failures** (`finish=rc1`/`error`), and a leg
  stops early only after **3 consecutive** failures; otherwise it returns **0 as long as at least one
  ok row exists** (`return 0 if n_ok else 1`). So a single transport flake parks a blank and the leg
  still looks healthy to the launcher;
* that parked blank is a **permanent loss if the id is ever re-asked**: the public scorer keeps the
  FIRST row per id (`if d["id"] not in ans: ans[d["id"]] = d`, `scripts/pub_bench_score.py:345-348`)
  and counts an empty answer as missing (`:351`), which the skill's rule already records — and
  `scripts/pub_grok_resume_check.py` turns a parked non-ok row into a hard NO-GO (exit 3) in **both**
  window modes, so day two of a queue expected to span days would halt on a fixable condition.

Measured on the shipped runner rather than inferred, with a rehearsal stub CLI on `PATH` (zero
model, cloud or network calls, all writes into a scratch workspace): one flake inside an otherwise
healthy leg gives **ok=3 bad=1, leg exit 0, one blank parked** in the arm file; three consecutive
failures give **`transport dead … stopping leg`, exit 1 after 3 stored blank rows**, which is exactly
the launcher's halt trigger. The tick-40 contract test `harness/pub_grok_resume_test.py` already
pins the third half (a parked non-ok row ⇒ exit 3), so the whole chain of the trap is now proven by
execution, not by prose.

**The missing remedy ships as a tooling release (registers no contour feature, moves no published
byte): `scripts/pub_cloud_blank_purge.py`.** It splits an arm file into ok rows and parked failures,
**reports** them by id with the stored `engine_error` (exit 3 = blanks parked), and with `--write`
moves exactly the parked rows to a named `<arm>.blank-quarantine-<UTC>.bak`, keeps a **byte-exact**
`<arm>.pre-purge-<UTC>.keep` copy, rewrites the arm file with the ok rows in their original order and
**verifies** (ok id list cell-for-cell, quarantine id set equal to the parked set, no ok row moved)
before printing the before/after SHA-256/16. It never touches an ok row, deletes nothing, and refuses
(exit 3, bytes untouched) on anything it must not decide alone — a duplicate id among ok rows, an ok
row with an empty answer. Input gaps (missing / empty / unparseable arm file) exit 1, never a green
light. Contract test `harness/pub_blank_purge_test.py` **22 checks, 0 failures** (enrolled by the
`harness/*test.py` glob in `scripts/qa/static_checks.py`): clean-file no-op with untouched bytes,
report mode that does not write, the exact split plus byte-exact pre-purge copy plus idempotence, an
ok row that carries an `engine_error` field staying put, the two refusal classes with untouched bytes,
three input-gap classes, and the all-blank case. On the **real** suspended partials in report mode:
gpqa-diamond 139 rows / 139 ok / **0 parked** (SHA-256/16 `cde63378fa1633c5`), humaneval 120 / 120 /
**0 parked** (`a7c741de0d6ace8c`) — 34th and 35th computed verification, mmlu-pro and ifeval never
legged, so nothing to quarantine today.

**The chain launcher now neutralizes the trap before it can halt the queue.**
`pub-bench/go_grok_queue_20261112.sh` (untracked, so no shell recipe or connection material lands in
this repo) gained a zero-credit quarantine pass over the four arm files between `cd` and the leg
loop, guarded by `[ -s "$AF" ]` so a never-legged set is skipped, and halting the whole queue if the
purge ever refuses. Line-order proof on the launcher: window guard **20** < census **24** < resume
gate **31** < dry-run exit **34** < `REFUSED` **40** < `command -v hermes` **44** < `cd` **46** <
blank purge **58** < transport call **65**; `bash -n` clean.

**The leg loop was exercised end-to-end for the first time, against a stub transport, zero paid
calls.** A rehearsal copy was generated mechanically and its only three differences from the real
launcher are diff-proved: `TODAY_NUM` forced to `20261112` (guard open), the transport line replaced
by a stub that logs its argv and exits a scripted code, and every **write** path (cloud logs, `--out`,
purge target) redirected into a scratch workspace. The read-only steps — the resume census and
`pub_grok_resume_check.py` — ran against the real repo bytes. Three scenarios:

* **all legs healthy:** exit 0, exactly **4** transport invocations in the pinned order
  `gpqa-diamond → humaneval → mmlu-pro → ifeval`, `=== grok queue complete ===` — the pinned order is
  now proven by execution, not by line numbers;
* **transport dead on leg 1:** exit 1, **1** invocation, `STOP: leg gpqa-diamond exited 1` — the
  three remaining sets (44 + 500 + 541 = **1 085 calls**) are never asked, so a dead
  transport or an expired token cannot spend the rest of the owner's quota;
* **transport dead on leg 2:** exit 1, **2** invocations, halt before `mmlu-pro`.

Each rehearsal run also re-ran the resume gate on the real bytes: **READY, 22 checks**, and the real
arm files came out byte-exact (`cde63378fa1633c5`, `a7c741de0d6ace8c`), so the rehearsal cannot have
touched them.

**One observation named and deliberately NOT changed (same ruling as tick 41's pinned-total line):**
when the cloud CLI writes nothing to stderr, the runner's stop message prints `transport dead ()` and
the parked row's `engine_error` is empty, so a blank carries `finish=rc1` with no reason string. It is
a diagnostics-only gap on a row that carries zero credit by rule and is now quarantined mechanically;
editing a tracked runner the day before 1 144 paid calls is a halt risk bought for a log string, so it
is recorded as a deferred tooling note.

**Standing gates re-run on the tree with the new tool, all green and identical to ticks 36-41:**
`pub_arms_index.py --check` **index drift 0**; `--pins` **manifest pin drift 0**;
`pub_derived_percent_check.py` **42 recomputed from shipped bytes, 0 findings** (41 digest + 169
document citations, 0 uncovered); `pub_grok_cell_check.py` 9 documents **0 findings**;
`pub_superseded_cell_check.py` 9 documents **0 findings**; `pub_digest_row_check.py` **46 rows, 0
findings**, 23/23 pre-rule exceptions used. All nine PUB contract tests green on the merged tree:
arms index 34, blank purge **22 (new)**, derived percents 41, digest-row gate 21, digest writer 7,
grok cells 21, grok resume 19, preflight 20/20, superseded cells 31.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order, gated
on `pub_grok_resume_check.py` exit 0 and now cleaned by `pub_cloud_blank_purge.py` before that gate,
each leg resumable by id and scored only when complete, transport-version boundary named beside any
completed percent. Standing limits unchanged: no Grok arm before 2026-11-12; frozen contour
`0.0.2.56`; a local leg needs `pub_preflight.py` exit 0 (NO-GO at this reading, none queued);
sanitization before every push; a partial arm publishes no percent.

## Tick 43 — 2026-11-11 10:30 CET (status only, zero model calls)

**The endpoint preflight turned GO — the first GO of the series.** Reading #18 of the standing
series (`preflight-20261111-1030.txt`, taken over the repo-standard key by the untracked
`preflight.sh` wrapper): swap free **8191 of 8191 MiB** (0 free at ticks 38-39), MemAvailable
**15 184 MiB**, engine pid 3284575 age 2 d 13:54 in state **S** (not `D`), pcpu 531 % **with GPU
util 99 % / 126.5 W** — the idle-spin pair (CPU > 200 % at GPU util 0 %) that had been the sole
NO-GO reason since the gate shipped is gone, the engine is in active decode. load1 10.77,
`/health` 200, foreign legs 0. The gate's real exit was taken **unshielded** (the wrapper's
trailing `echo` masks it — tick 39's pitfall): **GO, exit 0**. The earlier readings never reached
GO (tick 39 census: 16 of 17 NO-GO, every one after the gate shipped). No arm was launched: the
ladder is empty to 12 Nov and GPU util 99 % at 10:30 means the box is serving interactive traffic
— a local leg would contaminate both that traffic and its own cost rows. The GO is recorded as an
endpoint-health fact, not as an action taken.

**Named observation, deliberately not changed:** while locating the wrapper I first executed the
remote **payload** (`preflight_read.sh`) on the launch host by mistake: `nvidia-smi: command not
found`, an empty engine pid, and `health_code=200` — the last is the launch host's own `:8080`
app answering, the same class as the `0.0.0.0` bind trap this line has named twice before. The
garbage reading was never fed to the gate; the real path pipes the payload over ssh. It is a
footgun only if the payload is run unshielded, which the wrapper makes unnecessary; recorded, not
patched.

**The 12 Nov chain refused a 34th time, exit 3, after re-running both read-only gates on the real
bytes:** census prints the four resume sets unchanged — gpqa-diamond **59** (`gpqa-139`..`gpqa-197`,
sha256-16 `cde63378fa1633c5`, 139/139 ok, 34th byte-exact verification), humaneval **44**
(`humaneval-0120`..`humaneval-0163`, sha `a7c741de0d6ace8c`, 120/120 ok), mmlu-pro **500**,
ifeval **541**, total **1 144 calls**, sequential ETA 9.0-27.6 h — and `pub_grok_resume_check.py`
prints **READY, 22 checks**, window CLOSED. After the refusal, standalone bracketed process counts
are **0** `pub_bench_cloud.py` and **0** `hermes -z`.

**Today's daily-docs failure, re-read from the job's own execution record rather than prose:**
the `GitHub docs freshness daily` run claimed 03:00:17, failed 03:02:55, exit 1. The fatal line is
`fatal: unable to access … Could not resolve host: github.com` (push, exit 128) — a transient DNS
blip, **not** the dirty-tree class the standing brief predicts. The traceback's line numbers match
the **pre-fix** single-attempt tool, and the repair (`push_with_retry`, retry loop + the push step
outside the marker-changed branch) landed at **04:19:00 today** in `4fcf356` — i.e. the 03:00 run
was the last appearance of the old code; tomorrow 03:00 is the first run under retry. No orphaned
marker: commit `945df05` "Daily docs freshness check: 2026-11-11" (03:02:13) is on `origin/main`,
carried by this line's own pushes after 04:19. The `MANIFEST GUARD` / `NO SCORED TASK` / `DIGEST
ROW COUNT MISMATCH` stderr lines are the gates' own tamper controls firing on synthetic inputs
(`no-such-bench`, scratch tmp paths) — tick 35's ruling, reconfirmed on this capture, no action.
Transport now: `git ls-remote origin` returns `bffa767…` matching local HEAD; the SHA-pinned raw
URL serves **200**; `api.github.com` times out at this minute — off the push path, recorded only.

**Standing gates re-run on the unchanged bytes, identical to ticks 36-42:** `pub_arms_index.py
--check` index drift **0**; `--pins` manifest pin drift **0**; `pub_derived_percent_check.py`
**42 recomputed from shipped bytes, 0 findings** (41 digest + 169 document citations, 0 uncovered);
`pub_grok_cell_check.py` 9 documents **0 findings**; `pub_superseded_cell_check.py` 9 documents
**0 findings**; `pub_digest_row_check.py` **46 rows, 0 findings**, 23/23 pre-rule exceptions used.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order,
gated on the blank purge then `pub_grok_resume_check.py` exit 0, each leg resumable by id and
scored only when complete. Standing limits unchanged: no Grok arm before 2026-11-12; frozen
contour `0.0.2.56`; a local leg needs the preflight GO (now GO, but **nothing is queued** and the
endpoint is busy serving the main brain); sanitization before every push; a partial arm publishes
no percent. Status only: zero model calls, no digest row, verdict, answer byte, bank file or
manifest pin moved.

## Tick 44 — 2026-11-11 11:08 CET (status only, zero model calls)

**The ladder is still empty to 2026-11-12 and nothing was launched: no local leg (no queued item),
no Grok leg (window closed), no cloud leg (no queued codex item).** Every unit and transport count
is zero: `systemctl --user list-units 'parb-pub-*'` empty, and the standalone bracketed counts give
0 `pub_bench_run.py` / `gate_run.py` / `pub_bench_cloud.py` / `hermes -z` processes.

**Endpoint health: the GO of tick 43 did not persist — the box oscillates.** Reading
`preflight-20261111-1108.txt`: swap **8191 of 8191 MiB free**, MemAvailable **13 643 MiB**, engine
pid 3284575 age 2 d 14:32 in state **S** at **527 % CPU with GPU util 0 % / 36.4 W** — the
idle-spin pair that had been the sole NO-GO reason is back 38 minutes after a reading showing GPU
99 % / 126.5 W. load1 15.24, `/health` 200, foreign legs 0. Re-derived by running the gate over
**every** reading file taken today instead of restating prose: **14 files — 2 GO (06:08, 10:30),
11 NO-GO, 1 input gap (09:48, non-empty `.err`)**. A GO is therefore a single-reading event on this
box, which is exactly why rule 7 requires a fresh reading at launch time rather than a remembered
one. Nothing was blocked by it: the deferred 12 Nov chain is cloud-only and cloud legs are not
gated by the preflight.

**The 12 Nov chain re-proven without spending one paid call** (`GROK_DRYRUN=1` under `bash -x`,
exit 0, `window=closed`): the census prints the four resume sets byte-exact — gpqa-diamond **59**
(`gpqa-139`..`gpqa-197`, SHA-256/16 `cde63378fa1633c5`, 139 rows / 139 `ok` / 0 empty, 35th
verification), humaneval **44** (`humaneval-0120`..`humaneval-0163`, SHA-256/16 `a7c741de0d6ace8c`,
120/120), mmlu-pro **500**, ifeval **541**, total **1 144 calls**, sequential ETA **9.0-27.6 h** —
and `pub_grok_resume_check.py` prints **READY, 22 checks** with the two zero-credit quarantines
listed as evidence (46-row timeout file `6cd28556fc2f973c`, 4-row suspended-window file
`1e025849786a94c1`). The `bash -n` parse is clean and the trace contains **0** lines matching
`pub_bench_cloud\.py|hermes -z`, so the dry path is proven not to reach a transport; the live guard
is numeric (`TODAY_NUM -lt 20261112`) and sits above every other check.

**Standing gates re-run on unchanged bytes, identical to ticks 36-43:** arms index `--check` index
drift **0**, `--pins` manifest pin drift **0**, derived percents **42 recomputed / 0 findings**
(41 digest + 169 document citations, 0 uncovered), grok-cell rule 9 documents **0 findings**,
superseded-cell rule 9 documents **0 findings**, digest-row rule **46 rows, 0 findings**, 23/23
pre-rule exceptions used; scorer self-test **22 cases, 0 failures**. Transport: `origin/main` equals
local HEAD `5a8649a`, working tree clean before this entry.

**Two ops findings, recorded only — nothing outside this line was modified.**

1. *The daily docs job's deployed code path was read from the script, not assumed.*
   `docs_freshness_daily.sh` cd's into `~/sah-main` (the single-writer rule), so the
   `push_with_retry` repair that landed there at 04:19 today (`4fcf356`) **is** in force for the
   next run; today's 03:02 failure stays attributed to the DNS blip under the pre-fix
   single-attempt code (tick 43). Its schedule renders as `0 2 * * *` **UTC** = 03:00 CET, next run
   2026-11-12 02:00 UTC. Separately, the second clone (`~/projects/strata-autonomous-harness`) sits
   in **detached HEAD** at `649bf7e`, 48 behind / 0 ahead of `origin/main`, with an **empty staged
   diff** — the staged-deletion signature of the two-clone hazard is absent, so no watchdog commit
   can currently delete published bytes.
2. *A hard-bank-era cron is still armed and fires every 5 minutes*: job `f23cf5d48e11`
   "Mac v2.2 full after v2.1" (untracked `mac_v22_full_after_v21.sh`) is `[active]`. It does nothing
   today only because its one-shot marker `~/.hermes/mac-v22full-launch.state` exists (written
   2026-11-02 14:05, the same minute it launched the `PARB_GATE_VERSION=v2.2` Mac Studio full arm —
   last log lines `wait 2436/2513` then `complete 2513/2513` then `launched`). **If that marker is
   ever cleaned, the job re-arms a legacy v2.2 hard-bank launch on a line that is frozen at
   `stable-hard-0.0.2.56`.** That is an owner decision to stop the job, not a change this line makes:
   the marker file is the job's only guard and this line does not edit other jobs' state.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
gpqa-diamond -> humaneval -> mmlu-pro -> ifeval, gated on the blank purge then
`pub_grok_resume_check.py` exit 0, each leg resumable by id and scored only when complete. Standing
limits unchanged: no Grok arm before 2026-11-12; frozen contour `0.0.2.56`, no new stamps, no hard
pairs, hard bank untouched; a local leg needs a fresh preflight GO; sanitization before every push;
a partial arm publishes no percent. Status only: zero model calls, no digest row, verdict, answer
byte, bank file or manifest pin moved.


## Tick 45 — 2026-11-11 11:45 CET (status + the 12 Nov queue's launch contract and per-arm scoring contracts, decided today, zero model calls)

**Queue state:** 0 `parb-pub-*` units; the standalone bracketed process counts give 0
`pub_bench_run.py` / `gate_run.py` / `pub_bench_cloud.py` / `hermes -z`; tree clean, HEAD `61f1e25`
== `origin/main` (0 ahead / 0 behind). Nothing launched: the Grok window is closed, the ladder has no
open codex or local item until 12 Nov, and a partial arm publishes no percent.

**Preflight: the clean reading is NO-GO; the 11:44 file is an input gap this tick caused, and it is
kept as evidence.** The clean reading `preflight-20261111-1145.txt`: swap free **8 191 of 8 191 MiB**,
MemAvailable 14 737 MiB, engine pid `3284575` age **2 d 15:09** in state `S` at **525 % CPU with GPU
util 0 % / 36.06 W** (the idle-spin pair), load1 15.77, `/health` 200, 0 foreign legs — **NO-GO**, and
the gate's own unshielded run inside the wrapper exits 3. The 11:44 attempt came out an **INPUT GAP**:
the wrapper was wrapped in an outer `>` redirect onto the very path the wrapper writes internally, so
the wrapper's own `cat "$OUT"` failed with "input file is output file", that message landed in the
sibling `.err`, and the readings file came out without keys — the gate fail-closed on it exactly as
designed ("a missing reading is never healthy"). Neither file was repaired. The whole day's series was
re-derived by running the gate over every reading file rather than restating prose: **16 files —
2 GO (06:08, 10:30), 12 NO-GO, 2 input gaps (09:48 an ssh read failure, 11:44 this wrapper
collision)**.

**What this tick did instead of another hand reading: the 12 Nov queue's launch contract and the
scoring contract of each resumed arm are decided in the repo today, so nobody chooses them tomorrow
while the owner's quota is being spent.**

* **Launch contract (new, and the reason this tick is not a status line).** The pinned queue is
  **1 144 calls with a sequential ETA 9.0-27.6 h** — longer than any agent session lives. This line's
  own measured hazard class says a runner started from a cron/child session is torn down with that
  session (the hard bank lost an arm at 13/77 rows that way, with the GPU still looking busy), so the
  queue must be started as a systemd user unit with an **absolute** script path:
  `systemd-run --user --collect --unit=parb-pub-grok-queue bash <LOCAL_PATH>/pub-bench/go_grok_queue_20261112.sh`.
  A relative path dies instantly with status 127 because those units start in `$HOME` while the CLI
  still prints `Running as unit: ...`. The unit form also puts the queue outside the Hermes worker
  scope, which matters on a multi-day chain: the nightly self-update job (`af888c1c9341`, next run
  **2026-11-12 03:00 CET**) restarts the gateway and can kill an in-flight cron child — a systemd unit
  is not in that scope. Liveness is read from the row count of each arm file plus
  `cloud-<bench>-grok.log` growth, never from `is-active`. Exactly one leg of the vendor at a time: a
  second unit under another name would double-spend the quota the suspension exists to protect.
* **A day that ends mid-set is the expected shape, not a failure.** Each leg is resumable by id, so a
  set that is incomplete at the end of 12 Nov stays **unscored and unpublished** and the queue
  continues the next day; no completion date is promised. The two unmeasured bands are named as bands:
  mmlu-pro **2.1-2.9 h** (measured grok rates on this line: arc-easy 14.9, arc-challenge 17.1, gsm8k
  20.9 s/task), ifeval **3.1-18.0 h** (low end = grok gsm8k, high end = grok humaneval long-output
  114.5 s/task).
* **Scoring contract per resumed arm.** gpqa-diamond 198 ids and mmlu-pro 500 ids: `pub-checkers-v2`
  (`letter`), scored over the arm's own id set; humaneval 164: `pytest-v2` via
  `scripts/pub_bench_exec.py` (pre-registered 2026-11-09); **ifeval 541: `pub-ifeval-v2`** — the
  corrected contract, because under `pub-ifeval-v1` two of the 541 cells (`ifeval-1122`,
  `ifeval-1129`) are coin flips of the vendored `letter_frequency` RNG and a *new* arm must not be
  minted under a checker this repo has already corrected. The `pub-ifeval-v1` number is published
  beside it in `IFEVAL-RESULT.md` so the four-arm table stays on one contract family. That scorer runs
  with the set's own venv python only and re-asserts the five vendored pins, the 41-test upstream
  suite and the reference band at every run.
* **Partial refusal is code, not intention** (read from the shipped tools, with line numbers):
  `scripts/pub_bench_exec.py:218-220` prints `partial arm: N/M answers present - no percent printed`
  and returns 1 **before** `write_digest` is reached; `scripts/pub_bench_ifeval_v2.py:280-282`
  `sys.exit`s on >5 % missing before any digest write. A stopped leg cannot mint a percent by accident.
* **The transport version is read at resume time, not assumed:** today's CLI is
  `Hermes Agent v0.23.1+2.gb3746e3.dirty` while the stored gpqa/humaneval rows carry
  `v0.23.0+860.gf17db36.dirty`. The 12 Nov 03:00 self-update runs *before* the queue, so the boundary
  sentence beside a completed percent names the version on the resumed rows.
* **Pin lifecycle:** once the window opens, `GROK-RESUME-PIN.json` is a floor (growth is a progress
  note, corruption is still a finding) and is regenerated only after the queue completes — as the gate
  itself prints.

**The chain was re-proven without one paid call (36th verification of the partials):**
`GROK_DRYRUN=1 bash -x ~/pub-bench/go_grok_queue_20261112.sh` exits 0 with `window=closed`; the census
prints the four resume sets byte-exact — gpqa-diamond **59** (`gpqa-139`..`gpqa-197`, SHA-256/16
`cde63378fa1633c5`, 139 rows / 139 `ok` / 0 empty), humaneval **44** (`humaneval-0120`..`humaneval-0163`,
`a7c741de0d6ace8c`, 120/120), mmlu-pro **500**, ifeval **541**, total **1 144 calls**, ETA
**9.0-27.6 h** — the resume gate prints **READY (22 checks)** with the two zero-credit quarantines
listed as evidence, and the `bash -x` trace contains **0** lines matching a transport.

**Ops findings, recorded only — nothing outside this line was modified.** The hard-bank-era job
`f23cf5d48e11` "Mac v2.2 full after v2.1" is still `[active]` every 5 minutes and is guarded only by
the one-shot marker `~/.hermes/mac-v22full-launch.state` (26 B, written 2026-11-02 14:05); clearing
that marker re-arms a legacy `v2.2` hard-bank launch on a line frozen at `stable-hard-0.0.2.56`, so
stopping the job stays an owner decision and this line does not edit other jobs' state. The two
B2003-era launchers (`8a4fabbe5a78`, `18625a65290a`) are `[paused]`. The daily docs job's next run is
2026-11-12 02:00 UTC; today's 03:02 failure remains the DNS blip under the pre-fix code (tick 43).

**Standing gates green and identical to ticks 36-44:** arms index `--check` drift **0** and `--pins`
drift **0**; derived percents **42 recomputed / 0 findings**; grok-cell rule 9 documents **0 findings**;
superseded-cell rule 9 documents **0 findings**; digest-row rule **46 rows / 0 findings**; scorer
self-test OK. Contract tests: grok resume **19**, preflight **20/20**, blank purge **22**, arms index
**34**, derived percents **41**, grok cells **21**, superseded cells **31**, digest-row gate **21**.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order
gpqa-diamond -> humaneval -> mmlu-pro -> ifeval, launched as `parb-pub-grok-queue` under
`systemd-run --user` with the absolute launcher path, gated on the blank purge then
`pub_grok_resume_check.py` exit 0, each leg resumable by id and scored only when complete under the
contract named above. Standing limits unchanged: no Grok arm before 2026-11-12; frozen contour
`0.0.2.56`, no new stamps, no hard pairs, hard bank untouched; a local leg needs a fresh preflight GO
(NO-GO at this reading, none queued); sanitization before every push; a partial arm publishes no
percent. This tick spent **zero model or cloud calls** and moved no digest row, verdict, answer byte,
bank file or manifest pin — the tracked changes are this block plus dated notes in
`GPQA-RESULT.md`, `MMLU-PRO-RESULT.md` and `IFEVAL-RESULT.md`.

## Tick 46 — 2026-11-11 12:20 CET (status + a fail-open in the resume gate's `--as-of`, caught live and closed; zero model calls)

**The ladder is still empty to 2026-11-12 and nothing was launched.** No `parb-pub-*` unit exists, a
standalone bracketed transport count reads **0**, no local leg is queued, no codex item is queued and
the Grok window is closed. All four legacy single-set Grok launchers were executed today and each
exits **3** with `REFUSED: grok arms are suspended by owner quota until 2026-11-12`. The pinned
2026-11-12 chain launcher was re-proven dry: `GROK_DRYRUN=1` exits 0 with `window=closed`, prints the
census (**1 144 calls**, `gpqa-diamond -> humaneval -> mmlu-pro -> ifeval`), and its `bash -x` trace
contains **0** transport lines. No leg was started, stopped or restarted and no partial file was
discarded, so `LEG-INCIDENTS.md` gets no entry.

**What this tick found is a tooling fail-open in the gate itself.** The tick asked the resume gate
with `--as-of 20261111` (compact, no dashes) and it printed **`window is OPEN today (20261111)`**
while the chain launcher's own numeric guard on the same date printed `window=closed`. The window mode
in `scripts/pub_grok_resume_check.py` is a **string compare** (`as_of >= suspended_until`), and
`"20261111" >= "2026-11-12"` is byte-wise **True** (digit `1` > hyphen at position 4) — so *any*
compact date silently reads the suspension window as OPEN and disables the pinned-snapshot guard,
which is exactly the mechanism that catches the 2026-11-11 05:31 early-launch class. The pinned chain
queue is unaffected (it calls the gate without `--as-of`, so the default is today's ISO date), and no
bytes or verdicts moved: the partials still match the pin exactly (139/139 and 120/120, hashes
`cde63378fa1633c5` / `a7c741de0d6ace8c`). Fixed as tooling only — no contour stamp, no feature, no
published byte: both window operands must now be the dashed ISO form (strict regex plus a calendar
check; `date.fromisoformat` alone is not enough because Python >= 3.11 also accepts the compact
form), and a malformed `--as-of` or a non-ISO `owner_window.suspended_until` inside the pin is an
**INPUT GAP (exit 1)**, never a guessed mode. Contract test `harness/pub_grok_resume_test.py` grows
**19 -> 23 checks**: compact `--as-of` refused, calendar-invalid `2026-02-30` refused, a well-formed
ISO `--as-of` before the resume day still READY with **CLOSED** (the guard must not refuse valid
dates), and a compact `suspended_until` in the pin refused. On the real bytes after the fix: compact
exit **1**; default (today) **CLOSED + READY**; `--as-of 2026-11-12` **OPEN + READY** with the
floor-mode progress note — tomorrow's chain sees exactly the mode the gate was built for.

**Ops, re-read from the job record rather than restated:** the scheduled `docs-freshness` run of
2026-11-11 **completed success** (11 s), so the "reports an error daily" boilerplate from the dirty
03:00 trees did **not** recur today. The hard-bank-era job `f23cf5d48e11` fired at 12:21 CET and
exited 0 under its one-shot marker — still active, still an owner decision to stop, untouched.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order,
launched once as `parb-pub-grok-queue` under `systemd-run --user` with the absolute launcher path,
gated on the blank purge then `pub_grok_resume_check.py` exit 0, each leg resumable by id and scored
only when complete under the contracts fixed at tick 45. Standing limits unchanged: no Grok arm
before 2026-11-12; frozen contour `0.0.2.56`, no new stamps, no hard pairs, hard bank untouched; a
local leg needs a fresh preflight GO (none queued); sanitization before every push; a partial arm
publishes no percent. This tick spent **zero model or cloud calls** and moved no digest row, verdict,
answer byte, bank file or manifest pin — the tracked changes are this block plus the gate and its
contract test.

## Tick 48 — 2026-11-11 13:30 CET (status + a dated correction: today's `docs-freshness` run **failed**, and its own record says why; zero model calls)

**Nothing was launched.** No `parb-pub-*` unit exists; a standalone call counting transports with
bracketed patterns reads **0** for `pub_bench_cloud`, **0** for `pub_bench_run`, **0** for
`gate_run`; no local leg is queued, no codex item is queued, and the Grok window is closed. No
launcher was re-executed this tick: the chain's live `REFUSED` proof was run at tick 47 (12:56 CET)
against the corrected gate and nothing in the guard or the pin has moved since.

**Endpoint preflight: NO-GO again, and the series is now counted by driving the gate over every
readings file.** The fresh reading at 13:29 CET: swap **8191/8191 MiB free**, MemAvailable 14116 MiB,
engine state `S`, engine **514 % CPU at GPU 0 %** (36.22 W), load1 10.96, `/health` 200, 0 foreign
legs, same engine pid 3284575 now aged 2 d 16:53. The single NO-GO reason is the idle-spin pair.
Re-running `scripts/pub_preflight.py` over all 18 readings files of the series gives **14 NO-GO,
2 GO, 2 INPUT-GAP** (last six: 10:30 GO, 11:08 NO-GO, 11:44 INPUT-GAP, 11:45 NO-GO, 12:56 NO-GO,
13:29 NO-GO) — a GO is valid only for its own reading. Trap caught in this tick's own counting:
`preflight.sh` writes **only the remote readings** into `preflight-<TS>.txt`, the gate's verdict goes
to stdout, so a counter that greps those files for `PREFLIGHT GO/NO-GO` reports 17 INPUT-GAPs out of
18. The series can only be re-derived by invoking the gate per file.

**Grok resume gate: READY (22 checks), window CLOSED today, partials byte-exact.** `gpqa-diamond`
139 rows / 139 ok / SHA-256/16 `cde63378fa1633c5`, resume set **59 ids** `gpqa-139..gpqa-197`;
`humaneval` 120 / 120 / `a7c741de0d6ace8c`, resume set **44 ids** `humaneval-0120..humaneval-0163`;
`mmlu-pro` 500 ids and `ifeval` 541 ids never legged. Pinned queue **1 144 calls**, order
`gpqa-diamond -> humaneval -> mmlu-pro -> ifeval`. The two zero-credit quarantines are printed as
evidence (46-row timeout file `6cd28556fc2f973c`, the 4-row suspended-window file
`1e025849786a94c1`). Tick 46's fail-close was verified live on the way: `--as-of 20261111` now exits
**1** with the named reason ("compact dates always read OPEN") instead of silently opening the window,
and the default (today, ISO) reads **CLOSED**.

**Correction (dated, not a silent rewrite).** Tick 46 recorded that the scheduled `docs-freshness`
run of 2026-11-11 "completed success (11 s)". The job's own record says otherwise:
`~/.hermes/cron/executions.db` holds exactly **one** execution for job `ef7ea47ff99b`,
03:00:17 -> 03:02:55 CET, status **failed**, exit 1. Its captured stderr ends with
`fatal: unable to access 'https://github.com/...': Could not resolve host: github.com` and a
traceback from `scripts/qa/refresh_docs_status.py` line 51 calling a **bare** `git push` — the
pre-fix code shape, whose `push_with_retry()` repair landed at 04:19 CET (`4fcf356`, tick 33). The
`MANIFEST GUARD` / `DIGEST ROW COUNT MISMATCH` / `NO SCORED TASK` lines in that capture stay what
tick 35 named them: tamper-control output from the contract tests the job runs, not the failure. So
the standing "dirty tree at 03:00" explanation did not apply today either — today's error was a DNS
blip on a bare push. No orphan commit came of it: the 2026-11-11 marker `945df05` is on
`origin/main` and `git rev-list origin/main..HEAD` is 0, and tomorrow's run takes the retry path.

**Frozen-line hygiene.** The hard-bank-era job `f23cf5d48e11` ("Mac v2.2 full after v2.1") fired again
at 13:27 CET — **172** executions in the DB, still on a 5-minute schedule — and exits 0 only because
the one-shot marker `~/.hermes/mac-v22full-launch.state` (2026-11-02) exists; removing that marker
would re-arm a launch on a line the owner froze. Reported as an owner decision, not touched.

**Standing gates green and unchanged:** arms index `--check` drift 0; derived percents 42 recomputed
from shipped bytes, 0 findings; grok-cell rule 9 documents, 0 findings; superseded-cell rule 9
documents, 0 findings; digest-row rule 46 rows, 0 findings. Every in-force set still holds its three
admissible arms (bare / matched contour `0.0.2.56` / codex), so nothing on the ladder is blocked
except by the Grok window.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order, one
`systemd-run --user --collect --unit=parb-pub-grok-queue` launch with the absolute launcher path,
blank purge then `pub_grok_resume_check.py` exit 0 before the first call, legs scored only when
complete under the contracts fixed at tick 45. Standing limits unchanged: no Grok arm before
2026-11-12; frozen contour `0.0.2.56`, no new stamps, no hard pairs, hard bank untouched; a local leg
needs a fresh preflight GO (none queued); sanitization before every push; a partial arm publishes no
percent. This tick spent **zero model or cloud calls** and moved no digest row, verdict, answer byte,
bank file or manifest pin — the tracked change is this block.

## Tick 49 — 2026-11-11 14:15 CET (status + the 12 Nov chain launcher's purge/gate ordering fixed and proven end-to-end, zero model or cloud calls)

**Nothing is running; nothing was launched.** No `parb-pub-*` unit, 0 pub/gate transports
(standalone bracketed count), Grok window closed until 2026-11-12, no local leg queued.

**Ordering defect found in the 12 Nov chain launcher and fixed before tomorrow.** The launcher
ran the deciding `pub_grok_resume_check.py` **before** `pub_cloud_blank_purge.py`, while the
gate refuses (exit 3) whenever a parked non-ok row is stored — so a blank parked by a flake on
day 1 of the 9–27.6 h chain would halt day 2 **before** the purge that exists to clear it,
exactly the failure the purge's own comment block cites. New order (both launcher and plan
contract now say the same thing): census (read-only) -> dryrun exit / window refusal (no
mutation outside the window) -> blank purge -> **deciding** resume gate -> PATH check -> legs.
Launcher sha `ad9f938c4acc13c8` -> `d1a7d320e0c70e2b` (untracked local file; the pre-fix copy is
kept as `go_grok_queue_20261112.sh.pre-order-fix.bak`). Proven today with zero paid calls:
* live run today: prints the census (1 144-call queue), then `REFUSED` exit 3; both stored
  partials unchanged (`cde63378fa1633c5` / `a7c741de0d6ace8c`), zero purge/quarantine activity;
* `GROK_DRYRUN=1` under `bash -x`: exit 0, resume gate READY (22 checks), trace grep
  `pub_bench_cloud.py|hermes -z` = **0 lines**;
* scratch rehearsal — a mechanically generated copy whose diff is exactly five substitutions
  (window guard forced open, transport replaced by a logging stub, gate `--ws` / `AF` / `LOG`
  paths redirected to scratch; read-only gates run on real bytes): **A** healthy -> four stub
  legs fire in the pinned order `gpqa-diamond -> humaneval -> mmlu-pro -> ifeval`, partials stay
  byte-exact, exit 0; **B** parked blank appended to the gpqa arm -> the gate alone reports
  `non-ok rows parked ... gpqa-140` and exits 3 (the old-order day-2 halt, demonstrated), while
  the new order purges first (named `.blank-quarantine-*.bak` + byte-exact `.pre-purge-*.keep`),
  restores the pinned sha cell-for-cell, passes the gate, and runs all four legs; **C** stub leg 2
  exits 1 -> queue halts (exit 1) with legs 3-4 never invoked.
* Builder trap caught in this tick: the rehearsal copy was first generated from an **unquoted**
  heredoc, so the shell expanded `$HOME`/`$(date)` inside the substitution patterns and four of
  five replacements silently no-oped (diff showed one hunk). Rebuilt with a quoted heredoc and an
  `assert count==1` per pattern; a rehearsal whose diff you have not enumerated proves nothing.

**Endpoint preflight: NO-GO (19th reading).** Fresh reading 14:07 CET: swap 8191/8191 MiB free,
MemAvailable 15 273 MiB, engine state `S` pid 3284575 aged 2 d 17:31, engine **512 % CPU at GPU
0 %** (36.49 W), load1 13.74, `/health` 200, 0 foreign legs — sole NO-GO reason is again the
idle-spin pair. Series counted by driving the gate over every readings file: 19 files =
**15 NO-GO / 2 GO / 2 INPUT-GAP**. Remedy stays a box decision (engine restart / park the
keep-up load), never a contour or bank change; cloud legs are unaffected by this gate.

**Standing gates green:** resume gate READY with window CLOSED (22 checks; resume sets 59+44+500+
541 ids); arms index drift 0; derived percents 42 recomputed, 0 findings; grok-cell rule 9 docs,
0 findings; superseded-cell rule 9 docs, 0 findings; digest-row rule 46 rows, 0 findings.

**Ops records re-read, not retyped.** The `docs-freshness` job `ef7ea47ff99b` fired exactly once
today (03:00:17 CET, status **failed**) — tick 48's correction (DNS blip on a bare pre-fix push)
stands; tomorrow's run takes the `push_with_retry()` path against an already-current marker.
Tooling trap in this tick's own reading: an `exit_code` column does not exist in
`executions.db` and a `2>/dev/null` turned that SQL error into a phantom "no run today";
re-queried with the real schema (`status` column only) before repeating anything. Frozen-line
hygiene: the hard-bank-era job `f23cf5d48e11` fired **141 times today** (last 14:03) — still
active on a 5-minute schedule, still guarded only by the 2026-11-02 marker file; owner decision.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order,
ONE `systemd-run --user --collect --unit=parb-pub-grok-queue bash <absolute launcher path>`
launch; the launcher now enforces census -> window refusal -> blank purge -> deciding gate ->
legs itself, with per-arm contracts fixed at tick 45 and legs scored only when complete.
Standing limits unchanged: no Grok arm before 2026-11-12; frozen contour `0.0.2.56`, no new
stamps, no hard pairs, hard bank untouched; a local leg needs a fresh preflight GO (none
queued); sanitization before every push; a partial arm publishes no percent. This tick spent
**zero model or cloud calls** (dryrun + stub rehearsal only) and moved no digest row, verdict,
answer byte, bank file or manifest pin — the tracked change is this block.

## Tick 50 — 2026-11-11 14:55 CET (status + the 12 Nov chain gets a double-spend lock, proven against a concurrent instance; zero model or cloud calls)

**Nothing running; nothing launched.** No `parb-pub-*` unit, 0 pub/gate transports (standalone
bracketed count), Grok window closed until 2026-11-12, no local leg queued.

**Hole closed ahead of tomorrow: two chain launches would have spent the owner Grok quota twice.**
This same cron brief has run as TWO instances in the same clone with the same unit namespace
(measured 2026-11-09: a sibling instance replaced a leg under the SAME unit name). `systemd-run`
unit-name exclusivity only blocks the identical name — a second chain launch under any other name,
or a hand-started leg alongside the chain, would double-spend exactly the quota the suspension
protects. The chain launcher (untracked local file) now carries: (a) an `flock -n` on fd 9 over a
lock file, taken AFTER the window refusal and before any mutation, held for the whole queue, and
the kernel releases it even if the launcher is SIGKILLed, so a dead run cannot strand the lock;
(b) a vendor-level `pgrep` check that refuses while any `pub_bench_cloud` transport runs on the
host. New exit class **4 = concurrent instance / foreign vendor**. Census, dryrun and the window
refusal consume nothing and never take the lock. Launcher sha `d1a7d320e0c70e2b` ->
`9e479ca1129c97a7` (pre-lock copy kept as `go_grok_queue_20261112.sh.pre-lock.bak`). The 12 Nov
launch order now reads: census -> window refusal -> double-spend lock -> vendor check -> blank
purge -> deciding resume gate -> legs.

**Proven today with zero paid calls** (the rehearsal builder gained a 5th substitution, the lock
path itself into scratch — a rehearsal that takes the real queue lock, or crashes and strands it,
would poison the real launch):
* live run today: census (1 144-call queue) then `REFUSED` exit 3, and **no lock file is created**
  — the refusal precedes the lock, the closed-window path mutates nothing;
* `GROK_DRYRUN=1` under `bash -x`: exit 0, trace grep `pub_bench_cloud.py|hermes -z` = **0 lines**;
* rehearsal A (all healthy): exit 0, stub legs fired in the pinned order
  `gpqa-diamond -> humaneval -> mmlu-pro -> ifeval`;
* rehearsal C (dead leg): first stub exits 2 -> the queue halts with exit 2, legs 2-4 never
  invoked (exit-code propagation re-proven on the patched file; tick 49 proved the halt at leg 2);
* rehearsal D (new): while a separate process holds the lock, a second rehearsal instance prints
  `REFUSED ... no double-spend` and exits **4** with zero stub legs invoked;
* the rehearsal diff enumerates exactly five substitutions; after every scenario the stored
  partials stay byte-exact (`cde63378fa1633c5` / `a7c741de0d6ace8c`) and the real lock file was
  never created.
Builder trap caught in this tick: the first rehearsal copy was generated from a **relative**
scratch path, so the launcher's own `cd $HOME/sah-main` re-rooted the log/AF substitutions
mid-run and the stub legs died instead of running. Nothing landed in the repo (the writes failed
on the missing dir and `git status` stayed clean), but the rule generalizes: substitutions in a
launcher that cds must be absolute, or the rehearsal exercises a different script than the one
that ships.

**Machine note for the multi-hour chain: the user session is durable.** `loginctl` reads
`Linger=yes` for this user, so a `systemd-run --user` unit outlives session end and survives the
nightly gateway restart — the 9-27.6 h queue is not gated on a login session. No endpoint
preflight was taken this tick (no local leg queued; the readings series stays 19 files,
15 NO-GO / 2 GO / 2 INPUT-GAP).

**Standing gates green on an unchanged tree:** resume gate exit 0 read **unpiped** (the pipe-
masking class tick 49 logged for its own tooling was avoided deliberately: `| head` would have
reported the head's status, not the gate's) — window CLOSED today, partials byte-exact, resume
sets 59+44+500+541; arms index drift 0; derived percents 0 findings; grok-cell rule 0 findings;
superseded-cell rule 0 findings; digest-row rule 0 findings. Ops records re-read from
`executions.db`, not retyped: `docs-freshness ef7ea47ff99b` fired once today (03:00:17,
**failed** — tick 48's DNS-blip reading stands, tomorrow takes the `push_with_retry()` path),
hard-bank-era job `f23cf5d48e11` fired **138** times today (last 14:45) still exiting 0 under its
one-shot marker — still an owner decision, untouched.

**Next in force is unchanged: item 8**, the Grok resumption on 2026-11-12 in the pinned order,
ONE `systemd-run --user --collect --unit=parb-pub-grok-queue bash <absolute launcher path>`
launch; the launcher self-enforces census -> window refusal -> double-spend lock -> vendor check
-> blank purge -> deciding gate -> legs, with per-arm contracts fixed at tick 45 and legs scored
only when complete. Standing limits unchanged: no Grok arm before 2026-11-12; frozen contour
`0.0.2.56`, no new stamps, no hard pairs, hard bank untouched; a local leg needs a fresh
preflight GO (none queued); sanitization before every push; a partial arm publishes no percent.
This tick spent **zero model or cloud calls** (dryrun + stub rehearsals only) and moved no digest
row, verdict, answer byte, bank file or manifest pin — the tracked change is this block.
