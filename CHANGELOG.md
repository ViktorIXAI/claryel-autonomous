# Changelog

Contour (harness) generations. Rejected generations are listed under
**Rejected** — they are part of the record, not hidden history.

## [Unreleased] — v2.0 (experimental)
### Added
- Post-normalization for G (explicit contradiction marker) and H (compression
  under the 600-char limit). Evidence: 18 probe rows, one box. **Not adopted**
  (not paired, not cross-boxed).

## [1.9] — 2026-11-01 (RELEASED contour of this repo)
### Fixed
- D-ea (agent action-order) tasks were CHRONIC (avg 0.34) due to a
  contour/scorer wiring mismatch, not model failure. `d_order_steps()`
  mechanically normalizes the model's ordered tool list into the scorer's
  required `agent_steps` slots + summary `answer`. Event
  `contour:v19_d_order_to_steps`; contract test `gate_v19_d_test.py`.
### Results (paired, same task/rep keys)
- B2003: +0.047 avg content (229 improved / 79 regressed, n=2127); D 0.42→1.00
- Mac:  +0.051 avg content (183 improved / 0 regressed, n=2416); D 0.45→1.00

## [1.8] — 2026-10-31 (adopted, scope-limited)
### Added
- One targeted contour nudge per scorer-note kind (max 2 kinds/task), adopted
  only when the re-scored answer improves. Refusal of premature `answer` in
  D-loops (`gate:blocked_early_answer`).
### Results
- B2003 +0.012 (717 pairs; H +0.175, F +0.044; regressions E −0.015, K −0.046)
- Mac +0.007 (1317 pairs; H +0.085)

## [1.7] — 2026-10-31 (adopted; working baseline for a day)
### Added
- Mechanical form repair by code — model never called for format problems
  (`gate_fixers.py`, 12-case test suite incl. refusal paths). `PARB_CHEAP`
  default 0.
### Results
- A/B vs v1.3: 19/19 vs 19/19 correct; input −31%, generation −24%,
  wall −19%, form-related model calls −45%.

## Rejected (kept as research results)
- **v1.6** — cheap model repair made reachable (prev answer passed
  explicitly) + skeleton guard: −45% input tokens but 16/19 vs 19/19 correct
  financial answers; guard blind to corrupted values. Rejected.
- **v1.5** — skeleton guard on cheap repairs: identical to v1.3 because the
  guarded branch was dead code; guard fired 0 times. No-op, logged as an
  unverified-guard lesson.
- **v1.4** — repair without source document + retry cap 2→1 (two bundled
  changes): 19/19 → 3/19 correct. Banned; retry cap identified as the real
  cause post-hoc.

## [1.0–1.3] — 2026-10-31
- v1.0 baseline contour (gates + re-ask), v1.1 chunked extraction + completeness
  gates, v1.2 code-derived constraint filters + format gate, v1.3 strict format
  + `KEY:` field gates (format_ok 100%, cost +35–37% tokens).
  Byte-exact code snapshots for v1.0–v1.6 were not retained (`not_recorded`);
  the v1.2 scorer original is (`versions/v1.2/`).
