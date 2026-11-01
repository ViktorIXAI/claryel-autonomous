# Raw artifact index (frozen snapshot `release-2026-11-01`)

Raw run artifacts are NOT committed to git; they are attached to the GitHub
Release as `artifacts-release-2026-11-01.tar.zst`. Unpack it, then verify every
published number with `PARB_ARTIFACTS=./artifacts python3 analytics/aggregate.py`.
SHA-256 (first 16 hex) of each file in the archive:

| artifact | records | bytes | sha256/16 |
|---|---:|---:|---|
| gate-ledger-v12.jsonl | 549 | 241085 | `852e19c593bde8fa` |
| gate-ledger-v12m.jsonl | 645 | 287919 | `08713fd12abe6edb` |
| gate-ledger-v13.jsonl | 57 | 25500 | `86a155f9b5e4040a` |
| gate-ledger-v13m.jsonl | 65 | 29457 | `f77a824da71d5b24` |
| gate-ledger-v17m.jsonl | 40 | 18381 | `e6a7ea9793486a62` |
| results-v12.jsonl | 650 | 1004544 | `b355ca38c37ef57c` |
| results-v12m.jsonl | 645 | 966093 | `207af80fae319738` |
| v17-final/results-v17-b2003.jsonl | 787 | 1195207 | `155cdb8a432f6019` |
| v17-final/results-v17-mac.jsonl | 1321 | 2023966 | `869cb58733bdcf76` |
| v18-final/gate-ledger-v18-b2003.jsonl | 3117 | 1438457 | `8378c49194e5f7a8` |
| v18-final/gate-ledger-v18-mac.jsonl | 2513 | 1165219 | `4546744b4eb25020` |
| v18-final/results-v18-b2003.jsonl | 3117 | 6079371 | `2fffde97dde2c05a` |
| v18-final/results-v18-mac.jsonl | 2513 | 4808049 | `504e164a5b424f8f` |
| v19-final/gate-ledger-v18p.jsonl | 66 | 30722 | `79090508be697a71` |
| v19-final/gate-ledger-v19-b2003.jsonl | 2127 | 973293 | `868f553c854d981e` |
| v19-final/gate-ledger-v19calc-P2005.jsonl | 48 | 21790 | `6a035f9a25ab9889` |
| v19-final/gate-ledger-v19m.jsonl | 2416 | 1114743 | `6896f7ea5c868668` |
| v19-final/gate-ledger-v19p.jsonl | 66 | 30946 | `40e07ceaec145a8a` |
| v19-final/results-v18p.jsonl | 66 | 120065 | `67602da0c752017f` |
| v19-final/results-v19-b2003.jsonl | 2127 | 4172930 | `26c79a1b5a19b125` |
| v19-final/results-v19calc-P2005.jsonl | 48 | 83756 | `5f3c7300b7cd873b` |
| v19-final/results-v19m.jsonl | 2416 | 4664431 | `2d35300190d00b1c` |
| v19-final/results-v19p.jsonl | 66 | 124089 | `4ebbb714c5b5f7dd` |
| v20-final/gate-ledger-v20p-P2005.jsonl | 18 | 8324 | `caf7b1ef537c97bf` |
| v20-final/gate-ledger-v20pair19-P2005.jsonl | 18 | 8451 | `f4a9e2072d1109fd` |
| v20-final/results-v20h-P2005.jsonl | 5 | 12835 | `8b4d80fdff06d76d` |
| v20-final/results-v20pair19-P2005.jsonl | 18 | 41884 | `8be667c35d37cf31` |

## Supplementary: third-box smoke (not part of the frozen release)

| file | purpose | lines | bytes | sha256-16 |
|---|---|---:|---:|---|
| `logs/samples/smoke-p2005/results-smoke.jsonl` | smoke, P2005 (third-box install check) | 46 | 84751 | `9c753a9c70c9b6a8` |
| `logs/samples/smoke-p2005/gate-ledger-smoke.jsonl` | smoke, P2005 (third-box install check) | 46 | 21584 | `12d4119460cc1a97` |

Run of the *published* tree on P2005 (5-task subset, `plan_hash=f52458ff0f7b64fe`, contour v1.9, 60 s wall, 46 records). It caught the make_plan staging bug that was fixed the same hour (see `history/failures/`).

## Telemetry-bound smoke P2005SAH (run_id smoke-tel-4, 2026-11-01)

Same 5-task subset as the earlier P2005 install smoke, this time with 1 Hz
telemetry collector bound via run_id; join output restores per-attempt conditions.
Wall 60.2 s vs 60 s without collector — overhead within noise.

| file | lines | bytes | sha256 (first 16) |
|---|---:|---:|---|
| `logs/samples/smoke-p2005-tel/gate-ledger-smoke3.jsonl` | 46 | 21519 | `e869b7fcdca59356…` |
| `logs/samples/smoke-p2005-tel/results-smoke3.jsonl` | 46 | 84920 | `e2ca01280c2bb976…` |
| `telemetry/runs/smoke-tel-4.join.json` | 791 | 16655 | `24518609c7fc06b5…` |
| `telemetry/runs/smoke-tel-4.telem.jsonl` | 57 | 58378 | `83d8520e0cc5d6f2…` |

## Supplementary snapshot rows (2026-11-01, found by CI reproduce)

The pinned `artifacts-release-2026-11-01.tar.zst` asset turned out to lack three
files that `analytics/aggregate.py` reads (CI reproduce job caught this). The
files were collected from their source machines unchanged; the complete set is
republished as `artifacts-release-2026-11-01-v2.tar.zst` (old asset kept).
Recomputing from the complete snapshot reproduces `results/summary.json`
exactly (diffs=0) — no published number changed.

| file | lines | bytes | sha256 (first 16) |
|---|---:|---:|---|
| `results-v13.jsonl` | 342 | 530330 | `3754c3d3d8a47505…` |
| `gate-ledger-v17.jsonl` | 787 | 345741 | `8c102f0e9bfb2cd3…` |
| `results-v13m.jsonl` | 163 | 251238 | `db8e30b25a9c53c6…` |

v2 asset: 998186 bytes, sha256 `42063f2e907d8a00…`

## Holdout pilot mini-run (P2005SAH, contour v1.9, 2026-11-01)

14 unseen holdout tasks; interpretation in `results/holdout-mini.md`.

| file | lines | bytes | sha256 (first 16) |
|---|---:|---:|---|
| `logs/samples/holdout-p2005-mini/gate-ledger-holdout-mini.jsonl` | 71 | 32315 | `d08c01f8cfe13d37…` |
| `logs/samples/holdout-p2005-mini/results-holdout-mini.jsonl` | 71 | 125403 | `07e9450216129bf7…` |
