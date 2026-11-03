# Contour version chronology (`0.0.1.0 → 0.0.2.7`)

The current public version format is four digits: `A.B.C.D`.

- `A.B` is the operator release line. The operator controls these first two
  digits. The public repository currently uses `0.0`.
- `C` is the contour track. Track `1` contains the old `v1.x` contour family;
  track `2` contains the `v2.x` contour family.
- `D` is the contour revision inside that track. It increases when a contour
  change or measurement/reporting change must be distinguishable in paired
  results.

Because the `D` digit covers both kinds of change, each release also records a
**contour behavior** axis: the newest model-facing contour change that exists
in the code. Measurement and reporting releases move the stamped revision only;
contour behavior stays where it last genuinely changed — `0.0.2.2`, the F
diagnostic grounding. Both axes are written into every result row, ledger row
and version summary. The behavior axis is derived from the contour feature
table instead of being typed by hand, so it cannot drift ahead of the code, and
a revision that has not been built cannot be quoted as if it had changed the
contour.

Compatibility mapping:

| canonical | legacy name | contour behavior | meaning |
|---|---|---|---|
| `0.0.1.0` | `v1.0` | `0.0.1.0` | baseline contour |
| `0.0.1.9` | `v1.9` | `0.0.1.9` | D action-order normalization |
| `0.0.2.0` | `v2.0` | `0.0.2.0` | G/H post-normalization |
| `0.0.2.1` | `v2.1` | `0.0.2.1` | H safety normalization |
| `0.0.2.2` | `v2.2` | `0.0.2.2` | F diagnostic grounding |
| `0.0.2.3` | — | `0.0.2.2` | resource telemetry methodology, contour behavior unchanged |
| `0.0.2.4` | — | `0.0.2.2` | full-Mac resource/economic verdict, contour behavior unchanged |
| `0.0.2.5` | — | `0.0.2.2` | OS environment records, contour behavior unchanged |
| `0.0.2.6` | — | `0.0.2.2` | two-axis version record in every artifact, contour behavior unchanged |
| `0.0.2.7` | — | `0.0.2.7` | K tax-negation flag grounded in the task's own text |
| `0.0.2.8` | — | `0.0.2.7` | engine-stall guard and per-run condition record, contour behavior unchanged |

Legacy names remain valid as inputs and appear in historical records. New
artifacts should record the canonical four-part form.

English narrative of the decision log in
[`gate-versions.en.md`](../history/agent-decisions/gate-versions.en.md) (agent-authored decision entries, translated to English; verbatim Russian originals archived in the `ru-source-records-2026-11-01.tar.zst` release asset,
written *during* the runs — that file is the primary source; where numbers
differ slightly the difference is a mid-run snapshot vs. the final recomputed
aggregate in `results/summary.json`).

Method that applies to every entry: **A/B on the same frozen plan** — same
tasks, same `(task, rep)` keys, same generation seeds — on two physically
separate machines (B2003 = RTX 3060 12 GB desktop; Mac = Apple-Silicon Mac
Studio). One substantive contour change per version (its own violation of
this rule is logged in v1.4). Model weights and task prompts are frozen
across the whole chain.

## v1.0–v1.2 — baseline contour *(accepted, pre-history)*

