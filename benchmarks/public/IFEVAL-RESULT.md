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
| codex `gpt-6.1-sol` xhigh (subscription CLI, stdin transport) | 541 (full set) | `2c672531577dcc33` | transport does not expose sampling params | **no percent published: the arm is incomplete.** The leg ran 08:24 → 12:39 CET and stopped by its own fail-closed transport rule after 440 ok rows; the ChatGPT subscription hit its usage limit (CLI: `You've hit your usage limit … or try again at 1:32 PM`). The 440 stored rows stay on disk and the leg is resumable by id | — | — |
| grok-4.7 | 541 | `2c672531577dcc33` | — | suspended by owner quota, resumes 2026-11-12 | — | — |

Cross-arm standard for this window is three arms (bare local / contour matched shape / ChatGPT
codex): the Grok quota ran dry on the owner side on 2026-11-09 and no Grok percent is produced for
this set before 2026-11-12. As of 12:39 CET the same is true of the ChatGPT side for THIS set — the
codex leg stopped at 440/541 rows on the subscription usage limit, so the IFEval cross-arm comparison
is currently **two arms** and no ChatGPT IFEval number exists in this repository. The stopped leg and
its purged rows are recorded in `LEG-INCIDENTS.md`; the arm is resumable by task id and a completed
arm will be scored with the same `pub-ifeval-v1` contract.

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
