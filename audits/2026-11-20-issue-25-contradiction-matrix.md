# Issue #25 — bounded contradiction matrix (2026-11-20, Europe/Rome)

**Status: partial, NOT an exhaustive audit or independent benchmark validation.** Evidence reviewed at default-branch HEAD `3ad48b30ca0b6868698a3d49693988d5631b5183`. This file is a new, dated audit artifact; it does not replace the original [2026-11-06 audit](2026-11-06-documentation-alignment-audit.md), issue discussion, historical measurements or immutable logs.

## Verified coverage in this pass

Directly inspected: issue #25 body and 300 comments; eight recent commit identifiers; repository visibility/default branch and access metadata; open PR search; `README.md`, `docs/TESTING-PHILOSOPHY.md`, `docs/documentation-policy.md`, `docs/limitations.md`, `docs/zigbee-mesh-2026-11-18.md`, `CITATION.cff`, the original audit, and `.hermes-single-writer-STOP`. The commit-scoped workflow-run connector returned zero *pull-request-filtered* runs for this HEAD; this does **not** establish CI success or failure. Prior issue comments document a complete 2,538-entry tree enumeration, but this pass did not independently inspect every entry. Coverage of dashboard, all workflows/templates, full issue corpus and every tree file remains **unverified**.

## Contradiction / evidence matrix

| Path / surface | Claim or mismatch | Evidence / scope | Severity | Disposition |
|---|---|---|---|---|
| GitHub About / topics | Earlier audit records “autonomously evolving” About and `reproducible-research` topic, potentially inconsistent with restrained current project framing | [Original audit](2026-11-06-documentation-alignment-audit.md), [testing philosophy](../docs/TESTING-PHILOSOPHY.md), [documentation policy](../docs/documentation-policy.md); current live About/topic values **not independently re-fetched in this pass** | P2 | **Open; verify current metadata first**, then propose neutral wording to owner; no silent change |
| `CITATION.cff` | `version: 0.0.2.5` and `date-released: 2026-11-01` can be mistaken for current release metadata | CFF explicitly carries a 2026-11-06 historical-scope note; [original audit](2026-11-06-documentation-alignment-audit.md) records unresolved latest-release verification | P2 | **Open; preserve original attribution/version** until release ledger and stamped artifacts are reconciled |
| `docs/limitations.md` | Original “No cloud-collaboration ... results exist yet” may be read as current | File has an explicit 2026-11-06 early-v1/v2 historical-scope note, and original wording remains intact | P3 | **Scoped, not silently rewritten**; audit newer results separately before a current-facing summary |
| `docs/zigbee-mesh-2026-11-18.md` | “One router is enough” reads as a guaranteed remedy | Document reports star topology and weak links; later dated observations and [issue #25 discussion](https://github.com/ViktorIXAI/claryel-autonomous/issues/25) distinguish observation from diagnosis; no post-install measurement in this review | P2 | **Open**; phrase as a testable deployment hypothesis in a dated addendum after owner review; retain original measurement |
| Security CI / issue #25 | Prior secret-scan failure must not be conflated with credential leakage or CI success | [Failed run 44731083928](https://github.com/ViktorIXAI/claryel-autonomous/actions/runs/44731083928) and sanitized issue comments report 11 local-path/metadata findings, zero credential-like matches in that run; current HEAD workflow coverage unverified | P1 | **Open**; authorized private classification, remediation if warranted, rerun all relevant gates; do not disclose raw findings or weaken scanner |
| `README.md` | Multiple dated eight-/nine-set benchmark index counts could look contradictory | Dated 2026-11-09 and 2026-11-17 scope notes explain digest snapshots and checker-contract differences | P3 | **Already temporally scoped**; retain historical rows; no new score claims without paired replay |

## Open owner / maintainer decisions

1. Confirm authoritative current release and publication date before editing CFF/version statements.
2. Approve neutral About/topics wording after live metadata verification.
3. Privately classify the 11 reported security findings, with explicit decisions on sensitive metadata and exceptions; do not publish flagged values.
4. Decide whether Zigbee intervention claims should be updated by a dated addendum following controlled before/after observations.

## Completion gate (NOT satisfied)

Produce a path-by-path inventory with exclusions and coverage denominator, finish the contradiction matrix across current-facing docs/dashboard/workflows/templates/issues/PRs/metadata, preserve historical evidence, run and record exact docs/link/security CI results for the final HEAD, independently review corrections, and record unresolved owner questions. Issue #25 must remain open until these conditions are verified.

Provenance: direct connected GitHub reads on 2026-11-20; earlier observations are explicitly attributed to the dated issue log rather than presented as independently replayed measurements.
