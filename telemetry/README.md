# Telemetry

- `collector.py` — 13-metric procfs/nvidia-smi sampler used in phase 1
  (`telemetry/samp-phase1.csv`, 1-second cadence, control host during the
  baseline series; ~1.28 MB CSV published raw).
- Sensor availability per machine: see each passport (`hardware/inventory/`).
  Absent sensors are `not_available`; no estimates are ever published.
- Results rows additionally embed `mem_avail_mb` and contour stop-gate
  readings (RAM<700 MB, GPU>89 °C, endpoint health) — that is the only
  per-run telemetry binding until roadmap stage 6 wires full joins
  (`telemetry_ref` in `schemas/run.schema.json`).
- Known gap, recorded not hidden: B2003 phase-2 `samp.out` is 0 bytes
  (sampler misconfigured mid-series) — see `history/failures/`.
- Sampler overhead isolation (how much a benchmark slows because it is
  watched) is unmeasured: open item, stage 6. The −15 % figure in
  `benchmarks/performance/` is parallel *workload*, not sampler overhead.
