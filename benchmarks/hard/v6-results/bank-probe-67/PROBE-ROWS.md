# bank-probe-67 — v6.7 fairness + no-new-loss probe (rule frozen BEFORE rows: REVIEW-INBOX 2026-11-08 11:33 CET)

Bank under test: v6.7 `b4464127dc5b5b97` (subset ws `724e9a0150ce45f5`, guard-asserted
byte-identical to the published file for all 6 fixed tasks). Contour legs: stamp
`0.0.2.56` (behavior 2.56), matched seeds reps 64/65/66 (sp1 `sha256(task|rep)[:8]%999983`),
P2005 Basalt idle, harness = repo HEAD 988113f on BOTH sides (control ws `parb-b66ctl-contour`
bank v6.6 ws copy `590503cf1701a6ce`; candidate ws `parb-b67full-contour` bank v6.7 ws copy
`7e099f6a49ee715b`), fresh artifact names per rid, `queue.log` exit codes 0 across all six legs.
No GPU sampler (subset probe, minutes of endpoint time; paired-telemetry rule is for full pairs).

## (a) RAW fairness — arms contour-OFF on the v6.7 subset, reps 64/65/66

strict = `content==1.0 and format_ok`, scorer contract v6.2 (routing `CK.check`, raw scoreboard
rule "plain plan scorer, format strict"). Gate: every arm >= 2/3 on EVERY fixed task.

| arm | C-ex6-01 | F-ex6-01 | H-ex6-00 | H-ex6-03 | K-ex6-00 | K-ex6-01 |
|---|---|---|---|---|---|---|
| basalt | 3/3 | 3/3 | 3/3 | 2/3 (unknown_missing x1 — English-language unknown) | 3/3 | 3/3 |
| codex  | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| grok   | 3/3 | 3/3 | 3/3 | **1/3** (ungrounded_claims x2) | 3/3 | 3/3 |

**FAIRNESS: NOT FAIR** — grok 1/3 on H-ex6-03. The two losing draws put SESSION-STATE
statements into `claims` («В этой сессии есть только текущий запрос; сообщений друга в
контексте нет…») — the model treats its own context as confirming data, and the frozen
contract hard-zeros ANY non-empty `claims`. The confirmation-conditional wording is not yet
strong enough for this brain on this scenario; the wording iteration (claims never about
the session itself) is queued for a v6.7b candidate. The four K/F cells and C lifted 0/3->3/3
on every arm — the value-form and gold fixes work exactly as intended.

### (a2) C-ex6-01 offline fairness from saved cadence-255 bytes (prompt bytes unchanged)

basalt 3/3, codex 3/3, grok 3/3 strict under the v6.7 gold — zero new calls; the saved
unanimous `C,F` answers now score exactly.

## (b) contour no-new-loss — c66r64-66 (bank v6.6) vs c67r64-66 (bank v6.7), matched reps

| task | v6.6 passes | v6.7 passes | notes |
|---|---|---|---|
| C-ex6-01 | 3/3 | 0/3 | all three candidate draws answered `B,C,F` -> `set_mismatch` vs the new gold |
| F-ex6-01 | 3/3 | 2/3 | rep64 `no_json` (one collapsed draw, model-side lottery) |
| H-ex6-00 | 3/3 | 3/3 | clean |
| H-ex6-03 | 3/3 | 3/3 | clean |
| K-ex6-00 | 3/3 | 3/3 | clean |
| K-ex6-01 | 3/3 | 3/3 | clean |

Totals 18/18 -> 14/18: **NO-NEW-LOSS: DIRTY** per the frozen text (the C-ex6-01 flip clause
allows the direction but the totals floor still moves; the F `no_json` is a new note family
for that task). The C flip is *informatively asymmetric*: with the contour OFF, the SAME
brain answers `C,F` unanimously (18/18 raw draws across two probe generations), while the
contour legs included B in 3/3 fresh draws — the scaffolding's "choose ПОДХОДЯЩИЕ варианты"
coverage path steers toward the safety-sounding reversed statement. That is published as a
finding (candidate contour target on the fair gold), not used to excuse the guard: the frozen
rule is applied as written.

## VERDICT (frozen rule as written)

**v6.7 stays PROVISIONAL.** No promotion (a fails: grok H-ex6-03 1/3; b fails: totals floor +
F note family). Numbers published exactly as measured; no contour hypothesis is opened on the
K/F/H cells the raw bytes already refuted (they are FAIR now). Next iteration (queued):
claims-wording iteration for the session-state class on H-ex6-00/H-ex6-03 -> fresh probe at
reps 67/68/69 with fresh artifact names. No DIGEST percent row (subset probe; run_digest
fail-close by design; bank-wide percent context stays the map-256 row: 97.4% on v6.6).
