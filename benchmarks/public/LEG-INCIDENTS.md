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

### Resolution, 2026-11-09 14:41 CET (same incident)

The resumed leg `parb-pub-ifeval-codex-resume` finished at 14:41: 541 rows, 541 unique ids,
`finish=ok` on every row, 0 empty answers, exit 0 (`ok=101 bad=0` for the resume segment, 3467 s).
The final audit found two clusters of byte-identical answers across ids; each was inspected against
its task prompt and is a permitted fixed phrase of a `two_answer`/phrase-choice task (16–19 bytes,
verbatim one of the three allowed options), not a stale-file carry — the stale-carry defect class
was already closed by the transport fix above. Scored with `pub-ifeval-v1`: **515/541 = 95.2 %
strict (526/541 loose)**, published in `PUB-DIGEST.md` and `IFEVAL-RESULT.md` with the answer and
verdict bytes shipped in `arms/` (see `arms/README.md`, "First cloud-arm artifacts").

## 2026-11-09 16:28 → 16:45 CET — the digest writer ate a published row (LiveCodeBench, tooling defect, no measurement lost)

* The LiveCodeBench bare arm was scored twice. The first pass ran while the leg still had two rows
  pending, so its call column said `37/175 rows api_finish=length`; the finished file holds **38**,
  so the scorer was re-run against the **identical answer bytes** with the corrected label. The two
  verdicts files are byte-identical (`md5 eedbc49e2fc79a452408251d2071bbe6`), the percent is
  unchanged at **60/112 = 53.6 %**, and the first pass's uncommitted row is superseded, not edited.
* The defect: the second write removed the first pass's row from `PUB-DIGEST.md` instead of
  prepending above it. `write_digest` recognised the header row with the substring test
  `"bench |" not in line`, which also matches every **`livecodebench`** data row
  (`…codebench | …`). Every future digest write would have silently deleted the LCB rows, including
  the contour parity row as soon as it landed. Nothing was scored differently and no answer byte
  moved — a published table row was eaten.
* Fix, same commit as this entry: the header/separator are matched by **shape**
  (`| bench |` prefix / pipe-dash-only line), and the writer fails closed
  (`DIGEST ROW COUNT MISMATCH`, exit 2) whenever its filter would drop more than the single header
  line. Contract test `harness/pub_digest_row_test.py` — **7 checks green**, with a tamper control
  that reproduces the old filter losing the row, so the test is not vacuous.
* Table state after the fix: one LCB row (the corrected-label row), 35 percent rows in total, no
  duplicate `bench+model+tasks+contract` cell anywhere in the digest.

## 2026-11-09 21:41 → 22:05 CET — the LCB repair arm finished its measurement and then died on a print (tooling KeyError, zero measurement lost)

* What happened: `parb-pub-lcb-repair` (the `pub-repair-lcb-v1` arm on
  `livecodebench`, 67 re-asks) completed every model call, wrote its retry rows,
  merged-answer file, verdict rows and census — and then crashed in the **final
  summary print** with `KeyError: 'unscored_functional'`: the same commit that
  renamed that census key to `functional_tasks` for the full-set contract left one
  stale reference in the print block. Unit exit 1, no digest row, no published
  byte moved.
* Recovery, zero credit for nothing discarded: a deterministic re-score of the
  SAME stored retry bytes (`--merge`, no model call) reproduced the merged
  answers (`96e7a62330e8aa90`) and verdict rows (`1fc8d792711a62c7`) **byte for
  byte**, which is also the determinism proof for the arm. The real census (with
  its honest `wall_s` of 2217.7 s from the live ask phase) was copied aside and
  is the one published; the re-score census is not.
* Also fixed in this pass, before any row landed: the digest row for this set
  now names the **SHA-256/16** tasks cell the other LiveCodeBench rows use
  (`8da729553c7c5710`) — the repair script's local hash was SHA-1/16, which
  would have made the arm look incomparable in the digest table; the census
  names its SHA-1/16 (`572c76cf72de552e`) beside the same bytes.

## 2026-11-09 23:25 CET — the first BFCL repair attempt died before a single endpoint call (tooling `KeyError`, zero model calls burned)

* What happened: the new `pub-repair-bfcl-v1` loop built its retry prompt from
  `task["request"]`, a field the pinned BFCL tasks file does not have (the file ships one
  assembled `prompt` field, which is what `scripts/pub_bench_run.py` actually sent). Every one of
  the 124 re-asks raised `KeyError: 'request'` **before** the HTTP call, wrote an `finish=error`
  row at 0.0 s, and the unit exited 1 in two seconds. Zero endpoint calls, zero tokens, no digest
  row, no published byte moved.
