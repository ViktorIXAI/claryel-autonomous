# HumanEval (164 tasks) — arms so far (local brain + codex; grok queued, contour parity measured 2026-11-09)

Date: 2026-11-08. Pinned task file `benchmarks/public/humaneval.tasks.jsonl`, tasks sha16
`971d976289cd9357` (source: openai/human-eval `HumanEval.jsonl.gz`, see `MANIFEST.json`).
This set is scored by **execution**, not text matching: checker contract `pytest-v1`
(`scripts/pub_bench_exec.py`) runs the upstream `check(candidate)` tests for every stored answer
in a resource-limited child process (address/CPU/file-size/process rlimits, 25 s wall timeout,
private temp cwd, empty environment). No network isolation is claimed. The checker's own
self-test (reference solution passes, a deliberately wrong completion fails) is enforced before
any percent is printed; the percents below come from re-executing stored answer bytes, and
per-id verdict files (`verdicts-basalt.jsonl`, `verdicts-codex.jsonl` in the run archive) make
the flips auditable.

## Arms

| arm | model / transport | tasks | strict (executed) | wall time | call parameters |
|---|---|---|---|---|---|
| brain-basalt | `qwen3.8-flash-next-iq3_s-basalt`, IQ3_S on a 24 GB-class GPU, no contour | 164/164 | **158/164 = 96.3 %** | 1697 s (10.3 s/task) | temp 0.7, max_tokens 1200, single seed pass |
| codex | `gpt-6.1-sol`, codex-cli 0.166.0, reasoning xhigh, read-only sandbox, prompt via STDIN | 164/164 | **163/164 = 99.4 %** | 1484 s (9.0 s/task) | sampling parameters not exposed by the transport |
| contour-0.0.2.56, matched shape (item P0, 2026-11-09) | the FROZEN contour runtime `0.0.2.56` on the same endpoint model, category `P` (no hard-bank family scaffolding), validator slot = the `pytest-v1` execution checker that scored the bare row | 164/164 | **155/164 = 94.5 %** | 1190 s wall, 1175 s measured engine time (mean 7.16 / median 7.38 s/task) | temp 0.7, first rung 1200 (single rung), serve-default thinking, no request seed — the bare arm's call shape; see the parity section |
| grok | `grok-4.7`, hermes one-shot, toolsets off | not started yet (grok legs are serialized on the transport; its slot is after the GPQA grok leg) | pending — no percent published for a partial arm | — | — |

The matched set is the **full 164-task file** (`--limit` unused): cross-arm comparison on this
set needs no subset, and no ids were dropped in any completed arm (164/164 answered, 0 empty).

## Paired sign test on the matched 164

Exact two-sided sign test over discordant pairs only (`pytest-v1` verdicts per id, not text
checks):

| pair | W/L | diff | p |
|---|---|---|---|
| basalt vs codex | 1W / 6L | −3.0 pp | 0.125 |

* codex beats basalt on `humaneval-0032, 0124, 0132, 0134, 0145, 0147`; basalt beats codex on
  `humaneval-0064`.

**Verdict:** on execution-verified code synthesis the cloud arm is ahead by 6 net tasks, and at
n = 164 with only 7 discordant pairs the exact test cannot resolve it (p = 0.125). What *is*
quotable is that the local 24 GB quantized brain executes 158/164 = 96.3 % of upstream HumanEval
tests green in one pass; the honest caveat is saturation — codex at 99.4 % sits at the ceiling of
a benchmark that frontier models have mostly trained through (HumanEval is public since 2021 and
retired from serious 2026 aggregators). Contamination, not capability, may explain the cloud
number; that is why this line also runs unsaturated sets (GPQA Diamond above, SimpleBench next).

## Local resource telemetry (basalt leg)

GPU sampler at 2 s on the serving box: 667 samples over 1690 s, mean 116.7 W, peak 209 W,
mean utilization 97 %, estimated **54.85 Wh** for the leg. No sampled energy for cloud legs
(wall time only, per line rules).

## Contour parity (item P0): REFUSED on this set, stated rather than faked

> **SUPERSEDED as a refusal, 2026-11-09 01:05 CET.** A matched-shape contour row now exists and is
> published in the last section of this document; the bytes above stay exactly as written. The
> refusal was correct against an arm that could *iterate* against the grading oracle, and it does
> not describe the arm that actually ran: the published ledger shows one endpoint request per task
> on all 164 rows, 0 ladder steps, 0 gate fixes, 0 gate blocks and 0 contour events, so no answer
> was ever kept or rewritten because a test went green. The oracle concern is carried into the new
> section as an explicit measurement limit rather than deleted.

Item P0 asks every published set to carry a row from the frozen contour runtime `0.0.2.56`
scored by the same public checker. On HumanEval that construction is invalid: the public checker
*is* the hidden test suite, so wiring it into the harness validator slot would hand the contour
loop the grading oracle (it could keep an answer only because the scorer's tests went green),
while the bare arm never saw them. That measures the oracle, not the contour, so **no contour
parity row is published for HumanEval**. On the answer-only sets (gsm8k, ARC, GPQA) the checker
is a pure text function and parity runs are valid — they are published there instead.

## Matched-shape contour parity (item P0, 2026-11-09 01:05 CET) — the first contour row on a code set

**Why the refusal no longer applies.** The rule on this line is that a contour row is admissible
when its request shape equals the bare arm's (`PARB_SHAPE=bare PARB_LADDER=1200`: first rung 1200,
serve-default thinking, temperature 0.7, no request seed) **and** when the validator slot holds the
bytes that scored the bare row. For HumanEval those bytes are the `pytest-v1` execution checker
(`scripts/pub_bench_exec.py`, module sha16 `dce154f6c02b24fd`), so `scripts/pub_bench_contour_ws.py`
grew a `validator=exec` selector that puts exactly that module in the slot and refuses to stage
unless the checker's own self-test passes first (reference passes, wrong completion fails). Before
launching, the shim was proven on the box-free path: the workspace's category-`P` checker returns
`pub:exec_ok` for the reference solution and `pub:exec_fail:AssertionError` for a wrong body.

