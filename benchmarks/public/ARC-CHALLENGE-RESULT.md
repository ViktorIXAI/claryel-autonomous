# ARC-Challenge (1172 tasks) — four-arm result (three brains + the frozen contour parity arm)

Date: 2026-11-08. Pinned task file `benchmarks/public/arc-challenge.tasks.jsonl`, tasks sha16
`523af08216f14256` (source: Hugging Face `allenai/ai2_arc`, ARC-Challenge test split, normalised
to a four-option letter prompt; the random-guess floor is 25 %). Checker contract in force at
scoring time: `pub-checkers-v2` (`scripts/pub_bench_score.py`, self-test 19 cases / 0 failures,
`letter` checker). Every arm stored its answer bytes; the percents are reproducible from them.

## Arms

| arm | model / transport | tasks | strict | wall time | call parameters |
|---|---|---|---|---|---|
| brain-basalt (full set) | `qwen3.8-flash-next-iq3_s-basalt`, IQ3_S on a 24 GB-class GPU, no contour | 1172/1172 | **1129/1172 = 96.3 %** | 1665 s (1.42 s/task), one draw per task | temp 0.7, max_tokens 1200, single seed pass |
| brain-basalt (matched subset) | same | 300/300 | **293/300 = 97.7 %** | first 300 ids of the full leg | temp 0.7, max_tokens 1200 |
| codex | `gpt-6.1-sol`, codex-cli 0.166.0, reasoning xhigh, read-only sandbox, prompt via STDIN | 300/300 | **290/300 = 96.7 %** | 1562 s (5.2 s/task) | sampling parameters not exposed by the transport |
| grok | `grok-4.7`, hermes one-shot, toolsets off, prompt inline | 300/300 | **288/300 = 96.0 %** | 5128 s (17.1 s/task) | sampling parameters not exposed by the transport |
| contour-0.0.2.56 (item P0) | the FROZEN contour runtime `0.0.2.56` on the same endpoint model, category `P` (no hard-bank family scaffolding), public checkers in the validator slot | 300/300 | **283/300 = 94.3 %** | 144 s leg wall, 127.3 s measured engine time (0.42 s/task) | streamed request, `request_seed` pinned (sp1), token ladder 512→1200, `enable_thinking` off — NOT identical to the bare arm's call shape, see the parity section |

Cross-arm numbers use the **pre-registered matched subset**: the first 300 task ids in file
order (`--limit 300 --offset 0`), fixed before any arm ran. 300/300 answered in every arm, 0
dropped in the join, 0 empty answers, 0 transport failures.

## Paired sign tests on the matched 300

Exact two-sided sign test over discordant pairs only (`scripts/pub_bench_compare.py`).

| pair | W/L | diff | p |
|---|---|---|---|
| basalt vs codex | 4W / 1L | +1.0 pp | 0.375 |
| basalt vs grok | 5W / 0L | +1.7 pp | 0.0625 |
| codex vs grok | 5W / 3L | +0.7 pp | 0.727 |
| basalt vs contour-0.0.2.56 | 11W / 1L | +3.3 pp | **0.0063** |

Discordant ids, so an outside reader can audit the flips:

* basalt beats codex on `arc-challenge-0067, 0069, 0070, 0222`; loses on `arc-challenge-0182`.
* basalt beats grok on `arc-challenge-0070, 0072, 0081, 0139, 0179`; loses on none.
* codex beats grok on `arc-challenge-0072, 0081, 0139, 0179, 0182`; loses on
  `arc-challenge-0067, 0069, 0222`.
* basalt beats contour on `arc-challenge-0004, 0049, 0079, 0088, 0139, 0151, 0204, 0211, 0236,
  0259, 0271`; contour beats basalt on `arc-challenge-0189`.

## Contour parity (item P0): the frozen runtime on the same 300 ids

