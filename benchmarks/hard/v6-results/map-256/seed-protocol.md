# Seed protocol audit — map-256 (sp1, frozen)

`gseed = int(sha256("<task>|<rep>")[:8], 16) % 999983` — box-independent, per (task,rep),
regenerable by anyone from `plan-rep58/59/60.json` in this directory (full-bank plans: all 77
tasks per rep, 71 plain + 6 loop; the plans carry only task/rep/cat/level/mode/stage/series/
rep_group/gseed fields, no answer bytes).

Audit 2026-11-08 09:05 CET: **231/231** plan rows across the three reps match the formula
exactly (load each plan, recompute, compare — 0 mismatches).

Reps 58/59/60 are FRESH on bank v6.6 for every (task,rep): the bank consumed reps 28-30
(v6.6 first sweep), 37-46, 48-50 (pair-252), 52-54 (cadence-255) and 55-57 (pair-256, loop
rows only); the plain-row rep set 51 was a 2.55 smoke. Reps 58/59/60 were unused by any pair,
cadence, probe or smoke on any bank before this run.

Retry offsets are part of the protocol and are pinned by `harness/gate_run.py` constants:
2.11 seed+4096, 2.43 banned seed+8117, frozen 2.44 claim seed+12289, 2.47 C-set seed+17491,
2.56 second banned draw seed+16234. Only the live mechanisms spend their offsets; the ledger
events published here show exactly which fired (v47 C-set 1x, v243/v56 loop draws on loop
rows; no frozen-family events anywhere).
