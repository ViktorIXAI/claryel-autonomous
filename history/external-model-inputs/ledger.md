# External AI model input ledger

This project is less than two days old at the time this policy starts. The
honest record of what came from where starts here and becomes stricter going
forward, not retroactive fiction.

## Cutoff and policy

- **Cutoff: 2026-11-01 12:00 CET.**
- **Before the cutoff:** some task specifications given to the lab agent
  contained verbatim copy-pasted text from ChatGPT (and later from other
  external assistants). The exact boundaries of that text inside the pasted
  specifications were not recorded and cannot be reconstructed reliably.
  Everything published before this cutoff carries that provenance caveat.
- **From the cutoff onward:** every external AI contribution — specification
  drafts, audits, reviews, translations, second opinions — is logged in this
  file with: date/time, model/system used (as identified), purpose, and the
  SHA-256 of the exact text handed to the lab agent. The lab agent does not
  silently re-word external instructions; it records them first.
- Outbound use of cloud models *by the lab itself* remains default-deny
  (`benchmarks/privacy-boundary/gateway.py`); this ledger concerns human-
  mediated use of external assistants around the project, not lab traffic.

## Entries

### EXT-000 (acknowledgment of the pre-cutoff period)

- Period: 2026-10-30 … 2026-11-01 12:00 CET
- System: ChatGPT (OpenAI), later others
- Role: the owner drafted several task specifications by copy-pasting
  generated text, including the "independent evaluation" audit tasks of
  2026-11-01. The agent received these as owner specifications.
- Integrity note: intermediate drafts were not preserved; per-entry hashes for
  this period are unavailable (`not_recorded`). This is stated as a limitation
  in `docs/limitations.md`, not papered over.

### EXT-001 (external review published verbatim)

- Date: 2026-11-01 (afternoon CET)
- System: external conversational AI assistant used by the owner to produce a
  critical review of the then-public repository; the owner pasted the review
  text to the agent verbatim.
- Purpose: independent-position critique (benchmark overfitting risk,
  autonomy-evidence strength, positioning tone).
- Published as: `results/external-review-2026-11-01.md` (full English
  translation in repo). The verbatim Russian original now lives in the
  release asset `ru-source-records-2026-11-01.tar.zst` (removed from the
  git tree by the English-first language pass, unmodified inside the asset).
- SHA-256 (16-hex) of the review text as received: `c26848ffd40c75ce`

### EXT-002 (positioning text)

- Date: 2026-11-01
- System: same external review; the suggested positioning paragraph was
  adopted into README nearly verbatim.
- SHA-256 (16-hex) of the adopted English paragraph: `d84091ccb3d652d0`
  (stored verbatim: `history/external-model-inputs/ext-002-positioning-2026-11-01.txt`)

### EXT-003 (second critical audit, same day)

- Date: 2026-11-01 (evening CET)
- System: external conversational AI assistant used by the owner; the audit
  text was pasted to the agent verbatim.
- Purpose: 10-criterion re-audit of the updated public repo (7.0/10); named
  three scientific gaps (independent scorer dissent, holdout G degradation,
  missing budget-matched simple baselines) and four polish defects.
- Published as: `results/external-review-2026-11-01.md` § "Second audit"
  (English); English translation of the full audit:
  `history/external-model-inputs/ext-003-audit-2026-11-01.md`.
- SHA-256 of the audit text as received (Russian):
  `e5bd7fe19035258c3b31c73a57079d792529a032f5693e54e860e2c6be643b7f`
  (verbatim original archived in release asset `ext-records-2026-11-01-v2.tar.zst`).
- Actions taken in response (same day): budget-matched simple-baselines
  experiment run and published (`results/baselines.md`); independent scorer
  v2 with ~90% coverage (`results/independent-scorer-v2.md`); holdout-G
  generator bug found, fixed, pilot re-run; README quickstart fixed;
  privacy-boundary README corrected; CI failure history documented.