Identity: workspace `pub-humaneval-contour-matched`, bank label `pub-humaneval-164`, ws bank sha16
`c0b6d759ef6d8d5f`, tasks sha16 `971d976289cd9357` (the whole 164-id file in file order), contour
stamp `0.0.2.56` (behavior 2.56), harness git `1514c5ac` — **no new contour feature is registered;
the hard line stays frozen at `0.0.2.56`.**

| measure | **contour-0.0.2.56, matched shape** | bare arm (same 164 ids) |
|---|---|---|
| strict, executed | **155/164 = 94.5 %** | 158/164 = 96.3 % |
| first rung / ladder | 1200, single rung | 1200 |
| request seed / thinking | none / serve default | none / serve default |
| endpoint requests | **164 (0 ladder steps)** | 164 |
| contour events, gate fixes, gate blocks, answer edits | **0 / 0 / 0 / 0** | n/a |
| truncated at the 1200 ceiling | **3 (`humaneval-0032, 0064, 0094`), all 3 scored as SyntaxError losses** | finish reason not recorded |
| prompt tokens | **31,488** | 31,488 (identical — the matched-shape signature) |
| generated tokens (mean per task) | **100,173 (610.8)** | 98,892 (603.0) |
| engine time (mean / median per task) | **1175.0 s (7.16 / 7.38 s)** | 1696.7 s (10.35 / 9.16 s) |
| leg wall | **1190 s** | 1697 s |
| GPU energy | **39.11 Wh sampled** (468 samples, span 1186 s, mean 118.7 W, busy 0.87) = 238 mWh/task | 54.85 Wh **estimated** from utilisation, a different mechanism |

### Paired sign test (execution verdicts per id)

| pair | W/L | diff | p |
|---|---|---|---|
| bare vs contour (matched shape) | 6W / 3L | +1.8 pp for bare | 0.508 |

Contour wins `humaneval-0124, 0134, 0147`; bare wins `humaneval-0064, 0067, 0094, 0100, 0103, 0130`.
The decomposition matters more than the totals: two of the six bare wins (`0064`, `0094`) are rows
where **this contour draw** ran out of room at 1200 tokens and the code broke mid-function, and the
third truncated row (`0032`) failed in both arms. The other four bare wins are model-draw
differences (`0067` ValueError, `0100` SyntaxError without truncation, `0103` and `0130`
AssertionErrors), and the contour arm picked up three cells the bare arm missed. Nine discordant
cells out of 164 (5.5 %) is the resolution of this instrument, so the -1.8 pp is **not** a contour
effect: the sign test cannot separate these two draws (p = 0.508).

### The oracle question, answered with the ledger rather than with a claim

The published ledger (`arms/humaneval-contour-matched-ledger.jsonl`, 164 rows) gives:
`model_calls == 1` on 164/164 rows, `ladder_steps == 0` on 164/164, `gate_fixes == 0`,
`gate_blocks == 0`, and an **empty events column on every row**. So the test suite was read only
after each answer's bytes were final: nothing was selected, repaired or re-drafted because a test
went green. That is why this row is admissible while an arm that used test feedback would not be —
and it is the boundary for any future code-scaffolding arm: a harness that iterates against tests
must be scored on a held-out suite, which is a bank-design question the frozen line cannot answer.

**Verdict: a measured null, and this time on the set where a harness could in principle matter most.**
At the bare arm's shape the frozen runtime is behaviourally inert on code (zero machinery fired, one
request per task, prompt tokens identical to the bare arm) and the score difference sits inside the
draw noise. What is quotable as a cost is the **token ceiling**: 3 of 164 code answers ran out of
room and all three became format-level losses, which is a call-parameter effect, not a contour one.

### Caveats on this row

1. **Seconds and energy are not pairable across windows.** This leg ran 00:43–01:03 CET on an idle
   endpoint; the bare leg ran earlier, and its 54.85 Wh is an *estimate* from utilisation while this
   leg's 39.11 Wh is a `power.draw` integral. Two mechanisms, two windows — no cost claim between
   them.
2. **One draw per task, temperature 0.7, no request seed** (the bare policy, per the parity rule).
3. **Contamination**: HumanEval is a public static set retired for frontier comparison; the codex arm
   here scores 99.4 %, which is a memorisation-flavoured number, not an ability claim.
4. **Answer bytes shipped and re-scored after publication**: `arms/humaneval-contour-matched-*.jsonl`
   re-scored from the published copy with the pinned execution checker reproduces **155/164**; the
   answer fields give 0 leakage hits (the single pattern match is the word *bank* inside a restated
   task about a bank account).

## Next

* grok leg (full 164) queued behind the GPQA grok leg on the same transport; its row and a
  three-arm paired table land when it scores.
* LiveCodeBench (post-cutoff window) is the contamination-aware replacement for this set and is
  queued on the ladder, not tonight.
