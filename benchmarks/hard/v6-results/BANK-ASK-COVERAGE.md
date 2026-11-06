# Gold-ask coverage probe (bank vs prompt, scorer's own coverage rule)

Bank: `bank-hard-v6.json`. For every task, each gold `ask` item is tested against the prompt with the same `_token_cover` the scorer uses. Flagged items are **candidates**: some are legitimately inferable (computed sums, paraphrases), so the row is a question to answer, not a verdict.

| task | cat | gold ask item | covered by prompt? | tokens missing |
|---|---|---|---|---|
| K-ex6-01 | K | hosting | NO | hosting |
| H-ex6-01 | H | аудит-лог operations | NO | аудит-лог, operations |
| I-ex6-02 | I | ["45m", 2700] | NO | ["45m", 2700] |
| I-ex6-02 | I | ["90m", 5400] | NO | ["90m", 5400] |
| I-ex6-02 | I | ["2h", 7200] | NO | ["2h", 7200] |
| I-ex6-03 | I | ["us", 312.0] | NO | 312.0] |
| I-ex6-03 | I | ["eu", 200.75] | NO | 200.75] |

Checked 49 gold ask items over 77 tasks; 7 items flagged as not token-covered by the prompt.

Next step for each flagged cell, in order of honesty: (1) show the derivation from the prompt — if it exists, the cell is fine and the flag is a false positive; (2) if no derivation exists, record it as a bank defect with the missing evidence, do not paper it over with a gate; (3) never edit a frozen bank to hide the flag — publish a new bank version with a new hash.

## Adjudication of each flagged row (06.11 05:15 CET)

| task | gold ask item | verdict | why |
|---|---|---|---|
| K-ex6-01 | `hosting` | **candidate scorer defect** | the prompt is Russian ("услуга хостинга"), the gold ask token is English. Coverage is surface-token based, so a correct Russian answer can miss this component while a code-switched answer scores it. The category is exactly the contract-precision category, so this needs a language-normalized coverage rule or a bilingual gold list — decided by a new bank version, never by editing the frozen one. |
| H-ex6-01 | `аудит-лог operations` | **confirmed bank defect** | the prompt never names an audit-log artifact; already recorded in `bank-defect-b04.md`. Not repaired by any gate. |
| I-ex6-02 | `["45m", 2700]`, `["90m", 5400]`, `["2h", 7200]` | **false positive (derived values)** | these are unit conversions the task asks the model to compute; the numbers are not supposed to appear in the prompt. |
| I-ex6-03 | `["us", 312.0]`, `["eu", 200.75]` | **false positive (derived values)** | computed currency totals from rates the prompt does give. |

Net effect on the frozen bank: one confirmed unreachable cell (H-ex6-01) and one likely language-
mismatch cell (K-ex6-01), against 49 gold ask items checked. Both count equally against every arm, and
both stay in the scoreboards; the fix, when it comes, is a new bank version with a new hash, not an
edit of the old one.
