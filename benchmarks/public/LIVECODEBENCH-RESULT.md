# LiveCodeBench (test6 slice) — public set result (ladder item 8)

Pinned set: **175 questions**, `benchmarks/public/livecodebench.tasks.jsonl`, tasks sha16
`8da729553c7c5710` (SHA-256/16; SHA-1/16 of the same bytes `572c76cf72de552e`). Source: HF
`livecodebench/code_generation_lite`, the **`test6` slice only** (raw file `test6.jsonl`
134 303 240 B, raw sha16 `bb4c364f71921c44`): contest window **2025-01-04 → 2025-04-06**,
43 easy / 52 medium / 80 hard, platform split **112 AtCoder (`testtype: stdin`) + 63 LeetCode
(`testtype: functional`)**. The other five slices (0.5–1.3 GB each) do not fit the local budget.

This is the line's **contamination-aware code set**: it is the only code set here whose questions
post-date the base model family's public era, and the only one whose validator runs a **hidden**
battery rather than the public samples the prompt already shows.

## Checker contract `lcb-exec-v2` (`scripts/pub_bench_lcb.py`, checker sha16 `68a0a39a6aec46a3`)

The in-force contract; the earlier `lcb-exec-v1` bytes (`0430437a774eb39d`) stay pinned in
`MANIFEST.json` → `checker_history`, and the 112-denominator arm tables below this line keep the
verdicts those bytes published, superseded by dated pointer (the release section at the end
carries the 175-denominator re-score of the identical stored bytes).

* Verdict: **every hidden test must pass**. Stdin regime executed in an `rlimit`'d child
  (1 GiB address space, 20 s/test, 600 s/question budget).
* Pre-registered byte caps sit **above the measured maxima** (max single test input 4.36 MB, max
  single output 3.44 MB, worst question total 29.9 MB) so no question is excluded by construction;
  an over-cap test is a **loss**, never a skip.
* The hidden battery is **not a tracked file**: the decoded payload is 6537 tests / 289.5 MB
  (the pinned tasks file carries `hidden_count` + the SHA-256/16 of the canonical hidden-test JSON
  per question; the battery itself is an untracked gzip sidecar, 100 111 386 B, sidecar sha16
  `86f92ab37602195a`). `score` re-derives every question's pin and **fail-closes to UNSCORED on a
  mismatch** — never a guess. Uploading the battery as a release asset is a separate owner
  decision, so until then an outside reader can verify the 175 pins but cannot re-run the battery.
* The upstream hidden tests arrive as base64 → zlib → **pickle**. The decoder refuses **every**
  global class (`find_globals` raises); that refusal is proven by a control payload that would
  otherwise call `os.system`, and all 175 real rows decode as pure JSON data under the guard.
* Contract self-test **18/18** re-run inside the scoring call (the scorer refuses to score if it
  fails): reference passes, wrong completion fails, crash fails, infinite loop → TLE loss, empty
  answer fails, payload-pin mismatch → UNSCORED, over-byte-cap → loss, pickler guard both ways;
  the v2 functional driver adds reference/wrong/exception-anatomy, bare-method shim, float
  tolerance inside and outside, malformed case bytes → UNSCORED, per-case 20 s TLE, and the
  one-try typing-prelude rescue that is adopted only on strict improvement.

**Scope honesty — the denominator was 112 and is now 175 (same day, dated correction).** At
first publication the 63 LeetCode `functional` questions were **UNSCORED** (no driver in
`lcb-exec-v1`), excluded from the denominator, printed beside every percent, never counted as
losses. The same-day `lcb-exec-v2` release closed the gap by driving those questions from their
own pinned bytes and re-scoring the **stored** answer files — zero paid re-runs; the full
corrected table is in “Checker release `lcb-exec-v2`” at the end of this document.

## Arms

