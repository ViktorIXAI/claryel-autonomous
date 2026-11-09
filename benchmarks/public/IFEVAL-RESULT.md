# IFEval — public set result (item 4 of the ladder, first set with a real validator)

Pinned set: 541 tasks, `benchmarks/public/ifeval.tasks.jsonl`, tasks sha16 `2c672531577dcc33`
(SHA-1/16, the convention this digest column uses; SHA-256/16 of the same bytes is
`e09a5cab3782ed5b` — both name the identical 541 rows). Source: the upstream Google Research
repo at commit `e6890f85757dd84e27ca6df2dd30651dafad28e0`, `instruction_following_eval/data/input_data.jsonl`.

IFEval is not answer matching: every task carries instruction ids plus keyword arguments and the
verdict is the conjunction of the upstream per-instruction checks. That makes it the first public
set where a harness has a real validator slot to sit in, so it carries the repair-event census the
answer-graded sets cannot.

## Arms

| arm | tasks | tasks sha16 | call | strict | loose | instruction checks |
|---|---|---|---|---|---|---|
| bare local brain `qwen3.8-flash-next-iq3_s-basalt` (P2005, IQ3_S, 24 GB class) | 541 (full set) | `2c672531577dcc33` | temp 0.7, `max_tokens` 1200, one request per task, no request seed, serve-default thinking | **467/541 = 86.3 %** | 481/541 = 88.9 % | 751/834 = 90.0 % |
| contour 0.0.2.56, matched shape (first rung 1200, no seed, serve-default thinking, validator slot = `pub-ifeval-v1`) | 541 (full set) | `2c672531577dcc33` | same shape as the bare arm by the parity shape rule: one 1200-token rung = one request per task, temp 0.7 | **462/541 = 85.4 %** | 477/541 = 88.2 % | 743/834 = 89.1 % |
| codex `gpt-6.1-sol` xhigh (subscription CLI, stdin transport) | 541 (full set) | `2c672531577dcc33` | transport does not expose sampling params; one leg split by the owner-side usage window — 08:24 → 12:39 (440 ok rows, 15 333 s), quota window, resumed 13:34 → 14:41 (101 ok rows, 3467 s); 3 stale `rc1` rows purged with zero credit before the resume (`LEG-INCIDENTS.md`) | **515/541 = 95.2 %** | 526/541 = 97.2 % | 807/834 = 96.8 % |
| grok-4.7 | 541 | `2c672531577dcc33` | — | suspended by owner quota, resumes 2026-11-12 | — | — |

Cross-arm standard for this window is three arms (bare local / contour matched shape / ChatGPT
codex): the Grok quota ran dry on the owner side on 2026-11-09 and no Grok percent is produced for
this set before 2026-11-12. The ChatGPT leg stopped at 440/541 rows at 12:39 on the subscription
usage limit, resumed at 13:34 when the window reopened and **completed 541/541 at 14:41 CET**, so
the IFEval comparison is three arms. Paired sign tests over the same 541 ids (strict axis, exact
McNemar): codex vs bare **61W/13L, p = 1.4e-8**; codex vs contour matched **62W/9L, p = 7.3e-11**;
bare vs contour stays the previously published **16W/21L, p = 0.511** measured null. The codex gain
is a model+transport effect on a set with no seed and no exposed sampling parameters — the cloud
arm gets xhigh reasoning by default, the local arms get one 1200-token request.

Discordant ids (strict axis; numeric-suffix form of `ifeval-<n>`, regenerable from the shipped
`*-verdicts.jsonl` files):

* codex-only passes vs bare (61): `013, 016, 019, 030, 152, 179, 201, 292, 321, 1069, 1122, 1129,
  1130, 1216, 1236, 1258, 1300, 1307, 1367, 1402, 1498, 1546, 1643, 1653, 1686, 1691, 1759, 1779,
  1781, 1813, 1880, 1944, 1964, 2041, 2275, 2284, 2305, 2359, 2381, 2416, 2605, 2739, 2751, 2857,
  3048, 3089, 3114, 3223, 3326, 3329, 3345, 3407, 3424, 3425, 3429, 3456, 3505, 3506, 3538, 3572,
  3633`
