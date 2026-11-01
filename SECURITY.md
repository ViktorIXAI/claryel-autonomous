# Security Policy

## Scope

This repository contains benchmark harness code, synthetic task banks and
research logs. It contains **no** user data, credentials, or private keys —
and every published artifact passed a secret-scan before commit (see
`PUBLICATION-NOTES.md`).

## Reporting a vulnerability

Report privately via GitHub Security Advisories
(https://github.com/ViktorIXAI/strata-autonomous-harness/security/advisories/new).
Do not open a public issue for exploitable problems.

## If a secret is ever published here (incident procedure)

1. Immediately stop further publication (disable the pipeline / Actions).
2. Revoke or rotate the exposed credential at its source.
3. Purge the secret from git history (history rewrite) and force-delete the
   release asset; keep a *redacted* audit note of what happened and when.
4. Re-publish a sanitized tree; append the incident to `history/`.

Research-history completeness never outweighs secret safety: if a log line
contains a credential, the line is redacted and the redaction is documented.

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
