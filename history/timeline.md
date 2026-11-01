# Timeline (reconstructed from artifact timestamps + the decision log)

Times are host-local (CET) unless noted. `not_recorded` marks gaps rather
than guesses.

## 2026-10-30
- Operator starts the local-model benchmark effort; the agent designs the
  PARB suite (bank generator, validators, plan). Exact start hour `not_recorded`.

## 2026-10-31 (day of the text-gate contour chain)
- **00:50** task bank built (`bank_seed=20261031`, 178 tasks, plan frozen;
  baseline PARB runs begin: `state*.json`, `results*.jsonl`).
- **02:44** baseline phase finished (`done.stamp` on B2003).
- **07:34–07:48** first contour experiments; a 401-auth harness bug
  invalidates one smoke series and one partial series — both preserved as
  named artifacts (`gate-ledger-smoke.jsonl.401-invalid`,
  `gate-ledger.jsonl.partial-harnessbug`), bug fixed, series re-run.
- **08:31–10:42** v1.2 full series on both boxes (first comparable contour).
- **10:57** v1.3 A/B (format-first + `KEY:` gates) → accepted with cost note.
- **11:08 / 11:13 / 11:18** v1.4 / v1.5 / v1.6 A/B launches on the Mac
  (`ab_v1[456]_mac.sh`) → rejected / no-op / rejected.
- **11:25** `gate_fixers.py` + 12-case test suite written (v1.7); A/B arms
  `ab17*`; **~15:23** Mac v1.7 data complete → v1.7 adopted as working version.
- **16:50** v1.8 deployed (plan backed up first: `plan.json.v18-full-bak-*`),
  paired series launched on both boxes.
- **17:35–18:28** *parallel* browser-visual contour series (contour1,
  contour2) on the B2003 endpoint with host-side Chrome validation —
  the second contour family of the lab (single-shot 1/5 → contour2 5/5 on
  the hardest scene class).

## 2026-11-01 (v1.9 and the publication pass)
- **02:46** `gate_v19_d_test.py` written **before** the fix (test-first).
- **02:51–03:13** v1.8 final analysis + deep probes (v19p) → D-ea classified
  CHRONIC; hypothesis: contour/scorer wiring, not the model.
- **07:21–07:30** v1.9 calc/smoke runs; morning-report cron pulls artifacts
  and computes paired comparisons (this repo's aggregator lineage).
- **07:43–07:45** v1.9 code snapshot taken (`gate_run.v19.bak-0745`); paired
  v1.9 launches on both boxes (plans trimmed to v1.8 keys for exact pairing).
- **07:53** first v2.0 probes on the probe box (18 rows; experimental).
- **08:10–08:16** publication pass: artifact snapshot `release-2026-11-01`
  frozen (series still growing — marked), aggregates computed
  byte-reproducibly, secret sweep, publication notes written.
- **08:16+** v1.9 B2003 series continues uninterrupted through publication
  (brief: running tests are never stopped for publishing).

Where timestamps and the log disagree, both are kept and the disagreement is
a finding, not something to smooth over.
