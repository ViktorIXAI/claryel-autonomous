# MMLU-Pro (pinned 500-row subset of the 12,032-row test split) — four arms scored

Date: 2026-11-09. Pinned task file `benchmarks/public/mmlu-pro.tasks.jsonl`, tasks sha16
`c64264aede2498c7` (source: Hugging Face `TIGER-Lab/MMLU-Pro` test split, full-split raw sha16
`21420424edfbbbc2`; fetcher and split audit in `MANIFEST.json` and the pin commit). The 500 rows
are the pre-registered **stride-24 sample** — every 24th row of the split in file order, fixed
before any arm ran; a head slice would have been subject-skewed because the split is ordered in
14 contiguous category blocks. Measured on the bytes: the subset covers all 14 top-level
categories within 0.3 pp of the full-split mix (math 11.0 % vs 11.2 %, history 3.0 % vs 3.2 %)
and 86 of the 91 source subcategories. Checker contract in force: `pub-checkers-v2`
(`scripts/pub_bench_score.py`, self-test green, `letter` checker — 10-option A–J MCQ).

## Arms (matched set = the whole 500-row pinned subset)

| arm | model / transport | tasks | strict | wall time | call parameters |
|---|---|---|---|---|---|
| brain-basalt | `qwen3.8-flash-next-iq3_s-basalt`, IQ3_S on a 24 GB-class GPU, no contour | 500/500 | **432/500 = 86.4 %** | 2027 s (4.05 s/task), one draw per task | temp 0.7, max_tokens 1200, unseeded |
| contour-0.0.2.56 (item P0, matched shape) | the FROZEN contour runtime `0.0.2.56` on the same endpoint model, category `P`, public checkers in the validator slot | 500/500 | **429/500 = 85.8 %** | 2633 s leg wall, 2611.7 s measured engine time | bare-matched request shape: one 1200-token rung, unseeded, no `chat_template_kwargs`, no `reasoning_effort` (serve-default thinking), temp 0.7 |
| codex | `gpt-6.1-sol`, codex-cli 0.166.0, reasoning xhigh, read-only sandbox, prompt via STDIN | 500/500 | **462/500 = 92.4 %** | 3827 s (7.7 s/task) | sampling parameters not exposed by the transport |
| grok | `grok-4.7`, hermes one-shot, toolsets off (transport build `v0.23.1+2.gb3746e3.dirty`, newer than the earlier grok arms — sampling params still not exposed) | 500/500 | **430/500 = 86.0 %** | 8368 s wall (00:59:10–03:18:38 CET; early 12.3 s/task, slow reasoning tail after 460/500) | sampling parameters not exposed by the transport; one call per task, `PUB_CLOUD_TIMEOUT=2400` |

500/500 answered in every completed arm, 0 empty, 0 transport failures; the join dropped no ids
(`scripts/pub_bench_compare.py`, re-score of the stored answer bytes reproduces every digest row).

## Paired sign tests (matched 500)

Exact two-sided sign test over discordant pairs only.

| pair | W/L | diff | p |
|---|---|---|---|
| basalt vs contour-0.0.2.56 (matched shape) | 17W / 14L | +0.6 pp | 0.720 |
| basalt vs grok-4.7 | 28W / 26L | +0.4 pp | 0.892 |
| contour-0.0.2.56 vs grok-4.7 | 28W / 29L | −0.2 pp | 1.000 |
| basalt vs codex | 7W / 37L | −6.0 pp | 5e-6 |
| contour vs codex | 7W / 40L | −6.6 pp | 1e-6 |
| codex vs grok-4.7 | 38W / 6L | +6.4 pp | 1.2e-6 |

Discordant ids (`mmlu-pro-` prefix elided).

* basalt over contour: `0792 0936 11400 1344 1776 2376 3696 4992 5088 6096 6576 7344 7800 7896
  8352 9408 9504`; contour over basalt: `10128 11184 11352 11808 11880 1728 1824 3792 4200 6144
  6552 7200 8952 9768`.
* codex over basalt: `0480 0504 0864 1008 10128 11184 11304 11352 11568 11688 11808 11832 11880
  11976 1200 12024 1368 1680 1728 1824 3144 3480 3792 3912 4200 4440 4584 4944 5016 5520 6192
  6552 7200 7968 8952 9480 9768`; basalt over codex: `11400 11496 2472 2520 5904 6912 7248`.
* codex over contour: `0480 0504 0792 0864 0936 1008 11304 11568 11688 11832 11976 1200 12024
  1344 1368 1680 1776 2376 3144 3480 3696 3912 4440 4584 4944 4992 5016 5088 5520 6096 6192 6576
  7344 7800 7896 7968 8352 9408 9480 9504`; contour over codex: `11496 2472 2520 5904 6144 6912
  7248`.