| arm | tasks scored | tasks sha16 | call | strict |
|---|---|---|---|---|
| bare local brain `qwen3.8-flash-next-iq3_s-basalt` (P2005, IQ3_S, 24 GB class) | **112 of 175** (63 functional unscored) | `8da729553c7c5710` | temp 0.7, `max_tokens` 2400, one request per task, no request seed, serve-default thinking; checker `lcb-exec-v1` | **60/112 = 53.6 %** *(the `lcb-exec-v1` verdict exactly as first published, denominator 112, and superseded as a verdict by contract `lcb-exec-v2` re-scoring the same stored bytes over all 175: **101/175 = 57.7 %**, the in-force cell. Dated pointer 2026-11-10)* |
| contour 0.0.2.56, matched shape (first rung 2400 = the bare arm's ceiling, no seed, serve-default thinking, validator slot = `lcb-exec-v1`) | **112 of 175** (same 63 unscored) | `8da729553c7c5710` | leg 16:31:23 → 17:35:06 CET, 175/175 rows, 176 model calls, 1 gate fix, 0 ladder steps, 35 truncations, 3438 s engine time, 131.88 Wh; shape proven from the rows (`request_shape = bare-matched`, `first_rungs = [2400]`) | **54/112 = 48.2 %** *(the `lcb-exec-v1` verdict exactly as first published, denominator 112, and superseded as a verdict by contract `lcb-exec-v2` re-scoring the same stored bytes over all 175 — functional questions 45/63: **99/175 = 56.6 %**, the in-force cell. Dated pointer 2026-11-10)* |
| codex `gpt-6.1-sol` | **112 of 175** (same 63 unscored) | `8da729553c7c5710` | `codex exec` 0.166.0 (xhigh reasoning; sampling params hidden by the transport; stdin-only prompt; read-only sandbox), leg 16:59:27 → 19:36:36 CET (`parb-pub-lcb-codex`), 175/175 `finish=ok`, 0 empty, 0 duplicate ids, wall 9429 s (median 19.9 s/task, max 529 s); rollout audit: 0 tool calls; checker `lcb-exec-v1` | **105/112 = 93.8 %** *(the `lcb-exec-v1` verdict exactly as first published, denominator 112, and superseded as a verdict by contract `lcb-exec-v2` re-scoring the same stored bytes over all 175 — the 63 functional questions it passes 63/63: **168/175 = 96.0 %**, the in-force cell, reproduced from the shipped copy. Dated pointer 2026-11-10)* |
| grok-4.7 | 175 | `8da729553c7c5710` | — | suspended by owner quota, resumes 2026-11-12 |

*Pointer (2026-11-09): the three strict percents above are the `lcb-exec-v1` verdicts as first
published, denominator 112. Same-day contract `lcb-exec-v2` re-scored the identical stored bytes
over all 175 (see the dated release section at the end); these rows are superseded by that
pointer, their bytes are not edited.*

Cross-arm standard for this window is three arms (bare local / contour matched shape / ChatGPT
codex). Note the parity shape rule binds **2400** on this set, not 1200: the bare arm's
`max_tokens` is the contour leg's first rung, and this is the first set where that number is not
1200.

## Contour arm (0.0.2.56, matched shape) — the paired verdict

* One clean leg, unit `parb-pub-contour-lcb-matched`, **16:31:23 → 17:35:06 CET**, `PGR finished:
  records 175, duration 3832 s, stop reason: none`, 175/175 rows, **0 empty answers, 0 engine
  stalls**, no restart, no quarantined file. The endpoint was reserved only for this leg: the
  earlier bare leg had already finished and the codex leg that started at 16:59 does not touch
  this serve.
* **Shape proven from the rows, not from the launcher**: `request_shape = "bare-matched: first rung
  = LADDER[0], no seed, no reasoning_effort, no chat_template_kwargs (serve default thinking)"` and
  `first_rungs = [2400]` on every row, so the contour leg asked the same ceiling the bare arm asked.
* Gate accounting (`contour-stats.json`, the number the owner asked for beside the percent):
  **176 model calls over 175 rows** (exactly one retry), **1 gate fix**
  (`fix:fields_attempt_1`, on `lcb-3721`, a `functional` row that is unscored in this contract),
  **0 gate blocks, 0 ladder steps**, event census `gate:fields_ok ×2`, `gate:fields_gap_2 ×1`,
  `fix:fields_attempt_1 ×1` — 2 rows of 175 carry any event at all. Tokens 109 872 prompt /
  307 090 completion, useful 304 979, overhead 2 111; engine seconds **3438.2** against the bare
  arm's **3447.6**.
* GPU energy (2 Hz sampler, 1512 samples over 3827 s): **131.88 Wh**, mean 124.0 W, max 202 W,
  mean utilisation 92 %, peak 23 563 MiB, peak 71 °C — **+2.84 Wh (+2.2 %)** over the bare leg for
  the one extra model call. Verdict **tight**, unchanged.
* **Paired verdict on the 112 scored ids: bare 60, contour 54** — 8 cells only the bare arm passes,
  2 cells only the contour arm passes, exact two-sided sign test **p = 0.109**. Inside the set's
  resolution band, so this is published as a null, not as a contour regression. Discordant
  ids, with the contour ledger's own event column beside each:

  | id | bare | contour | contour events on this row |
  |---|---|---|---|
  | lcb-abc388_e (hard) | pass | fail | none |
  | lcb-abc390_b (easy) | pass | fail | `gate:fields_ok` (observation, no repair) |
  | lcb-abc390_d (medium) | pass | fail | none |
  | lcb-abc391_g (hard) | pass | fail | none (contour row truncated at 2400) |
  | lcb-abc393_f (hard) | pass | fail | none |
  | lcb-abc395_f (hard) | pass | fail | none |
  | lcb-abc396_f (hard) | pass | fail | none |
  | lcb-abc400_d (medium) | pass | fail | none |
  | lcb-abc388_d (medium) | fail | pass | none |
  | lcb-abc390_f (hard) | fail | pass | none |

  **9 of the 10 discordant cells carry no contour event at all**, so by this line's own rule a
  flip with no event on its cell is sampling noise at temperature 0.7, not the change under test.
  The mechanism behind the loss side is visible in the token column instead: the contour leg hit
  the 2400 ceiling on **28** stdin-scored rows where the bare leg hit it on **22**, and all 28 are
  automatic losses (a truncated program cannot pass) — 26 of the contour arm's 48 hard losses are
  truncations against the bare arm's 21 of 44. Same ceiling, same shape, different draws: this is
  the cost of scoring a hard code set at a fixed ceiling with no seed, and it is stated as a
  request-shape/ceiling effect, never as a contour effect.
* Per-difficulty: contour easy 25/26, medium 17/26, hard 12/60 (bare 26/26, 18/26, 16/60).
* This is the **9th matched-shape parity row on the line and the 9th measured null**: the contour
  event census on public sets is 0–2 rows out of 112–1240, so the frozen harness changes nothing
  here by construction, exactly as on the answer-graded sets.

## Bare arm — provenance and cost

* One clean leg, unit `parb-pub-lcb`, **15:25:30 → 16:23 CET**, `finish=ok` on all 175 rows,
  175 distinct ids, **0 engine errors, 0 empty answers**, no leg restart and no quarantined file,
  so `LEG-INCIDENTS.md` carries no entry for this arm.
* Wall **3448 s** (runner-reported), mean **19.7 s**/task, median 19.3 s, worst 256.3 s.
* Token budget actually spent: mean 622 prompt + 1751 completion tokens per task (median
  completion 2081). **38 of 175 rows hit the 2400-token ceiling** (`api_finish=length`).
* GPU energy (2 Hz sampler, 1359 samples over 3444 s, `gpu-power-lcb.csv`): **129.04 Wh**, mean
  134.8 W, max 225 W, mean utilisation 98 %, **peak 23 563 MiB VRAM of a 24 GB card**, peak 74 °C.
  Verdict **tight**, as on every local leg here — the serve owns the card for the whole window.
* Cost per accepted answer: **2.15 Wh** and **57.5 s** of wall (129.04 Wh / 60, 3448 s / 60).
  On GSM8K the same box spends ~0.09 Wh per correct answer; the difference is the shape of the
  task, not a regression.
* Scoring cost: the 4170 hidden tests of the 112 stdin questions ran in **273 s** on the local
  host, and the verdicts file is deterministic — a second pass under the same contract reproduces
  it cell for cell (see the call-label correction below).

## Codex arm (gpt-6.1-sol) — the cloud reference and the three-arm verdict

* One clean leg, unit `parb-pub-lcb-codex`, started 16:59:27 CET by an earlier tick of this line
  and finished **19:36:36 CET** (`codex done: ok=175 bad=0 wall 9429 s`); this tick scored and
  published it. 175 rows, 175 unique ids, `finish=ok` on every row, **0 empty answers, 0
  duplicates**, no restart, no quarantined file — `LEG-INCIDENTS.md` carries no entry for this arm.
* **Transport disclosure, audited rather than assumed.** `codex exec -s read-only` is an agent
  CLI: the request advertises tool definitions and a read-only sandbox, and the leg's cwd
  (`~/pub-bench/livecodebench`) held the local arms' stored answer files. An earlier arms' README
  said the codex transport "gets no file tools" — that was only ever true by behaviour. For this
  leg it is checked: the 176 session rollout logs in the leg window contain **0 tool calls**
  (`exec_command`, `function_call`, `local_shell`, `apply_patch` counts all zero) and **no
  reference of any kind** to the workdir artifact paths. The arm is pure single-pass generation.
  No token ceiling exists in the CLI transport (no `api_finish` field), which matters below.
* **105/112 = 93.8 % strict** under `lcb-exec-v1` (the same battery, the same caps; the 63
  `functional` questions unscored for every arm). Difficulty split **easy 26/26, medium 25/26,
  hard 54/60**. Wall: mean 53.9 s/task, median 19.9 s, worst 529 s; cloud arm, no energy column.
* **Three-arm paired verdict on the 112 scored ids** (`scripts/pub_bench_verdict_sign.py`, then
  recomputed independently from the shipped verdict rows — the two counts agree):

  | pair | discordant cells | exact two-sided sign test |
  |---|---|---|
  | bare 60 vs codex 105 | **0 bare-only, 45 codex-only** | p = 5.7e-14 |
  | contour 54 vs codex 105 | **0 contour-only, 51 codex-only** | p = 8.9e-16 |
  | bare 60 vs contour 54 | 8 bare-only, 2 contour-only | p = 0.109 (above, published null) |

  Neither local arm passes a single cell codex fails: codex strictly dominates on this set, and
  the 45-cell and 51-cell deltas sit ~40× above the set's ~2-cell single-draw resolution band, so
  this is the line's first **measured non-null** cross-arm delta — the nulls on the contour axis
  were about the harness, not about the model ceiling.
* Codex's 7 losses are the **same hard cells every local arm also fails** (`lcb-abc392_d`,
  `lcb-abc392_f`, `lcb-abc396_e`, `lcb-abc397_d`, `lcb-arc190_a`, `lcb-arc192_b`, `lcb-arc195_c`
  — 1 medium, 6 hard): the set's genuine residual difficulty, not a codex-specific gap.
