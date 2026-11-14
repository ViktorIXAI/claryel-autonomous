# Issue #25 — tree coverage and CI checkpoint (2026-11-14, 11:08 UTC)

**Scope:** bounded, evidence-preserving audit checkpoint; **not** an exhaustive semantic review or acceptance sign-off. Tree snapshot from GitHub REST `git/trees/main?recursive=1`, commit `98f6c3ce733c277a61729f401b647e7fc599456c`. Response `truncated=false`. Counts are file-path inventory only; content was **not** read for every file.

## Exact inventory at snapshot

- **2,461 Git tree entries**: **2,288 blobs/files**, **173 directories**.
- **334 Markdown**, **6 YAML/YML**, **433 JSON**, **257 Python**, **1 CFF**, **2 HTML/JS** files (extension-based counts, not a claim of exhaustive classification).
- Prefix-based file counts (overlapping the extension counts): `docs/` **73**; `audits/` **3**; `benchmarks/` **1,660**; `hardware/` **31**; `.github/workflows/` **5**; issue/PR template paths **2**.
- Workflows enumerated: `devsecops.yml`, `docs-freshness.yml`, `scoring-contracts.yml`, `secret-scan.yml`, `selftest.yml` (all under `.github/workflows/`).
- Root public-facing files include `README.md`, `AGENTS.md`, `CHANGELOG.md`, `CITATION.cff`, `CONTRIBUTING.md`, `PUBLICATION-NOTES.md`, `SECURITY.md`. The full tree is reproducible via the REST URL above, not reproduced here as a giant static file list.

## Evidence-backed contradiction / disposition matrix

| Path / surface | Claim or potential mismatch | Evidence and scope | Severity | Disposition |
|---|---|---|---|---|
| GitHub About description | “autonomously evolving” may be read as proven, unbounded autonomous capability | Direct repository metadata read 2026-11-14; `docs/TESTING-PHILOSOPHY.md` explicitly separates hypotheses from measured capability | P1 public interpretation | **Open**; recommend owner-approved, current-scope neutral metadata text; no repository metadata mutation in this checkpoint |
| GitHub topic `reproducible-research` | Potential academic framing inconsistent with documentation policy | Direct topics API 2026-11-14; `docs/documentation-policy.md` explicitly says avoid “reproducible research” as a current project self-label | P2 | **Open**; owner/maintainer metadata decision; retain source citations and historical terminology |
| `CITATION.cff` | `version: 0.0.2.5` and `date-released: 2026-11-01` may look current | CFF has explicit `TEMPORAL-SCOPE-2026-11-06` historical warning; no independently verified release/tag mapping | P2 | **Preserve**; do not replace version or authorship without release evidence |
| `versions/VERSIONS.md` | Header chronology ends at `0.0.2.7` although table includes `0.0.2.8` | Direct file read at snapshot | P2 | **Open**; date-scoped appendendum after validating later release chain; no silent header rewrite |
| `README.md` | Earlier six-set and later eight-set public benchmark counts | Both are expressly dated in existing 2026-11-09 audit clarifications | P3 historical interpretation | **Scoped already**; do not remove older observation or treat as live leaderboard |
| `.github/workflows/docs-freshness.yml` | Previously described scheduled CI as not independently verifiable | GitHub Actions REST run **43586408454**, scheduled **2026-11-14 10:40:43 UTC**, HEAD `98f6c3c...`, conclusion **success**; job `daily-docs-check` and `Check public docs are current and simple` step both **success** | P1 verification gap now resolved for this exact run | **Verified pass for this specific run and SHA only**. This does not establish link-check coverage, other workflows' success, or full #25 acceptance |
| `.hermes-single-writer-STOP` and issue #13 | Owner STOP and single-writer constraints | Direct STOP file and issue #13 read; STOP explicitly forbids `hard-v6-p0-fix` push/recreation; #13 stops FRESH100 | P0 security/authority | **Respect**; no benchmark execution, code changes, deletion, or conflicting agent work |

## CI verification boundary

The scheduled `docs-freshness` workflow is `schedule` + `workflow_dispatch`, configured with `20 3 * * *` UTC, and executes `python scripts/qa/docs_policy.py --daily`. The observed run at 10:40 UTC is later than its nominal cron; do not infer why it was delayed. Its run record and job steps establish a pass for the exact SHA above, **not** that the repository's link checker or all policy assertions were independently exercised. Workflow run: https://github.com/ViktorIXAI/claryel-autonomous/actions/runs/43586408454

## Remaining acceptance work / owner decisions

1. Content-review coverage of 2,288 files, current issues/PRs, dashboard, templates, all workflows, release/tag provenance and publication/source policy is **not complete**. This inventory closes only the *path enumeration* gap.
2. Independent link QA and other workflow status, and a complete path-by-path contradiction matrix remain outstanding.
3. Owner/maintainer to decide neutral GitHub About/topic wording; verify which revision is a released version before altering citation/version claims.
4. Do not conflate operator-reported hardware/preflight results with independently replayed tests; no such tests were run for this audit.

No existing evidence or history was deleted, rewritten, re-scored or reinterpreted as a new benchmark. This addendum is a new file, scoped to a specific commit and observation time. See issue #25 and `audits/2026-11-06-documentation-alignment-audit.md`.