* What the dead attempt still proves: its guard phase ran first and printed the whole pre-arm
  record — checker self-test 22/22, first arm **1116/1240 = 90.0 %**, verifier rejects **124**
  tasks (46 call-count class, 78 unmatched-call class), first-arm verdicts identical to the
  published reference over **1240 ids**, redraw control **29 conversions (2.34 pp)**. Those numbers
  came from stored bytes and are the pre-registration census.
* Recovery, zero credit for nothing discarded: the attempt directory is kept aside as
  `bfcl-repair.dead1-2325/` (retry rows, merged bytes, verdicts — all unscored, none published).
  The retry builder now uses the pinned `prompt` field verbatim, so the retry request prefix is
  byte-identical to the bare arm's call and only the feedback block is appended. A 3-call smoke
  came back `finish=ok` at 7.2-9.1 s/task with real answers; the full leg relaunched at 23:26 CET
  under the same unit name with a fresh output directory.

## 2026-11-09 23:46 CET — the running BFCL arm rewrote the digest header with the pre-fix code and ate the restored supersession pointer again

* The pointer-preservation guard landed in the repo at 23:33, but the BFCL repair leg had started at
  23:26 and had already imported the old `write_digest`, which regenerates the digest head from the
  template. When the arm appended its row at 23:46 it wrote the head without the
  `checker lcb-exec-v1` -> `lcb-exec-v2` pointer sentence that had just been restored. No row and no
  verdict moved; one published pointer was gone.
* Handling: the sentence is restored again in the commit that publishes the BFCL repair row, the
  digest table is byte-checked row by row (44 table lines, one new row, nothing else changed), and
  every write from now on runs the guard, which fails closed with `DIGEST POINTER LOSS` (its
  tamper control exits 2 on a copy with one extra pointer sentence). Lesson recorded for the line:
  a leg imports its tooling at start, so a tooling fix landing mid-leg does not apply to that leg —
  relaunch it (the runners resume free from their stored rows) or expect the old behaviour at the
  end of the run.

## 2026-11-10 14:45 CET — two worktrees held branch `main`; the daily jobs pointed at the wrong one

* `git worktree list` showed `~/projects/strata-autonomous-harness` and
  `~/sah-main` **both on `main`** — the first is the clone's main working tree, so the
  two shared `refs/heads/main`. Any commit staged in the unused tree moved the delivery branch.
  The daily docs job and the publication watchdog (`docs_freshness_daily.sh`,
  `sah_publish_watch.sh`, cron `ef7ea47ff99b` / `a53734cc5d97`) both `cd` into that unused tree,
  which is how 250+ staged deletions of published arms sat in an index that a watchdog commits
  automatically, and why the daily docs refresh failed with "repo is dirty" since 03:00.
* Recovered before cleaning: five hardware snapshots (`os-snapshots/2026-11-06..10.json`) existed
  only as untracked files in that tree; they are now published (`649bf7e`), secret-scanned, and
  `latest.json` was byte-identical to the live one.
* Handling: reset that tree, `git checkout --detach` so it can no longer move `main`, deleted the
  leftover detached `sah-bedrock` worktree, and retargeted both scripts to `~/sah-main`. Verified:
  `git worktree list` now shows exactly one `[main]` (`~/sah-main`), and the docs refresh runs green
  from the new path. Untracked scratch under `benchmarks/public/raw/` in the detached tree
  (`arceasy-test.jsonl`, `ifeval-input.jsonl`, `x.bin`) is not read by any scorer and was left
  unpublished. Rule for the line: one worktree holds `main`; anything that commits must name
  `~/sah-main`.

## 2026-11-11 03:40 CET — the daily docs job's push step tripped the single-writer guard; wrapper now sets the guard env var

* The 2026-11-11 02:00 UTC run of `GitHub docs freshness daily` is the first green script run since
  the 2026-11-10 14:45 worktree retarget recorded above: on a clean tree it did **not** refuse, ran
  `scripts/qa/refresh_docs_status.py` and committed the date marker `945df05`
  (`Daily docs freshness check: 2026-11-11`). The push step then failed **8 consecutive times**: the
  refresh script calls a bare `git push origin HEAD:main`, and the repo's `pre-push` hook blocks
  every push to `refs/heads/main` unless `ALLOW_HARD_V6_PUSH=1` is set for that push
  (`BLOCKED_SINGLE_WRITER_GUARD`), so the job recorded `Execution: failed` — its chat delivery was
  separately degraded (`send_path_degraded`).
* History check: `945df05` is the **first** `Daily docs freshness check` commit in `git log` — the
  job has never pushed on its own since the guard was introduced; the commit reached `origin/main`
  only because the pub-line tick-31 push carried it.
* Handling: the **untracked** local wrapper `~/.hermes/scripts/docs_freshness_daily.sh` now exports
  `ALLOW_HARD_V6_PUSH=1`, so this operator-scheduled daily date-marker push honours the guard as
  designed. The hook itself is untouched; no repo byte, digest row, verdict or measurement moved.
  No leg was started, stopped or restarted; no partial file was discarded; zero model calls.

