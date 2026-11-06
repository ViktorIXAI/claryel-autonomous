# 2026-11-06 13:00 CET — pair232: the J re-rank is on-target but unresolvable; 0.0.2.32 is not adopted

## Context

Pair `pair232` (run ids `e29r0..e29r2`, `e32r0..e32r2`) measured contour 0.0.2.32 (J ranking re-derived
from the prompt's own id/value table) against the adopted control 0.0.2.29 on bank v6.1, three identical
seeds, arms alternating per seed. All six arms: 77/77 rows, exit 0, tokens and seconds healthy, answer
bytes joined from sibling `results-*.jsonl` for every rescore (0 blank joins).

## Measurement

- Control 61/59/63 (mean 61.0), candidate 63/62/62 (mean 62.3): **+1.3 cells**.
- Noise floor of this exact comparison (measured on pair-230/231 controls): 12 of 231 same-stamp cells
  flip, mean moves ~1.4; usable resolution ≈ 2 cells.
- Per-seed sign tests: 3W/1L (p=0.63), 3W/0L (p=0.25), 0W/1L (p=1.0). Pooled 6W/2L p=0.29.
- Mechanism evidence: one fire in three seeds, on exactly its class (`J-ex6-06` seed 0: model's own id
  list re-sorted, 2/3 → 3/3 stable pass), zero extra model calls (326 vs 327), zero membership changes,
  bank coverage 3/7 reproduces / 4/7 refuses / 0 mis-sorts.
- Energy: seed-2 pair identical (4.78 vs 4.84 Wh); the seed-0/1 candidate windows were inflated by
  endpoint-side ~20 s transients on E/F tasks, not by the repair.
- Independent rescore of all six flipped cells from saved bytes: 0 mismatches.

## Decision

**Not adopted.** +1.3 is below the measured floor; the pair cannot claim an improvement, and the reading
rule published with pair-231 forbids calling it one. The mechanism stays registered in
`CONTOUR_FEATURES` (with this verdict in the comment) and is added to `UNADOPTED_FEATURES`:
`J_RERANK = CONTOUR_REVISION == (2, 32)`, so it does NOT inherit into 0.0.2.33 — an unadopted behaviour
must not silently ride along in the next candidate's measurement. Adopted control line remains 0.0.2.29.

The rule this generalizes: a behaviour inherits only if its measurement resolved it. Negative results
(2.30, 2.31) freeze by the existing rule; an unresolvable-but-harmless one (2.32) freezes the same way.
If its on-target value ever needs to be claimed, measure it as its own arm with enough seeds, not as a
passenger.

## Next step (executed)

0.0.2.33 built from the newest failure group of UNSTABLE-CELLS-V61.md (`fields_mismatch`/`missing`):
A-category threshold-table arithmetic (tariff chains recomputed by code from the prompt's own rows;
adopted 2.27 family), fail-closed, `gate_v50` synthetic-grammar proof, coverage 1/9 reproduce / 0 mis.
Paired arms `f29r*` vs `f33r*` launched 12:45 CET the same hour; the K template-echo and yes/no-lexicon
repairs observed in the same group are recorded as separate future candidates, not bundled.

## Publication-integrity fix found on the way

`publish_pair_arms.py` copied `run-record-*.json` and logs byte-raw (only JSONL was sanitized), so the
published run records of pair-230/231 carried the real LAN endpoint in `api_host`. Fixed: every artifact
kind now goes through the placeholder rules with JSON re-validation, and `api_host` values become
`[REDACTED]`; the 12 affected run-record files under `v6-results/` were backfilled in this commit.
Grep over `benchmarks/hard/v6-results/` afterwards: zero LAN addresses, zero host labels, zero local paths.
Pre-existing gitleaks history hits (`marks/privacy-boundary/test_gateway.py`, `marks/browser-visual/*`,
`scripts/publish/pipeline.py` — LAN IPs and ssh key paths, no credential material) are unchanged and
re-reported to the owner rather than rewritten.
