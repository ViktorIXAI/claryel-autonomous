# Contour version chronology (v1.0 → v2.0-dev)

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

## v2.0 — post-normalization for G/H *(experimental, NOT adopted)*

Explicit contradiction marker for G, H answers compressed under the 600-char
limit (`gate_run.py` `POST_NORMALIZE`, gated at `PARB_GATE_VERSION=v2.0`).
Evidence so far: 18 probe rows on an RTX-5090-class box (`logs/INDEX.md`,
`v20-*` artifacts). Not paired, not cross-boxed, not adopted — published as
work-in-progress evidence of the loop still running.

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