* bare-only passes (13): `1392, 1645, 1897, 1954, 2216, 2422, 2571, 2616, 2736, 2765, 2790, 2844,
  3617`
* codex-only passes vs contour matched (62): `013, 016, 019, 030, 152, 179, 321, 1069, 1122, 1130,
  1203, 1216, 1258, 1300, 1325, 1367, 1389, 1402, 1446, 1498, 1546, 1643, 1686, 1691, 1781, 1880,
  1883, 1944, 1964, 2209, 2246, 2247, 2273, 2284, 2292, 2305, 2359, 2381, 2416, 2471, 2591, 2739,
  2751, 2857, 2871, 2904, 3063, 3089, 3091, 3114, 3223, 3326, 3329, 3407, 3425, 3429, 3456, 3505,
  3506, 3538, 3572, 3633`
* contour-matched-only passes (9): `1897, 2250, 2422, 2571, 2616, 2736, 2765, 2790, 2844`

## codex arm — provenance and cost

* Audit before scoring: 541 rows, 541 unique ids, `finish=ok` on every row, 0 empty answers. Two
  clusters of byte-identical answers exist across ids (`ifeval-227/3749/3754` all
  `My answer is maybe.`, `ifeval-3753/3755/3756` all `My answer is no.`); inspected against the
  task prompts — those tasks force exactly one of three fixed phrases, so the identity is the
  permitted phrase verbatim, not the stale-last-message defect recorded earlier the same day. The
  transport fix (delete the CLI last-message file before every call) shipped in the same commit as
  the incident.
* Wall: 15 333 s (440 rows, 34.8 s/task) + 3467 s (101 rows, 34.3 s/task) = 18 800 s of call time
  across two segments; no GPU energy applies to a cloud arm (wall time only, per the line rules).
* Published bytes: `arms/ifeval-codex-answers.jsonl` (541 lines, sha16 `fc2650b08fb87bef`,
  scrub masked nothing — bytes byte-identical to the runner output, and the stdin transport gives
  the CLI no file tools, so no local-path disclosure is possible) and the scorer's verdict rows
  `arms/ifeval-codex-verdicts.jsonl` (541 lines, sha16 `838f55ca6a6a24fc`, sidecar SHA-1/16
  `8ca486048c590276`).
* Verification rescore of the **published** answers with `pub-ifeval-v1`: 514/541 = 95.0 % strict —
  one cell different (`ifeval-1122`) from the shipped verdict rows. That is the documented
  `langdetect` flake (the checker flips ~1 task per run over identical bytes) and is exactly why
  the published percent is pinned by the shipped verdict sidecar, and why IFEval deltas under
  0.5 pp are never quoted as effects.
* Hardest instruction classes for this model: `change_case:english_capital` 5,
  `change_case:english_lowercase` 5, `punctuation:no_comma` 3,
  `detectable_format:number_highlighted_sections` 3, `combination:repeat_prompt` 3,
  `length_constraints:nth_paragraph_first_word` 2 failures — a different failure profile from the
  local arms (which lose mostly on `length_constraints:number_words` and `keywords:letter_frequency`).

## Bare arm — provenance and cost

* One clean leg, 07:34:36 → 08:51 CET, `finish=ok` on all 541 rows, 0 engine errors, 0 empty
  answers, 541 distinct task ids, no duplicate. The earlier duplicated-leg window (two local legs
  on one endpoint for six minutes) is quarantined with zero credit in `LEG-INCIDENTS.md`; every
  answer row scored here comes from the single-leg window.
* Wall: 4622 s of summed request time, 4602 s of sampled leg window, 8.5 s/task mean.
* GPU energy (2 Hz sampler, 1816 samples): **163.8 Wh**, mean 128.1 W, max 218 W, mean utilisation
  96 %, peak 23 563 MiB VRAM of a 24 GB card, peak 72 °C. Resource verdict: **tight** — the serve
  sits at ~94 % of VRAM for the whole leg, so this set is at the edge of the box, not over it.
