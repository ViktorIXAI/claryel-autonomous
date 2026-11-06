# Contour 0.0.2.29 — C coverage plumbing and a fail-closed stamp gate

Date: 2026-11-06 (CET). Bank: hard v6.1 (`bank-hard-v6.json` sha16 `9ec86dfca4a6f85f`,
generated workspace `f4553aab304f60d7`). Decided by: Hermes under the owner's standing
"go, decide and keep moving" instruction; published on `main`.

## What the v6.1 four-arm exposed

Category C lost `C-ex6-01/02/03` with `format_ok=True`, `content=0.0` and **no contour events**.
Reading the ledger and the bank together: v6.1 C tasks carry no top-level `n_cand`, so
`coverage_gate` short-circuited to a plain `ask_ladder` — no per-candidate verdicts, and the
returned text was either a 1500-token essay or bare letters. The frozen scorer then parses
`ОТВЕТ:` if present, otherwise **the last line of the answer**, so an essay ending with
"A, B, C, D" scored `got=[A,B,C,D]`. That is a contour-side contract failure, not a model failure.

## Change (gated at 2.29, historical behaviour preserved)

1. When `n_cand` is absent, the option letters are read from the task text itself
   (`^([A-H])[:\-)] ` option lines); the per-candidate ПОДХОД / НЕ ПОДХОД protocol then runs
   normally. Event `contour:v229_coverage_from_prompt:N`.
2. The picked set is emitted as the answer line the task demands: `ОТВЕТ: A,C` (or `ОТВЕТ: NONE`
   when the model itself rejected every option). Event `contour:v229_answer_line_contract`.
   Letters come only from the model's own verdicts — nothing is inferred, no checker keyword is
   injected, zero extra model tokens.
3. Same plumbing applied to the code-computed logic path (`logic_by_code`).

Contract: `harness/gate_v44_coverage_choice_test.py` (12 checks) imports the real `check_C_v6`
and asserts both directions: the contour's line scores 1.0/format_ok, and a prose answer is still
punished — the scorer is untouched.

## Measured on the full bank (one rep, same seeds, same bank)

`four-arm-v61` arm (0.0.2.28) → `full-229` arm (0.0.2.29): plain **61/71 → 63/71**, loop 5/6 → 5/6,
C **5/8 → 6/8** (`C-ex6-03` recovered exactly as designed: the essay had A and D in its reasoning
but only A in its last line), A 7/9 → 8/9 (resample), H swapped one cell each way (resample).
3 wins / 1 loss / 73 ties, exact sign test p=0.625 — the mechanism is proven by the event trace and
the targeted cell, the effect size is not established by one rep.

## Bookkeeping defect found and closed on the way

The first paired C-only arms were launched as `PARB_GATE_VERSION=0.0.2.228 / 0.0.2.229`. Those
parse as contour **2.228/2.229**, which turns on every shipped feature, exits 0, and writes
ledgers that look healthy: two identical behaviours under two labels, reported as a pair with zero
flips. `gate_versioning.registered_stamp()` now rejects any stamp newer than the newest release
and `gate_run` calls it at import — deliberately **outside** the legacy fallback `try/except` that
used to swallow the error — so an official arm dies before reserving the serve. The documented
tolerance of `behavior_tuple` (a far-future stamp is a reporting release and tops out at the newest
feature) is kept and asserted in the same test (`gate_v45_stamp_guard_test.py`, 12 checks,
including a subprocess check that `import gate_run` exits non-zero on a bad stamp). The void
`results-cpair228/229.jsonl` files are kept in the workspace as evidence, recorded as void in the
inbox, and are not published as a measurement.

## Consequence for the ladder

`scripts/ladder_v6.py` now emits two sections: bank v6 (full-216…full-228) and bank v6.1
(`four-arm-v61` contour 0.0.2.28 = 61/71, `full-229` = 63/71). Same task ids, different task text —
the script refuses to put them in one table, and the v6.1 section prints the raw-arm reference
(bare basalt 56, Grok 54, ChatGPT 50) next to it.
