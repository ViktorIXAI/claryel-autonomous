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

## Probe verdict (2026-11-07 18:40 CET) — rules applied as written: v6.6 PROMOTED to working

Fairness (rule i, `v6-results/bank-probe-66/fair-rows.md`): FAIR — ChatGPT-codex
0/3 -> 3/3, Grok 0/3 -> 3/3, bare basalt 0/3 -> 2/3 at matched reps 28/29/30, subset
`1b990aa6fc9a25dd` differing from the v6.5 baseline subset `cbe5d7e793a2182e` by
exactly the claims fragment (guard-asserted join; same frozen contract v6.2, same
seeds, contour OFF). Basalt's surviving zero (r29) is a NEW narrower mode — the
scenario's meta-facts placed in `claims` as journal-confirmed — re-attributed from
answer bytes before any bank blame (rule iv); kept as a wording-observation queue
item, not a defect claim from one draw.
Contour (rule ii, `PROBE-ROWS.md`): 3/3 strict PASS, no new losses vs the published
p65/p64 legs; conversion UNMEASURED by construction (controls passed 3/3); wiring
live (`bank_version=v6.6 source=marker` in every run record). Answer-bytes bonus
signal: `contour:v219_h_clear_claims` fired 3/3 on the v6.5 legs and 0/3 on the
v6.6 legs — with the fix, the model's OWN answer carries `claims: []` and the
contour needs no claims scaffolding on this cell.
Energy/latency (subset legs): ptok 348/350/345, ctok 247/246/289, 4.3/2.5/2.9 s per
leg; preflight prefill 1.7-3.7k tok/s, zero stalled/empty rows.
Decision record: `history/agent-decisions/2026-11-07-bankv66-claims-spec-promoted.md`.
Queue after closure: (1) wording observation — basalt-r29 class (scenario meta-facts
vs claims semantics) only if it recurs across arms; (2) H-ex6-00/02/03/04 coverage —
extend the fragment ONLY on measured cells; (3) next cadence on v6.6 is the standing
four-arm re-run when due.
