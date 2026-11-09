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

## Checker contract `lcb-exec-v1` (`scripts/pub_bench_lcb.py`, checker sha16 `0430437a774eb39d`)

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
* Contract self-test **10/10** re-run inside the scoring call (the scorer refuses to score if it
  fails): reference passes, wrong completion fails, crash fails, infinite loop → TLE loss, empty
  answer fails, payload-pin mismatch → UNSCORED, functional regime named unscored, over-byte-cap →
  loss, pickler guard both ways.

**Scope honesty — the denominator is 112, not 175.** The 112 AtCoder `stdin` questions score
today. The 63 LeetCode `functional` questions stay **UNSCORED** — the driver that builds an
executable from each case's own type list is not in this contract — and are excluded from the
denominator, printed beside every percent. They are not counted as losses.

## Arms

| arm | tasks scored | tasks sha16 | call | strict |
|---|---|---|---|---|
| bare local brain `qwen3.8-flash-next-iq3_s-basalt` (P2005, IQ3_S, 24 GB class) | **112 of 175** (63 functional unscored) | `8da729553c7c5710` | temp 0.7, `max_tokens` 2400, one request per task, no request seed, serve-default thinking; checker `lcb-exec-v1` | **60/112 = 53.6 %** |
| contour 0.0.2.56, matched shape (first rung 2400 = the bare arm's ceiling, no seed, serve-default thinking, validator slot = `lcb-exec-v1`) | **112 of 175** (same 63 unscored) | `8da729553c7c5710` | leg 16:31:23 → 17:35:06 CET, 175/175 rows, 176 model calls, 1 gate fix, 0 ladder steps, 35 truncations, 3438 s engine time, 131.88 Wh; shape proven from the rows (`request_shape = bare-matched`, `first_rungs = [2400]`) | **54/112 = 48.2 %** |
| codex `gpt-6.1-sol` | 175 | `8da729553c7c5710` | leg running from 16:59 CET (`parb-pub-lcb-codex`) — a partial arm publishes no percent | pending |
| grok-4.7 | 175 | `8da729553c7c5710` | — | suspended by owner quota, resumes 2026-11-12 |

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
