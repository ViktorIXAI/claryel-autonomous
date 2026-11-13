# Publication edits vs. the original run snapshots

Every published code file is a snapshot taken from the live rig. The edits below
are the ONLY differences from the exact bytes that produced the archived results
(the raw snapshots stay on the rig; `logs/INDEX.md` pins the result artifacts
they produced).

| file | edit | why |
|---|---|---|
| `harness/gate_run.py` | snapshot = `gate_run.v19.bak-0745` (released v1.9 contour) | v1.9 is the version the README numbers refer to; the live file already contained unvalidated v2.0 edits and was NOT released |
| `harness/gate_run.py` | `PARB_KEY_FILE` default emptied; key file lookup simplified; plain `Bearer` header | portability: vanilla OpenAI-compatible endpoints need no key file; the old header-spelling trick was a workaround for the rig's own log-scrubber, meaningless here |
| `harness/parb_run.py` | `API`/`MODEL` moved to `PARB_API`/`PARB_MODEL` env | portability |
| `harness/parb_check.py` | one regex made a raw string (`"\s…"` → `r"\s…"`) | Python 3.12 SyntaxWarning; byte-level change, **semantics identical** ("\s" is not a recognized escape, Python keeps it literally); verified by re-running all scorer behavior checks — the rig's original bytes remain archived on the rigs |
| `harness/make_plan.py` | new | publication convenience; reproduces the frozen plan from `benchmarks/text-gates/bank.json` (in the original runs the plan was prepared once by `parb_prep.py` and frozen — the freeze discipline itself is unchanged) |
| `experiments/ab/analyze-0130.py` | rig-local absolute paths → relative | privacy/portability |
| launcher shell scripts | LAN hosts/users dropped, placeholders instead | privacy |

No file had logic, prompts, scorers or thresholds altered. `PARB_GATE_VERSION`
selects the contour generation at runtime (`v1.2` … `v1.9` gates are all inside
`gate_run.py`), so the published runner can reproduce every published comparison.

## Publication-pass additions (2026-11-01, afternoon)

New automation infrastructure published alongside the original snapshot — these
are new files, not edits of rig snapshots: publication pipeline
(`scripts/publish/`), auto-discovery aggregator (`analytics/aggregate_auto.py`),
independent scorer (`analytics/second_opinion.py`), dedup-sensitivity tool,
telemetry collector v2 + join, dashboard, holdout bank generator, privacy
gateway prototype, CI reproduce/link/sanity scripts.

P1005 passport + sanitized launch config added 2026-11-01 (evening): live-collected
hardware table, first-run IQ3_S benchmark numbers, and the tuned sm_60 launch
JSON with `$HOME` placeholders, no api_key, no LAN address, no account paths.

Allowed portability edits made this pass (code semantics unchanged): 
`make_plan.py`/`second_opinion.py` honour `PARB_BANK`; `check_links.py` uses
GET for GitHub HTML (HEAD 403 from datacenter IPs); `verify_release_hashes.py`
accepts both INDEX row formats; repo-move URL updates after the owner's rename
to `ViktorIXAI/autonomous` (2026-11-01 09:55 UTC — the rename was made by the
repository owner, not by the agent; old URLs 301 to new).

## 2026-11-02 — P3001 v2.1 contour sweep

Added results/p3001-parb-v21.md + post-snapshot artifact rows in logs/INDEX.md
(sha256-16 pinned, raw files held on the workstation until the next bundle).
G-ve-13/14 rows published explicitly as capacity rejects (HTTP 400,
113k-char documents vs 32k context), not capability failures — adjusted means
exclude them. No new secrets surface: scores/aggregates only; raw JSONL not
committed.

## 2026-11-02 — P3032 onboarding: AVX1 engine build + first 32k ladder

Added hardware/inventory/P3032.md, hardware/changes/P3032.md (onboarding,
failed CUDA-12.0 build round with exact ptxas diagnosis, successful
avx-floor/sm_86 build — builds are published per fleet rule),
results/p3032-iq3s-context-ladder.md + committed dataset jsonl, sanitized
launch profile. Two discarded ladder passes (prompt-cache contamination;
44k-token HTTP 400 capacity rejection) are published as evidence with
sha256-16 pins; raw logs on the workstation (logs/INDEX.md pending bundle).
No secrets surface: rates, temperatures, power, counts only.

## 2026-11-02 (late) — P3032 power-envelope A/B, cap kept at 150 W

