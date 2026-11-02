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
