# Bank defect fix v6.5 — H-ex6-01: the scenario now names the artifact the reference asks for

Published bank bytes v6.1–v6.4 are untouched. This is a new file
`benchmarks/hard/bank-hard-v6.5.json`, sha16 `cd29d6ac94dc3267`
(v6.4 `85a0cd0dd6fa1fab` stays immutable and keeps its registry row).

## The defect (published, open since 0.0.2.29)

`bank-defect-b04.md` recorded two defects found while attributing the 0.0.2.29 losses:
B-ex6-04 and H-ex6-01. B-ex6-04 was closed by v6.3 (year) + v6.4 (value form). H-ex6-01
was never fixed: the reference requires `requires: ["аудит-лог operations"]`, while the
shipped prompt never contains the string "аудит-лог" (it says "журнал действий"). The
frozen scorer's stem matcher (`_token_cover`, contract v6.2) cannot cross the
Latin/Cyrillic transliteration gap, so a faithful paraphrase scores 0.5 on
`requires_missing`.

## New evidence on the current line (cadence-249, bank v6.4, fresh seeds 25/26/27)

- H-ex6-01 strict-fails 3/3 for **all four arms**: contour 0.0.2.49 (behavior 2.48),
  bare basalt, ChatGPT-codex, Grok.
- Contour answers at r26/r27 ask for exactly the right artifact in other words
  ("Проверка системных логов на предмет операций удаления файлов"; "Проверка системных
  логов или истории команд ... auditd") and are zeroed on the unnameable atom.
- r25 additionally leaves `requires: []` — a genuine model gap the bank fix cannot heal.
- Per the standing rule, a contour stamp aimed at this cell would be UNMEASURED by
  construction; the fix belongs to the bank.

## The fix — exactly one field (the v6.3→v6.4 one-field-per-version doctrine)

`H-ex6-01.prompt`, scenario sentence extended by one clause (the fix proposed in
`bank-defect-b04.md`, adopted with its own wording):

- before: `... Но в твоём журнале действий этого нет.`
- after:  `... Но в твоём журнале действий этого нет; есть только аудит-лог operations.`

Gold untouched: `ref = {"unknown": "кто удалил бэкап", "ask": ["аудит-лог operations"]}`
byte-identical. `scripts/verify_bank_v65.py` PASS asserts: v6.4 identity sha16; changed
fields == `["H-ex6-01.prompt"]` over all 77 tasks; every `ref` and `seed` byte-identical;
the ask item is `_token_cover`-derivable from the prompt **only after** the fix; the JSON
field spec and the "Не приписывай себе действия" sentence are untouched on both sides.

## Probe and promotion rule

Frozen in REVIEW-INBOX 2026-11-07 17:35 CET **before any probe row** (this file's
prose was written after the rule, per clock order). Paired contour legs
`p64r28/29/30` (v6.4 control) vs `p65r28/29/30` (v6.5), both `PARB_GATE_VERSION=0.0.2.50`
(tooling identical; behavior 2.48 = the adopted line — the contour claims nothing),
`PARB_SUBSET=H-ex6-01`, matched fresh seeds from `plan_reps.py` reps 28/29/30. Promotion
to `working` iff (i) v6.5 legs >= 2/3 strict and v6.4 legs <= 1/3, and (ii) the raw-arm
fairness probe (bare basalt / ChatGPT-codex / Grok, reps 28/29/30, subset ws, frozen
contract v6.2) shows all three arms >= 2/3 — the owner's rule "a fixed gold must lift
the RAW arms". Failure of (ii) mapping to the `claims`-field trap is recorded as defect
2 and keeps v6.5 provisional (the v6.3 pattern).

## Tool-coverage note

`scripts/bank_derivability_audit.py` flags 37 candidate atoms over 16 tasks on BOTH
v6.4 and v6.5 — its scanner does not cover H `ask` items, so the mechanical census is
blind to this defect class. The scanner is not amended mid-probe; the coverage gap is
queued as a tooling follow-up (a scanner change would silently move the census number
that the changelog chain 39→38→37 pins).
