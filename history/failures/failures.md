# Failures, invalid runs and rollbacks — the complete record

A failure here is a *measured* result. Nothing in this file was deleted,
smoothed or re-narrated.

## Rejected contour versions (paired evidence, verbatim log entries)

**v1.4 — banned.** Cheap form-repair without the source document, *plus*
retry cap 2→1, bundled. A/B (Mac, 19 reps): correct answers **19/19 → 3/19**
while saving −59% input tokens / −43% time. Post-hoc cause (found only after
v1.5): the no-document branch was dead code; the retry cap did the damage
(fixes 29→16 → unfinished formats → `missing_7`, wrong numbers).
Rules born here: one change per version; test that a code path *executes*
before crediting it.

**v1.5 — no-op.** Skeleton guard (row-count + key-set check before accepting
a cheap repair). A/B identical to v1.3; the guard fired **zero times** — the
guarded branch was unreachable (`msgs0` had no previous answer). An
unexercised guard is an unverified guard.

**v1.6 — rejected.** Plumbing fixed so the cheap path actually runs; guard
now live. −45% input tokens; correct 16/19 vs 19/19; guard passed every
corrupted financial answer (skeleton intact, *values* wrong). Lesson: pick
the guard yardstick to the failure class — structure cannot catch corruption.

## Invalidated runs (kept as artifacts, never silently dropped)

- `gate-ledger-smoke.jsonl.401-invalid` (B2003 rig): whole smoke series
  invalidated by a 401 auth-handling bug in the *harness* — every call
  failed auth. Preserved under `-401-invalid` name; fixed; re-run.
- `gate-ledger.jsonl.partial-harnessbug` (B2003 rig): partial series
  aborted due to a harness bug mid-run; the file name itself declares its
  status.
- `telemetry samp.out` on B2003: 0 bytes — the phase-2 sampler wrote nothing
  (logging gap); phase-1 CSV exists from the control host instead. Recorded
  as `not_recorded` coverage, not hidden.

## Harness bugs found and fixed in-flight (highlights)

- **v1.9 class**: scorer/contour wiring mismatch made correct model answers
  score 0.33 for three versions (see `logs/samples/D-ea-*` before/after pair).
- **plan-exhaustion vs crash**: runners end with an explicit stop-reason line;
  "no" (plan exhausted) at different wall times on two boxes is *normal* —
  misreading it as a crash was an early reporting trap, fixed in reporting code.
- **dead-branch reporting** (v1.4/v1.5 above).

## Rollbacks

v1.4/v1.6 → reverted to v1.7 path (`PARB_CHEAP=0` default), decision entries
record the revert with numbers. No published version was ever silently
replaced: the release line moves only forward with a logged verdict.

## The publication pass has its own failures (2026-11-01)

The *new* publication wrapper `make_plan.py` (not part of the original runs)
was smoke-tested on a third machine (P2005) and **failed on first try**: it
staged `plan.json` but not `bank.json` into `PARB_ROOT`, so the runner loaded
a 681-position plan and filtered it to 0 tasks (tasks missing from bank map).
Caught in 90 seconds of smoke, fixed the same hour (wrapper now stages both
files, mirroring what `parb_prep.py` did in the original runs). Contour code
unaffected. Recorded because this project's rule applies to itself.
## Publication pass failure: pinned release asset was incomplete (2026-11-01)

The first `contour-v1.9` artifacts asset (`artifacts-release-2026-11-01.tar.zst`)
was missing three files that the pinned `analytics/aggregate.py` SPECS read:
`results-v13.jsonl`, `results-v13m.jsonl`, `gate-ledger-v17.jsonl`. An external
researcher following the reproduce recipe would have gotten incomplete series
(v1.3 stats and the v1.7 B2003 ledger) with no error, because missing files
silently yield `None` stats.

- **Found by:** the new CI `reproduce` job (hash verification vs `logs/INDEX.md`
  + required-file set) — first run, 2026-11-01. This is why the job exists.
- **Fix:** files collected unchanged from their source machines; complete set
  republished as `artifacts-release-2026-11-01-v2.tar.zst` (original asset kept
  as-is — history not rewritten).
- **Integrity check:** recomputation from the complete snapshot reproduces the
  published `results/summary.json` with **diffs=0**. No published number
  changed; only the archive's completeness changed.
- **Lesson applied:** CI now fails loudly when any file a published aggregate
  reads is absent from the public archive (silence is a bug).

## Holdout bank v1 shipped category-G tasks without their long documents (2026-11-01)

The first published `bank-holdout.json` (v1) generated G tasks via
`parb_bank.build()` but skipped the prep-stage document assembly that
`parb_prep.py` performs for the dev bank. Result: the model received only
the 5 questions (≈485 chars) and no document, so the published holdout-mini
G score of 0.167 measured a broken task, not model or contour behaviour.
Caught during the second external audit follow-up by inspecting the three
G rows (`ptok` far below `target_tokens`, answers "нет данных"). Fixed in
generator v2 (`assemble_G`, same layout as dev prep); ids and refs
unchanged; corrected pilot re-run published in `results/holdout-mini.md`.
The invalid v1 pilot rows remain in `logs/samples/holdout-p2005-mini/`
unmodified, annotated as invalid for G.

## Baseline experiment v1 rows did not store answers (2026-11-01)

The first baselines run stored only `answer_sha256`, which made independent
re-scoring of the arms impossible. Re-ran all 264 arm calls with answers
stored (same seeds; scores identical). Lesson: research artifacts must
carry the bytes needed for independent verification, not just hashes.

## CI failure history (2026-11-01, requested by the second audit)

14 failed Actions runs on 2026-11-01; all causes known, all classes now green:

* 4× `secret-scan` (14:39–14:48 UTC): gitleaks install/binary-path issues in
  the runner, then the scanner walking the repo scan root, then a step-env
  mistake. Fixed by `11cb6f9`, `2601d25`, `82a09a8`, `3943c31`; green since.
* 2× `contour self-tests` at `d114fd8`: broken relative link
  `versions/VERSIONS.md → gate-versions.en.md` caught by the link checker —
  the checker doing its job after the English-first move. Fixed next commit.
* 2× `contour self-tests` at `4030f44`/`c6ff7a1`/`adc51f2`/`c45a4bd`/`ea1f36e`:
  INDEX row-format regex in the hash verifier and stale path assumptions in
  `sanity_data.py` after directory reshuffles; fixed in the same sittings.
* 8× `pages build and deployment` (09:48–09:58 UTC): Pages source/path config
  during the repo rename chain (`autonomous` → `claryel-autonomous`); the
  deploy job lagged the renames. Green since the rename-proof pass.

No failure was ever hidden by re-running until green: each has a fix commit
or a documented cause above.

## Publication watchdog commits sweep up unrelated work-in-progress (2026-11-01)

`ce60f32` ("publish: pipeline packages") was created by the publication
watchdog's `git add -A` and silently committed a batch of in-progress
research files (holdout v2, EXT-003 registration, baselines data) under a
misleading message. Content and hashes were unaffected, and the intended
commit (`0d28de5`) later restates the same work with a proper message —
but commit hygiene matters for an audit trail. Fix queued for the watchdog:
stage only pipeline-generated paths, never `-A`.
