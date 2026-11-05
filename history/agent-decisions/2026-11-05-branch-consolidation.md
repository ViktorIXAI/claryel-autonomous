# 2026-11-05 — branch consolidation: one visible line (main)

Operator complaint, verbatim in effect: results kept appearing on side branches he had
never asked for, so the project history was invisible to him and every status report
started with an apology about where things lived. He had told the agent not to create
such branches and then forgot he had said it — which is exactly the failure mode: the
delivery surface must be the place he looks, not a branch an agent invents.

Decision:
- `main` is the single published line. Every contour stamp, benchmark arm, scoreboard,
  pair report, ladder, decision record and coordination log lands there the day it is
  made. Side branches are private scratch at most and are deleted once merged; they are
  never a delivery surface.
- Merged into `main` here: `hard-v6-loopd-hermes` (contour 0.0.2.15-0.0.2.25 series,
  hard bank v6 arms `full-216`..`full-223`, ladder/pair tooling, publication fixes) and
  `hard-v6-draft` (issue #14 frozen-answer scoreboards, 77-row audit, v5 pins restored).
  Conflicts were only `.gitignore` (kept the deeper negation set),
  `benchmarks/hard/MANIFEST.sha256` (regenerated with `scripts/write_hard_manifest.py`,
  `verify_manifest --v5` PASS) and `SCOREBOARDS-14.md` (kept the superset version).
- Two publication holes closed on the way: `.gitignore` pattern `results*.jsonl` was
  negated only one directory level, so per-arm answer rows for contour 0.0.2.18-0.0.2.23
  were silently never shipped; and three published artifacts still carried the host label
  instead of `<HOST>`. Both fixed, all answer bytes backfilled.

Honest status of the newest stamps: 0.0.2.24 (I duration re-sort) and 0.0.2.25 (G
conflict-by-code) exist in code and have offline replay evidence on saved answer bytes,
but no paired full arm and no contract test yet. They stay marked unmeasured in the
ladder; their numbers do not enter any verdict until a paired arm runs.

External review state (issue #15 "measurement validity", PR #17) remains OPEN and is the
operator's merge decision; nothing here merges an external PR.
