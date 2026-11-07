# Seed protocol audit — pair-250 (sp1, frozen)

`gseed = int(sha256("<task>|<rep>")[:8], 16) % 999983` — box-independent, per (task,rep),
regenerable by anyone from `plan-rep41/42/43.json` in this directory.

Audit 2026-11-07 23:41 CET: **231/231** plan rows across the three reps match the formula
exactly (load each plan, recompute, compare — the plans carry only task/rep/cat/level/mode/
stage/series/rep_group/gseed fields, no answer bytes).

Reps 41/42/43 are FRESH on bank v6.6 and were never used on any bank (cadence 16-18 and 25-27,
pair-246 19-21, pair-247 22-24, pair-248 34-36, pair-249 37-39, bank probes 28-33; smoke rep 40
sits outside every pair seed). Both arms of each rep read the same `plan-repNN.json` (the
launcher copies it over `plan.json` before every arm), so control/candidate cells are
seed-matched by construction.
