# GSM8K (test, 1319 tasks) — three-arm result

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
2. **The harness cannot change this score.** GSM8K is graded on the final answer only
   (`number` checker on the `ANSWER:` line), so contour vs no-contour is invisible here. That
   is stated in `PUB-PLAN.md` and is why the contour arm only joins benchmarks 4 (IFEval) and
   9 (BFCL).
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
