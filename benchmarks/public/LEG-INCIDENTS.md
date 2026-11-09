# Leg incident log

Append-only. An incident is anything that touched measurement integrity: a restarted leg, an engine
restart mid-leg, a duplicated leg, a discarded partial file. Discarded files keep zero credit and are
never scored. This file exists so a percent row's provenance never depends on someone remembering.

## 2026-11-09 07:29–07:35 CET — duplicated IFEval bare leg (IFEval)

Two local arms of the same set ran against the same endpoint at the same time: the operator launched
unit `parb-pub-ifeval-bare` at 07:28:37, and the 07:20 loop tick launched `parb-pub-ifeval` at
07:29:1x, both writing `~/pub-bench/ifeval/pub-basalt.jsonl`. Cause: the operator instruction issued
to the loop had not been delivered — the manual fire was skipped with `Job is already being fired by
the scheduler`, so the tick ran on the base prompt, which already listed IFEval as the next set.

Effect and handling:
* 11 interleaved rows were written while two legs shared one 24 GB endpoint; both legs were stopped,
  the file moved to `~/pub-bench/ifeval/pub-basalt.dup-collision.bak` (zero credit, never scored),
  and one clean leg restarted as `parb-pub-ifeval` at 07:35 with its GPU sampler
  (`parb-pub-ifeval-samp`, `gpu-power-pub-ifeval.csv`).
* Consequence for published numbers: the IFEval bare arm's wall time and sampled energy are attributed
  from 07:35 onward only; the 11 discarded tasks were re-run by the clean leg, so the answer set is
  complete and every answer row comes from a single-leg window. No percent was computed from the
  contaminated window.

Rule going forward: before launching any local leg, `systemctl --user list-units 'parb-pub-*'` and
`pgrep -f pub_bench_run.py` must both be clear for that endpoint. A manual operator launch must
name the unit it uses, so a tick can recognise it.