* v1.0: structured output → code gate → refusal retry ("re-ask naming the
  violation") → max-token ladder (512→1024→2048) on truncation.
* v1.1: chunked extraction for invoices >8 line items; completeness gate for
  logic tasks; structural gate for diagnosis tasks.
* v1.2: constraint filters *computed by code from the task text* (the checker
  re-derives conditions instead of trusting the model); format gate respects
  the required format (CSV/JSON/row-count/column-name); task range A–J.

Final recomputed baseline: B2003 n=590 avg 0.905 / format 92%;
Mac n=645 avg 0.823 / format 94%; ~1170–1210 input tokens per attempt,
1.29–1.41 model calls per attempt.

## v1.3 — format-first + `KEY:` field gates *(accepted, at a cost)*

Required-format enforcement plus field-completeness gates on `KEY: value`
answers → format_ok 100% on both boxes; category H 52% → 100%; means 92–95%.
Cost: +35–37% tokens per task (fixes + ladder).

## v1.4 — cheap repair without the source document *(REJECTED)*

Hypothesis: format repair can be done from the previous answer alone, without
re-sending the source document, and one repair attempt suffices.
Result (A/B subset, Mac): **19/19 → 3/19 correct** financial answers while
saving −59% input tokens / −43% time. Verdict: banned.

Post-mortem recorded in the log: v1.4 silently bundled **two** changes
(no-document repair + retry cap 2→1), and the no-document branch was **dead
code** — it never ran because the repair context did not contain the model's
previous answer. What actually destroyed accuracy was the retry cap.
Two lessons, still in force: never bundle changes; dead code hides the real
cause.

## v1.5 — skeleton guard on cheap repairs *(no-op)*

Guard added: accept a cheap repair only if the answer skeleton (data-row
count + key set) is intact, else `gate:cheap_repair_rejected` and retry with
full context; retry cap restored to 2. A/B was **identical to v1.3** — the
guard fired **zero times** because the cheap branch was still unreachable.
Lesson: an unexercised guard is an unverified guard; test guards, not just
happy paths.

## v1.6 — cheap repair made reachable *(REJECTED for finance)*

Fixed the plumbing: the previous answer is passed explicitly (`prev=r["text"]`)
into all three repair gates. Cheap path now actually runs; guard now actually
rejects things. A/B: −45% input tokens, but **16/19 vs 19/19** correct, and
the skeleton guard let every corrupted answer through (skeleton intact,
*values* wrong). Rejected: for financial tasks the guard yardstick is the
wrong yardstick.

## v1.7 — form repaired by code, model not called *(ACCEPTED as working version)*

Gates first repair presentation themselves: extract JSON/CSV regions, strip
trailing commas, `True/False`, quote bare keys, pull `KEY:` fields out of
prose. Data is never invented: if rows or keys are missing the fixer refuses
and the normal retry path runs. Offline fixer suite: 12 cases, refusals
included (`harness/gate_fixers_test.py`, must stay 12/12).

A/B (identical task set, 19 records/arm, Mac): v1.3 19/19 vs v1.7 **19/19**,
input −31%, generation −24%, wall time −19%, model calls spent on form −45%.
Side discovery: the mixed arm (v1.7 + cheap model repair) scored 16/19 —
proving the cheap *model* repair (v1.4/v1.6) was the poison, not code
repair. `PARB_CHEAP` default flipped to 0 (off; experiments only).

## v1.8 — one targeted nudge per scorer-note kind *(accepted, scope-limited)*

Design (validated later): when the scorer's notes name a failure *kind*
(`no_final_answer`, `too_few_safe_steps`, `contradiction`/`conflict_not_flagged`,
`cause_not_named`, `bad_negation_kept`), the contour may send **one** nudge
(max 2 kinds/task) restating *answer-form requirements of the same task* —
never rewording the task — then keeps the better of the two answers.
Plus: in D-loop tasks, an `answer` before any read/plan step is refused once
and fed back as a tool result (`gate:blocked_early_answer`).
Fired-vs-adopted events are logged separately, because on easy tasks nudges
fire while adoption is 0 — pure extra-call cost. Versions are judged **on the
weak categories**.

Paired (task,rep) v1.7→v1.8: B2003 +0.012 avg (717 pairs; 43↑ 21↓; H +0.175,
F +0.044; small regressions E −0.015, K −0.046), Mac +0.007 (1317 pairs;
18↑ 4↓; H +0.085).

## v1.9 — D-ea was a harness bug, not a model failure *(RELEASED)*

Deep-probe classification (see `experiments/probes/`) labeled D-ea
(action-order tasks) **CHRONIC**: every probe rep < 0.75 across v1.7 and
v1.8 (avg 0.34, format_ok ~1%). Chronic means the contour is blind to the
*class* — the next move is structural, not more nudges.

Diagnosis: `order_gate` accepts the model's *prose* tool sequence, but the
scorer (`parb_loop.check_D_loop`) demands `agent_steps` JSON actions plus an
`answer` slot → guaranteed 0.33 with notes
`format:non_json_step,no_final_answer`. The model had been answering
correctly all along; the wiring was wrong.

Fix (no prompt edit, no reference edit): `d_order_steps()` mechanically
converts the model's own ordered tool list into the parser-required slots and
adds a summary `answer` step. Event `contour:v19_d_order_to_steps`.
Test-first: `harness/gate_v19_d_test.py`.

Paired v1.8→v1.9: B2003 **+0.047** (229↑ 79↓, D category 0.42→1.00),
Mac **+0.051** (183↑ **0**↓, D 0.45→1.00). D-ea subset: 0.34→1.00 on both
boxes. v1.9 is the released contour of this repository.

## v2.0 — post-normalization for G/H *(accepted, Mac complete; B2003 partial)*

Explicit contradiction marker for G, H answers compressed under the 600-char
limit (`gate_run.py` `POST_NORMALIZE`, gated at `PARB_GATE_VERSION=v2.0`).
Mac paired v1.9→v2.0 subset n=2416: avg +0.013, perfect 72.1%→79.8%, better
185 pairs, worse 0. G improved 0.833→1.000; no observed regression on the Mac
pair. The B2003 partial pair (n=674) added avg +0.0086 with 57 improved /
24 regressed. The B2003 v2.0 run was later stopped at 674 rows by a human-directed
speed-up so v2.1 could be evaluated earlier.

## v2.1 — H safety normalization *(candidate final configuration; running)*

One contour change only: H answers are mechanically safety-normalized. The
contour removes false action claims from calculation/derivation tasks,
redacts invented version/serial-shaped tokens in missing-data refusals, and
adds an explicit uncertainty marker when a refusal omitted the required
marker. Full-mode H is not rewritten. Event tags: `contour:v21_*`.

Evidence so far: unit tests 10/10, full gate self-tests unchanged; P2005 H
smoke 9/9 strict and 9/9 format. Current live-partial aggregate (15:0x CET):
B2003 n=118, avg 0.9986, format 100%; Mac n=162, avg 0.9856, format 100%.
Paired v2.0→v2.1 B2003 n=117 (+0.0112, 3 improved / 0 regressed), Mac n=162
(delta 0, 0 regressions). Mac full v2.1 and B2003 v2.1 are running
on paired subsets. B2003 v2.0 was stopped early on explicit operator
instruction to accelerate v2.1; B2003 v2.1 started 14:46 CET on the v1.9
paired subset (2421 rows). The original plan stopped at v2.1; full P3001
evidence later confirmed chronic F weakness, so the line was reopened with a
v2.2 change scoped to that class.

## v2.2 — F diagnostic grounding *(targeted acceptance; full Mac run pending)*

The P3001 full v2.1 sweep found F at 0.70, specifically `too_few_safe_steps`:
the model diagnosed the failure correctly but phrased safe diagnostics in
Russian prose rather than the canonical tool/resource tokens demanded by the
F scorer. `f_diagnostic_normalize()` classifies the failure from the visible
synthetic log, appends evidence-backed component/cause/safe-step tokens,
removes unsupported thermal claims, and suppresses decoy blame in the
cause/component lines. Event tags: `contour:v22_*`.

Paired F subset results:
- P2005 (n=30, same task/rep/seed): 0.7167 → 1.0000; 29 improved, 1 unchanged,
  0 regressed.
- Mac Studio (n=30, same task/rep/seed): 0.7500 → 1.0000; 30 improved,
  0 regressed.
- P3001 budget worker (n=30, same task/rep/seed): 0.7167 → 1.0000; 27 improved,
  3 unchanged, 0 regressed; perfect answers increased from 3 to 30.
- Recorded B2003 v2.1 F answers replayed offline through v2.2: n=323, every F
  task average becomes 1.0000.

Contract tests: 8/8. The Mac full v2.2 suite starts automatically after the
Mac full v2.1 suite finishes; no full-suite v2.2 verdict is claimed yet.

## 0.0.2.3 — resource telemetry and documentation policy *(current tooling release)*

This revision does not change the model-facing contour. It makes the
measurement layer part of the release:

- `telemetry/resource_quality.py` joins answer quality with end-to-end
  latency, peak RAM, peak VRAM, GPU power and estimated GPU energy;
- `telemetry/collector2.py` adds multi-GPU selection and macOS RAM/swap
  parsing;
- `harness/gate_versioning.py` adds the four-part version scheme and keeps
  legacy `v1.x`/`v2.x` inputs compatible;
- `scripts/qa/docs_policy.py` checks that public pages remain current,
  structured and free of inflated self-labeling.

Initial P3001 12 GB evidence: n=30, answer mean 0.9944, perfect 29/30,
latency median 5.88 s / p95 7.96 s, peak VRAM 11,385 MB of 12,288 MB,
peak GPU power 113.4 W. The run passed quality but exposed only 903 MB VRAM
headroom, which is exactly why resource telemetry is now a permanent part of
full paired gates.

## 0.0.2.4 — full-Mac resource and economic verdict *(current release line)*

This revision does not change the model-facing contour. It closes the Mac
round requested for the resource-analytics decision.

Full Mac paired result, `0.0.2.1` vs `0.0.2.2`:

- 2513 unique paired rows;
- content mean: 0.9394 → 0.9833, +0.0438;
- F category: 0.6741 → 1.0000, +0.3259;
- perfect attempts: 2006 → 2344;
- improved pairs: 338;
- regressed pairs: 0;
- raw ledger total: 28,088.7 s → 13,294.5 s;
- p99 non-zero attempt latency: 177.35 s → 25.31 s.

Telemetry join on the Mac run:

- 1 Hz RAM sampling, 11,282 samples;
- attempt-level resource coverage: 1734 / 2513 attempts;
- peak RAM used inside attempt windows: 177,900 MB;
- minimum RAM available inside attempt windows: 133,631 MB;
- dedicated VRAM and system power: `not_available` on rootless macOS collector.

The Mac profile shows large unified-memory headroom. The 12 GB P3001 profile
shows the opposite: 11,385 MB of 12,288 MB VRAM used, 903 MB headroom, despite
a high answer-quality score. That contrast is the basis for the permanence
decision.

Decision: keep resource telemetry permanently in full paired gates and
hardware-class runs. Quick smoke runs may skip it only when the machine is
idle and the objective is a simple endpoint check.

See [`results/parb-v22-mac-full-resource.md`](../results/parb-v22-mac-full-resource.md)
for the full report and cost/benefit estimate.

## 0.0.2.5 — OS environment records and deterministic docs pass *(current release line)*

This revision does not change model-facing contour behavior. It closes a
reproducibility gap: Ubuntu version alone did not say whether the machine ran a
Desktop or Server image, and a future migration would otherwise look like a
kernel change only.

Added:

- `harness/os_record.py`: records OS distribution, Ubuntu codename, Desktop or
  Server flavor, evidence used for that classification, kernel and architecture.
- `scripts/fleet/os_fleet_audit.py`: collects the same record from localhost and
  each configured remote machine, writing a dated JSON snapshot.
- `hardware/inventory/OS-FLEET.md`: current human-readable fleet OS table.
- `hardware/os-snapshots/`: date-stamped machine OS snapshots.
- Gate results, gate ledgers and telemetry headers now carry the same `os` record.
- Daily local docs refresh uses deterministic offline link validation; strict
  online link checking remains in CI and pre-push with transport retries.

Current fleet facts are recorded in [`OS-FLEET.md`](../hardware/inventory/OS-FLEET.md):
P2005 and B2003 are Ubuntu 24.04.5 Desktop; P1005 is Ubuntu 24.04.5 Server;
Mac Studio, MacBook and Mac mini are macOS desktop systems. P3001 and P3032
were offline during the audit and require a live flavor recheck after power-on.

## 0.0.2.6 — two-axis version record *(current release line, contour unchanged)*

This revision does not change model-facing contour behavior. It closes a naming
gap that made reports ambiguous: the fourth digit named both contour changes and
measurement/reporting changes, so `0.0.2.3`–`0.0.2.5` read as if they were three
new contour generations, and a run file named for one revision could hold rows
stamped with another.

Added:

- `harness/gate_versioning.py` records the contour feature table
  (`CONTOUR_FEATURES`) and derives **contour behavior** from it, instead of
  trusting the stamped revision alone;
- every gate result row, ledger row and version summary now carries
  `contour_behavior` plus a `contour_changed_at_this_release` flag;
- the runner prints both axes at start, so a log alone answers which contour the
  model actually faced;
- contract tests: tooling stamps `0.0.2.3`–`0.0.2.6` must all report contour
  behavior `0.0.2.2`; the feature table must stay strictly increasing and never
  run ahead of the stamp; behavior must top out at the newest implemented
  contour change.

Consequence for reports: the contour is named by its behavior axis
(`0.0.2.2`, the last real contour change) and the tooling by the release line
(`0.0.2.6`). A number for a contour change that has not been built is never
quoted as if it existed.

## 0.0.2.7 — K tax-negation grounding *(candidate; paired A/B pending)*

**Diagnosis from the accepted contour.** Re-running the full Mac pair
(`0.0.2.1` → `0.0.2.2`, 2513 paired rows) leaves every category at 1.0000 except
K, which did not move at all: 0.7888 before and 0.7888 after, perfect share
15.5%. Per-task breakdown shows the whole loss sits in one item, `K-ha-04-0`:
158 reps, every one exactly 0.75, note `bad_negation_kept`, score spread 0.00.
Zero spread with a constant shortfall is the deterministic signature seen before
in `v1.9` (D action order) and `v2.2` (F diagnostics): the contour is blind to
the class, so seed variance and more nudges cannot help. The decision log already
recorded that the `v1.8` nudge fired 158 times on this item and was adopted 0
times — pure extra model calls.

**Bank rule the contour now implements.** An audit of all 13 K items found one
consistent convention: an explicit tax-exclusion sentence in the task text
("This quote excludes all taxes", "не включает НДС", "IVA esclusa") means
`EXCLUDES_TAXES: yes`; when the text says nothing about taxes the reference is
always `no`, because an unsupported exclusion claim is not a grounded answer. A
payment term such as "net 45 days" is never a tax statement — that wording is
what pushed the model toward an unsupported `yes`.

**Change.** `k_negation_normalize()` rewrites only the value token of the flag
line, in the language the model used, from the task's own visible text; a missing
flag line is added only when the prompt asked for it and the scorer's line budget
still holds. The prompt, the scorer and the hidden reference are untouched. Event
tags: `contour:v27_k_negation_flag_yes`, `contour:v27_k_negation_flag_no`,
`contour:v27_k_negation_line_added_*`. Because the correction runs before the
`v1.8` nudge step, the note disappears and the wasted nudge retry disappears with
it.

**Revision band.** Revisions 2.3–2.6 are permanently measurement stamps, so this
contour change could not take one of those numbers: registering a feature inside
that band would silently switch it on for archived `0.0.2.3`–`0.0.2.6` rows. A
contract test now forbids any contour feature in the reserved band, and contour
gates start at `contour_at_least(2, 7)`.

**Evidence so far.** Contract tests 10/10 offline (`harness/gate_v27_k_test.py`):
silent-quote correction (the published failure), correct answers untouched in both
directions, Russian value token corrected in Russian, Italian silent quote
untouched, missing-line add inside the line budget, non-K tasks untouched, and
the feature off at `0.0.2.2` / on at `0.0.2.7`. Static QA suite green. **No
quality number is claimed yet**: adoption requires a paired run over the
`(task, rep)` keys that contour `0.0.2.2` already covered on the same box.
Expected effect if it holds: K 0.7888 → 1.0000 and overall 0.9833 → ~0.999 on the
Mac pair, plus 158 fewer model calls per 158 rows.

## 0.0.2.8 — engine-stall guard *(measurement validity; contour unchanged)*

**What was nearly believed.** The full P2005 pair `0.0.2.1 -> 0.0.2.2` printed
-0.1319 over the 298 joined keys — a headline that would have said the accepted
contour is a regression on the main brain.

**What the artifacts actually said.** In that joined subset, 86 of 298 keys on the
2.1 side and 134 of 298 on the 2.2 side produced **no answer bytes and reported no
engine error** (29 % and 45 %): the serve accepted the connection, held it for the
full 20 s client timeout, and returned nothing. Restricted to the **130 keys where
both sides answered**, the same pair measured **-0.0089** (0 improved, 2 regressed) —
flat, which is what the accepted contour predicts. The engine log explains the
degradation: parked conversation snapshots of 2.6 GiB
(`conversation cache: parked 107235 tokens ... bytes=2643951576 evictions=28`) with
`K/V trimmed to 8192 cells` and 717 RAM-admission refusals, on a 60 GiB host sitting
at ~58 GiB used. That is over-parking, the same failure mode measured once before:
parking a giant snapshot starves live KV, and the next requests come back empty.

**Counting rule learned the hard way.** A stall is an empty answer with no engine
error. Rows with `model_calls = 0, ptok = 0, ctok = 0, seconds = 0.0` are the contour
answering **by code** — valid rows that belong in the means. An early count of "297
zero-token rows" conflated the two and was corrected the same day.

**Machine check.** With the node idle, the same request shape returned in 8.0 s for
14 161 prompt tokens, 31.0 s for 59 837 and 87.3 s for 161 496 — about 1.9k tok/s of
prefill, no empty completions. Context length was never the problem; the parked
snapshots were. `--conversation-cache-min-free-mib` was raised from 1536 to 3072 on
that box (parking is now refused while the host is under memory pressure) and the
node was restarted.

**Harness rule added.** An answer-less response with no HTTP error and no usage
block is a **stall**, not a wrong answer. The identical sample (same seed, so the
measured distribution is untouched) is retried once; if it stalls again the row is
flagged `engine_stalled` and excluded from quality means by both aggregators, and a
run whose last 20 rows exceed a 25% stall rate stops with
`stop_reason: engine_stall_rate`. Each run now also writes
`run-record-<run_id>.json` (box, model, API host, both version axes, git sha, plan
size, `/health`, stall policy) so the conditions of a measurement are auditable
afterwards — the missing piece that made this diagnosis take hours.

**Read on the contaminated data, for the record.** Restricting the partial pair to
the 82 keys where neither side stalled: 0.9961 (2.1) against 0.9820 (2.2), 0
improvements, 2 regressions, both in E. That is not an acceptance and not a
regression: it is a small sample whose `F` category — the one contour 2.2 targets —
was 100% stalled on both sides, which is why the pair is being re-measured under the
guard instead of being reported.

## Cross-cutting rules the chain produced

1. One substantive change per version; bundle violations get logged against
   the author (v1.4).
2. Adoption only on paired `(task, rep)` deltas; means across different plan
   mixes are meaningless (v1.8 tables).
3. Every adopted version is replicated on a second physical machine.
4. A guard that never fires is a bug in the test, not a passing test (v1.5).
5. Token savings are audited per *correct answer*, not per answer (v1.6).
6. CHRONIC failures are suspected harness bugs before being blamed on the
   model (v1.9).
7. A version number names a change that exists in the code and has been paired-
   tested. A planned change gets no number until it is built, and a tooling
   revision never borrows the contour axis (0.0.2.6).
