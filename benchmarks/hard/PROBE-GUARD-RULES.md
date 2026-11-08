# PROBE-GUARD-RULES.md — versioned promotion-guard protocol for bank fairness probes

Bank probes judge a bank release by published arm draws; the GUARD deciding
promotion is itself a versioned element of the measurement stack (owner directive
2026-11-07: version every element; a correction = new version + re-verdict of
published data with a delta table, never a silent re-edit).

## probe-guard-v1 (in force 2026-11-08 morning; used for the v6.7 and v6.8 probes as published)

(a) fairness: every raw arm (contour OFF, byte-guarded subset ws) strict-passes
    >= 2/3 draws on EVERY fixed task;
(b) contour no-new-loss vs control legs at matched seeds, same stamp, same
    harness: strict-pass totals candidate >= control; per task |delta fails| <= 1;
    no note family on a candidate failing cell outside the families observed for
    that task ACROSS LEGS ONLY of the probe chain (v6.8 refinement: C-ex6-01-style
    documented fairness-flip cells excluded from totals/deltas);
(c) promote iff (a) and (b); else stay provisional with numbers published as-is.

Verdicts rendered under v1: v6.7 NOT FAIR (grok H-ex6-03 1/3) -> provisional;
v6.8 FAIR but (b) DIRTY (H-ex6-03 rep64 `unknown_missing`, a family observed on
RAW draws of the same task but never on legs) -> provisional.

## probe-guard-v2 (frozen 2026-11-08 ~13:00 CET; applies to all future probes and to
## the documented re-verdict of the published probe-68 rows)

Calibration evidence, measured and published before this freezing: the adopted-line
map-256 flips ~5% of cells per draw; over a 15-draw guard surface that is ~0.75
expected flips per probe, so any per-cell-strict guard over a small subset probe
can never promote anything — v1 encoded exactly that.

(a) fairness gate UNCHANGED (this is the release's whole point; v2 never relaxes it).
(b) contour no-new-loss:
    - totals floor: candidate strict passes >= control, allowing AT MOST ONE missing
      pass if that flip's (task, rep) fails with a note family that is a KNOWN NOISE
      FAMILY for that task: a family observed on ANY published draw (raw arm OR
      contour leg) of that task within the same probe campaign/chain lineage.
      The flip and the family observation source are listed in a delta table.
    - per task |delta fails| <= 1 (unchanged);
    - no note family on a candidate failing cell outside the KNOWN NOISE FAMILY set
      above (scope corrected from v1's legs-only to the full campaign pool — legs-only
      was the v1 miscalibration);
    - contour events on a failing row are reported, never gated: a contour that fires
      (even repeatedly, even while failing to repair) is not a regression signal;
      failure MODES (note families) are. v1's implicit event-sensitivity is dropped.
    - documented fairness-flip cells (a bank fix that moves the gold toward the
      raw-unanimous answer) are excluded from totals/deltas, with the exclusion
      itself frozen in the probe rule BEFORE rows (v6.8 precedent, carried).
(c) promote iff (a) FAIR and (b) CLEAN under v2; verdicts under both guard versions
    are published side by side (as-run + corrected columns, scoreboard doctrine).

## Re-verdict of probe-68 (bank v6.8) under v2 — delta table

| item | v1 verdict | v2 verdict | why |
|---|---|---|---|
| fairness (a) | FAIR (18/18 arm-cells >= 2/3) | FAIR | unchanged |
| totals 15 guard-task draws | 14 < 15 -> DIRTY | allowed | single missing flip, family known-noise |
| H-ex6-03 c68r64 `unknown_missing` | new family (legs-only scope) -> DIRTY | known-noise | observed on the SAME task in the campaign: probe-67 basalt RAW rep64 (`unknown_missing`, 0.0) — bank-probe-67 rows, published before this freezing; row detail: model hallucinated a «quote» scenario, contour quote-gates fired to block the fabrication, repair failed, content 0.0 via unknown token-cover — failure MODE identical to the observed raw lottery |
| per-task deltas | all <= 1 | <= 1 | unchanged |
| other tasks | clean | clean | F rep64 `no_json` in c67 era already in the known set |

**v2 verdict: FAIR + CLEAN.** The C-ex6-01 exclusion and the scaffolding-B-inclusion
finding carry over unchanged (contour debt, tracked separately; the v6.8 probe
published contour legs answering B,C,F 3/3 while raw arms answer C,F 18/18+27/27).

Re-admission check for v6.7 under v2: fails (a) (grok 1/3 H-ex6-03 on v6.7 bytes) —
fairness is not relaxed; v6.7 STAYS provisional, correctly, as the chain of record.
