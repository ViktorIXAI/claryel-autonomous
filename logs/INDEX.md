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
