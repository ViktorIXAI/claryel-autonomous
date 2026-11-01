# Roadmap (project-brief stages, honest status)

| # | stage | status (2026-11-01, late) |
|---|---|---|
| 1 | Inventory & audit | **done** — sources located, provenance gaps marked (`docs/limitations.md`) |
| 2 | Archive | **done** — frozen snapshot `release-2026-11-01`, SHA-256 index `logs/INDEX.md`; completeness bug found by CI and fixed with a supplement asset (see `history/failures/`) |
| 3 | Public structure | **done** — this repository (public GitHub, MIT standard text, README, CHANGELOG, docs; link integrity enforced in CI) |
| 4 | Autonomous-dev history | **done** — v1.0–v1.9 chain + autonomy ledger + verbatim decision log; v1.0–v1.1 sub-attribution honestly `unknown/not_recorded` |
| 5 | Results | **done** — pinned aggregates + auto-discovered full history `results/summary-full.json` incl. rejected v1.4/v1.5/v1.6 deltas, paired per machine |
| 6 | Telemetry binding | **done (v2)** — `telemetry/collector2.py` (run_id, units, sources, `not_available`), `join.py` per-attempt conditions, overhead measured ≤0.4%; phase-1 CSV + B2003 gap kept documented |
| 7 | Independent verification | **partial→done** — CI `reproduce` job re-hashes the public archive and recomputes the summary on every push; independent scorer `analytics/second_opinion.py` published incl. its dissent (`results/independent-scorer.md`); dedup-rule sensitivity shows published deltas are rule-insensitive; full third-party adoption still open |
| 8 | Automated publication | **done (first cycle proven)** — `scripts/publish/pipeline.py` (collect→verify→privacy-scan→immutable snapshot→aggregate→publish→public re-check); watchdog proven live: auto-published `pkg-series-v12-v20.de4f3a8446e0` when the Mac series grew; scheduled every 6 h |
| 9 | Install for others | **done** — Mode 1 quickstart + self-tests + smoke on a third box; holdout bank (`benchmarks/holdout/`) with disjoint ids validated in CI; pilot run published (`results/holdout-mini.md`) |
| 10 | Local+cloud privacy layer | **partial** — working prototype `benchmarks/privacy-boundary/gateway.py` (default-deny, 12 deny categories, lane policy) + 18 synthetic tests in CI; no real data ever sent; paraphrase-leak resistance is an open research problem, no finished-protection claim |
| 11 | Public dashboard | **done** — https://viktorixai.github.io/claryel-autonomous/dashboard/ rendered entirely from repo JSON (`scripts/build_dashboard.py`) |
| 12 | Research expansion | **in progress** — v2.0-dev contour runs (auto-published); holdout pilot found a real G-category generalization gap; full 206-task holdout series next; v2.0 must beat dev **and** holdout sets |

Standing constraints while executing the roadmap: running series are never
killed for publication purposes; configurations are not changed without
cause; old data is never deleted or rewritten; unmeasured stays null.
