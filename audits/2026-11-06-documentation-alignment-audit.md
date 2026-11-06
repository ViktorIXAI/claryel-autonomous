# Documentation alignment audit — 2026-11-06

Status: **partial, evidence-preserving review; NOT a complete repository-wide audit**. No frozen results, version ledgers, benchmarks, code, release artifacts or historical attribution were modified.

## Canonical intent
See [Testing Philosophy](../docs/TESTING-PHILOSOPHY.md). Claryel Autonomous is open engineering experimentation, distinct from the Claryel business; current work measures local AI harnesses; Mix AI collaboration, error evaluation, cost of verified outcomes, changing conditions and repeated retrospective analysis are research directions. Economic scenarios and forecasting are distant hypotheses, not delivered features. No academic-status, superiority, autonomy or product-completeness claims are warranted merely by these aims.

## Confirmed findings and action
| Finding | Evidence | Action and reason |
|---|---|---|
| README duplicated `Where the evidence lives` heading | README snapshot | Removed duplication; presentational defect |
| README used 'Current version' for early 0.0.2.7/0.0.2.8 history despite later v6 series | README and later v6 evidence | Relabeled release table as historical, avoiding a false latest-version claim; actual latest version NOT independently determined |
| README status from 2026-11-03 and checked 2026-11-05 | README | Marked as historical rather than asserting fresh verification; the automatic freshness policy may need further adjustment |
| Documentation policy avoided grand academic claims, but philosophy and metadata used research terminology | docs/documentation-policy.md, docs/TESTING-PHILOSOPHY.md, CONTRIBUTING.md | Clarified practical engineering framing; 'research' in ordinary experimental sense does not mean academic science |
| Open questions focused on local AI despite Mix AI direction | docs/open-questions.md | Added new questions as prospective rather than measured results |
| CITATION.cff pointed to older repository URL and title contained outdated version range | CITATION.cff | Corrected canonical URL and neutralized title; left release version and historical author attribution untouched pending verification |
| GitHub repository About says 'autonomously evolving' and topic includes 'reproducible-research' | GitHub repository metadata | **Unresolved:** not editable through available file-content action; owner or metadata-capable maintainer should adjust to neutral wording |
| docs/limitations.md describes no cloud-collaboration results and older F/H scores | docs/limitations.md | **Unresolved:** historical scope may be valid for the original series but needs dated scope notes and newer evidence references |
| CITATION.cff version field 0.0.2.5 conflicts with later releases | CITATION.cff vs README | **Unresolved:** do not guess current release; confirm latest released/stamped version before changing |
| README daily freshness check conflicts with intentional historical snapshot | docs/documentation-policy.md, README | **Unresolved:** adjust CI to validate a current evidence index rather than treating historical rows as live; test first |
| Publication notes claim 'ONLY differences' from archived bytes | PUBLICATION-NOTES.md | **Unresolved:** historical claim needs scoped date; do not overwrite without provenance |
| Agent self-improvement/autonomy claims may be over-read as unbounded | README, docs/autonomy.md, GitHub About | **Unresolved:** preserve historic ledger and add current-scope caveat after validating operational boundaries |

## Audit rules for next pass
1. Inventory the complete repository tree and every current-facing Markdown, YAML, CFF, dashboard, issue, PR, workflow and GitHub About/topic metadata. This pass examined selected high-level documents only; no exhaustive inventory was possible.
2. Categorize findings: contradictory facts, stale time/version claims, unsupported superiority/academic/product claims, historic statements needing date scope, security-sensitive statements, harmless third-party citations, or merely different wording.
3. Preserve historical experiment files verbatim; corrections should be append-only and cite old/new evidence. Do not bulk-replace words such as 'research' or 'scientific' inside external titles, quotations or immutable records.
4. Validate all proposed changes with docs QA, links, test suite and owner review. No benchmark/scorer/security/production changes without explicit approval.
5. Check current open issues/PRs and agent pause/single-writer rules before any agent executes further edits.
6. Reconcile canonical project scope with version and experiment evidence, rather than forcing old measurements to match new aspirations.

## Open questions for owner
- Does 'remove any mention of scientific status' mean only self-description, or also third-party paper titles, source references and historic quotations? Recommended: self-description only.
- Should public GitHub About/topics be changed to emphasize open engineering experiments and Mix AI, while keeping benchmark and local-AI topics? Recommended: yes.
- Which dated revision is the current verified release? Do not infer from old README.
- Should old limitations and publication notes remain unchanged as archival documents with a prominent newer addendum? Recommended: yes.
