# Methodology

## Frozen substrate
- One model build per series: GGUF identifiers + sizes + SHA-256 in
  `hardware/inventory/model-iq3s.md`; serving engine + launch flags pinned
  per machine in `hardware/configurations/`.
- Task bank generated deterministically from templates under
  `bank_seed=20261031`; plan (task × rep × series positions) frozen before
  any run, `plan_hash` recorded in the state file.
- Temperature 0.7 with per-(task, rep) generation seeds — variance is real
  (±0.3–1.0 at rep level is normal), which is *why* every version comparison
  is paired on identical keys.

## Contour versioning
- One codebase, generations selected at runtime (`PARB_GATE_VERSION=v1.2…v1.9`);
  each run stamps `contour_version` into every results and ledger row so
  generations never mix in one statistic.
- One substantive change per version; unit tests for mechanical fixers first
  (refusal paths included); smoke subset before overnight launches.

## Comparison discipline
- **Paired `(task, rep)` A/B** is the adoption metric; per-category means
  across different plan mixes are descriptive only.
- **Cross-box replication**: adopted versions reproduce on a second physical
  machine with identical seeds (`gseed = sha256(task|rep) mod 999983` for
  extended reps — box-independent by construction).
- Failure classification feeds the next hypothesis:
  CHRONIC (structural contour change) / LOTTERY (retry & selection) /
  FIXED (confirmed win) — see `experiments/ab/classify_v19p.py`.
- Cost and physical execution tracked next to quality: model calls, tokens
  (useful vs overhead), end-to-end seconds, peak host RAM, peak/min available
  memory, peak VRAM and headroom, peak GPU utilization/power, estimated GPU
  energy, and per-correct-answer economics for finance categories.
- Dedup rule everywhere: `(task, rep[, box])` keeping the best `content`;
  raw logs are never edited.

## Independent verification
`analytics/aggregate.py` recomputes `results/summary.json` from the raw
release archive — a third party never has to trust our tables, only the
SHA-256-pinned JSONLs in `logs/INDEX.md`.

## What is deliberately *not* done here
No LLM-as-judge scoring (validators are code + data references); no prompt
tuning on measured tasks (contour nudges are answer-form reminders, logged
and adoption-gated); no cherry-picked windows (in-progress series are marked
in-progress); no silent rescaling (scorer changes would be versioned and
visible).
