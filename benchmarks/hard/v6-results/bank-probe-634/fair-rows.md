# raw-arm fairness probe rows (bank v6.4, B-ex6-04, reps 22/23/24)

Rule pre-registered 2026-11-07 12:56 CET in REVIEW-INBOX before any row. Contour is OFF here
(raw_v6 protocol: one shot, no fixers). ws bank.json = byte-identical B-ex6-04 object from
`bank-hard-v6.4.json` (full-file sha16 `85a0cd0dd6fa1fab`, subset ws sha16 `abf6f00bd3476078`,
byte-identity guard in the build step). Scorer: frozen contract v6.2 `c8c0c7dd114dfc32`
(harness/parb_check_v6.py `89437d8cfe1fc6c8` — asserted at scoring time), gold from the FULL v6.4
file, strict = `content == 1.0 and format_ok`. Transport disclosure grep (bank/gold/paths): zero hits.

| arm | rep | content | format_ok | strict | model | cli | s |
|---|---|---|---|---|---|---|---|
| basalt | 22 | 1.0 | True | PASS | qwen3.8-flash-next-iq3_s-basalt | direct HTTP temp 0.7 | 4.5 |
| basalt | 23 | 1.0 | True | PASS | qwen3.8-flash-next-iq3_s-basalt | direct HTTP temp 0.7 | 2.4 |
| basalt | 24 | 1.0 | True | PASS | qwen3.8-flash-next-iq3_s-basalt | direct HTTP temp 0.7 | 2.4 |
| codex | 22 | 1.0 | True | PASS | gpt-6.1-sol | codex codex-cli 0.166.0 | 10.9 |
| codex | 23 | 1.0 | True | PASS | gpt-6.1-sol | codex codex-cli 0.166.0 | 7.1 |
| codex | 24 | 1.0 | True | PASS | gpt-6.1-sol | codex codex-cli 0.166.0 | 8.9 |
| grok | 22 | 1.0 | True | PASS | grok-4.7 | hermes Hermes Agent v0.23.0+495.gcb71f75.dirty (2026.9.24) · upstream cb71f750 toolsets off | 8.4 |
| grok | 23 | 1.0 | True | PASS | grok-4.7 | hermes Hermes Agent v0.23.0+495.gcb71f75.dirty (2026.9.24) · upstream cb71f750 toolsets off | 5.4 |
| grok | 24 | 1.0 | True | PASS | grok-4.7 | hermes Hermes Agent v0.23.0+495.gcb71f75.dirty (2026.9.24) · upstream cb71f750 toolsets off | 6.4 |

strict by arm (of 3): basalt 3/3, codex 3/3, grok 3/3. v6.2 baselines (cadence-246, reps 16/17/18):
basalt 3/3 (year guessed from priors), codex 0/3, grok 0/3 (both said the year is not stated).

**FAIRNESS VERDICT: FAIR** — the frozen rule (all three raw arms >=2/3) holds: codex and grok
flip 0/3 -> 3/3 proving the v6.4 prompt states the contract, and basalt 3/3 -> 3/3 shows no
regression for the arm that had already guessed it. B-ex6-04 is closed as a bank defect fully
fixed at the bank level; nothing on the contour line is claimed for it.
