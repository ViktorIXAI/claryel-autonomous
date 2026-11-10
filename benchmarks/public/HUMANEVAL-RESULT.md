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
| grok | `grok-4.7`, hermes one-shot, toolsets off | **suspended by owner quota, resumes 2026-11-12** (leg ran from 04:07 CET 2026-11-09, stopped 07:57 CET with 120 of 164 rows stored — a stored-row count, not a score; 44 ids to go, resumable by id) | no percent for a partial arm | — | — |

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

## Checker correction: contract `pytest-v2` (2026-11-09) — corrected re-score of all three arms; the grok arm will be scored at v2

**Trigger (measured, not assumed).** During the in-flight grok leg (81/164 rows at write time), a
dry run of the partial answers showed 14 of the 80 present rows failing with `SyntaxError`, and the
failing rows were **correct Python wrapped in un-fenced prose** (grok answers in Russian with
non-ASCII punctuation `—` and `→` around the code). Under pytest-v1 the extraction is "fenced
blocks, else the whole text", so the prose was compiled as code. That is an extraction artifact,
not a model result; scoring the grok arm at v1 would have published a number that measures the
transport's answer style.

**The new contract (versioned, never patched in place).** `scripts/pub_bench_exec.py` now ships
`pytest-v2`: the v1 extraction stands whenever it composes to a syntactically valid program — so
**every v1 pass stays a pass byte-identically** (monotone by construction; flips can only be 0→1).
Only a syntactically broken v1 text triggers the window scan: the largest contiguous line window
that (a) contains the task's `def <entry>` and (b) composes to a valid program. It is purely
structural — gold is never read, the test suite is never used as extraction feedback — and
fail-closed: no parseable entry-containing window means the v1 bytes stand, i.e. the original loss
stands. Boundary, stated: a body-only completion wrapped in prose stays a loss (no `def` anchor to
search around). The checker self-test now pins all four properties before any percent prints:
prose-wrapped correct code passes, prose-wrapped wrong code still fails, v1-clean answers extract
identically, prose without any entry def fails.

**A/B re-score on the same stored answer bytes** (`scripts/pub_exec_v2_ab.py`, zero model calls,
task sha unchanged `971d976289cd9357`):

| arm | pytest-v1 (as-run, rows above stay published) | pytest-v2 (corrected) | flips (0→1 only) |
|---|---|---|---|
| brain-basalt | 158/164 = 96.3 % | **159/164 = 97.0 %** | `0124` (fenced answer carried a stray fence marker that broke v1 compilation; the function itself was complete and green) |
| codex | 163/164 = 99.4 % | 163/164 = 99.4 % | none |
| contour-0.0.2.56 matched | 155/164 = 94.5 % | **157/164 = 95.7 %** | `0064`, `0100` |

**Corrected paired tables at v2** (exact two-sided sign test over discordant cells):

| pair (v2) | W/L | discordant ids | p |
|---|---|---|---|
| codex vs basalt | 5W / 1L | codex-only `0032,0132,0134,0145,0147`; basalt-only `0064` | 0.219 |
| basalt vs contour (parity) | 4W / 2L | basalt-only `0067,0094,0103,0130`; contour-only `0134,0147` | 0.688 |

No verdict changes: the cloud-vs-local gap and the parity null were and stay inside the resolution
floor; the correction moves the local numbers by at most one or two tasks. The v1 rows above and
in `PUB-DIGEST.md` remain published **as-run** (bytes never edited); the corrected percents are
added as new digest rows labelled `checker pytest-v2 (corrected offline rescore)`. The codex row
needed no corrected digest row (identical number). Future contour arms stage the v2 checker bytes
into the validator slot; published workspaces keep their pinned v1 copies, which is why their
as-run numbers can still be reproduced exactly.

**Sequencing correction.** The grok leg for HumanEval started at 04:07 CET on 2026-11-09, **in
parallel** with the still-running GPQA grok leg on the same transport (not strictly behind it as
the earlier Next section said); the parallelism costs throughput (~2× per-row time) and is stated
here because cross-arm cost numbers are only valid inside one transport window. The grok arm will
be published at `pytest-v2` (the v1 number for that arm would be a style artifact), with the
transport caveat (prose-wrapped answers) named next to the percent.

## Next

* grok leg (full 164) queued behind the GPQA grok leg on the same transport; its row and a
  three-arm paired table land when it scores.
* LiveCodeBench (post-cutoff window) is the contamination-aware replacement for this set and is
  queued on the ladder, not tonight.

## Grok status on this set (2026-11-09, supersedes the grok bullet above)