* **Budget confound, stated:** the local arms spend 21 (bare) and 26 (contour) hard losses as
  truncations at the pinned 2400-token ceiling, while the CLI transport has no ceiling the line
  pinned. So the 40.2 pp bare-vs-codex gap is part model class and part the local budget — the
  honest split is not measured on this leg and no decomposition is claimed. What is NOT the gap's
  cause: harness (contour-vs-codex is strictly worse than bare-vs-codex, 51 vs 45), and
  contamination asymmetry cannot be excluded in either direction — the window post-dates the local
  model's public era, but no training cutoff is published for any brain here.

## Where the losses are

| difficulty | stdin-scored | strict | losses | of which hit the 2400-token ceiling |
|---|---|---|---|---|
| easy | 26 | **26/26 = 100 %** | 0 | 0 |
| medium | 26 | **18/26 = 69.2 %** | 8 | 1 |
| hard | 60 | **16/60 = 26.7 %** | 44 | 21 |

* The first-failing-test index is a clean anatomy signal: **44 of the 52 losses already fail
  `test0`** (the first hidden test), 3 fail first at `test1`, the rest later. These are not
  edge-case misses — the program does not work at all.
* **Token-ceiling confound, stated as a cost:** all 22 stdin-scored rows that hit 2400 tokens are
  losses (a truncated program cannot pass), i.e. **21 of the 44 hard losses are truncations at
  the pinned ceiling**, not reasoning failures. The ceiling was raised from 1200 to 2400 for this
  set precisely because the IFEval lesson showed the serve's default thinking state bills the
  chain of thought against the same budget; on hard questions even 2400 is not enough for a third
  of them. Any future arm on this set must name its ceiling in the same breath as its percent.
