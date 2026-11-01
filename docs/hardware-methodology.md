# Hardware methodology

A **machine passport** (`hardware/inventory/<id>.md`) is the unit of
comparability. No performance claim in this repo may reference a machine
that lacks a passport, and no comparison may mix passports without naming
both.

## Passport fields (see the JSON schema in `schemas/hardware.schema.json`)
internal id · public anonymized name · vendor/model · CPU (model, physical/
logical cores) · GPU (model, architecture, VRAM) · RAM (size, type, speed,
channel config — from `dmidecode` where permitted, else `free` +
`not_available`) · storage · OS + kernel · GPU driver · CUDA/ROCm/Metal ·
serving engine + version · model build id (link to model passport) ·
launch config (sanitized, `hardware/configurations/`) · sensor availability
matrix (`not_available` is a value, never an estimate).

Passports in this repo were **live-collected** (2026-11-01) with the commands
recorded at the bottom of each passport file; historical descriptions in
older notes were re-verified, not copied.

## Configuration change log (`hardware/changes/`)
Every material change (RAM modules, GPU swap, cooling, driver, OS, engine
version) gets its own entry with date (or `not_recorded`), evidence and the
series affected. Comparisons spanning a change boundary are flagged.

## Telemetry rules
- Active benchmarks: 1 s–5 s sampling (`telemetry/collector.py`, 13 metrics
  in the phase-1 CSV; per-run results rows additionally carry
  `mem_avail_mb` and GPU stop-gate values).
- Sensors with no hardware backing are published as `not_available`;
  temperatures and watts are never inferred.
- Monitoring overhead: the sampler is deliberately cheap (procfs/nvidia-smi
  only). Its isolation-measured overhead on benchmark throughput is
  **not yet quantified** (roadmap stage 6); the *parallel-workload* penalty
  (a second contour sharing the endpoint) **is** measured at ≈ −15 % decode
  (browser-visual series log) and reported separately — they are different
  effects and are never conflated.
- All samples share epoch timestamps with results rows for later joins.

## Cross-box A/B rules
Identical frozen plan + identical per-`(task, rep)` seeds; `gseed` derived
from `sha256(task|rep)` so every box draws the same samples; verdicts
require agreement across passports, disagreement gets investigated (see
v1.8 E/K regressions vs Mac's zeros).
