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
| contour 0.0.2.56, matched shape (first rung 2400 = the bare arm's ceiling, no seed, serve-default thinking, validator slot = `lcb-exec-v1`) | 175 ids, same slice | `8da729553c7c5710` | leg in flight from 16:31 CET, no percent until it completes — a partial arm publishes nothing | pending |
| codex `gpt-6.1-sol` | 175 | `8da729553c7c5710` | — | not launched yet |
| grok-4.7 | 175 | `8da729553c7c5710` | — | suspended by owner quota, resumes 2026-11-12 |

Cross-arm standard for this window is three arms (bare local / contour matched shape / ChatGPT
codex). Note the parity shape rule binds **2400** on this set, not 1200: the bare arm's
`max_tokens` is the contour leg's first rung, and this is the first set where that number is not
1200.

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
