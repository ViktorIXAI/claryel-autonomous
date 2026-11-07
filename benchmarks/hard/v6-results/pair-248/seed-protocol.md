# Seed protocol audit — pair-248 (sp1, frozen)

`gseed = int(sha256("<task>|<rep>")[:8], 16) % 999983` — box-independent, per (task,rep),
regenerable by anyone from `plan-rep34/35/36.json` in this directory.

Audit 2026-11-07 21:12 CET (`scripts/measurement_stack.py` era tooling): **231/231** plan rows
across the three reps match the formula exactly (re-run: load each plan, recompute, compare — the
plans carry only task/rep/cat/mode/stage/gseed fields, no answer bytes). This closes the audit gap
that the pair ledgers carry `contour_version` but no per-row seed: the seed lives in the plan, so
the plan ships with the pair from pair-248 on.

Reps 34/35/36 are FRESH on bank v6.2 (never used by cadence 16-18, pair-246 19-21, pair-247
22-24, bank probes 28-33); smoke rep 40 was outside every pair seed.