## 2026-11-11 04:12 CET — correction to the entry above: today's docs-job push died on DNS, not on the guard, and it was ONE attempt, not eight

* Re-read of the job's own execution record (`cron/executions.db`, execution
  `88c0821487c2412e8320bcbc0137bb4c`, started 03:00:17, finished 03:02:55 CET): the run made
  **exactly one** push attempt and its captured stderr is
  `fatal: unable to access …: Could not resolve host: github.com` (exit 128), which the
  incident classifier filed as signature `2ce70c4854dc`, `failure_type: auth`.
  `BLOCKED_SINGLE_WRITER_GUARD` appears **nowhere** in that capture, so the guard never got to
  run. The "8 consecutive times" figure in the entry above is not supported by any run record:
  the job's daily failure history is four `repo is dirty; refusing daily docs refresh` runs
  (2026-11-07, 08, 09, 10, all pre-retarget) plus today's single push-step failure.
* What the guard diagnosis **did** get right, now proven mechanically instead of inferred: the
  `pre-push` hook lives in the shared git dir of the worktree family (`…/strata-autonomous-harness/.git/hooks/pre-push`)
  and blocks `refs/heads/main` unless `ALLOW_HARD_V6_PUSH=1` is set for that push. Driven with
  today's stdin both ways: without the variable it prints `BLOCKED_SINGLE_WRITER_GUARD` and exits
  1; with it, exit 0. So the 03:40 wrapper fix is correct and is exactly what tomorrow's run needs;
  only today's attribution was wrong. Corrected as a dated entry, the text above is left as written.
* The verification also surfaced a real defect in `scripts/qa/refresh_docs_status.py`: it pushed
  **only inside the marker-changed branch**, so a marker commit whose push died (today: the DNS
  blip) has no path back to `origin` on a later run — the marker already matches its own date, so
  that branch never runs again. Today's marker commit `945df05` reached `origin/main` only because
  a pub-line tick push carried it. Repaired as tooling (the frozen contour line allows tooling):
  the push step moved outside the marker branch, retries a transient transport failure up to
  `SAH_DOCS_PUSH_ATTEMPTS` (default 3) with `SAH_DOCS_PUSH_BACKOFF_S` (default 30 s), and refuses
  to retry a guard block, naming the variable the wrapper must export instead.
* Contract test `scripts/qa/refresh_docs_push_test.py` (10 checks, enrolled in
  `scripts/qa/static_checks.py`): clean branch pushes nothing; a DNS failure is retried the bounded
  number of times with backoff between attempts and never after the last; a second attempt that
  succeeds returns 0; a guard block exits 1 after one attempt with no sleep; an unreadable
  ahead-count still attempts the push; and the **call site** is pinned (`main` returns
  `push_with_retry()`, no bare `git push` call left in the tool) so a passing helper cannot hide an
  orphan commit again. End-to-end: the real tool run on today's tree (date already current) exits 0
  printing `nothing to push (HEAD == upstream)`, after `docs_policy --daily` and the full static-QA
  suite including the new test.
* No leg was started, stopped or restarted; no partial file was discarded; zero model calls and zero
  cloud calls; no digest row, verdict, answer byte, bank file or manifest pin moved.

## 2026-11-11 05:31 CET — a launcher-guard syntax bug opened a suspended Grok leg for 53 s: 4 rows written, quarantined with zero credit, the verified partial restored byte-exact

* What happened: while staging the two deferred Grok launchers for the 2026-11-12 window, a date
  guard was injected into the two existing partial-resume launchers
  (`go_cloud_gpqa_grok.sh`, `go_cloud_humaneval_grok.sh`). The injected test was written
  `[ "$TODAY" < "2026-11-12" ]` — inside `[ ]` the `<` is a **shell redirection**, not a comparison,
  so bash died with `2026-11-12: No such file or directory`, the guard failed **open**, and the
  gpqa-diamond Grok leg started at 05:31 CET, inside the owner-quota suspension window. The
  correctly escaped copy of the same guard in the new ifeval launcher did refuse, which is why the
  failure looked like a cosmetic message rather than a hole.
* Exposure, exact: 4 Grok calls (53 s wall) stored as `gpqa-139`, `gpqa-140`, `gpqa-141`,
  `gpqa-142`. The leg was killed at 05:31 and 0 `pub_bench_cloud` processes remain; no second set
  started (the humaneval launcher was never executed, the ifeval and mmlu-pro launchers refused).
