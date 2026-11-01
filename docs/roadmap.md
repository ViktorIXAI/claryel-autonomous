# Roadmap (project-brief stages, honest status)

| # | stage | status (2026-11-01) |
|---|---|---|
| 1 | Inventory & audit | **done** — sources located, provenance gaps marked (`docs/limitations.md`) |
| 2 | Archive | **done** — frozen snapshot `release-2026-11-01`, SHA-256 index `logs/INDEX.md`, release archive attached |
| 3 | Public structure | **done** — this repository (public GitHub, MIT, README, CHANGELOG, docs) |
| 4 | Autonomous-dev history | **done** — v1.0–v1.9 chain + autonomy ledger + verbatim decision log; v1.0–v1.1 sub-attribution honestly `unknown/not_recorded` |
| 5 | Results | **done** — quality/cost/paired tables, regressions, rejected versions, raw archives downloadable |
| 6 | Telemetry binding | **partial** — phase-1 CSV + collector + sensor matrices published; per-run telemetry joins and sampler-overhead isolation: next |
| 7 | Independent verification | **done** — `analytics/aggregate.py` reproduces `results/summary.json` byte-identically from the archive; third-party scorer = planned |
| 8 | Automated publication | **pending** — first publication was manual + scanned; pipeline design in `docs/privacy-architecture.md`; fine-grained token, no history deletion |
| 9 | Install for others | **done** — Mode 1 quickstart + self-tests + smoke; CPU-only works (any OpenAI-compatible endpoint) |
| 10 | Local+cloud privacy layer | **pending** — design merged, tests specified, implementation not started; no privacy claims until then |
| 11 | Public dashboard | **pending** — GitHub Pages generator over `results/` next; every chart will link its data files |
| 12 | Research expansion | **in progress** — v2.0 contour experiments running on the probe box; model-generation rotation (Qwen successors when confirmed available) planned; cross-box held-out task validation next |

Standing constraints while executing the roadmap: running series are never
killed for publication purposes; configurations are not changed without
cause; old data is never deleted or rewritten; unmeasured stays null.
