# Seed protocol audit — pair-256 (sp1, frozen)

`gseed = int(sha256("<task>|<rep>")[:8], 16) % 999983` — box-independent, per (task,rep),
regenerable by anyone from `plan-rep55/56/57.json` in this directory (loop-only plans: the six
`D-ex6-l*` loop tasks per rep; the plans carry only task/rep/cat/level/mode/stage/series/
rep_group/gseed fields, no answer bytes).

Audit 2026-11-08 08:20 CET: **18/18** plan rows across the three reps match the formula exactly
(load each plan, recompute, compare — 0 mismatches).

Reps 55/56/57 are FRESH on bank v6.6 for every loop (task,rep): the loop pool consumed reps
37-54 on this bank (pair-249 37-39, pair-250 41-43, pair-251 44-46, pair-252 48-50, cadence-255
52-54; rep 51 was the 2.55 D-plain smoke, which runs no loop tasks). Reps 55/56/57 were unused
by any pair, cadence, probe or smoke on any bank before this run.

Retry offsets are part of the protocol and are pinned by `harness/gate_run.py` constants:
2.11 seed+4096, 2.43 banned seed+8117, frozen 2.44 claim seed+12289, 2.47 C-set seed+17491,
and the 2.56 second banned draw seed+16234. Only the candidate arms may spend the 16234 offset,
and only while the best after two candidates still carries a `banned_attempted` stem — verified
per row in the ledgers published here.
