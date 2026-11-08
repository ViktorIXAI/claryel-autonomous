# Seed protocol audit — cadence-255 (sp1, frozen)

`gseed = int(sha256("<task>|<rep>")[:8], 16) % 999983` — box-independent, per (task,rep),
regenerable by anyone from `plan-rep52/53/54.json` in this directory.

Audit 2026-11-08 06:4x CET: **231/231** plan rows across the three reps match the formula
exactly (load each plan, recompute, compare — the plans carry only task/rep/cat/level/mode/
stage/series/rep_group/gseed fields, no answer bytes).

Reps 52/53/54 are FRESH on bank v6.6 and were never used on any bank (cadence 16-18 and
25-27, pair-246 19-21, pair-247 22-24, pair-248 34-36, pair-249 37-39, pair-250 41-43,
pair-251 44-46, pair-252 48-50, bank probes 28-33; smoke reps 40, 47 and 51 sit outside
every published seed set).

Contour legs (0.0.2.55) read `plan-repNN.json` copied over `plan.json` before each leg, so
cell seeds follow sp1 exactly. The three raw arms (bare basalt HTTP temp 0.7, ChatGPT-codex
CLI, Grok CLI) are plain chat calls: they carry no gseed field and are temperature-sampled;
their cells are paired to the contour arm by the (task, rep) **index**, identical to
cadence-246/249. The raw arms' bank copy (`~/parb-b66-raw-reps/bank.json` at run time) is
byte-identical to the contour workspace copy; the scorer re-asserted workspace-vs-published
field identity at scoring time (77/77 tasks).
