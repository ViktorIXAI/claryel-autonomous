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

## Holdout pilot mini-run v2 (corrected bank, P2005SAH, contour v1.9)

Same 14 tasks/seeds with the G-document generator bug fixed
(`history/failures/failures.md`); interpretation in `results/holdout-mini.md`.
The v1 rows above remain published unmodified, annotated invalid for G.

| file | lines | sha256 (first 16) |
|---|---:|---|
| `logs/samples/holdout-p2005-mini2/gate-ledger-holdout-mini2.jsonl` | 73 | `e4187ad6622c33eb…` |
| `logs/samples/holdout-p2005-mini2/results-holdout-mini2.jsonl` | 73 | `b445fae9410294e5…` |

## Budget-matched simple baselines (P2005SAH, 2026-11-01)

Design and results: `results/baselines.md`; code `experiments/baselines/`.

| file | lines | sha256 (first 16) |
|---|---:|---|
| `experiments/baselines/data/baselines-results.jsonl` (S0/S1/S2/S4, answers stored) | 264 | `d69c1f30eb242f7d…` |
| `experiments/baselines/data/contour-p2005.jsonl` (v1.9 same-box subset) | 102 | `7bcb36d4b03083b1…` |
| `experiments/baselines/data/contour-p2005-ledger.jsonl` | 102 | `a035bad687c8b3f6…` |

## Russian source records (verbatim originals, archived)

The repository presents English-first documentation. Verbatim Russian
originals of decision records and reviews are preserved unmodified in the
release asset `ru-source-records-2026-11-01.tar.zst`
(sha256 `a37a9c922105f61dfcdfaf0d2543ae6c4b956056967a7bc6cd028fd0014ef839`):

| member | content |
|---|---|
| gate-versions.log | agent decision log, Russian original (in-repo English translation: `history/agent-decisions/gate-versions.en.md`) |
| ext-001-review-2026-11-01.ru.txt | external review Russian original (translated copy: `results/external-review-2026-11-01.md`) |
| external-review-2026-11-01.md | review file as it appeared with the Russian section inline (pre-translation snapshot) |
| contour-prompts.md / task-prompts.md | pre-translation versions incl. verbatim Russian prompt quotes |
| NOTES-method.md | pre-translation Russian method notes |

External audit EXT-003 verbatim Russian original is archived separately in
release asset `ext-records-2026-11-01-v2.tar.zst`
(sha256 `4cf55907304ba0c9e52d729b17dea97685bb98ea54fe4444aa8396cb76f654c8`;
member `ext-003-audit-2026-11-01.ru.txt`, text sha256
`e5bd7fe19035258c3b31c73a57079d792529a032f5693e54e860e2c6be643b7f`).

Russian strings that are *functional experiment data* (task prompts in
`bank.json`, contour prompt literals in `gate_run.py`, model outputs in
result JSONL, detector regexes, ledger event tags) stay verbatim everywhere —
they are the measured system, not documentation.

## Post-snapshot artifacts (pending next release bundle)

| artifact | records | bytes | sha256/16 |
|---|---:|---:|---|
| p3001/results-p3001-v21.jsonl | 178 | 425485 | `b08d27f902db3b89` |
| p3001/ledger-p3001-v21.jsonl | 178 | 79870 | `2acb03c7b8b46920` |
| p3001/p3001-v21.log | 180 | 22756 | `0179a686232ba68c` |

Held on the workstation (`~/parb/`) until the next release bundle; numbers
cited in results/p3001-parb-v21.md.

## Pending bundle: p3032 onboarding + IQ3_S context ladder (2026-11-02)

Raw run artifacts are held on the rig and the workstation mirror (not in
git, no Release yet). SHA-256 (first 16 hex) for future bundle verification:

| artifact | records | bytes | sha256/16 |
|---|---:|---:|---|
| bench-sampler-pass1.csv | 122 | 14281 | `a0b69e05204c85b3` |
| bench-sampler-pass2.csv | 96 | 11362 | `a5c8a394e2944529` |
| bench-sampler-pass3.csv | 152 | 17987 | `29ca83244f5f4da2` |
| bench-ladder.jsonl (pass 1) | 5 | 1114 | `d7e8e1664ec8bc1f` |
| bench-ladder2-run.log (capacity rejects) | 28 | 1807 | `50fa0064c68491bf` |
| bench-ladder3-run.log | 6 | 1010 | `ea2d5336679d0596` |
| bench-engine-lines-pass1.txt | 78 | 11003 | `dd949fbbbd8889a8` |
| strata serve engine log (sanitized twin committed as launch json) | — | 56323 | `708f68d35beca386` |
| build-floor round-1 raw build log (failure) | — | 322188 | `7a70d58def37131a` |
| results/p3032-iq3s-context-ladder.jsonl (committed) | 5 | 1010 | `c1781708b2f5ba3f` |
| bench-sampler-pass4.csv (uncapped A/B) | 144 | 16992 | `865a033293003a09` |
| bench-ladder4-run.log | 6 | 1010 | `d6c6320afd7906da` |
| results/p3032-iq3s-power-envelope.jsonl (committed) | 5 | — | — |

## Pending bundle: P3032 contour sweep v2.4 (2026-11-02)

| artifact | records | bytes | sha256/16 |
|---|---:|---:|---|
| results-p3032-v22.jsonl | 178 | 396343 | `44fff0c6aee73d7a` |
| gate-ledger-p3032-v22.jsonl | 178 | 80166 | `dc7db7980a35c2b4` |
| telem-p3032-v22.jsonl (1 Hz, run_id p3032-v22) | 3429 | 3929260 | `0a41d41b7def3a16` |
| runner log | — | 22520 | `9f71c3f3b20f092d` |

## Pending bundle: P3032 slow-disk swap test (2026-11-02)

| artifact | records | bytes | sha256/16 |
|---|---:|---:|---|
| slowart.tar (bundle: ladder jsonl 6, engine log, telemetry 1241, serve log, orchestrator) | — | — | `ed90e2a0d2a58ce4` |
|   inner: slow-ladder.log | 6 | 652 | `ce22481ce94396e1` |
|   inner: strata engine log (slow run) | — | 30858 | `2a2867500be4ef21` |
|   inner: telem-slow3.jsonl (1 Hz) | 1241 | 1412473 | `4493a8d9c1dd08aa` |
|   inner: slow-serve.log | — | 20694 | `269771f5249177a8` |
|   inner: orchestrator slow3.sh | — | — | `09b093d516401ec2` |

## Pending bundle: P1005 post-swap quick contour sweep v0.0.2.2 (2026-11-03)

| artifact | records | bytes | sha256/16 |
|---|---:|---:|---|
| results-quick-v22.jsonl | 178 | 392880 | `92098862a4883ca2` |
| gate-ledger-quick-v22.jsonl | 178 | 80643 | `89a59bb8e298391f` |
| telemetry-quick.csv (60 s sampler) | 41 | 3494 | `57a6536a2e0e9b70` |
| runner log | — | 22624 | `62e87ea2bfe7003b` |
