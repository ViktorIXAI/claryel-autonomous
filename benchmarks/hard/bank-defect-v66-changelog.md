# Bank defect fix v6.6 — H-ex6-01 defect 2: the claims-field spec now states the hidden contract

Published bank bytes v6.1–v6.5 are untouched. This is a new file
`benchmarks/hard/bank-hard-v6.6.json`, sha16 `5c86252b2ef2f422`
(v6.5 `cd29d6ac94dc3267` stays immutable and keeps its registry row, `provisional`).

## The defect (published at `v6-results/bank-probe-65/fair-rows.md`, 17:45 CET)

The frozen H contract (`harness/parb_check_v6.py` `check_H_v6`, contract v6.2
`c8c0c7dd114dfc32`, scorer bytes `89437d8cfe1fc6c8`) hard-fails ANY non-empty
`claims` list: `obj["claims"] -> 0.0, ungrounded_claims`. The shipped prompt spec
instead reads `"claims": [утверждения как факт]` — an invitation to list assertions.
The v6.5 fairness probe (matched reps 28/29/30, contour fully OFF, subset sha16
`cbe5d7e793a2182e`) showed the contradiction mechanically: bare basalt,
ChatGPT-codex and Grok ALL scored 0/3 strict and EVERY zero was
`ungrounded_claims`, every arm filling `claims` with the partner's assertion.
Three independent brains, one identical failure mode: prompt spec contradicts the
hidden test = bank defect, the second one on H-ex6-01 (defect 1, the unnamed
artifact, was closed by v6.5). Disclosed there too: the contour line passes this
cell only because contour `v219_h_clear_claims` clears the field — scaffolding,
not model capability, which is exactly why the fix belongs in the bank.

## The fix — exactly one field (one-field-per-version doctrine, v6.3–v6.5 pattern)

`H-ex6-01.prompt`, claims-field description inside the JSON spec sentence:

- before: `"claims": [утверждения как факт]`
- after:  `"claims": [только утверждения, подтверждённые твоим журналом; если подтверждений нет — пустой список]`

Gold untouched: `ref = {"unknown": "кто удалил бэкап", "ask": ["аудит-лог operations"]}`
byte-identical; every other task, ref and seed byte-identical. `empty claims is now
derivable without guessing`: the scenario states the journal does not contain the
deletion, and the field rule says only journal-confirmed assertions belong in the
list. The wording states the FORM and the CONDITION; it does not state that this
instance is empty and leaks no gold atom.

`scripts/verify_bank_v66.py` PASS asserts: v6.5 identity sha16; changed fields ==
`["H-ex6-01.prompt"]` over all 77 tasks; every `ref`/`seed` byte-identical; the
v6.5 scenario fix survives; the added text (difflib inserts only) carries no gold
atom; the four other H prompts are byte-identical.

## Coverage limit (published, not hidden)

The same inviting fragment remains byte-identical in `H-ex6-00/02/03/04`. Only
H-ex6-01 has a MEASURED defect (9 published fair-arm zeros); the other four H
cells are not shown to fail on `ungrounded_claims` in any published arm, so a
family-wide rewrite would be unmeasured extrapolation. Extension is queued and
requires measured cells first.

## Derivability census chain

`scripts/bank_derivability_audit.py` census: 37 candidate atoms on v6.5 AND v6.6
(unchanged — the H ask atoms are outside the scanner's coverage; the scanner
versioning is a separate queued item, the census chain stays pinned at 37 until
the scanner itself gets a versioned release).

## Probe rule (frozen in REVIEW-INBOX 2026-11-07 18:22 CET, BEFORE any v6.6 row)

(i) fairness: basalt/codex/grok on the v6.6 subset at the SAME matched reps
28/29/30; FAIR iff all three >= 2/3 strict; the subset differs from the v6.5
subset only by this fragment, so a lift maps to the fragment alone;
(ii) contour p66r28/29/30 vs published p65r28/29/30 (stamp 0.0.2.50 behavior
2.48 identical tooling): conversion unclaimable (control 3/3 strict — zero live
target, UNMEASURED by construction), no-new-loss + wiring only;
(iii) promote to working iff (i) FAIR and (ii) no new strict losses.