Added results/p3032-iq3s-power-envelope.md (+jsonl): one ladder pass at the
card's 187 W factory max. Decision: prefill cap-independent, warm decode
+10-24 %, but the box's PSU/power cable is the weak point (177.4 W peak
observed) — the maintainer ordered the uncapped state explicitly short-term;
cap restored same day and recorded as standing. No new secrets: watts,
degrees, rates only.

## 2026-11-02 (late2) — P3032 power policy change

Maintainer decision: the 150 W cap is permanently removed (GPU
removal/replacement planned). Inventory and change record updated; the
A/B envelope doc kept as historical record.

## 2026-11-02 (late) — P3032 contour sweep, harness v2.4 (contour 2.2)

Added results/p3032-parb-v24.md: full 178-task rep0 plan on P3032 uncapped,
mean 0.9867 capacity-valid, F-category 0.70->1.00 vs P3001 v2.1, p50 12.6 s,
1 Hz resource telemetry complete (VRAM 91% = tight by 12 GB rule; single
185.9 W peak recorded under uncapped state — hardware decision on record).
G-ve-13/14 published as capacity rejects. Raw sha-pinned above.

## 2026-11-02 (late) — P3032 slow-disk swap test

Added results/p3032-slow-disk-comparison.md: full model stack moved to the
system SATA SSD with the NVMe unmounted — 3-4.3x slower prefill, 4x slower
decode; GPU starves. Three orchestration failures published with diagnosis
(self-kill via fuser, second-instance race, expert-profile path miss). Raw
bundle sha-pinned. No secrets: rates/temps only.

## 2026-11-03 — P1005 RTX 3060 era + platform-state restructure

Published the closed RTX 3060 era (gpu-unlock 2.0 verified active, 187 W
ceiling, paired v2.2 quick runs 0.9759/0.9829, raw 3060 records) and then the
GPU return to a Tesla P100 — see hardware/changes/P1005.md (CHG-001/002).
The P1005 passport was restructured to the **platform convention**: the
published anchor is chassis + board; CPU, RAM, storage and GPU are numbered
hardware states (S1/S2/S3), and every benchmark line names its state. Going
forward any P1005 component swap follows the same shape: CHG entry before the
box goes down, state re-numbering in the passport, same-suite before/after
table. No new secrets: rates, watts, degrees, PCI ids only; launch config
stays `$HOME`-sanitized.

## 2026-11-03 — 0.0.2.6 two-axis version record

The operator asked where contour releases 2.3/2.4/2.5 had gone, after reports
mixed "contour 2.2" (what was under test) with "release 2.6" (a number that had
never been built). Root cause was in the published scheme itself: the fourth
digit named both contour changes and measurement/reporting changes. Public
documents now state both axes for every release, `versions/VERSIONS.md` gained a
`contour behavior` column and a 0.0.2.6 section, the reproduction guide warns not
to infer a contour change from a stamped revision, and `CHANGELOG.md` records the
change plus the reason. No measurement was re-interpreted: no published number
moved, only the labels that identify which axis each number belongs to. Old rows
stamped `0.0.2.3`–`0.0.2.5` remain valid and now derive behavior `0.0.2.2`
automatically from the contour feature table.
- 2026-11-05 — **publication hole found**: `.gitignore` pattern `results*.jsonl` was negated only for
  `benchmarks/hard/v6-results/*.jsonl` (one level), so the per-arm answer rows under
  `full-2NN/` were never committed for contour arms 0.0.2.18-0.0.2.23 even though they were copied
  into the tree — an outside auditor could not re-score those arms from answer bytes (the ledgers
  carried scores, not answers). Fixed by deep negations (`v6-results/**/*.jsonl|csv|log|md`) and all
  sanitized answer rows backfilled: full-218 .. full-223 plus the k-218 / j-probe-218 probe sets.
- 2026-11-06 — **run-record endpoint leak found and fixed in publication**: `scripts/publish_pair_arms.py`
  applied the placeholder rules only to JSONL; `run-record-*.json` and logs were copied byte-raw, so the
  already-published run records of pair-230 and pair-231 carried the real LAN endpoint in `api_host`.
  Every artifact kind now goes through the rules (JSON re-validated after substitution) and `api_host`
  values publish as `[REDACTED]`; the 12 affected files under `benchmarks/hard/v6-results/` were
  backfilled in the same commit. Post-fix grep over `v6-results/`: zero LAN addresses, host labels and
  local paths. History of pre-existing gitleaks hits (`marks/*`, `scripts/publish/pipeline.py`) stays
  unmodified and re-reported to the owner (evidence-preservation policy).
