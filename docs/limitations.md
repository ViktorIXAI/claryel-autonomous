<!-- TEMPORAL-SCOPE-2026-11-06 -->
> **Historical scope note (added 2026-11-06; exact UTC time not recorded).** These limits refer to early v1/v2 experiments. Later cloud comparisons and hard-v6 artifacts exist; old no-cloud statements are not global present-day claims. See [preservation policy](EVIDENCE-PRESERVATION.md) and [project direction](TESTING-PHILOSOPHY.md). Original text is retained below.

# Limitations — read before quoting any number

## Evidence & provenance
- **Code snapshots**: byte-exact source is published for v1.9 (this repo's
  `harness/gate_run.py` == snapshot `gate_run.v19.bak-0745`, self-test
  proven) and for the v1.2 scorer original (`versions/v1.2/`). Byte-exact
  code for v1.0–v1.8 was **not retained** (`not_recorded`); runtime version
  switches exist, but the codebase around them evolved. The decision log is
  the authority for what those versions did.
- **Authorship attribution** is session-level (the agent's own runtime
  sessions + logs), not per-line cryptographic. The agent wrote the contour;
  no human code edits are recorded — treat that as strong log evidence, not
  a signed statement.
- Raw agent session transcripts are not published (they contain home-network
  details); the published evidence layer is the decision log, artifacts and
  timestamps.

## Measurement
- Single model family, single quantization (IQ3_S), one seed plan;
  temperature 0.7 → per-rep variance ±0.3–1.0 is normal. **Never** compare
  unpaired runs across versions.
- v1.9 figures include in-progress series (marked; snapshot pinned).
- Cross-version means are descriptive; paired `(task,rep)` deltas are the
  metric. Scorer evolution across the v1.2 boundary means comparisons before
  v1.2 are not in scope of published deltas.
- Category F (and partially H) stayed contour-resistant (~0.68–0.90); not
  everything is a harness bug, and we have no cure yet.

## Contamination risk (stated plainly)
The contour was *designed while looking at all bank categories*, so these
numbers certify performance on the frozen bank, not on unseen task text.
Mitigations so far: extension reps (rep ≥307) are unseen *repetitions* with
box-independent seeds; honest rule for the future: validate versions on
held-out task sets. `docs/EVOLUTION.md` requires it going forward.

## Hardware & telemetry
- B2003 runs with **one** 24 GB DDR5-5600 module (single-channel; second slot
  empty — configuration change predates the log, exact date `not_recorded`).
  Speed numbers are config-specific.
- Per-component power: available on B2003 GPU (nvidia-smi) and P2005 GPU
  (dynamic nvidia-powerd governor, 142–175 W), **not_available** for B2003
  CPU/whole-system and for Mac Studio sensors; no energy cost per correct
  answer is claimed.
- Phase-1 telemetry CSV (`telemetry/samp-phase1.csv`) covers the *control*
  host during baseline; B2003's own `samp.out` is empty (0 bytes) — a
  recorded logging gap, not hidden data. Per-run ↔ telemetry binding is
  roadmap stage 6.
- Model SHA-256: recorded in `hardware/inventory/model-iq3s.md` once the
  hash job completes (sizes + mtimes already pin the builds; hash values are
  appended, never backfilled).

## Scope
- No cloud-collaboration or privacy-boundary *results* exist yet — only
  design. Nothing in this repo claims measured privacy guarantees.
- Russian task text by design (frozen benchmark language); an English bank
  is planned but unvalidated — cross-language generalization of the contour
  is an open question.
