# Performance methodology (four speeds, never conflated)

1. **Pure model decode** — raw tokens/s from direct generation logs
   (`harness/parb_log_speed.py`, aggregate output-tokens / measured seconds;
   per-call `tps_eff` is misleading on tiny outputs — endpoint overhead dominates).
2. **Model inside contour** — ledger `seconds` per attempt (includes gates).
3. **Task solve rate** — attempts and wall time per *correct* answer.
4. **System incl. retries** — `model_calls`, `useful_tokens` vs
   `overhead_tokens`, `tps_lost_pct`.

Observed anchors: same contour/plan, B2003 vs Mac: per-attempt seconds ≈7.7 vs
4.3 (v1.9) — ~1.8× hardware gap, quality deltas independent of it; parallel
contours on one endpoint cost ≈ −15 % decode (measured, logged in
browser-visual runs). Cross-machine comparisons compare *same contour, same
seeds*; pure tokens/s of one box is never quoted against task time of another.