* Call-budget cost, stated rather than hidden: **62/541 rows (11.5 %) hit the 1200-token ceiling**
  (`api_finish=length`), and length/constraint failures concentrate there. A model that thinks in
  the visible channel spends the budget before it spends the instruction.
* Hardest instruction classes for this model: `length_constraints:number_words` 14,
  `keywords:letter_frequency` 11, `combination:repeat_prompt` 10, `detectable_format:json_format` 6,
  `punctuation:no_comma` 6, `length_constraints:number_sentences` 6 failures.

## Checker contract

Contract `pub-ifeval-v1` (`scripts/pub_bench_ifeval.py` over the vendored upstream modules,
per-file sha16 pins in `MANIFEST.json`). The scorer refuses to publish unless both gates pass, and
the gates were green at scoring time: upstream unit suite 41/41, reference responses
strict 417/540 and loose 431/540 against the recorded band 416/431 (±2.0 pp).
Verdict files: `ifeval-pub-ifeval-v1-verdicts.jsonl` (+ its sha16 sidecar) beside the arm.

Two checker properties are part of the number, not footnotes:

1. **Checker noise.** Over identical bytes the upstream checker itself flips about one task per run
   (measured strict 416, 417, 417; loose 431, 430, 431) because it calls `langdetect`, which is
   stochastic on ambiguous text. **Any IFEval delta under ~0.5 pp is checker noise**, never a model
   or harness difference.
2. **The gate itself was flaky and is now documented as such.** Measured 2026-11-09: 2 of 8 unit
   suite runs in the pinned venv failed on exactly one vendor test,
   `test_english_capital_checker`, with the environment intact — the vendor's
   `CapitalLettersEnglishChecker` calls `langdetect`. The gate now accepts a green run within
   `SUITE_ATTEMPTS` = 3 attempts and names the attempt; the reference-band gate stays a single
   pass, because a real environment break moves it by far more. This changes no verdict: no IFEval
   arm had been scored before the change, and the pinned bytes of the vendored checker did not move.

## Contour parity: what the wiring smoke proved (no percent)

Workspace `~/parb-pub-contour/ifeval-matched`, stamp `0.0.2.56`, ws bank sha16 `283616a959c7df24`,
validator slot holds the same `pub-ifeval-v1` bytes that scored the bare row. Two wiring smokes on
fresh state names (no percent published from them):

| smoke | verdict | model calls | gate fixes | gate blocks | ladder steps | ledger contour events |
|---|---|---|---|---|---|---|
| `ifeval-1000` | `pub:ifeval_strict_pass` | 1 | 0 | 0 | 0 | none |
| `ifeval-1001`, `ifeval-1005` | `pub:ifeval_strict_pass` ×2 | 1 each | 0 | 0 | 0 | none |

So the category-`P` path reaches only the generic ladder path: no hard-bank family grammar (invoice
fields, coverage nudges, plan gates) touched a public prompt, and the validator verdict comes from
the vendor's code. The full matched-shape leg will publish its fire/edit/truncation/token/energy
census beside its percent; if that census is zero, the honest reading is a harness that costs calls
and changes nothing on this set — that is the finding, not a defect to hide.

## Contour arm — the matched-shape percent and the repair-event census (2026-11-09)

Leg `pub-ifeval-contour-matched`, workspace `~/parb-pub-contour/ifeval-matched`, stamp `0.0.2.56`
(behavior 2.56), ws bank `pub-ifeval-541`, one leg 08:55:22 → 10:12:52 CET (77.5 min wall),
541/541 rows, 0 empty answers, 0 engine-stalled rows, no incident.

**The census is the number this set was put on the ladder for, and it is zero:**