Owner quota decision 2026-11-09: no grok arm launches before **2026-11-12**. The humaneval grok leg
that was running was stopped at 07:57 CET with **120 of 164** rows stored; those partials are kept
intact and resumable by id, and **no percent is published for them**. The grok cell in any table on
this set reads "suspended by owner quota, resumes 2026-11-12". The `pytest-v2` re-score of that arm
happens only on the completed set.

## Published answer bytes of the bare arm (2026-11-09 23:5x CET): a completeness gap on this set, closed

Until now this set published the contour arm's answer bytes but **not the bare arm's**, so the bare
row (159/164, `pytest-v2`) could not be re-checked by anyone outside the machine that ran it. Shipped
through `scripts/publish_pub_bare_arm.py`, which prints its own index lines and refuses partial arms:

| file | rows | SHA-256/16 |
|---|---|---|
| `arms/humaneval-basalt-answers.jsonl` | 164 | `4f61b87d5e8d130b` |
| `arms/humaneval-basalt-verdicts.jsonl` | 164 | `6878c8b128c3c05d` |

Nothing masked (164 of 164 rows byte-identical to the runner output), and the verdict rows were
regenerated from the shipped answers by `pytest-v2` — 159 pass, reproducing the digest row exactly.
The published contour-matched copy was re-scored the same way in the same session: **157/164**, which
is also what its digest row says.

## Repair arm `pub-repair-humaneval-v1` — pre-registration, written before any call exists

Ladder item 5 is a verdict-only repair pass over the bare arm's failures. Everything below is fixed
**before** the arm runs, so the judgment cannot be chosen after the result.

* **Headroom census, computed from stored bytes (zero model calls, `pytest-v2` self-test asserted
  first):** the bare arm fails **5 of 164** cells — `humaneval-0032`, `-0132`, `-0134`, `-0145`,
  `-0147`. All five are **wrong-value** failures (an assertion in the hidden battery fires); **none**
  is a syntax error, a crash class or a parse failure. Ceiling for a repair pass on this set is
  therefore **5 cells = 3.05 pp**, and the failure class is the one a verdict-only re-ask is weakest
  on: "your program returned a wrong value" carries no information the model did not already have.
* **Redraw control, from published bytes of the same brain:** the contour-0.0.2.56
  bare-matched arm passes **2 of those same 5 cells** (`humaneval-0134`, `-0147`) with no feedback at
  all — 1.22 pp of the 3.05 pp ceiling is a plain second draw.
* **Decision rule:** the repair percent is reported **only** beside the redraw control, and the
  mechanism claim requires the matched sign test on the 5 shared cells. On this set a verdict-only
  re-ask names only the class ("the program returned a wrong value on the hidden tests" / "crashed" /
  "did not compile") — no test body, no gold value, no example input/output, because HumanEval ships
  no public tests and the verifier here **is** the scorer.
* **Small-sample warning, mandatory and pre-registered:** at 164 tasks the resolution floor is ~2 pp
  (≈3 tasks); with 5 discordant cells the *best possible* exact sign test result is 5/0, p = 0.0625,
  i.e. **this arm cannot reach p < 0.05 even by fixing every failure**, and any 1-vs-2 outcome is
  noise. It is worth running only as a wiring/cost measurement on a code set, and it will be
  published as such whatever it returns.
* **Next tick:** ship the `humaneval` validator branch in `scripts/pub_bench_repair.py` and run the
  5-cell arm (plus the 2 control conversions from the same rule), with the same artifact set
  (retry rows, census, merged answers, verdict rows) and the same byte-pinned publication path.

## Repair arm `pub-repair-humaneval-v1` (2026-11-10 00:09–00:10 CET): the pre-registered null, and it is a perfect one

The arm ran exactly as pre-registered above: 5 verdict-only re-asks over the bare arm's failures, at
the first arm's 1200-token budget, coarse failure class only, no test body, no gold value, no example
pair, no exception-class name. Wiring guard first: the branch reproduced the **published** bare-arm
verdict rows cell for cell (**164/164 ids**) before any model call, and the checker self-test
(`pytest-v2`) ran before scoring.

| arm | verdict | redraw-conversions of the bare arm's 5 failures |
|---|---|---|
| bare first arm (published) | **159/164 = 97.0 %** | — |
| redraw control — contour-0.0.2.56 bare-matched arm, no feedback | 157/164 overall | **2** (`-0134`, `-0147`) |
| `pub-repair-humaneval-v1`, keep-best = retry-only | **161/164 = 98.2 %** | **2** (`-0134`, `-0147`) |