- 2026-11-06 — published pair232 (`benchmarks/hard/v6-results/pair-232/`, six arms: ledgers, answer rows,
  logs, run records) plus `PAIR-232-V61.md` (verdict: +1.3 cells under the noise floor, not adopted;
  measured energy windows from `scripts/gpu_energy.py`). Decision record under `history/agent-decisions/`.

## 2026-11-08 — pair-257 sampler artifact: script copy replaced by prose (CI secret-scan finding)

The first publication of the pair-257 GPU sampler included a masked copy of the sampler
SCRIPT (`gpu257-sanitized.txt`); path/IP masking left a key-file path following the `-i` flag as connection
material and the CI secret-scan (`secret_scan.py --dir . --strict` on the checkout) failed
on rule `ssh-connection-material`. The file was removed and replaced by
`gpu-sampler-command.txt` (prose description, the pair-250 standing rule: samplers and
launchers are published as prose; real scripts stay untracked). No other pair-257 artifact
changed; the repo-wide strict scan is green again. Git history still contains the masked
file under the no-history-rewrite rule (the value there is a local key PATH, not a secret;
history scanning is non-blocking by policy and is the owner's separate decision).

## 2026-11-08 CORRECTION (same day, ~20 min later) — the pair-257 secret-scan cause claim above is WRONG; retract it

Verified by local reproduction: the published `gpu257-sanitized.txt` NEVER triggered the
repo scanner (`secret_scan.py --strict` on the exact committed file: exit 0, zero findings;
the `ssh_material` and gitleaks `ssh-connection-material` rules need the `-i` flag
adjacent to a key path, a `.key` suffix, or a literal IP, none of which the masked file contained).
The CI `secret-scan` failure on commit a36774c was the "Install pinned Gitleaks" step dying
on GitHub HTTP 504s (the same infra flake window also failed the link-integrity job, whose
log shows every external link returning `http 504`). The scan never ran. The
script->prose replacement was therefore a PRECAUTION consistent with the pair-250 rule, not
a response to a real finding, and the prose file stands on its own. Both commits
(85967f7 message included) repeated the wrong cause; per the honesty rules this retraction
is appended rather than the history rewritten. Rule reminder captured: before committing a
CI-failure cause, read WHICH step failed (gh run view --json jobs steps), never infer from
adjacent evidence.

## 2026-11-08 — the pair-257 incident writeup itself tripped `--strict`

`secret_scan.py --strict` fails on ANY finding, including metadata-class ones, and the
two incident paragraphs quoted the rule pattern verbatim (a key path after the `-i`
flag; the backticked command example). Rewritten to describe the adjacency in words without
reproducing it. Meaning unchanged; the retraction stands as written.

## 2026-11-09 — BFCL v4 bare arm: a sanitizer that edits scored bytes

Publishing `bfcl-basalt-*` (1116/1240 = 90.0 %) hit a case the sanitizer was wrong about: one answer
echoes a fake dataset path that the **pinned upstream task bytes themselves carry** (it is the
argument value the gold requires for `parallel_167`, present in both the prompt and the gold). The
blanket path mask turned it into `/user<LOCAL_PATH>`, which (a) is not a real machine path and (b) is
not valid call syntax — the scrubbed file no longer parses, so the published arm would have stopped
reproducing its own percent.

Change, as a proof rather than an escape hatch: `publish_pub_bare_arm.py --tasks <pinned task file>`
keeps a path-shaped token only when that exact token (leading slash included — the first revision
dropped it and the self-test caught the mismatch) also occurs in the pinned file, and reports it as
`upstream_pinned_path`. Contract test: `--selftest`, 4 assertions, including that a machine path is
still masked while a keep-list is active. Byte facts published: answers SHA-256/16
`4ac238d09babcb45` / SHA-1/16 `419e9dbcdff4872d` (byte-identical to runner output), verdicts
`389aed67b18d0d58` (byte-identical to scorer output); the published bytes re-scored to the same
1116/1240 before the commit. The scanner suppresses the token only under a sha16-bound exception for
these exact bytes, one rule (`absolute_local_path`), no credential-class rule involved, and the
exception record does not quote the token.

Process note on this commit: two `patch` calls in the same session landed on unintended boundaries —
one deleted a `sha16` key from an unrelated scanner exception record and one truncated the head of
the `bfcl` row in `PUB-PLAN.md`. Both were caught by re-running the scanner (a record lost its byte
pin) and by reading the table line back, and repaired in the same commit; the rule they reinforce is
to diff every non-mexact patch before publishing, not to trust the tool's success flag.

## 2026-11-11 — P3001 state S3-a ladder; the 59 tok/s figure gets a state label

What was published: `results/p3001-rtx3050-iq3s-ladder-2026-11-11.md` with two raw
runner JSONL files and an engine-accounting extract, `benchmarks/ladder/` runner
sources plus method notes, the updated `hardware/inventory/P3001.md` passport rows,
`hardware/changes/P3001.md` (CHG-001 closed, CHG-002 states table + checklist,
CHG-003 outage), four new fleet rows in `hardware/changes/configuration-changes.md`,
the S3-a launch twin, and `logs/INDEX.md` byte pins.

Rules that shaped it:

* **No historical measurement was rewritten.** The RTX 3060 (S1) numbers in
  `results/p3001-initial-benchmarks.md` and `results/p3001-parb-v21.md` are byte-for-byte
  as published; the new file cites them as S1 and states that GPU, RAM, engine dir,
  serve profile, context cap and traffic mix all changed between states, so they are
  **not** a controlled GPU comparison. A controlled A/B is listed as an open item.
* **A circulated number was traced instead of reused.** "≈59 tok/s on P3001" is real
  text, but the serve log puts it on S1/S2 rows (`1230 tok → 59.2`, `1225 → 59.3`,
  `1213 → 59.7`; `725 → 58.9`, `512 → 59.1`), where decode rides on 96–100 % draft
  acceptance. The same class of real-text request on the current S3-a (RTX 3050)
  profile decoded at **25.7 tok/s**. Both are published with their state labels.
* **Runner defects are disclosed, not hidden.** The real-text client crashed on a
  reply-field assumption, so that row is quoted from the engine's own accounting line
  and labelled as such; the runner published here carries the fix.
* **An infrastructure failure is published, not repaired silently.** CHG-003: a
  malformed serve profile landed at 14:11:29 UTC (`--kv` missing before `int8`,
  `--gpu` with no value), and two engine starts died at 14:11:38 and 14:15:02 UTC with
  `unknown argument: int8` — nothing listening on :8080 during that window. The box was
  fixed by others (profile rewritten again at 14:25), and the endpoint was verified
  healthy at 14:35 UTC under a **new, unmeasured** profile; that is recorded as a
  fairness warning rather than smoothed over. This audit changed nothing on the box.
* **Sanitization:** serve `api_key`/`tokenizer` values omitted, the box's LAN address
  never written to the repo, account paths replaced with `$HOME`, prompt payloads not
  published (the generators live in the runner sources, so rows stay reproducible).
* One `patch` call again landed on a shifted boundary (a duplicated phrase in the
  results file); caught by reading the diff, repaired in the same commit — the standing
  rule from 2026-11-09 holds: diff every non-mexact patch.



## 2026-11-13 — P1006 first sighting: passport + onboarding incident (key delivery)

Added hardware/inventory/P1006.md (passport from live reads: MSI B550-A PRO /
Ryzen 5 5600X / 64 GB DDR4-3200 non-ECC / Intel Arc A750 8 GB `8086:56a1` on the
open-source stack / one 990 PRO 1 TB holding root and a 604 GiB Arc-SYCL data
tree at 92 % full) and hardware/changes/P1006.md CHG-001.

The published part is the failure mode, not the machine: the standard console
block fetches the fleet public key over HTTP, the fetch timed out at 132 s while
the rest of the block ran, and the self-check line reported `key=0` — a box with
a listener, a sudoers drop-in and a firewall rule, and no key. Measured the same
day: the key-server's own host firewall (default-deny inbound) drops the key port,
which produces a ~130 s timeout from another fleet host rather than a refusal.
Recovery was an inline key write, verified by `ssh-keygen -lf` digest on the box
and by a passwordless-sudo probe from the control host. Standing rule recorded
fleet-side: read the `key=` field of every onboarding self-check, and paste the
key inline unless the firewall rule was opened deliberately.

No inference role claimed: the fleet engine has CPU and NVIDIA paths only, so this
box is published as an Arc/SYCL experiment bench. Sanitization: no address, user,
key path or hostname in either file (AGENTS.md rule 1); capacity and restart state
published as open maintainer decisions, nothing patched or rebooted on the box.
