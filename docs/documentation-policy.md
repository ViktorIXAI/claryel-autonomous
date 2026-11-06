# Documentation Policy

This repository has one public landing document: `README.md`. It is a working
status page, not a marketing page and not a scientific paper. The policy below
exists so the landing page cannot drift away from what the code, logs and
hardware passports actually say.

## Daily check

At least once per calendar day:

1. `scripts/qa/docs_policy.py --daily` checks that `README.md` has the current
   required sections and a status date no older than one day.
2. The public status date is updated only when a person or an agent has
   reviewed the current status, not as a blind date bump.
3. The review checks five things:
   - is the "current version" statement still true;
   - are the headline results still paired and dated;
   - are running jobs marked as running, partial, rejected or accepted;
   - do documentation links point to files that still exist;
   - is the wording simple enough for an engineer, not a research-paper claim.
4. If a check fails, the next commit must either fix the stale statement or
   move the claim into `history/` with a date.

GitHub runs the daily check through
`.github/workflows/docs-freshness.yml`. The Hermes operations schedule runs a
maintenance pass that updates the status line when the check is clean or writes
a concrete correction task when it is not.

The local maintenance pass checks link targets inside the repository without
depending on the public internet. GitHub Actions and pre-push checks perform the
online link check, with transport retries, so a temporary network timeout cannot
by itself block a dated status refresh.

## Simple public wording

Public pages must say what the system does and what evidence exists. Avoid
grand framing. Do not present this repository as an academic paper, a formal
study program or a source of scientific conclusions. It is a working harness,
benchmark record, and economic/resource measurement log.

Allowed phrasing:

- "open automation harness"
- "paired A/B testing"
- "resource and cost measurement"
- "engineering status"
- "economic evaluation"
- "decision log"

Avoid these promotional or academic self-labels in current project descriptions (do not rewrite historical quotes or citations):

- "scientific study"
- "scientific methodology"
- "research history"
- "research infrastructure"
- "reproducible research"

External scientific articles can still be cited when they provide useful
context or methods. They are recorded as sources, not as proof of this
repository's own claims.

## Structure

The README must stay short enough to be useful in one reading pass. The stable
shape is:

1. what this project does;
2. current version and current status;
3. current headline results;
4. how to run it;
5. where the evidence lives;
6. source and citation policy;
7. repository map.

Long historical evidence stays in `history/`, `results/`, `versions/` and
`logs/`. The landing page links to it instead of repeating it.

The project-wide direction is documented in `docs/TESTING-PHILOSOPHY.md`. Describe Claryel Autonomous as open engineering experimentation; do not imply academic status, validated forecasting, proven Mix AI synergy, or a finished product. Distinguish historical observations, current measurements, hypotheses and distant interests. Correct current-facing claims with dated explanations; never silently rewrite frozen artifacts or attribution logs.

## Update rules

When something changes:

- version change: update `README.md`, `CHANGELOG.md`, `versions/VERSIONS.md`,
  and `docs/methodology.md`;
- benchmark result change: update the paired result table, not raw prose;
- hardware change: update the machine passport and hardware methodology;
- source/evidence change: update `docs/source-policy.md` and the source index;
- rejected version or failed run: keep it and label it rejected/failed.

The daily check is structural and mechanical. Human judgment still decides
whether a number is meaningful, whether a status is accepted, and whether a
statement is honest.

## Evidence retention and correction protocol (added 2026-11-06)

The owner requires maximum preservation of historical material. Apply [Evidence Preservation and Temporal Provenance](EVIDENCE-PRESERVATION.md): **do not delete or silently replace original evidence or historical claims**. When a current-facing statement needs clarification, attach a dated, versioned correction and a link to the prior source. Preserve both earlier and later interpretations. Record exact timestamps and environments when available; never infer missing historical metadata. Third-party titles, quotes and archived language remain intact with appropriate scope notes.

Earlier wording in this policy about moving a claim into `history/` should be read as *adding a historical copy or cross-reference*, never removing its original provenance. Corrections to mutable README summaries remain visible through Git history and must be documented in a dated audit entry.