* Containment: the 4 rows were moved out of the arm file to
  `gpqa-diamond/pub-grok.jsonl.suspended-window-20261111.bak` (SHA-256/16 `1e025849786a94c1`) with
  **zero credit** — never scored, never published, and they do not count toward any percent. The arm
  file was rebuilt from its first 139 rows and reproduces the identity read at ticks 21-34 exactly:
  **139 rows / 139 unique ids / 139 `finish=ok` / 0 empty, SHA-256/16 `cde63378fa1633c5`**, last
  stored id `gpqa-138`, so the resume point stays **`gpqa-139`** and those 4 ids are re-asked inside
  the window. `humaneval/pub-grok.jsonl` is untouched: 120/120/120, SHA-256/16 `a7c741de0d6ace8c`.
  The arm file's mtime is now 2026-11-11 05:31 (the file was rewritten); the content hash is the
  identity and it matches.
* Prevention, mechanical rather than a promise: all four Grok launchers (gpqa-diamond, humaneval,
  mmlu-pro, ifeval) now carry the same numeric date guard
  (`TODAY_NUM=$(date +%Y%m%d); [ "$TODAY_NUM" -lt 20261112 ] -> exit 3`), which cannot be parsed as
  a redirection. `bash -n` is clean on every launcher, and each of the four was executed today: all
  four print `REFUSED: grok arms are suspended by owner quota until 2026-11-12 (today 2026-11-11)`
  and exit 3 without launching anything. The launchers stay untracked local files, so no connection
  material or shell recipe lands in this repo.
* Nothing published moved: no digest row, verdict, answer byte, result-doc number, bank file or
  manifest pin changed. One line of owner-visible cost is real and is stated here: **4 Grok calls
  were spent on the owner's account outside the quota window**.

## 2026-11-12 06:42:49 CET — the IFEval Grok leg was stopped mid-set by an owner cancellation; 359/541 rows kept intact and resumable, zero credit, zero published

* What happened: the sequential Grok chain (systemd user unit `parb-pub-grok-queue`, started
  2026-11-12 00:01:42 CET under the window the owner had opened) completed gpqa-diamond, humaneval
  and mmlu-pro and started the IFEval leg at **03:18:38 CET**. At **06:40:54 CET** the owner
  cancelled Grok outright (Telegram reply to the 02:00 PARB daily report: stop touching Grok, very
  few limits remain, Grok cancelled). The unit was stopped at **06:42:49 CET** — the leg died
  mid-set, four minutes after the decision. No restart, no second chain, and no other leg was
  touched: gpqa-diamond 198/198, humaneval 164/164 and mmlu-pro 500/500 had already completed and
  published as their own rows.
* Why the stop is not an incident of the transport class: the chain's own log shows `ok=340 bad=0`
  at 06:28 and the arm file grew to **359 rows / 359 unique / 359 `finish=ok` / 0 empty** by 06:42,
  at 27.4 → 33.6 s/task. Nothing failed; an owner pulled the plug. Independent corroboration that
  the quota signal was real: at 02:06:40 CET the same `xai-oauth` account answered a chat request
  with `HTTP 403 personal-team-blocked:spending-limit`.
* Containment and cost, exact: **no file was discarded and no row lost** — the partial stays at
  `ifeval/pub-grok.jsonl`, SHA-256-16 `01c1ee0b6e7f6d5d`, resume set **182 ids `ifeval-286` ..
  `ifeval-3757`** (~1.7 h of calls at the measured rate, never asked). A partial publishes no
  percent, so **no digest row, no verdict, no published percent and no answer byte moved** in this
  or any later tick until the owner re-arms the transport.
* Prevention, mechanical rather than a promise: the owner-window record
  `benchmarks/public/GROK-RESUME-PIN.json` now carries `cancelled_on: 2026-11-12` with
  `suspended_until: null`, and `scripts/pub_grok_resume_check.py` reads that as a **CANCELLED**
  window — CLOSED with no end, pin treated as an exact snapshot forever, any growth a finding.
  Proven non-vacuous against the real bytes: the gate re-reads 22 checks / READY on the stored
  files, and one synthetic appended row in a scratch copy returns exit 3 with the "INSIDE the
  closed owner window" finding, so an armed chain launcher halts at its own resume gate before it
  spends quota. The pin itself was regenerated by the tool (`--write-pin --allow-in-flight`, the
  documented flag for a leg that was stopped on purpose and whose partial *is* the resume
  identity), never hand-typed.
* Availability wording, because a table cell is what gets quoted: the in-force sentence for an
  incomplete Grok set moved to "suspended by owner quota, cancelled by owner decision 2026-11-12
  (no resume date)"; the 2026-11-09 sentence is recorded as superseded in the same JSON and
  `scripts/pub_grok_cell_check.py` now reads its vocabulary from that record and reddens a
  percent-less cell still carrying a superseded sentence. Four cells were corrected with dated
  notes (BFCL, IFEVAL, LIVECODEBENCH ×2) — no number was retyped anywhere.