**The two sets are identical.** The repair converted exactly the cells a plain second draw already
converts: repair-only **0**, control-only **0**, both 2 → matched sign test **0/0, p = 1.0**. Against
the first arm the arm-level move is 2/0, p = 0.5 — not significant, as pre-registered (the best this
arm could ever reach on 5 discordant cells was p = 0.0625). The +1.2 pp on the percent **is** the
redraw floor, nothing more. Every asked cell was in the `wrong_value` class, and that class tells the
model nothing it did not already have: a bare "your program returned a wrong value" is not a repair
signal on a set that ships no public tests, which is the opposite of the BFCL result where naming
call-count vs unmatched-call moved 45/124 and beat the redraw 23/7.

*Cost, published because this is what a wiring measurement is for:* 5 calls, all `finish=ok`,
**1 ceiling hit at the inherited 1200-token budget** (the thinking block eats the budget before the
code does — the same ceiling the BFCL arm hit once in 124), 2 796 prompt + 4 444 completion tokens,
median **8.78 s** per call, ask phase wall **49.2 s**, 0 transport errors. Sampled GPU energy
**1.51 Wh** over the 48 s window (20 samples at 2 s, mean 113.3 W, GPU busy 0.85); a window this short
is a per-call cost figure, not a run-level one, and the endpoint is the fleet's main brain.

*What this arm certifies.* Nothing about capability. It certifies that the repair loop runs honestly
on an **execution** set — the checker gates before and after, the wiring guard matches published
verdict bytes, keep-best never adopted a worse answer (0 cells made worse), and the merged arm
re-scores to its published percent from the shipped bytes. It also certifies the negative: **a repair
pass is not automatically a mechanism**; on a set whose only feedback channel is "wrong", it is a
second draw with extra tokens. The ladder keeps the LCB pattern (public tests in the validator slot)
as the only code-set repair that showed a real effect.

*Artifacts* (`benchmarks/public/arms/`, SHA-1/16 sidecars, and no scanner exception needed — these
answer bytes are clean code, the infra scan is 0 findings):
`pub-repair-pub-repair-humaneval-v1.jsonl` (`f8a5792dc4ae00e0`, 5 retry rows),
`pub-repair-pub-repair-humaneval-v1-census.json` (`ed7937b51eb16f70`, carries the pre-registration
numbers inside it), `pub-repair-humaneval-v1-merged-answers.jsonl` (`5064a5e658289487`),
`pub-repair-humaneval-v1-verdicts.jsonl` (`647b5a0992ea3f1f`), plus the redraw-control sidecar
`humaneval-contour-matched-verdicts-v2.jsonl` (`84949a2520f4fdf3`, generated offline from the
published contour-matched answers by `pytest-v2`, scorer-only — never shown to any model). The digest
row names the SHA-256/16 `971d976289cd9357` of the pinned task file, unchanged.

## Budget-matched control (2026-11-10 00:48–00:54 CET): at 1200 the ceiling, not the feedback, was the limit

The v1 row reported **1 ceiling hit of 5 retries**, so 161/164 was published as a lower bound. Two more
arms ran over the **same 5 first-arm failures** at the same temperature; the first arm stays the pinned
1200-byte arm and none of its bytes moved:

* `pub-repair-humaneval-v2` — identical wording, retry budget **2400** (`PARB_MAX_TOKENS=2400` renames
  the contract; a different request shape is never the same contract);
* `pub-redraw-humaneval-2400` — the **matched redraw control**: the re-ask is the bare task prompt
  verbatim, no verdict block, no previous answer. Guard pinned before the leg: a control prompt
  containing the verdict header or the first 200 chars of the previous answer aborts the run, and a
  unit check proves both branches (repair prompt ≠ bare prompt, control prompt == bare prompt).

| arm (5 re-asks over the same cells) | re-ask shape | conversions | which cells | keep-best |
|---|---|---|---|---|
| first arm (published) | — | — | — | 159/164 = 97.0 % |
| redraw control @1200 (the published contour-matched arm) | 1200, no feedback | 2 | `-0134`, `-0147` | 157/164 overall |
| `pub-repair-humaneval-v1` @1200 | 1200 + verdict class | 2 | `-0134`, `-0147` | 161/164 = 98.2 % |
| `pub-redraw-humaneval-2400` | 2400, no feedback | 2 | `-0134`, `-0147` | 161/164 = 98.2 % |
| `pub-repair-humaneval-v2` | 2400 + verdict class | **4** | `-0032`, `-0132`, `-0134`, `-0147` | **163/164 = 99.4 %** |

Two effects come apart cleanly now, and the numbers are generated from the shipped verdict files by
`scripts/pub_bench_verdict_sign.py` (one sign-test source, key aliases `ok` / `strict`):

