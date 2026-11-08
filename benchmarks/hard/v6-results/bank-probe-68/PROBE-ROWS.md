# bank-probe-68 — bank v6.8 (`7a9527bf2e4ebbff`), rule frozen in REVIEW-INBOX before rows; guard decision under probe-guard v1 AND v2 (delta table in `../../PROBE-GUARD-RULES.md`)

## setup

- candidate contour legs `c68r64/65/66`: ws `~/parb-b68full-contour` (bank v6.8
  `7a9527bf2e4ebbff`, ws copy `361f7bdb24d6ac71`, pins `WS-GENERATED.v68full.sha256`),
  stamp `0.0.2.56`, harness `988113f` in run records; control = the PUBLISHED
  `c66r64/65/66` legs of bank-probe-67 (same seeds, same stamp, same harness HEAD).
- raw fairness arms on the byte-guarded v6.8 subset ws (`1d6b89806bc4e3be`, guard
  printed at scoring): basalt 18, codex 18, grok 18 rows.
- seeds sp1 identical to probe-67 reps; plans published, sp1 audit 0 mismatches.
- all six legs exit 0.

## (a) raw fairness — **FAIR**

basalt, codex, grok all strict-pass 3/3 on C-ex6-01, F-ex6-01, H-ex6-00,
K-ex6-00, K-ex6-01; H-ex6-03: basalt 2/3 (one `claimed_actions` lottery draw),
codex 3/3, **grok 3/3** — the claims-wording fix removed the exact failure mode
of probe-67 (grok no longer writes session-state statements into `claims`).
18/18 arm-cells >= 2/3.

## (b) contour no-new-loss — v1 DIRTY, v2 CLEAN (re-verdict under the new guard version)

guard tasks (C-ex6-01 excluded per the rule frozen in the v6.8 REVIEW-INBOX entry —
its flip is raw-proven bank fairness vs contour scaffolding debt, reported below):

| task | v6.6 control | v6.8 candidate |
|---|---|---|
| F-ex6-01 | 3/3 | 3/3 |
| H-ex6-00 | 3/3 | 3/3 |
| H-ex6-03 | 3/3 | **2/3** |
| K-ex6-00 | 3/3 | 3/3 |
| K-ex6-01 | 3/3 | 3/3 |

- The one flip: `c68r64` H-ex6-03, `unknown_missing`. Answer bytes: the model
  hallucinated a «quote in a document» scenario entirely absent from the prompt;
  the contour quote-gates (`gate:quote_not_in_source`, `fix:quote_attempt_1`)
  correctly blocked the fabricated citation and `contour:v219_h_clear_actions`
  fired — the contour behaved; the model misread. Failure mode `unknown_missing`
  was already observed on the SAME task in this campaign: probe-67 basalt RAW
  rep64 (published in bank-probe-67, before this guard freezing).
- C-ex6-01 (excluded from guards, reported): v6.8 contour legs repeat the probe-67
  scaffold flip 0/3 (`fields_mismatch`, extra B) — stable scaffolding bias, contour
  debt unchanged.
- verdict under probe-guard-v1 (as-run): (a) FAIR, (b) DIRTY -> provisional.
- verdict under probe-guard-v2 (frozen 2026-11-08 ~13:00 CET with the calibration
  evidence and re-verdict delta table in `../../PROBE-GUARD-RULES.md`):
  **(a) FAIR, (b) CLEAN -> PROMOTE.** The v1 column above stays as published;
  the promotion below is rendered under v2 and says so.

## promotion

- `BANK-VERSIONS.json`: v6.8 -> **working** (status_note names the v2 re-verdict and
  the v1 as-run column), v6.6 -> superseded, v6.7 stays provisional (chain of record;
  fails fairness under both guard versions — v2 does not relax (a)).
- bank chain: v6.8 = v6.7 + claims wording on H00/H03; v6.7 = v6.6 + six gold/spec
  fixes; every byte delta in the two changelogs.
- next full-bank consequence (queued): map legs on v6.8 (re-draw 25/26/27 on the v6.8
  ws = map-258 legs) to put a v6.8 percent on the scoreboard; the 97.4% (75.0/77)
  figure stays attached to v6.6/map-256 and is NEVER quoted for v6.8.
- contour debt (unchanged, tracked): C-ex6-01 scaffold flip on the adopted line —
  contour answers B,C,F (B included via its own scaffolding) where raw brains answer
  C,F unanimously. Future contour candidate: gate B-inclusion on the model's own
  justification text. Target map rebuilt from v6.8 legs when map-258 lands.

## seeds, energy, hygiene

- seed-protocol.md unchanged; queue via systemd unit `parb-probe68`; raw calls at
  idle; contour legs share one serve sequentially.
- artifacts sanitized (<LAN_IP>/<LOCAL_PATH>); secret scan strict over the tree.