* basalt over grok: `10272 10632 1080 11040 11400 11496 11592 11760 1344 1440 1488 2520 3360 3864
  3984 4272 4536 4824 5568 5904 6576 7248 7344 7896 7992 8400 9720 9816`; grok over basalt: `0504
  0888 1008 10128 11184 11304 11568 11688 11808 11832 11880 11976 12024 1416 1824 2616 3480 3792
  4200 4440 4944 5520 6144 6192 7968 9768`.
* contour over grok: `10272 10632 1080 11040 11352 11496 11592 11760 1440 1488 1728 2520 3360
  3864 3984 4272 4536 4824 5568 5904 6552 7200 7248 7992 8400 8952 9720 9816`; grok over contour:
  `0504 0792 0888 0936 1008 11304 11568 11688 11832 11976 12024 1416 1776 2376 2616 3480 3696
  4440 4944 4992 5088 5520 6096 6192 7800 7968 8352 9408 9504`.
* codex over grok: `0480 0864 10272 10632 1080 11040 11352 11592 11760 1200 1344 1368 1440 1488
  1680 1728 3144 3360 3864 3912 3984 4272 4536 4584 4824 5016 5568 6552 6576 7200 7344 7896 7992
  8400 8952 9480 9720 9816`; grok over codex: `0888 1416 2472 2616 6144 6912`.

The local-vs-codex gap (44–47 discordant ids, p ≤ 5e-6) sits well above the noise floor measured
below, so the direction is real; −6 pp is the honest size on this set. The same separation holds
against the third external arm: codex beats grok on 38/6 discordant ids (p = 1.2e-6), while
grok-4.7 (86.0 %) lands inside the local cluster — basalt 86.4 %, contour 85.8 %, both pairs
non-significant (p = 0.892 / 1.000). On this set the local 24 GB brain with no contour matches the
cloud grok arm within draw noise; only codex separates.

## Contour parity (item P0) on MMLU-Pro: admissible shape, null delta, visible cost

Staged by `scripts/pub_bench_contour_ws.py` with the parity shape switch
(`PARB_SHAPE=bare PARB_LADDER=1200`); the row's own shape is stamped in `gen.request_shape` and
the run record (`bare-matched: first rung = LADDER[0], no seed, no reasoning_effort, no
chat_template_kwargs (serve-default thinking), ladder rungs 1200`), pinned by
`harness/gate_shape_parity_test.py`. This is the fourth matched-shape parity row on the line
(gsm8k, arc-easy, arc-challenge, gpqa, humaneval before it), and the PARITY SHAPE RULE was applied
from the start — no escalation-shape row was published for this set.

Ledger/stats census over 500 rows (frozen stamp `0.0.2.56`, behavior 2.56, from
`contour-matched-stats.json`):

| measure | value |
|---|---|
| contour/repair events, gate fires, gate fixes, gate blocks | **0 / 0 / 0 / 0** (public category `P` reaches no family grammar) |
| token-ladder escalations | **0** — 500 requests for 500 tasks (`model_calls 500 + ladder_steps 0`) |
| rows truncated at the 1200 ceiling | **0** |
| prompt + generated tokens (accepted calls) | 126,651 in + 190,184 out (bare leg: identical 126,651 in + 186,601 out) |
| engine time inside a 2633 s wall | 2611.7 s (bare leg: 2026.2 s inside 2027 s) |
| GPU energy (sampled, own unit + own csv) | **93.19 Wh** over 2622 s (mean 127.9 W, busy 0.88); bare leg **74.29 Wh** over 2022 s (mean 132.3 W, busy 0.90) |

The −0.6 pp parity delta is **not quotable**: the contour leg with zero events is the same model
at the same request shape on a fresh unseeded draw, and the two configurations disagree on 31 of
500 cells (6.2 %) — that discordance **is** this harness's single-draw resolution floor at
temp 0.7 on 500 MCQ rows, and 17W/14L (p = 0.720) sits inside it. The quotable parity finding is
the cost side, same as on the other matched rows: 0 gates fired, identical request count and
identical prompt bytes, yet **+28.9 % engine seconds and +25.4 % sampled GPU energy** (5.22 vs
4.05 s/task, 186.4 vs 148.6 mWh/task). The two legs ran back-to-back on the same 24 GB endpoint
(02:06–02:40 vs 02:45–03:29), and per the line's endpoint-window rule this tail is published as
**endpoint state, not measured harness overhead** — with 500 requests and 0 ladder steps there is
no per-request mechanism left to attribute it to.

## Caveats

1. **Contamination.** MMLU-Pro's test split has been public since 2024 and is heavily
   represented in 2026 training corpora; codex 92.4 % is at the top of published frontier numbers,
   so neither cloud number is a clean knowledge measurement. This line keeps the set as a
   local-brain regression yardstick, not an IQ claim.
2. **Subset, not full split.** Every number here is on the pre-registered stride-24 500-row
   subset (sha `c64264aede2498c7`), never on the 12,032-row split. Subsets are never re-cut after
   seeing scores.
