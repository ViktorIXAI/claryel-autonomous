# Telemetry

- `collector2.py` — v2 sampler (updated 2026-11-02): JSONL, self-describing
  header (units + per-metric source), `run_id` binding via `PARB_RUN_ID`,
  macOS and Linux paths, every absent sensor literally `null` +
  `not_available` with a reason. 1 Hz, ~2 KB/s. Linux nvidia-smi now selects
  the largest-VRAM GPU by default, or the `PARB_GPU_INDEX` device.
- `join.py` — binds results to telemetry: per-attempt windows
  (`[t_wall − attempt_seconds, t_wall]`) report medians of CPU/GPU/RAM
  metrics inside the window; no samples in window ⇒ `not_available`.
  Example output committed at `runs/smoke-tel-4.join.json`.
- `resource_quality.py` — required methodology join: answer quality,
  end-to-end latency, peak RAM/VRAM/power, min available RAM and estimated
  energy per attempt, with p50/p95/max aggregate summaries.
- `resource_quality_test.py` — synthetic test for window joins, peak/min
  selection, latency and energy calculations.
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
- `run_gate.sh` starts the collector automatically when `PARB_TELEM` is
  non-empty, then starts the gate. This is the recommended full-run path.
- `scripts/telemetry/run_with_collector.sh` starts a collector, runs any command,
  then stops the collector on exit.
- Permanent policy: resource telemetry is required for full paired gates and
  hardware-class runs. It may be skipped only for idle endpoint smokes where
  the goal is to check that the endpoint responds.
- Full-Mac evidence for the policy is recorded in
  `results/parb-v22-mac-full-resource.md`.
- Known gap, recorded not hidden: B2003 phase-2 `samp.out` is 0 bytes
  (sampler misconfigured mid-series) — see `history/failures/`.
