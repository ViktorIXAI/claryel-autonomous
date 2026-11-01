# Dynamic research regime

**Status: adopted as the standing protocol from 2026-11-01.** This document
defines how the experiment runs as a *living lab* rather than a frozen
snapshot, and what comparability guarantees the regime preserves.

## Why dynamic

The field moves faster than a static lab can follow, and a benchmark that
never changes becomes a target the harness overfits. Both problems are
addressed the same way: the substrate, the tools and the tests all keep moving,
and the published record keeps every version of them.

What rotates, and how it is recorded:

| axis | regime | recorded as |
|---|---|---|
| machines | computers join and leave at will; hardware set is never fixed | machine passports in `hardware/inventory/` with join/leave dates; every result row carries its `box` |
| model weights | the frozen model of a *window* may later be replaced by a newer open model | a new window with a new model passport; old windows never re-run |
| inference engine | the Strata engine updates continuously (release watcher tracks upstream); engine version is part of every window | engine version + engine release note in the window record |
| harness contour | continues to evolve under the versioned A/B discipline (`docs/EVOLUTION.md`) | contour version in every result row |
| task bank | tasks saturated at or near 100% are retired from the active scoring set; new harder tasks and holdout families replace them | each bank generation is a new frozen bank with its own seed and id set; old banks stay published |
| scoring criteria | validators change only through the same one-change-per-version A/B rule; score changes caused by validator changes are attributed, not hidden | ledger fields + `results/independent-scorer.md` dissent records |

## Comparability rule: static windows

Cross-window numbers are never compared directly. The unit of comparison is a
**static window**: one (model, engine, machine class, bank, contour-comparison)
tuple, closed by a paired A/B run. Between windows we publish *what changed*
(model version, engine version, bank generation, hardware swap) and treat
cross-window deltas as descriptive only. This is the same discipline already
used inside windows (paired (task, rep) deltas), lifted one level up.

Term used in reports:

- **dynamics** — change measured *within* short-lived static windows of an
  otherwise frozen stack;
- **result** — the end-to-end outcome on practical tasks at the end of a
  window. Result is the primary axis; window-level score deltas are the
  secondary axis.

## Test-bank saturation rule

Several categories currently score ≈1.0. Near-perfect scores on
self-generated tasks are treated as **instrument saturation**, not as
capability proof (this was also the conclusion of the external review in
`results/external-review-2026-11-01.md`). Consequences:

1. saturated task families stop being the optimization target; the agent must
   generate harder families (`harness/parb_bank_holdout.py` pattern, new seed,
   disjoint ids, verified disjointness in CI);
2. held-out banks are generated *after* a contour version is frozen and are
   never used during that version's development;
3. planned next step, published as not-yet-done: budget-matched simple
   baselines — single retry, plain JSON validator, generic agent framework —
   so that any harness gain must beat the cheap ten-line alternative, not
   just the raw model.

## Practical objective

The point of the whole regime is not benchmark aesthetics. It is:

- working practical automation on **extremely affordable hardware**
  (consumer-class GPUs, home servers, one desktop-class Mac),
- data staying **local**, with optional cooperation with **inexpensive cloud
  models** under the default-deny privacy gateway
  (`benchmarks/privacy-boundary/`),
- and honest measurement of which of these goals each harness generation
  actually advances, including regressions.

## External-model provenance

External AI models are used for drafting specifications and for review. That
use is now logged, not hidden — see
[`history/external-model-inputs/ledger.md`](../history/external-model-inputs/ledger.md).
