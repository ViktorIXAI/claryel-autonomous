# GSM8K (test, 1319 tasks) — four-arm result (three brains + the frozen contour parity arm)

Date: 2026-11-08. Pinned task file `benchmarks/public/gsm8k.tasks.jsonl`, tasks sha16
`7dd0080ff23b8bc3` (source: openai/grade-school-math `test.jsonl`, normalised to one
`ANSWER:`-terminated prompt per task, see `MANIFEST.json`). Checker contract in force at
scoring time: `pub-checkers-v2` (`scripts/pub_bench_score.py`, self-test 18/18, `number`
checker only). Every arm stored its answer bytes; the percents below are reproducible from
them.

## Arms

| arm | model / transport | tasks | strict | wall time | call parameters |
|---|---|---|---|---|---|
| brain-basalt (full set) | `qwen3.8-flash-next-iq3_s-basalt`, IQ3_S on a 24 GB-class GPU, no contour | 1319/1319 | **1284/1319 = 97.3 %** | 5828 s of measured call time (mean 4.42 s/task), one draw per task | temp 0.7, max_tokens 1200, single seed pass |
| codex | `gpt-6.1-sol`, codex-cli 0.166.0, reasoning xhigh, read-only sandbox, prompt via STDIN | 300/300 | **293/300 = 97.7 %** | 2263 s (7.5 s/task) | sampling parameters not exposed by the transport |
| grok | `grok-4.7`, hermes one-shot, toolsets off, prompt inline | 300/300 | **288/300 = 96.0 %** | 6270 s (20.9 s/task) | sampling parameters not exposed by the transport |
| contour-0.0.2.56 (item P0) | the FROZEN contour runtime `0.0.2.56` over the same endpoint model, category `P` (no hard-bank family scaffolding), public checkers in the validator slot | 300/300 | **290/300 = 96.7 %** | 1426 s wall, 1194 s measured call time (mean 3.98 s/task) | streamed request, `request_seed` pinned (sp1), token ladder 512→1200, `enable_thinking` off — NOT identical to the bare row's call shape, see the parity section |

Cross-arm numbers use the **pre-registered matched subset**: the first 300 task ids of the
pinned file in file order, fixed before any arm ran (`--limit 300 --offset 0`). No ids were
dropped in the join (300/300 answered in all three arms), and no arm was partial: 0 empty
answers in every leg, 0 transport failures.

On that same 300-id subset the local brain scores 295/300 = 98.3 %; the 97.3 % headline is the
full 1319-task set, which is the arm the local budget was planned for.

## Paired sign tests on the matched 300

Exact two-sided sign test over discordant pairs only (`scripts/pub_bench_compare.py`), so the
same task ids and the same order are compared, never two different averages.

| pair | W/L | diff | p |
|---|---|---|---|
| basalt vs codex | 6W / 4L | +0.7 pp | 0.754 |
| basalt vs grok | 9W / 2L | +2.3 pp | 0.065 |
| codex vs grok | 8W / 3L | +1.7 pp | 0.227 |

Discordant ids are listed so an outside reader can audit the flips, not just the totals:

* basalt beats codex on `gsm8k-0100, 0146, 0184, 0255, 0267, 0288`; loses to it on
  `gsm8k-0012, 0085, 0093, 0234`.
* basalt beats grok on `gsm8k-0040, 0100, 0125, 0144, 0147, 0161, 0184, 0231, 0288`; loses on
  `gsm8k-0012, 0085`.
* codex beats grok on `gsm8k-0040, 0093, 0125, 0144, 0147, 0161, 0231, 0234`; loses on
  `gsm8k-0146, 0255, 0267`.

**Verdict:** on GSM8K the local 24 GB quantized brain is statistically indistinguishable from
both cloud brains (the smallest gap, basalt vs grok, still lands at p = 0.065 with only 11
discordant pairs). A 300-task MCQ-style math set cannot resolve a 2-point difference; that is
a resolution limit of the instrument, not a finding about the models. The line therefore moves
to unsaturated sets (ARC, then SimpleBench at 81.9 % best public) rather than quoting a winner
here.

## Contour parity (item P0): the frozen runtime on the same 300 ids

Owner request 2026-11-08: every published set also carries a row from the **frozen contour
runtime `0.0.2.56`** (tag `stable-hard-0.0.2.56`), same ids, same public checkers. The arm ran as
a systemd user unit on the same endpoint as the bare leg, staged by
`scripts/pub_bench_contour_ws.py` (harness modules copied verbatim, contract guard green, bank
label `pub-gsm8k-300`, tasks sha16 `7dd0080ff23b8bc3`) and scored with the same
`pub-checkers-v2` bytes as every other row here.

### What the harness actually did (from `gate-ledger.jsonl`, 300 rows)

| measure | value |
|---|---|
| contour/repair events fired | **0** (no `contour:*`, no `fix:*`, no gate block, no answer edit) |
| token-ladder escalations 512→1200 | 37 rows (12.3 %) — 337 real endpoint requests for 300 tasks |
| rows still truncated at the 1200 ceiling | 6 (5 of them ended with no `ANSWER:` line and scored as losses) |
| model calls per row / gate fixes / gate blocks | 1 / 0 / 0 |
| prompt + generated tokens (accepted call per row) | 27,164 in + 104,629 out |
| measured call time | 1194.4 s (mean 3.98 s/task), 0 engine-stall rows |
| GPU energy (sampled, new since the bare leg) | 46.53 Wh over 1420 s, 562 samples, mean 118 W, 88 % busy |

