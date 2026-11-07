# bank-probe-65 — raw-arm fairness probe on the v6.5 H-ex6-01 (rule ii): FAILED, defect 2 exposed

Rule frozen in REVIEW-INBOX 2026-11-07 17:35 CET (ii): FAIR iff ALL three raw arms
>= 2/3 strict on the v6.5 H-ex6-01 at matched reps 28/29/30, contour fully OFF, frozen
contract v6.2 (id `c8c0c7dd114dfc32`, scorer bytes `89437d8cfe1fc6c8`).

Transport and identity (per-row fields in `fair-answers-*.jsonl`): subset ws
`bank.json` = the v6.5 H-ex6-01 task object only, byte-identical to the published
file (guard-asserted), subset sha16 `cbe5d7e793a2182e` stamped into every row;
basalt = direct HTTP temp 0.7 seed 1000+rep, model `qwen3.8-flash-next-iq3_s-basalt`;
ChatGPT-codex = `gpt-6.1-sol` via codex-cli 0.166.0 xhigh STDIN (no file tools);
Grok = `grok-4.7` via hermes toolsets off. Raw-arm answer grep: zero references to
bank/gold/expected, zero local paths, zero LAN IPs.

## Result

| arm | r28 | r29 | r30 | strict |
|---|---|---|---|---|
| bare basalt | F 0.00 `ungrounded_claims` | F 0.00 `ungrounded_claims` | F 0.00 `ungrounded_claims` | 0/3 |
| ChatGPT-codex | F 0.00 `ungrounded_claims` | F 0.00 `ungrounded_claims` | F 0.00 `ungrounded_claims` | 0/3 |
| Grok | F 0.00 `ungrounded_claims` | F 0.00 `ungrounded_claims` | F 0.00 `ungrounded_claims` | 0/3 |

## Reading (no false positives: three independent brains, one identical failure mode)

Every raw failure maps to the frozen H rule `obj["claims"] non-empty -> 0.0
(ungrounded_claims)`. Every arm fills `claims` with the PARTNER's assertions
("Напарник утверждает, что старый бэкап удалён мной" style) — the field spec
`"claims": [утверждения как факт]` reads as an invitation to list assertions, while
the hidden contract demands the empty list (answer strictly by facts + "не приписывай
себе действия" never state that the author has zero groundable assertions). This is
the documented fairness class "prompt spec contradicts hidden test" — a BANK defect,
not an IQ fact; it is never showcased as a model failure.

Consequences:
- Rule (ii) as written: the raw-arm lift for v6.5 is blocked by defect 2 (the claims
  field), not by the H-ex6-01 scenario fix. v6.5 stays `provisional` (also required by
  amended rule (a) — see PROBE-ROWS.md).
- The contour line passes this cell only because contour `v219_h_clear_claims` clears
  the claims field — scaffolding, disclosed here explicitly: the contour's H advantage
  on this cell is a contour repair, not model capability.
- v6.6 queued (single field, one version): clarify the `claims` field spec in the H
  task family so `[]` is derivable without guessing (candidate wording to be frozen
  in REVIEW-INBOX before any v6.6 row; gold untouched; fairness probe re-run at
  matched reps — the lift signature is the three arms flipping 0/3 -> >= 2/3).
- Baseline caveat stated in the pre-registration: the v6.4 raw baseline (0/3 on all
  arms, cadence-249 reps 25/26/27) used different rep seeds; the failure mode in that
  baseline was the same `ungrounded_claims` zero on basalt/codex (answer bytes in
  `../cadence-249/answers-*.jsonl`).
