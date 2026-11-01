# v2.1 — candidate final configuration (running)

- **Change:** `h_safety_normalize()` for H-category answers:
  - remove false action claims such as “the email was sent”;
  - redact version/serial-shaped tokens only in missing-data refusals that
    already admit uncertainty;
  - add an explicit uncertainty marker when an existing refusal lacks one.
- **Guardrail:** the contour never adds a factual claim and never softens or
  rewrites a correct full-mode H answer.
- **Test:** `harness/gate_v21_h_test.py` — 10/10.
- **Targeted evidence:** P2005 H smoke — 9/9 content and 9/9 format; events
  `h_action_claim_removed`, `h_missing_redacted`, `h_uncertainty_added`.
- **Running paired evidence (partial):** B2003 n=118, avg 0.9986, format 100%;
  Mac n=162, avg 0.9856, format 100%. Paired B2003 v2.0 → v2.1:
  n=117, avg +0.0112, 3 improved / 0 regressed. Mac paired: n=162, delta 0,
  no regressions.
- **Versioning decision:** v2.1 is the final configuration for this
  configuration line; no v2.2 is planned unless new paired evidence shows a
  regression.
