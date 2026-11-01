# Telemetry

- `collector2.py` — v2 sampler (2026-11-01): JSONL, self-describing header
  (units + per-metric source), `run_id` binding via `PARB_RUN_ID`, macOS and
  Linux paths, every absent sensor literally `null` + `not_available` with a
  reason. 1 Hz, ~2 KB/s.
- `join.py` — binds results to telemetry: per-attempt windows
  (`[t_wall − attempt_seconds, t_wall]`) report medians of CPU/GPU/RAM
  metrics inside the window; no samples in window ⇒ `not_available`.
  Example output committed at `runs/smoke-tel-4.join.json`.
- **Sampler overhead, measured:** identical 5-task/46-record smoke on
  P2005SAH — 60 s without collector, 60.2 s with 1 Hz collector + join.
  Overhead within measurement noise (≤0.4%).
- Overclock/throttle evidence: `gpu_throttle` (nvidia-smi
  `clocks_event_reasons.active`) sampled per second; P2005 dynamic power
  142–175 W band visible as `gpu_power_w` variance.
- `collector.py` + `samp-phase1.csv` — phase-1 sampler (13 metrics, 1 Hz,
  control host during the baseline series; ~1.28 MB CSV published raw).
- Sensor availability per machine: see each passport (`hardware/inventory/`).
  Absent sensors are `not_available`; no estimates are ever published.
  macOS temperature/power/GPU sensors are root-required and published as
  `not_available`, not sudo'd around.
- Results rows additionally embed `mem_avail_mb` and contour stop-gate
  readings (RAM<700 MB, GPU>89 °C, endpoint health).
- Known gap, recorded not hidden: B2003 phase-2 `samp.out` is 0 bytes
  (sampler misconfigured mid-series) — see `history/failures/`.