* **the budget alone moves no verdict.** the redraw@2400 verdict map is *byte-identical* to the
  repair@1200 map (both sha16 `647b5a0992ea3f1f`) — same two cells, 0 worse, 0.0 pp;
* **at a matched request shape the feedback converts 2 cells a plain redraw does not**: repair-only
  `-0032` and `-0132`, control-only none, 0 cells made worse → **2/0, p = 0.50**. Directional only:
  with 5 discordant cells this set cannot reach significance (the pre-registered best case was
  p = 0.0625), and it is the same direction the BFCL arm measured at scale (23/7, p = 0.0052).
* against the first arm, v2 is **4W/0L, p = 0.125**.

Whole-set pairings between independent draws are *not* the mechanism test and are published with their
noise named: the contour-matched control vs `repair@1200` puts 4 extra wins on cells the **first arm
already passed** (`-0067`, `-0094`, `-0103`, `-0130`) — those are the control's own draw losses.

*Cost, published per arm.* v2: 2 796 prompt + 10 031 completion tokens, **0 ceiling hits at 2400**,
median 19.84 s/call, ask-phase wall 108.6 s, sampled GPU energy **3.72 Wh** (43 samples at 2 s, mean
125.2 W, GPU busy 0.91, window 00:48:18→00:50:05). Control: 1 084 prompt + 10 387 completion tokens,
1 ceiling hit, median 19.51 s, wall 103.6 s, **3.65 Wh** (41 samples, mean 129.0 W, busy 0.95). The
feedback costs ~1.7k prompt tokens per re-ask.

*What this corrects, by addition rather than by editing.* The v1 reading ("the feedback converts
nothing") was a **budget artifact**: at 1200 the retry spends ~889 completion tokens on average and one
retry is cut mid-thinking, so the verdict text never gets used; at 2400 every retry finishes naturally
(~2000 tokens) and the verdict does get used. The v1 row and its artifacts stay published byte-for-byte;
this section is the dated correction. The repair number to quote for HumanEval is now **163/164 =
99.4 %**, with the honest bracket that a matched redraw at the same shape scores 161/164 = 98.2 %.

*Honesty about order.* The control was launched **after** the v2 row, so the budget-vs-feedback
hypothesis is post-hoc with respect to v2. It is matched in shape and prompt-guarded, and it could only
shrink a claim, not inflate one — here it shrank the budget claim to zero and left the feedback claim at
2/0. The tooling that made it possible ships in the same commit as the arm (`PARB_REDRAW_CONTROL=1` in
the HumanEval branch of `scripts/pub_bench_repair.py`, plus the verdict-key aliases in
`pub_bench_verdict_sign.py`); a control is published as a sidecar + census, never as a digest row.

*Artifacts* (`benchmarks/public/arms/`, SHA-1/16 sidecars, scanner-clean, 0 exception records):
`pub-repair-pub-repair-humaneval-v2.jsonl` (`d04cbd44cab50133`, 5 retry rows),
`pub-repair-pub-repair-humaneval-v2-census.json` (`506acf41b499386a`),
`pub-repair-humaneval-v2-merged-answers.jsonl` (`de1bfeb8b7f658b0`, re-scored to 163/164 from the
shipped copy with the pinned checker, the only failing cell `-0145`),
`pub-repair-humaneval-v2-verdicts.jsonl` (`820de9e186579895`);
`pub-repair-pub-redraw-humaneval-2400.jsonl` (`f72175d8bfb6fc67`),
`pub-repair-pub-redraw-humaneval-2400-census.json` (`7cb74bc109a9b193`),
`pub-redraw-humaneval-2400-merged-answers.jsonl` (`16ff67099a3c944c`),
`pub-redraw-humaneval-2400-verdicts.jsonl` (`647b5a0992ea3f1f`).

## Codex answer bytes for this set are now published (2026-11-10 02:45 CET)

The `pytest-v2` correction table above rescored all three arms, but only the bare and contour answer
bytes were shipped, so the codex row (163/164 = 99.4 %) was still re-checkable only on this machine.
Shipped now: `arms/humaneval-codex-answers.jsonl` (164 rows, `d660e00fa0cfeb1b`) plus verdict rows
`arms/humaneval-codex-verdicts.jsonl` (164, `714a4005f8defed2`, checker `pytest-v2`, self-test
asserted at re-score time). Re-score of the shipped copies: **163/164 = 99.4 %**, the single loss
`humaneval-0064` — the same cell the corrected paired table lists as basalt-only, so the table
above needs no edit. Scrub masked nothing; bytes byte-identical to the runner output, zero
path/IP/key hits.
