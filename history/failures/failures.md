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
