# 2026-11-08 — pair-251: contour 0.0.2.54 (H unknown grounded from the prompt's own denial sentence) UNMEASURED; flag frozen to (2,54); line stays 0.0.2.53

Decision: NOT adopted. The pre-registered rule (REVIEW-INBOX 2026-11-07 23:56 CET + commit
8118580, frozen before any w5*r4x row) makes the pair UNMEASURED when zero control rows
strict-fail the target; the pair's own control arms strict-PASSED `H-ex6-03` in 3/3 seeds
(null-unknown drew once and still passed strict). Zero live target => zero conversions possible.
UNMEASURED is never a pass; it is also not a measured loss.

Actions executed (owner delegation 2026-11-07: decide, publish the proof, migrate by version):
- `H_UNKNOWN_PROMPT` redefined `contour_at_least(2, 54)` -> `STAMP_REVISION == (2, 54)` (the
  2.30/2.31/2.32/2.34/2.36/2.41/2.42/2.44 freeze pattern; `contour_at_least` would smuggle an
  unproven trigger into every future arm and poison the adoption rule).
- `harness/gate_v68_h_unknown_test.py` pins the freeze mechanically at the definition site
  (source-text assert) since no registered stamp > 2.54 exists yet to test the OFF side.
- `harness/gate_versioning.py` registration kept for the record + VERDICT annotation.
- Full CI contract suite re-run locally: 34/34 PASS (python3.12); v6.6 contour ws pins rebuilt
  at the frozen bytes (`WS-GENERATED.v66full.sha256`), `verify_manifest --v6` PASS.
- Published `pair-251/` (six arms' results/ledgers/logs/run-records, plans, seed-protocol.md,
  sanitized launcher, sampler prose, energy windows) + `PAIR-251-V66.md` + DIGEST.md row
  (single-shot 96.9%, loop-D 83.3%, whole bank 95.9%, bank sha16 590503cf1701a6ce, stamp axis
  2.53 + 2.54, 6 arms) + README current-version paragraph.

Evidence (all from published ledgers joined to results bytes; see PAIR-251-V66.md):
guards all clean (1 `from_prompt` + 5 `matched`, census surface only, zero control events, zero
frozen-band fires, v228 parity, adopted-family parity within noise); flips 9 over 231 cells
W3/L6 p=0.508 — under the measured ~2-cell floor; energy matched windows 10.62 vs 10.94 Wh.

Class ruling: `H-ex6-03` `unknown_missing` live rate on the adopted 2.53 line is at/near zero
over 9 fresh draws (pair-249/250/251) — closed for contour work; a future re-arm needs a NEW
stamp + NEW flag + NEW event names and only if a rebuilt stability map shows it live again.
Cadence: 4 measured-era stamps since cadence-249; four-arm re-run due after the next stamp.
