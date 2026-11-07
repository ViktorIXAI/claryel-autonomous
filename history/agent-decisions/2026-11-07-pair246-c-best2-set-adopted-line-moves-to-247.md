# 2026-11-07 — pair-246: C best-of-2 `set_mismatch` trigger MEASURED and ADOPTED; line moves to 0.0.2.47

Decision by the autonomous contour loop under the owner's 2026-11-07 delegation ("decisions are
yours... version every element"). Recorded here because it moves the adopted line.

- Pre-registered rule (REVIEW-INBOX 2026-11-07 10:04 CET, `run_pair246.sh` header, commit
  `1a590a1`): ADOPT iff (a) live target >=1 control C cell strict-fails with `set_mismatch`,
  (b) >=1 conversion carrying both v47 events, (c) guards clean. Otherwise freeze to (2,47).
- Measured (arms s46r19/s47r19/s46r20/s47r20/s46r21/s47r21, bank v6.2, idle endpoint):
  (a) 6 live-target cells; (b) 2 evented conversions (C-ex6-00 r19+r20); (c) all guards clean
  (fires only on cat==C, none in control, zero C regressions, frozen bands silent).
- Verdict per the rule text: **ADOPT 0.0.2.47**. `C_BEST2_SET` inherits as line behavior from
  2.47; gate_v49 pins 2.47 == 2.46 + exactly C_BEST2_SET.
- Full-pool movement (209 -> 207, 3W/5L, p=0.727) is at the published noise floor and is NOT the
  adoption basis — the adoption basis is the pre-registered cell-level rule.
- New experimental fact for the queue: chronic C-ex6-02 fired 3/3 and converted 0/3 — the retry
  draw repeats the same omitted candidate. Biased draw, selection spent; no further resampling
  stamp may target it. Closed for this mechanism class with direct evidence.
- Tooling picked up in the same publication: `scripts/publish_pair_arms.py` workspace is now
  `PARB_WS_DIR`-overridable (default unchanged), needed because pair-246 arms live in the v6.2
  workspace.
- Artifacts: `benchmarks/hard/v6-results/pair-246/` (24 files), `PAIR-246-V62.md`,
  REVIEW-INBOX 10:47 CET.
