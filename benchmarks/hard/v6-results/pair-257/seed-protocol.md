# Seed protocol audit — pair-257 (sp1, frozen)

`gseed = int(sha256("<task>|<rep>")[:8], 16) % 999983` — box-independent, per (task,rep),
regenerable by anyone from `plan-rep61/62/63.json` in this directory (loop-only plans: the six
`D-ex6-l*` loop tasks per rep; plans carry only task/rep/cat/level/mode/stage/series/rep_group/
gseed fields, no answer bytes).

Audit 2026-11-08 10:00 CET: **18/18** plan rows across the three reps match the formula exactly
(load each plan, recompute, compare — 0 mismatches). `gate_run.py` uses `seed = pos["gseed"]` as
the draw seed (L3613); the results-row `seed` column is the static bank task seed, identical
convention as every published pair since v6.1.

Reps 61/62/63 are FRESH on bank v6.6 for the loop pool: prior loop reps on this bank were 37-39,
41-43, 44-46, 48-50, 52-55 (pairs/cadence), 55-57 (pair-256), 58-60 (map-256). Reps 61/62/63 were
used by no pair, cadence, probe or smoke before this run.

Retry offsets are part of the protocol and pinned by `harness/gate_run.py` constants: 2.11
seed+4096, 2.43 banned seed+8117, frozen 2.44 and re-armed-2.57 claim seed+12289, 2.47 C-set
seed+17491, 2.56 second banned draw seed+16234. Only the 2.57 candidate arms may spend the 12289
offset on a first-draw claim note, and no claim row ever spends 16234 (no-third-draw-on-claim) —
verified per row in the ledgers published here (1 v57 fire in x57r63, no v56 on that row).
