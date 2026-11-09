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

## 2026-11-09 07:57 CET — Grok arms stopped mid-leg by owner-side quota (gpqa-diamond, humaneval)

Two Grok legs were in flight when the owner reported the Grok subscription quota is exhausted until
2026-11-12: `parb-pub-gpqa-grok` at 139/198 and `parb-pub-humaneval-grok` at 120/164. The last rows of
both files were `finish=ok` with no transport error — the stop was a quota decision, not a failure.

Handling: both units stopped, partial answer files left in place and resumable by task id (pinned ids,
pinned call parameters), and no percent is published for a partial arm. The two arms can be rejoined
later without invalidating anything already stored, because a rescore reads stored answer bytes only.

Effect on published tables: GPQA-Diamond and HumanEval stay three-arm (bare / contour matched shape /
ChatGPT) until the Grok legs resume; the queued Grok legs (mmlu-pro 500, ifeval 541) are deferred.

## 2026-11-09 12:39–12:40 CET — ChatGPT codex IFEval leg stopped by the subscription usage limit

The IFEval codex leg (unit `parb-pub-ifeval-codex`, started 08:24:06) stopped by itself after
**440 ok rows of 541**: three consecutive calls returned rc=1 with stderr
`ERROR: You've hit your usage limit … or try again at 1:32 PM`, which is the fail-closed transport
rule firing, not a model or scoring event. A probe at 13:08 reproduced the same error, so the
subscription is out of quota for this window.

Findings and handling:

* **Three rows were poisoned and were purged.** `codex exec --output-last-message F` only writes the
  output file on a successful call, and the runner read that file unconditionally, so the three rc=1
  rows carried the *previous* task's answer bytes (1493 chars, byte-identical to `ifeval-3315`'s
  answer) under their own ids. They were flagged `rc1` (not `ok`), so no percent was ever computed
  from them, but leaving them in the file would have been a live trap: the public scorer keeps the
  **first** row per id, so a later successful retry would have lost to the poisoned row. The three
  rows were moved to `~/pub-bench/ifeval/pub-codex.rc1-stale.bak` (zero credit, never scored) and the
  answer file now holds exactly the 440 `finish=ok` rows (backup `pub-codex.jsonl.pre-purge.bak`).
* **Tooling fix in the same commit**: `scripts/pub_bench_cloud.ask()` now deletes the last-message
  file before each codex call, so a failed call can never store another task's answer bytes.
* The leg stays **resumable by id** (the runner's done-set skips only `finish=ok` ids, and the 440 ok
  rows are untouched). No IFEval codex percent exists in this repository, and the IFEval cross-arm
  table stays two-arm (bare / contour matched shape) until the leg finishes.
* BFCL's codex arm was not started after this point: launching a 1240-prompt cloud leg into an
  exhausted subscription would burn the endpoint window for nothing.

## 2026-11-09 13:05–13:15 CET — the publication scrub edited a scored answer (caught pre-commit)

The first publication of the BFCL contour arm ran `scripts/publish_pub_arms.py` with no pinned-task
proof, so the scrub masked the upstream fake dataset path carried **inside an answer value**
(`parallel_167`, the argument value `bfcl-ast-v1` matched against). Two harms, both real:

* it edited the exact bytes the published checker verdict was computed from (AGENTS.md rule: answer
  text is never edited), and
* the path character class `[^\s",]*` also swallowed the JSON escape `\"` that closes the value, so
  one published line stopped being parseable JSON at all — an auditor re-scoring the published
  answers file would have hit a decode error on line 768 and lost a row.

Handling: the regex class now stops at a backslash, `--tasks <pinned file>` was wired to the
`pinned_path_tokens()` proof that already existed but was never called (the proof keeps a token that
occurs verbatim in the byte-pinned task file, which no machine path can satisfy), and
`scripts/qa/publish_scrub_test.py` (13 checks, enrolled in `scripts/qa/static_checks.py`) pins all
four obligations plus a non-vacuity control that re-runs the old pattern and shows it really breaks
the JSON. The arm was re-published with the proof (`upstream_pinned_path` ×4 masked-kept, 0 local-path
masks on that file), every artifact line parses, and the PUBLISHED answers file re-scores to exactly
the published **1122/1240** with the shipped checker. The first attempt's files were replaced before
any commit and are kept locally as `*.first-attempt.bak` with zero credit; the already-published bare
arm's files were checked and are unaffected (they re-score to 1116/1240).

## 2026-11-09 12:39 → 13:34 CET — ChatGPT usage limit stops the IFEval codex leg, and its 3 failed rows carried another task's answer (IFEval, codex arm)

* `parb-pub-ifeval-codex` (started 08:24:06) stopped at **440 ok rows of 541**: `codex exec` exited 1
  with its own limit message (`You've hit your usage limit … or try again at 1:32 PM`) on three
  consecutive tasks, which is the line's fail-closed trigger. A one-line probe at 13:08 reproduced the
  same message, so the transport was out of quota, not misconfigured. No IFEval codex percent exists.
* Defect found in the stopped file: the three `rc1` rows are not empty — each carries **1493 bytes
  byte-identical to the answer of a different, already-recorded task** (`ifeval-3315`, sha256/12
  `5e95398fc181`), for ids `ifeval-332`, `ifeval-3323`, `ifeval-3324`. Cause: `codex exec
  --output-last-message FILE` writes the file only on success, so a failed call leaves the previous
  successful answer in place and the runner stored it under the failed task's id. Because the public
  scorer keeps the FIRST row per id, those rows would have outlived any retry and scored as answers
  the model never gave for those tasks.
* Handling: the three rows were purged to `pub-codex.rc1-stale.bak` (zero credit, never scored; the
  pre-purge file is kept as `pub-codex.jsonl.pre-purge.bak`), and `pub_bench_cloud.ask()` now deletes
  the last-message file before every codex call so a failed call cannot inherit one. The leg was
  resumed at 13:34 as `parb-pub-ifeval-codex-resume` after the quota window reopened; the resumed file
  audits clean — 454 rows, 454 unique ids, 0 empty answers, and 0 answers duplicated across ids.
  The partial still publishes no percent: it is 454/541 until the leg ends.
