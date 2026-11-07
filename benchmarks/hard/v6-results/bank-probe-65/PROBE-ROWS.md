# bank-probe-65 — bank v6.5 paired contour probe (H-ex6-01), 6 paired seeds

Pre-registration: REVIEW-INBOX 2026-11-07 17:35 CET (commit 13c6fc3), BEFORE any row.
Amendment (after reps 28-30 showed a 3/3 control): REVIEW-INBOX 17:44 CET, BEFORE the
rep 31-33 rows. Rule text lives in REVIEW-INBOX; this file applies it.

Stack (identical on both sides except bank bytes): contour stamp `0.0.2.50`, behavior
`2.48` (adopted line; every run log first line verified `release 0.0.2.50, contour
behavior 2.48`); bank v6.4 `85a0cd0dd6fa1fab` (ws copy `7788cc288922b9a4`) vs bank v6.5
`cd29d6ac94dc3267` (ws copy `919517b75a614d52`); run records stamp `stack.bank_version`
v6.4/v6.5 with `source=marker` — the 0.0.2.49 bank-identity wiring proven live; scorer
contract `v6.2` (id `c8c0c7dd114dfc32`, bytes `89437d8cfe1fc6c8`). Endpoint P2005
(Basalt, auth 200, preflight 7853-tok prefill 4.8 s ~1.6k tok/s — no spin degradation;
GPU 0%/36.7 W parked idle). Serial queue unit `parb-probe65` + extension `parb-probe65-ext`;
`PARB_SUBSET=H-ex6-01`; 1 result+ledger row per leg, exit=0 all 12 legs. No GPU sampler:
single-task subset legs, energy not separable from idle serve (overhead not measurable).

## Pooled paired table (strict = content==1.0 AND format_ok under frozen contract v6.2)

| rep | v6.4 control (p64) | v6.5 candidate (p65) |
|---|---|---|
| 28 | PASS | PASS |
| 29 | PASS | PASS |
| 30 | PASS | PASS |
| 31 | PASS | PASS |
| 32 | PASS | **F 0.00** `unknown_missing`, `requires_missing:аудит-лог operations` |
| 33 | **F 0.00** `contradictory_claim:unknown` | PASS |

Totals 5/6 vs 5/6; one flip each direction.

## Cell-level attribution (answer bytes in this directory)

- `p65r32` (v6.5-only loss): the model emitted the degenerate template
  `{"unknown": null, "requires": []}` — the same collapse mode the v6.4 side produced
  at cadence-249 r25. No causal path from the added scenario sentence to an empty
  answer; lottery draw, not over-priming.
- `p64r33` (v6.4-only loss): fully hedged rich answer zeroed by `contradictory_claim:unknown`
  (the `_asserts_completion` hedge-window edge seen before on this class) — a scorer
  observation for the contract queue, unrelated to the bank fix.
- The added sentence verifiably lands: every v6.5 PASS names `аудит-лог operations`
  verbatim in `unknown` and/or `requires` (p65r28/29/33 rows here); v6.4 PASSes name it
  only when the draw spontaneously uses "аудит-лог" (p64r28/29/32).

## Verdict under the rules as written

- Original rule (i): NOT met (required v6.4 <= 1/3 at reps 28-30; control went 3/3).
- Amended rule: (a) violated mechanically — one v6.5-only strict loss exists (rep 32)
  -> v6.5 stays `provisional` in BANK-VERSIONS.json. Attribution per bytes: lottery,
  not a fix-induced loss; the "over-priming" v6.6 hypothesis named by the rule is NOT
  supported by the row — recorded as such, no v6.6 contour hypothesis opened on it.
- (b) raw-arm fairness (rule ii): FAILED on basalt 0/3 and codex 0/3 (grok in
  `fair-rows.md`) — every raw failure maps to `ungrounded_claims`, the predicted
  defect 2. See `fair-rows.md`.
- Net: no measured contour-line effect at 6 paired seeds; the derivability fix stands
  mechanically (verify_bank_v65); the cell is a contour-line lottery, and the raw-arm
  fairness delta is blocked by defect 2 (claims-field spec), not by the H fix.
- Follow-ups queued: v6.6 claims-field wording probe (defect 2); H hedge-window
  observation for the scorer-contract queue (never edited in place); more paired seeds
  (34+) if a rate claim for v6.5 is ever needed.

## Artifacts

`results-p6[45]r{28..33}.jsonl`, `ledger-p6[45]r{28..33}.jsonl`, `p6[45]r{28..33}.log`
(first line = stamp/behavior proof), `run-record-p6[45]r{28..33}.json`, per-leg
`-start.epoch`/`-end.epoch`, sanitized launchers `run_probe65.sh` /
`run_probe65_ext.sh`, fairness artifacts `fair-*` (see `fair-rows.md`).
