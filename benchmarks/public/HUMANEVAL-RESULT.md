# HumanEval (164 tasks) — arms so far (local brain + codex; grok queued, contour parity refused)

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

Item P0 asks every published set to carry a row from the frozen contour runtime `0.0.2.56`
scored by the same public checker. On HumanEval that construction is invalid: the public checker
*is* the hidden test suite, so wiring it into the harness validator slot would hand the contour
loop the grading oracle (it could keep an answer only because the scorer's tests went green),
while the bare arm never saw them. That measures the oracle, not the contour, so **no contour
parity row is published for HumanEval**. On the answer-only sets (gsm8k, ARC, GPQA) the checker
is a pure text function and parity runs are valid — they are published there instead.

## Next

* grok leg (full 164) queued behind the GPQA grok leg on the same transport; its row and a
  three-arm paired table land when it scores.
* LiveCodeBench (post-cutoff window) is the contamination-aware replacement for this set and is
  queued on the ladder, not tonight.