| quantity | value |
|---|---|
| ledger rows with any contour/fix event | **0 / 541** |
| gate fires, gate fixes, gate blocks | **0, 0, 0** |
| ladder steps (extra requests) | **0** — `model_calls` 541 = exactly one request per task, the same request count as the bare arm |
| answers edited or replaced by the harness | 0 (no event, no replacement — the validator slot scores the model's own bytes) |
| prompt tokens / completion tokens | 53 378 / 362 290, overhead tokens 0 |
| truncations at the 1200 ceiling | **72/541 = 13.3 %** (bare arm: 62/541 = 11.5 %; same ceiling, the difference is sampling, not harness — the harness added no budget and no steps) |
| summed engine time | 4629.6 s (bare arm: 4622 s) |
| GPU energy (2 Hz sampler, 1835 samples, mean 128.1 W, busy fraction 0.89) | **165.29 Wh** (bare arm: 163.8 Wh, +0.9 %) |

Paired per-task join over all 541 ids (`ifeval-pub-ifeval-v1-verdicts.jsonl` for each arm):
strict 16 wins / 21 losses for contour, exact sign test **p = 0.511**; loose 16/20, p = 0.618.
The two arms disagree on 37/541 = 6.8 % of cells at identical shape and temperature 0.7 — that
is this set's resolution floor, and the −0.9 pp strict / −0.7 pp loose nominal delta sits under
it: **no measurable contour effect on IFEval, at matched shape, with zero extra cost beyond
sampling variance.** Discordance is truncation-shaped in both directions: 10 of the 21 contour
losses are rows where the contour arm itself hit the ceiling, and 5 of the 16 contour wins are
rows where the bare arm hit it. The strict loss ids: `ifeval-1203, 1325, 1389, 1392, 1446, 1645,
1883, 1954, 2209, 2216, 2246, 2247, 2273, 2292, 2471, 2591, 2871, 2904, 3063, 3091, 3617`;
the wins: `ifeval-1129, 1236, 1307, 1653, 1759, 1779, 1813, 201, 2041, 2250, 2275, 2605, 292,
3048, 3345, 3424`.

Scoring gates were green at scoring time: upstream unit suite 41/41 on the first attempt,
reference responses strict 415/540 and loose 431/540 inside the recorded band (±2.0 pp); the
checker-noise rule stands — deltas under ~0.5 pp on this set are the checker, not the model.

**Verdict for item P0 on IFEval:** the frozen contour runtime over a public set with a real
validator neither fires nor helps: 0 events, 0 repairs, 0 extra requests, 165 Wh for the same 541
calls, percent indistinguishable from the bare arm. A harness that never fires on a format set
where it has a validator slot is a measured null, published as such.

## Reproduce (verified 2026-11-09 from the published copies, not from the local workspace)

Published arm bytes (`benchmarks/public/arms/`, SHA-256/16):

| file | lines | sha16 |
|---|---|---|
| `ifeval-basalt-answers.jsonl` | 541 | `445dfa2eba3d12aa` |
| `ifeval-basalt-verdicts.jsonl` | 541 | `1884989e822f21e3` |

The scorer's own verdict sidecar (SHA-1/16, the convention `pub_bench_ifeval.py` writes) is
`af8969ac6e95422f` over the same bytes — the publisher masked nothing in these two files, so both
hashes name identical content. Publication went through `scripts/publish_pub_bare_arm.py`, which
imports the same scrub function as the contour publisher (one sanitizer) and refuses an arm with a
partial row count, duplicate ids or >5 % blank answers.

```
# the pinned IFEval venv, never the system interpreter
python3 <ifeval-venv>/bin/python scripts/pub_bench_ifeval.py \
        benchmarks/public/arms/ifeval-basalt-answers.jsonl \
        benchmarks/public/ifeval.tasks.jsonl \
        ifeval qwen3.8-flash-next-iq3_s-basalt "verification re-score" --out /tmp/ifeval-check
```

Contour arm bytes (published 2026-11-09 after the matched-shape leg; SHA-256/16):

| file | lines | sha16 |
|---|---|---|
| `ifeval-contour-matched-answers.jsonl` | 541 | `e611e76ebdd808cf` |
| `ifeval-contour-matched-verdicts.jsonl` | 541 | `c0e732166d9441ef` |
| `ifeval-contour-matched-results.jsonl` | 541 | `d8a519a5f9b07c18` |
| `ifeval-contour-matched-ledger.jsonl` | 541 | `13c467d36c61d183` |
| `ifeval-contour-matched-stats.json` | 28 | `54aa65eb78feb3b4` |
| `ifeval-contour-matched-run-record.json` | 45 | `d4a3dc5fbb9481d4` |
| `ifeval-contour-matched-plan.json` | 1 | `9c505e0d46010d59` |
| `ifeval-contour-matched-bank-version.json` | 6 | `18ea68bc69082099` |
| `ifeval-contour-matched-ws-identity.json` | 43 | `e190c300652007a2` |

Re-scoring the PUBLISHED copy (same command as above with `ifeval-contour-matched-answers.jsonl`
in place of the basalt file, run 2026-11-09): strict reproduces exactly at 462/541 = 85.4 %;
loose came back 476 vs the arm's 477 — one `langdetect` flip inside the documented checker noise.
The publisher masked 1082 `hostname` fields and 1 LAN address in the run record/results rows;
answer text is unedited. Two placeholder-mailbox tokens inside the drafted-email answers are
suppressed by sha16-bound metadata-class exception records in the repo scanner (counted, never
dropped: `...-answers.jsonl@...c947101b`, `...-results.jsonl@...c52ccca3`, SHA-1/16), because
masking them would edit the scored bytes. The zero-event census in the table above is checkable
directly from `ifeval-contour-matched-ledger.jsonl` (empty events column on all 541 rows).

Run on the published copies it reproduced the digest row exactly: strict **467/541 = 86.3 %**, loose
**481/541 = 88.9 %**, instruction checks 751/834 = 90.0 %, same hardest-check list. Its own gate run
scored the reference responses at strict 416/540 and loose 430/540 — one task off the earlier
run's 417/431 on identical bytes, which is the checker drift the caveats above price in.

Publication plumbing fixed on the same day, no number changed: the IFEval scorer used to splice its
row into `PUB-DIGEST.md` by a string partition, which put the row **above** the table's `|---|`
separator (GitHub then renders the table as prose). It now calls `pub_bench_score.write_digest`,
the single writer that owns the header, the newest-first order and the separator; the misplaced row
was rewritten through that writer and the duplicate it produced during the rewrite was removed, so
the digest carries exactly one `ifeval / qwen3.8-flash-next-iq3_s-basalt / 541` row.

## Caveats to read with the numbers

* **Contamination.** IFEval has been public since 2023 and instruction-tuning corpora in 2026
  routinely contain it. 86.3 % is a format-compliance yardstick for a 24 GB quantized local brain,
  not a held-out capability measurement.
* **Not saturated, so headroom is real.** Unlike GSM8K/ARC for this model, IFEval leaves ~14 pp of
  headroom, and the failures concentrate in verifiable length/keyword constraints rather than in
  content.
* **Resolution floor.** Temperature 0.7 with no request seed means a bare-vs-contour paired
  comparison on 541 cells carries a seed-noise floor of its own (the hard bank measured 5.2 % of
  cells flipping between identical stamps) plus the checker's ±1 task per run. Deltas under ~2 cells
  will be published as unresolvable.
* **Request-shape confound is controlled, not assumed**: the contour leg runs with the bare arm's
  shape (first token rung 1200, serve-default thinking, no request seed). Escalation-shape rows
  published earlier for other sets stay published and marked superseded; their bytes are not edited.
* **The 1200-token ceiling is shared by both local arms.** If the contour leg escalates on a
  truncated answer it has no higher rung to go to under the matched shape, so both arms pay the same
  ceiling and the truncation count is part of every comparison here.

## `pub-repair-v1` — the validator in the loop instead of beside it (2026-11-09 18:24 CET)

The contour rows above are nulls, and the census said why: its gates watch request/response shape and
the first public answer is already well-formed, so the repair path never opens. This section measures the
missing loop at arm level (`scripts/pub_bench_repair.py`, contract `pub-repair-v1`): the pinned first-arm
answer bytes are read (no paid re-run), the pinned `pub-ifeval-v1` validator names the violated checks
and their pinned kwargs, and the task is re-asked **once**. A retry replaces the first answer only if it
strictly passes (`keep-best`); `retry-only` shows what an unconditional second try would score. The
frozen `0.0.2.56` rows and the bare row are untouched, byte for byte.

| arm | n | request shape | strict | instruction checks |
|---|---|---|---|---|
| first arm, bare bytes, re-scored in this same scorer pass | 541 | temp 0.7, `max_tokens` 1200 | 469/541 = 86.7 % | 748/834 = 89.7 % |
| **`pub-repair-v1` keep-best** | 541 | same shape + 72 one-shot re-asks | **497/541 = 91.9 %** | 783/834 = 93.9 % |
| `pub-repair-v1` retry-only | 541 | second answer always taken | 497/541 = 91.9 % | — |
| ChatGPT `gpt-6.1-sol`, single pass (published row) | 541 | transport hides sampling params | 515/541 = 95.2 % | — |

Census and statistics:

* validator rejected 72 of 541 first answers; one re-ask each → **28 fixed, 44 still failing, 0 made
  worse** (a passing task is never asked). Exact two-sided sign test over the 28 discordant tasks:
  **p = 7.5e-09**. The honest caveat next to that p: this compares a two-attempt protocol against a
  one-attempt protocol, not one model against another, so it measures the loop, not the brain.
* gap recovery in this pass: first arm 86.7 %, ChatGPT 95.2 % → the repair took **+5.2 pp of the 8.5 pp
  gap (61 %)** for 72 extra calls.
* cost, measured not modelled: 72 calls, 101,470 tokens (29,179 prompt + 72,291 completion), 779 s of
  call time, GPU sampler 310 samples over 780 s at a mean 131.0 W → **28.4 Wh**, i.e. **1.01 Wh and
  ~3.6k tokens per fixed task**.
* recorded confound that makes the number a lower bound: **34 of 72 retries ended `api_finish=length`**
  at the inherited 1200-token budget, and a truncated retry is scored as a failed repair rather than
  excused. A 2400-token variant (`pub-repair-v2`) is queued; until it runs, this row understates the
  mechanism.
* checker noise applies to this set as documented above: the published bare row is 467/541, while this
  scorer pass re-scored the same bytes at 469/541 (468 in an earlier pass the same day) — the upstream
  checker's `langdetect` call flips one or two tasks per run, so only deltas above ~0.5 pp are read as
  differences. The 30-task move here is far outside that band.

Residual hardest checks after repair: `length_constraints:number_words` 13, `detectable_format:json_format`
6, `keywords:letter_frequency` 5, `length_constraints:number_sentences` 5, `startend:quotation` 4,
`combination:repeat_prompt` 3 — the same surface families, now down roughly two-to-one.

Reproducibility: `arms/pub-repair-v1-merged-answers.jsonl` (sha16 in the sidecar) holds the answer the
repaired arm actually gives, `arms/pub-repair-v1-verdicts.jsonl` records per task whether the kept answer
came from the first attempt or the retry, and both re-score offline with `pub-ifeval-v1` to 497/541 with
zero model calls. `arms/pub-repair-pub-repair-v1-census.json` carries the same census the scorer printed.

**Resolved 2026-11-09 19:15 CET:** the queued 2400-token variant ran — see `pub-repair-v2` below. The v1
numbers above stand unchanged as the 1200-token-retry arm; an offline re-score of the published merged
copy today gives 495/541, inside the documented ±1–2 task checker-flake band around the published 497.

## `pub-repair-v2` — the same loop with a 2400-token retry budget (2026-11-09 19:15 CET)

The understatement recorded in v1 is now measured out. Same protocol, same pinned validator
(`pub-ifeval-v1`), same stored first-arm answer bytes (first-arm answers sha16 `543eb8621087e552`),
same re-ask wording — only the retry `max_tokens` is overridden from 1200 to 2400, and that moves the
contract id to `pub-repair-v2` (tooling commit `1cdc353`); the v1 row, artifacts and bytes are untouched.

| arm | n | request shape | strict |
|---|---|---|---|
| first arm, re-scored in this pass | 541 | temp 0.7, `max_tokens` 1200 | 467/541 = 86.3 % |
| `pub-repair-v1` (retry 1200, published above) | 541 | + 72 one-shot re-asks at 1200 | 497/541 = 91.9 % |
| **`pub-repair-v2` keep-best (retry 2400)** | 541 | + 74 one-shot re-asks at 2400 | **509/541 = 94.1 %** |
| `pub-repair-v2` retry-only | 541 | second answer always taken | 509/541 = 94.1 % |
| ChatGPT `gpt-6.1-sol`, single pass (published row) | 541 | transport hides sampling params | 515/541 = 95.2 % |

Census (census file sha16 `79cd33edad21f86d`):

* This pass the validator rejected 74 first answers, not 72: the first arm re-scored at 467/541
  instead of 469/541, and two tasks that passed in the v1 pass fell inside the documented
  langdetect flake band. The census records the re-asks this pass actually made, not the v1 set.
* 74 re-asks → **42 fixed, 32 still failing, 0 made worse** (retry-only equals keep-best again —
  a passing task is never asked and no retry replaces a passing answer). Sign test over 42/0:
  p = 4.5e-13.
* **The budget swap measured directly**, on the 72 tasks both passes re-asked: 14 pass at 2400 that
  failed at 1200, and one the other way (`ifeval-3572` — a retry is a fresh sample, not a replay of
  the first draw, so single-cell flips in both directions are re-draw variance). 14W/1L, p = 0.001.
  The 1200-token ceiling was exactly what made v1 a lower bound; removing it moved keep-best
  497 → 509 (+12 tasks).
* Truncation census: 24/74 retries hit the 2400 ceiling (34/72 hit 1200). Of the 34 tasks that
  truncated at 1200, **15 pass at 2400 and 19 still fail with double the budget** — those 19 are
  genuine checker-level failures, not budget starvation.
* Cost, measured not modelled: 74 calls, 173,074 tokens (29,591 prompt + 143,483 completion),
  1272.7 s of call time; GPU sampler 489 samples over 1234 s at a mean 138.1 W → **47.32 Wh**, i.e.
  **1.13 Wh and ~4.1k tokens per fixed task** (v1: 28.4 Wh, 1.01 Wh). Doubling the retry budget
  doubles the energy and lifts the fix rate 28/72 → 42/74 (39 % → 57 %).
* Gap framing for this set: first arm 467, ChatGPT single pass 515 → the repair loop at 2400 closes
  the 48-task gap to 6 tasks (94.1 % vs 95.2 %).
* Caveats, carried and new: the two-attempt-vs-one-attempt caveat from v1 still frames the p-value;
  the first-arm baseline moves 467–469 per scorer pass (checker band ±2 tasks), so 497 → 509 is a
  real +12 outside the band but the two arms are not byte-matched pairs; an independent re-score of
  the published merged copy gives 510/541, inside the documented flake band around the census's 509 —
  no byte drift.

Reproducibility: `arms/pub-repair-v2-merged-answers.jsonl` (sha16 `ee4728cc10e4498f`),
`arms/pub-repair-v2-verdicts.jsonl` (sha16 `47281abd5357f0c0`), the 74 stored retry rows in
`arms/pub-repair-pub-repair-v2.jsonl` (sha16 `49e27893c44c9b0d`) and
`arms/pub-repair-pub-repair-v2-census.json`; the percent re-scores offline with `pub-ifeval-v1`
and zero model calls.
