# 2026-11-07 — bank v6.4 becomes the working hard bank; B-ex6-04 defect closed (v6.3 stays provisional)

Decision by the autonomous measurement agent under the owner's 2026-11-07 delegation
("decisions are yours, keep improving the tests and the scoring system, version every element").

## What was decided
1. `bank-hard-v6.3.json` (sha16 `73f7a04d57473545`) and `bank-hard-v6.4.json`
   (sha16 `85a0cd0dd6fa1fab`) are published as NEW bank versions; v6.2
   (`3c866ea7daae611c`) and all older published bytes stay byte-frozen.
2. `B-ex6-04` was carrying TWO independent bank defects (unstated gold year; unspecified
   value-form for `penalty_per_week`), each fixed in exactly one prompt field in one version.
3. Probe verdicts under pre-registered rules: v6.3 0/3 strict => PROVISIONAL (condition (i)
   failed, rule applied as written even though the year fix provably worked); v6.4 3/3 strict
   against 0/3 fresh controls on v6.2 AND v6.3 at identical sp1 seeds => **v6.4 is the WORKING
   hard bank**, the cell leaves the defect queue.
4. The mechanical guard that predicted the second defect before it was probed
   (`scripts/bank_derivability_audit.py`, `type_form` check) is published as standing tooling:
   every future bank version runs the derivability census before arms are paid for.
5. Fairness gate for the new bank (owner rule: a fixed gold must lift the RAW arms): a
   pre-registered raw-arm probe (bare basalt / ChatGPT-codex / Grok, reps 22/23/24,
   byte-identical B-ex6-04 task object from v6.4) decides the cell is FAIR, not just
   contour-passable. Rule frozen in REVIEW-INBOX 12:56 CET before any fairness row existed.

## Why
- 15 published line rows (contour 2.45-2.48) strict-failed the cell, and the raw arms split on
  luck (basalt 3/3 by year-guess, codex/grok 0/3 saying the year is absent) — the signature of an
  unstated gold atom, not a model gap.
- No contour stamp was aimed at the cell (correct: a stamp aimed at a defective cell is
  UNMEASURED by construction).
- The v6.3 verdict shows why pre-registration matters: an intermediate fix that provably moved
  one field still failed the frozen rule and was labeled provisional rather than quietly bundled.

## Evidence artifacts
- `benchmarks/hard/v6-results/bank-probe-634/` — 9 arms (p62r22-24, p63r22-24, p64r22-24):
  results/ledger/run-records/logs/epochs, sanitized launchers, `PROBE-ROWS.md`.
- `benchmarks/hard/bank-defect-v63-v64-changelog.md` — every changed byte.
- `scripts/build_bank_v6{3,4}.py`, `scripts/verify_bank_v6{3,4}.py`,
  `scripts/bank_derivability_audit.py`.
- `benchmarks/hard/REVIEW-INBOX.md` entries 12:16 / 12:20 / 12:56 CET (host clock).
- Known provenance gap, queued: run records stamp `bank_sha16` but `bank_version` label is empty;
  next tooling release has the builder write a bank-version marker the runner reads.
