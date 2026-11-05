# Scoring protocol (hard bank family)

Three scoring modes are kept permanently distinct. Reports must name the
mode; historical scores are never silently re-judged — a contract change
requires a new bank/scorer version plus a migration note.

| mode | format required? | category D judged by | applies to |
|---|---|---|---|
| `strict_loop` | yes | agent-loop scorer (`parb_loop.check_D_loop`): requires structured tool-call step traces | contour arm (its answers ARE agent loops); NOT fair for single-shot chat arms |
| `strict_plain` | yes | plain plan scorer (`parb_check.check_D`) on final text | OFFICIAL mode for single-shot (raw) arms |
| `content_only` | no | plain | auditor variant only; surfaced to reconcile external recounts, never used for our own claims |

Bank and scorer revisions:
- bank v-next -> v5: E `valid_price` spec reworded unambiguous (4 hard task
  prompts; ids stable); affected raw arms re-run on exactly those tasks.
- scorer `NEG_CLAIM` H guard added (v33 contract test). A/B rescore on the
  231 published raw answers: zero score change (recorded 2026-11-05).
- frozen hashes for the current audit: see `audit-20261105/README.md`.

Regression pins (verified by `scripts/audit_hard_v5.py` at the frozen
commit): raw `strict_plain` = 45/54/56, `strict_loop` = 43/52/56,
`content_only` = 45/58/56; contour recorded 70/77 with non-D cells
independently re-scorable and category D reported as not-independently
re-scorable unless a step-trace archive exists.
