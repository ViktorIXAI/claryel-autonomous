# Security Policy

## Scope

This repository contains benchmark harness code, synthetic task banks and
research logs. Published artifacts and the current branch are screened with
Gitleaks plus infrastructure-pattern scanners. Machine-specific SSH targets,
host users, key paths and private redaction rules live only in an untracked
local `publish.env`; public code reads environment variables.

Automation runs a Gitleaks scan on the current checkout and on all branches
and tags. Publication pipelines re-scan staging and package archives before
upload. Raw scanner reports are kept outside the public repository.

## Reporting a vulnerability

Report privately via GitHub Security Advisories
(https://github.com/[owner]/[repository]/security/advisories/new).
Use the current repository URL shown by `git remote get-url origin` when
configuring a local automation or advisory link.

## If a secret is ever published here (incident procedure)

1. Immediately stop further publication (disable the pipeline / Actions).
2. Revoke or rotate the exposed credential at its source.
3. Record the exact path, commit, release and asset in a private report.
   Rewrite history or delete a release only after maintainer approval.
4. Re-publish a sanitized tree; append a *redacted* incident summary to
   `history/`. Never include the secret itself in the public incident note.

Research-history completeness never outweighs secret safety: if a log line
contains a credential, the line is redacted and the redaction is documented.

## Stricter publication policy adopted 2026-11-01

- A non-critical risk review confirmed that old visual-release browser metadata
  did not contain usable stored passwords or cookies. Existing history and
  releases were therefore left unchanged, but browser profile state is now
  prohibited from future packages.
- Package builders must exclude browser-profile directories and files, including
  Chrome profile state, cache, cookies, login data, preferences and session
  stores.
- Every publication path must run the scanner before upload. A current-code
  credential-like finding is blocking. Historical infrastructure findings are
  reported and moved to local configuration, but history/release deletion
  remains an explicit maintainer decision.
- Public reports may contain paths, rule identifiers, commit/release references
  and counts only. Secret values must never be printed in logs, issues, commits,
  releases or dashboards.
- If a future scan finds a real credential, it must be revoked/rotated even if
  it has not yet been observed in use.

## Execution-safety notes for users running the suite

- Category-E tasks execute model-generated Python on your machine
  (`parb_check.run_py`). Treat the host as disposable or run inside a
  container if you require isolation.
- Category-D agent tools are fully mocked — nothing real is executed.
- The harness talks only to the OpenAI-compatible endpoint you configure.
  No telemetry, no accounts, no outbound calls otherwise.

## Publication permissions

Automation (future pipelines) should get fine-grained tokens limited to the
`strata-autonomous-harness` repo with contents+release write, no
delete-history rights; protected branches disallow force-push. The historical
record is never deleted because it shows bad results.
