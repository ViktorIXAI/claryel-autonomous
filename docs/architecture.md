<!-- TEMPORAL-SCOPE-2026-11-06 -->
> **Historical scope note (added 2026-11-06; exact UTC time not recorded).** This diagram describes an early contour architecture, not all later hard-v6 or Mix AI work. See [preservation policy](EVIDENCE-PRESERVATION.md) and [project direction](TESTING-PHILOSOPHY.md). Original text is retained below.

# Architecture of the lab

```
                    ┌────────────────────────────────────────────────┐
                    │  FROZEN SUBSTRATE (never touched by versions)  │
                    │  model build · task bank (parb_bank.py seeds)  │
                    │  plan.json (+plan_hash) · validator refs       │
                    └───────────────┬────────────────────────────────┘
                                    │ same (task, rep, seed) keys
                    ┌───────────────▼────────────────────────────────┐
                    │  CONTOUR (the thing that evolves)              │
                    │  ask_ladder (512→1024→2048 on truncation)     │
                    │  gates: json · format · fields(KEY:) · order   │
                    │         · code-exec(hidden tests) · loop-guard │
                    │  fixers: mechanical form repair (no model call)│
                    │  nudges: answer-form reminders (adopt-if-better)│
                    │  slot normalizer (v1.9) · post-normalizer (v2.0)│
                    │  F diagnostic grounding (v2.2)                 │
                    └───────────────┬────────────────────────────────┘
        results-*.jsonl ◄───────────┤───────────► gate-ledger-*.jsonl
        (score, notes, answer)      │             (calls, tokens, events)
                    ┌───────────────▼────────────────────────────────┐
                    │  ANALYSIS: classify_v19p (CHRONIC/LOTTERY/     │
                    │  FIXED) · gate_report · analytics/aggregate    │
                    │  → ONE hypothesis → new contour version        │
                    └────────────────────────────────────────────────┘
```

## Components (file map)

| file | role |
|---|---|
| `harness/gate_run.py` | contour runner (v1.9); all generation switches (`PARB_GATE_VERSION`) |
| `harness/parb_run.py` | contour-free control runner (baseline without gates) |
| `harness/parb_check.py`, `parb_loop.py` | validators/scorers; agent-loop mock tools |
| `harness/gate_fixers.py` | v1.7 mechanical form repair + refusal rules (12-case suite) |
| `harness/parb_bank.py` | deterministic task-bank generator (11 categories) |
| `harness/parb_plan.py`, `make_plan.py` | frozen plan builder + `plan_hash` |
| `harness/gate_report.py`, `analytics/aggregate.py` | reporting + independent recompute |
| `harness/stop_series.sh` | state-matched process stop (never cmdline-regex kills) |
| `telemetry/collector.py` | 13-metric hardware sampler |
| `benchmarks/browser-visual/contour_run2.py` | second contour family: browser/JS code-gen loop |

## Event taxonomy (ledger `events[]`)
`gate:*` (validation outcomes: `format_gap_json`, `computed_by_code`,
`order_ok`, `tests_50_of_50`, `blocked_*_before_read`, …) ·
`fix:*` (repair attempts) · `ladder:*` (token-budget steps) ·
`contour:*` (version-specific: `v18_nudge_fired_*` vs adoption `fix:v18_nudge_*`,
`v19_d_order_to_steps`). Fired-vs-adopted are **separate events** — a nudge
that fired but wasn't adopted is pure cost, and the books show it.

## Isolation choices
Mocked tools for D-loops; code tasks executed with declared fixtures;
resource stop-gates (RAM <700 MB, GPU >89 °C, endpoint unhealthy) pause/stop
cleanly and are recorded in the state file. One endpoint, your address,
nothing else.