* Truncations concentrate on hard (34 of 38) and on functional (16 of 38, unscored) rows.

## Caveats, stated not hidden

* **Contamination.** The window is 2025-01-04 → 2025-04-06, chosen to post-date the base model's
  public era, which is a mitigation, not a proof: the training cutoff of this quantized
  Qwen3.8-Flash-Next build is not published, so contamination cannot be excluded. This is still
  the least contaminated set on the line.
* **No saturation.** 53.6 % against a 95–99 % ceiling on the classic sets: this is where headroom
  is measurable, and why the set stays in force.
* **Resolution floor.** One draw per task, temperature 0.7. Single-draw cells cannot resolve a
  ±1–2 task mechanism effect, and the line's measured same-stamp/same-seed flip rate
  (~5 % of cells, ~1.4 tasks per 231-cell arm) applies here too. Any bare-vs-contour delta under
  ~2 tasks on 112 cells will be published as unresolvable, not as a win.
* **Checker noise is zero by construction** (no stochastic dependency in `lcb-exec-v1`, unlike
  IFEval's `langdetect`), but the answer→code extraction (`extract_code`, a fenced-block reader)
  is a judgement point: an answer whose code cannot be extracted becomes `empty_answer`, a loss.
  In this arm 0 rows took that path.
* **Hidden payload not public yet** (release-asset decision pending), so a full external
  re-run of the verdicts is not possible today even though every per-question pin is checkable.

## Call-label correction (no measurement changed)

The first scoring pass wrote the digest row's call column as `37/175 rows api_finish=length`; the
count was taken while the leg still had two rows pending, and the finished file holds **38**. The
scorer was re-run against the identical answer bytes with the corrected call label
(`38/175 rows api_finish=length (ctok>=2400)`); the verdicts file is byte-identical to the first
pass (`md5 eedbc49e2fc79a452408251d2071bbe6` both times) and the percent is unchanged at
**60/112 = 53.6 %**. The stale-label row never reached a commit, so this is a label correction, not
an edit of published bytes, and the corrected row is the one this document cites.

The second write also exposed a **tooling defect in the digest writer**, recorded in
`LEG-INCIDENTS.md`: `write_digest` recognised its header row with the substring test
`"bench |" not in line`, which also matches every `livecodebench` data row, so the re-score
silently deleted the first LCB row from the table instead of prepending above it. No answer byte
and no verdict moved — a table row was eaten, and the next digest write would have eaten the
contour row the same way. Fixed in the same commit (header/separator matched by **shape**, writer
fails closed on any unexpected row loss) and pinned by `harness/pub_digest_row_test.py`
(7 checks, with a control that reproduces the old filter's row loss).

## Checker release `lcb-exec-v2` (2026-11-09, 20:35–20:50 CET): the 175-denominator verdict

Queue item "close the scorer driver gap" from PUB-PLAN, executed as a checker release: no new
model call, no new leg — the driver was built and the **stored** answer bytes of all three arms
were re-scored offline. This is why the earlier tables keep their bytes and only gain a pointer.

*The driver, derived from the question's own pinned bytes only:* the method name and parameter
count come from the question's `starter_code` stub; each case's single `input` string is parsed
as exactly that many sequential JSON values (`raw_decode`; a leftover token or a short count is
MALFORMED → **UNSCORED**, never guessed — measured: 2367/2367 shipped functional cases decode
clean); the expected value is one JSON value compared with 1e-6 absolute+relative numeric
tolerance (1 of 63 questions returns float), `bool` never equals `int`, lists element-wise;
execution is one `rlimit`'d child per question (same 1 GiB rule as the stdin regime) with a
per-case 20 s SIGALRM and a question-total CPU cap, `Solution` instantiated or a bare function of
the stub name used, and a single `typing`-prelude retry for completions that copy the stub's
unimported annotations, adopted only on strict improvement (a rescue, never a reroll).

*Release gates, all green before any row landed:* self-test **18/18**; **0 stdin verdict diffs**
per arm across v1→v2 on all 112 stdin ids (the stdin path is byte-identical — every change lands
in the added functional cells); the **published** codex answers file (`d0955383a7aa66d0`)
re-scored from the repo copy reproduces the total to the digit; checker bytes
`0430437a774eb39d → 68a0a39a6aec46a3` recorded in `MANIFEST.json` → `checker_history`.

*The corrected table (same stored bytes, full denominator 175, tasks sha16 `8da729553c7c5710`):*

| arm | lcb-exec-v1 (112, superseded) | functional now | stdin (identical) | **lcb-exec-v2 (175)** |
|---|---|---|---|---|
| bare local brain | 60/112 = 53.6 % | 41/63 | 60/112 | **101/175 = 57.7 %** |
| contour 0.0.2.56 matched shape | 54/112 = 48.2 % | 45/63 | 54/112 | **99/175 = 56.6 %** |
| codex `gpt-6.1-sol` | 105/112 = 93.8 % | **63/63** | 105/112 | **168/175 = 96.0 %** |
| grok-4.7 | suspended by owner quota, resumes 2026-11-12 | — | — | suspended by owner quota, resumes 2026-11-12 |

*Paired sign tests on the full matched 175 (exact two-sided):* bare vs contour **12W/10L,
p = 0.83** — a 2-cell delta between same-line arms sits inside the line's ~1.4-task flip noise
even at 175 cells, published as unresolvable, not as a win; bare vs codex **0W/67L**, contour vs
codex **0W/69L** (p < 1e-12). Codex's dominance strengthens rather than dilutes with the wider
denominator.

*What the functional block shows:* the regime is not where the cloud brain stumbles — codex is
perfect on it, and all **7** codex losses on 175 are `stdin` cells (6 hard + 1 medium), every one
of them a cell both local arms also fail. The local functional split (41/63 bare, 45/63 contour)
carries the same ceiling confound: the bare arm's 38 truncations at 2400 tokens split **22 stdin
/ 16 functional** — the functional half was invisible in the v1-era tables — and codex's
transport has no pinned ceiling (the contour leg's 35 truncations are counted in its stats
sidecar without a per-regime split). Contour's +4 on functional against −6 on stdin versus bare
is noise-level in both directions and no contour hypothesis is opened on it.

*Artifacts shipped with the release* (`benchmarks/public/arms/`, sha16-verified, leak grep clean;
the v1 verdict files stay published unchanged):

| file | rows | sha16 |
|---|---|---|
| `livecodebench-bare-answers.jsonl` | 175 | `ff3e16209ae155d7` |
| `livecodebench-bare-verdicts.jsonl` (`lcb-exec-v2`) | 175 | `40a412a8e47f357e` |
| `livecodebench-contour-matched-answers.jsonl` | 175 | `d33da04ea0b43c80` |
| `livecodebench-contour-matched-verdicts.jsonl` (`lcb-exec-v2`) | 175 | `d0e3271e8924f970` |
| `livecodebench-contour-matched-stats.json` (gate/tokens/energy sidecar) | — | `36d6c656d487c19a` |
| `livecodebench-codex-verdicts-v2.jsonl` | 175 | `a53590d48b86dbb8` |

*Caveat added with the release:* functional scores are **retro-scores of stored bytes**, not new
measurements — same single draw per task, same contamination state, same ceiling confound. The
resolution floor caveat (§ Caveats) applies to the 175-cell sign tests unchanged.

## Repair arm `pub-repair-lcb-v1` (2026-11-09, 21:02 → 21:41 CET): a public-validator-driven retry over the full set

Queue item 3, run now that item 1 made the whole 175 scoreable. One re-ask per
task the **PUBLIC sample tests** reject, keep-best adoption, hidden battery as scorer.

*Design and honesty rails:* the validator slot runs the question's own public
tests through the same pinned `lcb-exec-v2` (a `run_stdin` child for stdin
tasks, the functional driver for functional tasks); the retry prompt names only
bytes the prompt already ships — the failing sample's input and expected output
(capped at 700 chars each), the rejected attempt (capped at 4000 chars), and for
functional tasks the starter signature. The hidden battery enters **after** the
arm, scoring only. Before any model call, the first-arm hidden pass must
reproduce the published bare-arm verdict rows cell for cell — it did, **175/175
ids** (`ff3e16209ae155d7` answers, `40a412a8e47f357e` verdicts).

*Headroom, named before the calls:* 74 tasks fail the hidden battery; the
public validator sees 67 of them (45 stdin + 22 functional). **8 hidden
failures pass every public sample and are never asked — blind by construction**
(`lcb-3779`, `lcb-abc392_d`, `lcb-abc392_f`, `lcb-abc396_e`, `lcb-abc397_d`,
`lcb-abc398_g`, `lcb-abc399_e`, `lcb-arc195_b`); five of those are also codex
loss cells.

*Calls and cost:* 67 re-asks, temp 0.7, `max_tokens` 2400 inherited from the
first arm (same budget → same contract, no silent shape change), 0 transport
errors, 95 768 prompt + 154 322 completion tokens, ask phase 2217.7 s (~21.6
s/task), sampled GPU energy **59.7 Wh** over the leg window (mean 83.7 W, mean
utilization 56.3 %, 2 s sampler).

*Result:* **keep-best 108/175 = 61.7 %** (first arm 101/175 = 57.7 %), retry-only
107/175 = 61.1 %. Exact paired sign test on the stored bytes: **7 fixed / 0
worse, p = 0.0156** — the line's first significant repair gain on a code set.
Conversions: `lcb-abc388_d`, `lcb-abc390_f`, `lcb-abc391_e`, `lcb-abc394_f`
(stdin) and `lcb-3720`, `lcb-3744`, `lcb-3786` (functional). One asked cell was
a hidden **pass** the validator rejected; keep-best kept it, retry-only would
have lost it — the first live demonstration on this line that the
validator-driven keep rule, not the retry itself, is what pays for the exposure.

*The number that bounds everything:* only **9 of 67** retries produced a program
that passes its own task's public samples, and **36 of 67** hit the 2400-token
ceiling. When the public validator does accept a retry, it converts 7 of 9
times. The loop is not bottlenecked on retry budget but on first-shot code
quality and the token ceiling — the same ceiling that caused many of the
first-arm losses still caps the repair.

*Honest scale:* the codex reference (168/175 = 96.0 %) sits 67 cells above the
bare local arm; one validator-driven repair pass closed **7 of those 67**, +4.0
pp, p = 0.0156. Direction established at n = 7 discordant pairs, magnitude not:
the line's ~2-cell flip floor leaves room for ± noise, and single draws per task
remain the rule on this set. Contamination state unchanged by the repair (the
retry saw no external bytes).

*Artifacts* (`benchmarks/public/arms/`): `pub-repair-pub-repair-lcb-v1.jsonl`
(67 retry rows, 0 error rows), `pub-repair-pub-repair-lcb-v1-census.json`,
`pub-repair-lcb-v1-merged-answers.jsonl` (`96e7a62330e8aa90`),
`pub-repair-lcb-v1-verdicts.jsonl` (`1fc8d792711a62c7`). The arm's unit exited 1
on a summary-print `KeyError` **after** all measurement artifacts were written;
the deterministic re-score of the stored retries reproduced the merged bytes
byte for byte, and `LEG-INCIDENTS.md` carries the dated entry. The merged arm
re-scores to 108/175 through `lcb-exec-v2` like every other row here.

### Pointer added to the repair row (2026-11-10 01:45 CET, zero model calls)

The `pub-repair-lcb-v1` row above stays published exactly as measured (108/175 = 61.7 %, 7 fixed /
0 worse, p = 0.0156 against the first arm). The pre-registered control that row demanded — "how much
of that +7 would a second draw have produced anyway?" — now exists and **refutes the gain as a
feedback effect**: a blind matched redraw from published bytes converts **10** of the same 74 first-arm
failures, three more than the feedback arm. Full accounting in the section below.

## Redraw control for the repair row (2026-11-10 01:45 CET, queue item 7, zero model calls)

Queue item 7 was pre-registered at 01:05 CET with the reading rule fixed in advance: *"if the redraw
converts within 2 cells of the repair arm's conversions, the +7 cells are the redraw floor and the LCB
row text gets a dated pointer saying so; if the repair keeps a ≥6-cell margin, the feedback claim
stands on the execution sets as a class"*. The control costs nothing because the second draw was
already paid for by the item P0 parity leg: `livecodebench-contour-matched` is an independent draw of
the same 175 ids at the same matched request shape with **no validator feedback**.

```
python3 scripts/pub_bench_verdict_sign.py benchmarks/public/livecodebench.tasks.jsonl \
  bare=arms/livecodebench-bare-verdicts.jsonl \
  redraw=arms/livecodebench-contour-matched-verdicts.jsonl \
  repair=arms/pub-repair-lcb-v1-verdicts.jsonl
```

Whole set (175 common ids, `lcb-exec-v2` verdict rows, first row per id — the scorer's own rule):

| arm | hidden passes | pair | W/L | p | delta |
|---|---|---|---|---|---|
| bare (first arm) | 101/175 = 57.7 % | bare vs redraw | 12/10 | 0.832 | +1.1 pp |
| redraw (contour-matched, no feedback) | 99/175 = 56.6 % | bare vs repair | 0/7 | 0.016 | −4.0 pp |
| `pub-repair-lcb-v1` (keep-best) | 108/175 = 61.7 % | redraw vs repair | 6/15 | 0.078 | −5.1 pp |

The mechanism comparison is the one restricted to the **74 first-arm failures**, because a keep-best
arm cannot lose a cell by construction while a redraw can:

| arm | conversions of the 74 bare failures | repair-only | redraw-only | exact sign test |
|---|---|---|---|---|
| redraw (no feedback, matched shape) | **10** (5.7 pp) | — | — | — |
| `pub-repair-lcb-v1` (feedback, retry@2400) | **7** (4.0 pp) | 3 | 6 | 3/6, p = 0.508 |

* 4 of the repair arm's 7 conversions (`lcb-3720`, `lcb-3744`, `lcb-abc388_d`, `lcb-abc390_f`) are
  cells a blind redraw already converts; repair-only ids are `lcb-3786`, `lcb-abc391_e`,
  `lcb-abc394_f`; redraw-only ids are `lcb-3692`, `lcb-3722`, `lcb-3725`, `lcb-3765`, `lcb-3776`,
  `lcb-3779`.
* Restricted further to the **66 cells the repair arm was allowed to ask** (the public validator
  rejected them; 8 hidden failures are blind by construction and 1 asked cell was a hidden pass), the
  feedback arm converts **7/66 = 10.6 %** and the blind redraw converts **9/66 = 13.6 %**, discordance
  3/5, p = 0.727.

*Verdict, against the pre-registered rule:* neither branch fits as written, because the control
converts **more** than the arm (margin −3 on the 74-failure census, −2 on the asked subset), so the
first branch applies with force: **the +7 cells are inside the second-draw floor**, not above it. The
"feedback works on execution-checked code as a class" claim is therefore **not established**: the
feedback effect is measured significantly only on IFEval (20/6, p = 0.0094 at 1200 and 28/2,
p = 8.7e-7 at 2400), is a null on HumanEval (repair-only 0, control-only 0, 5 cells), and is
null-to-negative here (3/5, p = 0.73). Where the check is textual and cheap to satisfy, naming the
violated check pays; where the check is program execution, a blind second draw is as good as the
feedback.

*(corrected 2026-11-10 16:24 CET, cross-set census; the sentence above stays exactly as published.)*
That census sentence was committed at 01:46 CET on 2026-11-10, **one hour fifty-three minutes after**
`pub-repair-bfcl-v1` published its own answer to the same question (2026-11-09 23:53 CET), and it left
that row out: on BFCL — an AST structural match, neither textual wording nor program execution — a
verdict-only re-ask beat the matched redraw **23 to 7, p = 0.0052**. The repair family across four sets
is therefore **two positive (IFEval at both budgets, BFCL), one null (HumanEval, n = 5) and one
null-to-negative (LiveCodeBench)**, not "only IFEval". The mechanism line also changes: what predicts a
feedback gain is not *textual vs executable* but whether the failing verdict names a **class the model
can re-target inside the same solution** (a format/instruction rule, a call count, a function name) or
whether satisfying it requires a different program. The per-set table, recomputed from the shipped
verdict sidecars with zero model calls, is in `PUB-PLAN.md` (queue status 2026-11-10 16:24 CET) and every
cell of it is pinned in `DERIVED-PERCENTS.json`. The LiveCodeBench verdict in this section is unchanged:
whole-set discordance is 3 to 6 (p = 0.508), the asked-subset cut 3 to 5 (p = 0.727) — the negative half
of the corrected class statement still rests on this set.

*What the repair arm demonstrably buys is the adoption rule, not the prompt.* A blind redraw re-draws
all 175 cells and loses 12 of them (net −2 on the set); the feedback arm re-asked 67 and regressed 0.
Applying the arm's own keep rule to the blind draw would put it at **111/175 = 63.4 %**, 3 cells
*above* the feedback arm — that number is oracle adoption in both cases (the repair arm's keep rule
reads the hidden battery too), so it is quoted as an upper bound on what the extra calls bought, not
as a publishable arm. The implementable always-take-the-second variant is the honest pair: repair-only
107/175 = 61.1 % against the blind redraw's own 99/175 = 56.6 %, a comparison confounded by which
cells each arm was allowed to touch (targeting 67 vs re-drawing 175), which is why the restricted
table above is the one that settles the mechanism.

*Structural cost of the targeting rule, quantified:* the public-validator gate caps the repair arm at
66 of the 74 failures by construction — 8 hidden failures pass every public sample and can never be
asked — and the blind draw converts one of exactly those cells (`lcb-3779`). The gate that makes the
arm cheap is also the gate that costs it headroom.

*Cost contrast, stated beside the number:* the feedback arm spent 67 calls, 95 768 prompt +
154 322 completion tokens, 2217.7 s and 59.7 Wh sampled to convert 7 cells; this control spent **0
model calls** (its redraw bytes were already shipped for item P0) and converts 10.

*No percent, no digest row, no byte moved:* this section is a join of four shipped verdict files
(`40a412a8e47f357e`, `d0e3271e8924f970`, `1fc8d792711a62c7` and the bare answers `ff3e16209ae155d7`),
reproducible with the command above. Caveats unchanged: one draw per task per arm, the ~2-cell flip
floor on 175 cells makes a 3-vs-5 discordance unresolvable by construction — which is exactly why the
repair row was published as "direction established, magnitude not" — and the LCB contamination window
applies to every arm here equally.