3. **Single draw, temp 0.7.** The 6.2 % discordance rate between identical-shape configurations
   bounds every per-arm delta: deltas under ~3–4 pp at n = 500 are unresolvable here; the 6 pp
   codex gap clears that bar with p ≤ 5e-6.
4. **Guessing floor.** 10-option MCQ gives a 10 % floor; not binding at these scores.
5. **Cloud transports hide sampling parameters** (codex and grok rows).
6. ~~**Open item:** the grok arm for this set is not started~~ — **closed 2026-11-12:** the grok
   arm completed inside the owner quota window (leg 00:59:10–03:18:38 CET) and published
   430/500 = 86.0 %; the set is now complete on the four-arm template. *(Reason corrected
   2026-11-10: the earlier delay was the owner quota suspension — no grok arm launches before
   2026-11-12 — not transport serialization behind the GPQA/HumanEval legs, which was the wording
   when this table was written.)*

## Reproduce

`scripts/pub_bench_score.py benchmarks/public/mmlu-pro.tasks.jsonl <answers.jsonl>` (self-test +
`pub-checkers-v2`), `scripts/pub_bench_compare.py` for the sign tests, and
`scripts/gpu_energy.py` over the leg csv windows for the energy rows. Published arm artifacts
(results/ledger/answers/stats/run-record/plan per arm) ship under `arms/` via
`scripts/publish_pub_arms.py`.

## Answer bytes for the MMLU-Pro bare and codex arms are now published (2026-11-10 02:40 CET)

The two non-contour rows in `PUB-DIGEST.md` (bare 432/500 = 86.4 %, codex 462/500 = 92.4 %) had no
stored answers. Shipped now: `arms/mmlu-pro-basalt-answers.jsonl` (500 rows, `fc9e8741edfec51e`) and
`arms/mmlu-pro-codex-answers.jsonl` (500, `17230236196545a4`). Re-score from the shipped copies under
`pub-checkers-v2` (self-test 22/22, zero model calls): 432/500 and 462/500, exactly as published.
Scrub masked nothing; zero path/IP/key hits. The grok leg on this set was never started (deferred by
the owner quota window), so there is nothing to ship for it.

## Grok leg on this set: contract pre-registered (2026-11-11, tick 45)

The grok arm has never been started here (owner quota window). It is leg 3 of the 2026-11-12 queue
(**500** ids, `mmlu-pro-0000`..`mmlu-pro-12024`, ETA band **2.1-2.9 h** labelled as an extrapolation
from measured grok rates on other sets — 14.9 / 17.1 / 20.9 s/task — not from a leg of this set). When
complete it is scored by `pub-checkers-v2` (`letter`) over the **500** pinned ids with the same
matched-set rule as the bare and codex rows (first 500 ids of the pinned file in file order, frozen
before any arm ran), and the row names the transport version of its rows. A partial arm publishes no
percent and its bytes stay unshipped while partial.

## Grok arm completed inside the quota window (2026-11-12 03:18 CET)

Leg 3 of the 2026-11-12 Grok queue, launched once by the guarded chain unit and resumed by id
(the pre-registered contract `pub-checkers-v2`, `letter`, over the 500 pinned ids — unchanged from
the tick-45 pre-registration above). Wall 8368 s (started 00:59:10, `done: ok=500 bad=0` at
03:18:38 CET); rate 12.3 s/task through 460/500 then a slow reasoning tail, the same shape as the
GPQA Grok leg — the ETA line at 460/500 said 8 min, actual finish was ~20 min later, so the
pre-registered band for this set (2.1–2.9 h extrapolation) held (2.33 h actual).
* Stored arm file: 500 rows / 500 unique ids / 500 `finish=ok` / 0 parked non-ok rows
  (`scripts/pub_cloud_blank_purge.py` report mode, exit 0), SHA-256/16 `5731d720f13ef8a5`.
* Shipped as `arms/mmlu-pro-grok-answers.jsonl` (500 lines, SHA-256/16 `5731d720f13ef8a5`,
  SHA-1/16 `8f306afb5bc8026f`); the scrub masked nothing and the shipped bytes are identical to
  the runner output. Re-score of the shipped copy under `pub-checkers-v2` (self-test 22/22)
  reproduces 430/500 = 86.0 %.
* Privacy grep of the answer fields: one benign English-word hit (`banks` in a macroeconomics
  answer, `mmlu-pro-6720`); zero path/IP/credential hits.
* Transport build for this leg is `v0.23.1+2.gb3746e3.dirty` (the CLI self-updated on 2026-11-11;
  the earlier Grok arms carry `v0.23.0+860.gf17db36.dirty`) — recorded per the rule that a row
  names the transport version of its own rows; sampling parameters remain hidden by the transport.
* Digest row: `mmlu-pro | grok-4.7 | 500 | c64264aede2498c7 | … checker pub-checkers-v2 |
  430/500 = 86.0 %`. No published byte of an earlier row moved.
