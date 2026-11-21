# Issue #25 latest field-commit review — 2026-11-21

## Scope and provenance

This append-only note records a bounded review of four repository commits that appeared after the previous issue #25 checkpoint:

- [1f90f43](https://github.com/ViktorIXAI/claryel-autonomous/commit/1f90f43c53d9ff7229d0af7f0f4546419357ff21)
- [b885079](https://github.com/ViktorIXAI/claryel-autonomous/commit/b88507990025c1caaf0324f3e2defba6edafdb8a)
- [99c81f5](https://github.com/ViktorIXAI/claryel-autonomous/commit/99c81f5a67b27f32a1a7b86dc44647a7ae05ab8d)
- [9a08fba](https://github.com/ViktorIXAI/claryel-autonomous/commit/9a08fba8db84c51384378ad3ac50d6aaa24cd3f8)

Review date: 2026-11-21 UTC. This note preserves the repository-reported observations and does not independently reproduce the field tests.

## Evidence ledger

| Commit | Repository-reported observation | Audit boundary |
|---|---|---|
| 1f90f43 | WAN/DNS outage coincided with the relay becoming unavailable; the relay's `local`/ `duplex` labels did not establish a usable local-control path; watchdog gained egress and telemetry-staleness probes. | Reported field evidence; no independent network replay or security certification. |
| b885079 | Watchdog tested one-shot `RELAY SILENT` / egress alerts and added a pending-commit push when egress returns, guarded by `ALLOW_HARD_V6_PUSH=1`. | Current-facing operational behavior; requires separate review of authorization, branch hygiene, and failure handling before treating as approved policy. |
| 99c81f5 | A stale neighbour-table fallback delayed a `LOST` alert; the fallback was narrowed to `REACHABLE`/`DELAY`, with scratch-copy seeded tests reported. | Reported test evidence; no independent CI or live replay verified here. |
| 9a08fba | CCR5009 management ports were observed open on a link-local address; IPv4 was absent; a read-only snapshot attempt was blocked by a configured password, and no guessing was attempted. | Security-relevant observation; credentials remain unknown and no configuration snapshot was obtained. |

## Findings for issue #25

1. These commits add new current-facing operational claims and security-relevant observations that were not covered by the prior source-verification addendum.
2. The repository text distinguishes observation from proof in several places, but no independent CI result for the current HEAD was available through the connected status/workflow lookups.
3. The management-port observation and password-blocked snapshot are not evidence of a secure configuration; they are evidence of an incomplete inspection boundary.
4. The push-on-egress-return behavior is not silently treated as approved. It should remain an owner-reviewed operational change, especially because the audit acceptance criteria prohibit unsupported security claims and require explicit rationale.

No historical document, frozen benchmark, secret, credential, production setting, or security policy was changed by this audit note.