The zero is not luck: `gate_run`'s contour machinery is keyed to the hard-bank task families
(A–K), and a public task is category `P`, so the family grammars are unreachable by construction.
The only reachable behaviour is the generic ladder (a truncation gets one more attempt at the
next rung). Two accounting properties of the frozen runner are published rather than hidden:
`model_calls` counts one per task (the ladder retries are in `ladder_steps`, so the true request
count is 300 + 37 = 337), and the token totals cover the accepted call per row, so the 37
discarded 512-token attempts are not inside `ctok_total`.

### Paired test against the bare row (same 300 ids)

`scripts/pub_bench_compare.py`, exact two-sided sign test over discordant pairs:
**bare 295/300 = 98.3 %, contour 290/300 = 96.7 %, 6W/1L, p = 0.125.**

* bare wins: `gsm8k-0062, 0084, 0139, 0162, 0163, 0255`; contour wins: `gsm8k-0085`.
* Of the six bare wins, two are ladder/ceiling losses (the answer hit 1200 tokens with no
  `ANSWER:` line: `0062`, `0139`), one is a checker artifact (`0084`: the answer contains two
  `ANSWER:` occurrences, the first quoting an intermediate line `$15 + 7 = 22$`; the contract
  reads the first match, so the correct final `ANSWER: 15` is not what gets parsed), and three
  are genuine wrong values in this draw (`0162`, `0163`, `0255`).
* The contour arm's 10 losses decompose the same way: 5 truncations without an `ANSWER:` line,
  5 wrong values (including the `0084` first-match artifact).

**Verdict (P0, GSM8K): no measurable gain and a real cost.** The frozen harness fires zero
gates on an answer-graded set, costs ~12 % extra requests through the ladder, and its ceiling
policy turns 5 long-reasoning answers into format losses. The −1.7 pp delta sits on 7 discordant
pairs, far below the ~2-cell/5 %-flip resolution floor of this harness, so the direction is not
a measurement of contour quality — it is a sample-draw difference plus truncation policy. What
*is* quotable is the cost side: a harness that never fires is pure overhead, and the parity row
makes that visible instead of assuming it.

Two honest confounders: the frozen runner streams the request, pins a request seed (sp1) and
starts at rung 512, while the bare row used one non-streamed, unseeded 1200-token call — so the
two rows are different draws of the same model, not the same sample with/without gates. And a
foreign session (one established connection from another LAN host, ~120 k-token prompts with
thinking enabled) shared the serve during this leg, which is why per-task seconds range 2.4–17.4 s
and why its energy figure is not pairable against the bare leg (which has no sampled energy).

## Resources

* Local leg: prompt 173,082 tokens + generated 360,442 tokens = 533,524 tokens for 1319 tasks
  (mean 131 in / 273 out per task), mean 4.42 s per task. **GPU energy was NOT sampled for
  this leg** — no sampler was attached when it ran; the number stays missing rather than
  estimated. From the ARC legs on, a GPU sampler runs per local leg.
* Cloud legs: wall time only (no local resources consumed).

## Honest caveats

1. **Contamination and saturation.** GSM8K is a public, static 2021 set and is retired for
   frontier comparison in 2026 aggregators (last reported public GSM8K number 92.6 % — see
   `PUB-PLAN.md`). Our local quantized brain scores 97.3 %, i.e. above the public frontier
   number quoted for much larger models, which is a strong sign that memorisation cannot be
   excluded. This row is a plumbing and regression yardstick, **not** an intelligence claim.
2. **The harness cannot change this score, and now that is measured, not assumed.** GSM8K is
   graded on the final answer only (`number` checker on the `ANSWER:` line), so contour vs
   no-contour was expected to be invisible here — the item P0 parity arm (section above) ran the
   frozen runtime on these same ids and it fired **zero** gates while costing 12 % extra
   requests. Item P0 (owner request 2026-11-08) nevertheless requires the parity row on every
   published set, precisely so this claim is auditable rather than stated.
3. **One draw per task, temperature 0.7.** No best-of-N, no retry, no seed sweep. On a set this
   saturated a single-draw flip is worth at most one task per arm; all three paired verdicts
   above are within that noise floor except where noted.
4. **Cloud arms hide their sampling parameters.** The CLI transports do not expose
   temperature/max_tokens, so their rows are labelled by transport instead of a fake pin. They
   are not run at a matched temperature and this is not fixable through the transport.
5. **Cloud transports are file/tool capable.** codex runs in a read-only sandbox with STDIN
   prompt and grok runs with toolsets off. Both answer sets were grepped for
   `bank|gold|expected|/home/|/Users/|<LAN_IP-prefix>|answer_key` before publication: the only
   two matches are the word *gold* inside task text the model was restating (`gold coins` in
   `gsm8k-0033`, `marigolds` in `gsm8k-0074`), i.e. 0 leakage hits and 0 local paths.
