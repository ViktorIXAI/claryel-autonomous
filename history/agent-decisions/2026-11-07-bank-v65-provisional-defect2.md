# 2026-11-07 — bank v6.5 stays PROVISIONAL; H-ex6-01 defect fixed derivably, but the raw-arm lift is blocked by defect 2 (claims-field spec)

Decision (delegated per owner directive 07.11, no owner wait):
- `bank-hard-v6.5.json` (`cd29d6ac94dc3267`) published as PROVISIONAL: H-ex6-01 scenario
  names the artifact the reference asks for; `scripts/verify_bank_v65.py` proves the fix
  is one prompt field, all 77 golds byte-identical, and the ask item becomes
  `_token_cover`-derivable from the prompt only after the fix.
- Paired contour probe at 6 matched seeds (reps 28-33): 5/6 vs 5/6, one flip each
  direction, both attributable to seed lottery by the answer bytes. The frozen rules
  are applied as written: rule (i) unmet (control 3/3 at reps 28-30), amended rule (a)
  violated (one v6.5-only loss, rep32) -> provisional. NO contour effect claimed;
  NO v6.6 hypothesis opened on the rep32 draw (its bytes show the degenerate empty
  template the v6.4 side also produces; the rule's "over-priming" wording is recorded
  as not supported).
- Raw-arm fairness (rule (ii)) FAILED: all three arms 0/3, every zero `ungrounded_claims`
  -> DEFECT 2 (claims-field spec invites assertions; contract demands []). v6.6 will
  clarify exactly that one field and re-probe raw lift. The contour's pass on this cell
  is disclosed as `v219_h_clear_claims` scaffolding value.

Why not promote: the frozen promotion rule is mechanical and predates the rows;
overriding it after seeing a v6.5-only loss is exactly the kind of silent goalpost move
the version chain exists to prevent. Why not revert: the derivability proof is
contract-level and draw-independent, and every v6.5 PASS names the artifact verbatim.
The provisional status carries both facts honestly.

Artifacts: `benchmarks/hard/v6-results/bank-probe-65/` (PROBE-ROWS.md, fair-rows.md,
12 contour legs + 9 fair rows + launchers + epochs + sanitized run records),
`benchmarks/hard/bank-defect-v65-changelog.md` (appendix), BANK-VERSIONS.json (v6.5
provisional), REVIEW-INBOX 17:35/17:44/17:45 CET entries.
