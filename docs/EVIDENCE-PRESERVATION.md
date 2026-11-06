# Evidence Preservation and Temporal Provenance Policy

Status: active documentation policy. Adopted: 2026-11-06 (calendar date only; exact adoption timestamp not independently recorded). Scope: Claryel Autonomous. This document adds rules prospectively; it does not retroactively establish missing metadata.

## Core rule: preserve, annotate, never silently erase

Original observations, benchmark outputs, agent decisions, rejected versions, historical statements and their errors remain part of the record. A later correction **does not overwrite the original evidence**. Use a dated addendum, a new versioned evaluation, or an explicit supersession note pointing to both the earlier and later interpretation.

No bulk deletion, rewriting of Git history, force-push, replacement of frozen bank prompts/references, or silent modification of raw result bytes. Existing code and current-facing explanatory documents may require maintenance; where changing text, retain a discoverable prior version in Git and append a dated explanation with old/new meaning. Prefer annotations over removal. Any exceptional deletion for secrets, personal data, licensing or legal obligations requires maintainer review and a non-sensitive audit record; do not publish sensitive values merely to preserve them.

## Record fields (where available)

For each new experiment, revision, interpretation or correction, capture:

- **Identity:** immutable run/event ID, task ID, artifact path, SHA-256 or Git blob/commit SHA.
- **Time:** UTC ISO-8601 event timestamp with timezone; local timezone separately when useful; distinguish event time, collection time, publication time and later review time.
- **Version:** project/contour stamped revision and actual behavior version; model ID and quantization/hash, inference engine/build, agent/harness/scorer versions, prompt/task-bank/reference versions, API/client version, tool policy.
- **Environment:** hardware passport and hardware state, OS/kernel, GPU/VRAM/RAM, relevant power/memory settings, network/cloud provider where relevant, subscription/API tier and known limits.
- **Conditions:** task input, prompt template, seed/sampling parameters, context length, retries, budget, tool permissions, run order, execution outcome, resource/cost measurement units and collection method.
- **Evidence:** original output bytes or privacy-safe reference, execution logs, validator result, independent review, known missing artifacts, failures and provenance links.
- **Interpretation:** claim and scope, uncertainty, observed versus inferred, limitations, author/agent/reviewer, approval state, competing explanations and open questions.
- **Revision trail:** previous claim and source link, new interpretation, reason, supporting evidence, review timestamp, affected scoreboards/decisions, whether re-scored historical bytes or reran on a new environment.

Record unavailable values as `not_recorded`, `not_available` or `unknown` as appropriate; never manufacture historical timestamps, model IDs, hardware states or costs. Date-only records must be explicitly labeled as date-only.

## Distinguish four operations

1. **Original observation**: immutable raw answer, environment and scoring as actually recorded.
2. **Historical reinterpretation**: new commentary or scorer applied to *preserved* old answers; preserve both verdicts.
3. **Replication / rerun**: a fresh execution with a new run ID and complete new conditions; do not call it a retroactive correction.
4. **Documentation clarification**: a dated note about an older statement; preserve discoverable earlier wording and explain scope.

A correction must not silently alter the denominator, task eligibility, metric, scorer, category or comparison arm of a previously published headline number.

## Comparability and fast-changing environments

Use frozen snapshots for causal comparisons. In longitudinal analysis, explicitly log changes in models, inference engines, quantization, agent tools, hardware, cloud provider/tier, costs and evaluator. When multiple factors change, do not attribute causation without controls. Record the difference between observed prices and estimated lifetime costs.

## Public presentation

Current-facing summaries may state that a historical claim is superseded, but link to the exact original evidence and dated correction. Do not erase failed forecasts, unsuccessful tests or evaluator defects. No academic-status, proven-synergy or guaranteed-product assertions without evidence. Historical quotes, third-party publication titles and citations remain intact with context.

## Security and approval

Preservation is subject to privacy, security and licensing constraints. Never publish credentials, private user data, protected transcripts or secret infrastructure details. Store only sanitized public evidence and non-sensitive integrity/provenance references. Do not change production systems, security boundaries, agent permissions or frozen experiments without explicit owner approval.

## Minimum correction entry template

```yaml
record_id: correction-YYYYMMDD-unique-id
event_time_utc: not_recorded
review_time_utc: not_recorded
publication_time_utc: not_recorded
source_path: path/to/original
source_commit: not_recorded
affected_run_ids: []
original_claim: "quote or exact reference"
original_scope: "as originally documented"
new_interpretation: "what changed"
reason: "why"
evidence: []
reviewer: not_recorded
confidence: not_recorded
status: proposed
historical_data_modified: false
```

This template is guidance for new records, not a claim that past records contain all fields.