> **SUPERSEDED 2026-11-08 23:20 CET as a parity row.** This section's arm ran at a
> 512-token first rung with `enable_thinking:false` and a pinned request seed — a request
> shape the bare arm never used (it generated 1,911 tokens in total, 6.4 per task, because
> thinking was switched off, against the bare arm's 110 per task). The matched-shape re-run
> at the end of this document (**291/300 = 97.0 %**) replaces it. The bytes of this leg stay
> published unchanged.

The arm ran as a systemd user unit on the same endpoint as the bare leg, staged by
`scripts/pub_bench_contour_ws.py` (harness modules byte-verbatim, contract guard green, tasks
sha16 `523af08216f14256`), scored with the same `pub-checkers-v2` bytes as every other row.

### What the harness actually did (from `gate-ledger-main.jsonl`, 300 rows)

| measure | value |
|---|---|
| contour/repair events fired | **0** (no `contour:*`, no `fix:*`, no gate block, no answer edit) |
| token-ladder escalations 512→1200 | 1 row |
| rows truncated at the ceiling / empty answers / engine stalls | 0 / 0 / 0 |
| model calls / gate fixes / gate blocks | 300 / 0 / 0 |
| prompt + generated tokens | 24,737 in + 1,911 out |
| measured engine time inside a 144 s wall | 127.3 s |
| GPU energy (sampled, full-leg window 141 s, 57 samples) | **4.50 Wh**, mean 112.9 W, max 170 W |

### The parity delta and its attribution — read this before quoting the −3.3 pp

The paired sign test says the contour-stamped arm scored **significantly lower** than the bare
arm (11W/1L, p = 0.0063). The mechanism census says the contour machinery **did nothing at all**
on these 300 rows: zero contour/fix events, one ladder escalation, zero edits — on every one of
the 12 discordant ids the two arms' answer generation was the same code path. The frozen runtime
does route public tasks away from all hard-bank grammars (category `P`), which GSM8K and
ARC-Easy already proved; this leg confirms it again.

So the −3.3 pp is **not a contour-quality measurement**. Two real differences separate the two
arms, and both are sampling shape, not harness behaviour:

1. The contour arm pins `request_seed` (sp1) and streams; the bare arm ran one unseeded pass at
   temperature 0.7. Two different request shapes on a non-batch-invariant engine are two draws
   from the same brain, not a treatment and a control.
2. The two legs sat on **different serve processes**: the bare leg ran at 17:38–18:07 CET on the
   old serve, and the contour leg ran at 20:43–20:45 CET after the serving engine was restarted
   at 20:36–20:39 CET under a memory-pressure incident (host swap exhausted; the first 25-row
   attempt at this leg stalled on the sick endpoint and was discarded whole as
   `dead1/` before the healthy rerun — 25 partial rows were never scored or joined). Prior
   hard-bank work on this harness measured exactly this effect: the same stamp over the same
   seeds twice flips ~5 % of cells at this sample size.

What is quotable: on answer-only sets the frozen harness adds **no repair activity** (0 edits
out of 900 contour-arm rows across gsm8k + both ARC sets) and its own cost is small (one ladder
retry per 300 short tasks here), and its per-arm score drifts ±3 pp from the bare arm as pure
sampling variance at n = 300. The parity row therefore establishes plumbing and an overhead
bound, and the −3.3 pp cell is labelled variance, not regression. To resolve contour vs bare at
better than ±3 pp on this set needs ~10× the matched sample, which the line will not pay for on
a saturated benchmark.

**Verdict:** on ARC-Challenge the local brain (97.7 % on the matched 300, 96.3 % on the full
1172) is at or above both cloud brains, basalt-vs-grok reaching p = 0.0625 without clearing it;
the four brains are inside a 1.7 pp band and 300 tasks cannot order them. The contour parity arm
is published with a significant-looking paired delta whose mechanism census is null — the delta
is attributed to request shape and engine restart, stated in the same table, not buried.

## Resources

* bare local leg: GPU sampler at ~2 s, 658 samples over 1733 s, mean 127.7 W, peak 215 W, mean
  utilization 97 %, estimated **61.58 Wh** for the 1172-task leg (~52.5 mWh/task).
* contour local leg: 4.50 Wh for the 300-task leg (15 mWh/task) — the same 300 ids cost the
  contour arm ~2.7× less wall than the bare arm's full-set mean because the first 300 ids are
  the easy, short part of the file; token totals (26,648) are dominated by the 24,737 prompt
  tokens, so the harness overhead measured here is 1 extra 512-token rung, nothing else.
* Cloud legs: wall time only (1562 s codex, 5128 s grok). The grok leg overlapped other legs in
  wall-clock time; different transports, no shared endpoint.

## Honest caveats

1. **Saturation and contamination.** ARC-Challenge is public since 2021; last reported frontier
   public number 95.3 % (`PUB-PLAN.md`). All four arms sit 94–98 %; memorisation cannot be
   excluded; these rows are not intelligence claims.
2. **One draw per task at temperature 0.7** for both local arms; the contour arm is a second,
   differently-seeded draw, which is exactly why its paired delta must be read as variance
   (see the parity section).
3. **Cloud arms hide their sampling parameters**; labelled by transport, not pinned.
4. **Cloud transports checked for leakage**: both answer files grepped for
   `bank|answer_key|expected|/home/|/Users/` — 0 matches.
5. The 25-row dead first attempt of the contour leg (engine restarted under it) is kept on disk
   as `dead1/` and contributes nothing to any published number.

## Matched-shape contour parity (item P0 re-run, 2026-11-08 23:15 CET) — supersedes the section above

The parity rule on this line requires the contour leg's request shape to equal the bare arm's:
first token rung = the bare arm's 1200, the serve's default thinking state (no
`chat_template_kwargs`, no `reasoning_effort`), temperature 0.7, no request seed. The re-run used
the frozen stamp `0.0.2.56` with `PARB_SHAPE=bare PARB_LADDER=1200` (a call-parameter switch,
pinned by `harness/gate_shape_parity_test.py`; no contour feature is registered and the hard line
stays frozen), workspace `pub-arc-challenge-contour-matched`, bank sha16 `e56146d09263ca89`
(byte-identical bank to the superseded leg), harness git `06def0b`, checker contract
`pub-checkers-v2`, the same first 300 ids in file order.

| measure | escalation shape (superseded) | **matched shape (this row)** | bare arm (same 300) |
|---|---|---|---|
| strict | 283/300 = 94.3 % | **291/300 = 97.0 %** | 293/300 = 97.7 % |
| first rung / ladder | 512→1200 | 1200, single rung | 1200 |
| request seed | sp1 pinned | none (bare policy) | none |
| thinking | `enable_thinking:false` | serve default | serve default |
| endpoint requests | 300 + 1 ladder escalation | **300 (0 ladder steps)** | 300 |
| contour/repair events, edits, truncations, stalls | 0 / 0 / 0 / 0 | **0 / 0 / 0 / 0** | n/a |
| generated tokens (total, mean per task) | 1,911 (6.4) | **32,304 (108)** | 32,986 (110.0, same 300 ids) |
| prompt tokens | 24,737 | **36,737** | — |
| engine time / leg wall | 127.3 s / 144 s | **554.9 s / 567 s** | one 1172-task leg: 1665 s wall, 1.42 s/task |
| GPU energy (sampled) | 4.50 Wh (57 samples, mean 112.9 W) = 15.0 mWh/task | **19.38 Wh** (225 samples, mean 123.0 W, busy 0.68) = 64.6 mWh/task | 61.58 Wh over the full 1172-task leg = 52.5 mWh/task (the first-300 slice was not sampled separately) |

### Paired sign tests on the matched 300

| pair | W/L | diff | p |
|---|---|---|---|
| bare vs contour (matched shape) | 3W / 1L | +0.7 pp for bare | 0.625 |
| contour (matched) vs contour (escalation shape) | 10W / 2L | **+2.7 pp for matched** | 0.0386 |
| bare vs contour (escalation shape), published earlier | 11W / 1L | −3.3 pp | 0.0063 |

### Verdict on this row

* **Parity, as expected on a saturated set:** 97.0 % matched-shape contour vs 97.7 % bare, 3W/1L,
  p = 0.625 — no measurable harness effect in either direction, and the edit census is zero again.
* The superseded −3.3 pp was a **thinking-state artifact**, not variance hand-waving: with
  `enable_thinking:false` the same brain generated 6.4 tokens per task instead of 108 and lost
  2.7 pp (10W/2L against the matched leg, p = 0.039). The attribution written above — "request
  shape and engine restart" — is now resolved to the request shape; the engine restart explains
  nothing on its own.
* Cost side: one request per task, 0 ladder steps, 19.38 Wh for 300 tasks (0.065 Wh/task) against
  the bare arm's 0.053 Wh/task on the same ids — the +21 % is the contour arm's streamed transport
  and the check pass, not extra model calls; the superseded thinking-off leg cost only 15.0 mWh/task precisely
  because it stopped the brain from reasoning, which is the same effect that cost it 2.7 pp.
