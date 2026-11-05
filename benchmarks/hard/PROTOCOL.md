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

## Hard bank versions

| bank | file | note |
|---|---|---|
| v5 | `bank-hard-v5.json` (archive) and historical `bank-hard.json` at commit of v5 audit | Contour **70/77** and the raw-arm scores in `SCOREBOARD.md` / `audit-20261105/` are **score under v5 checkers only**. Not evidence of contour-vs-bare superiority (see issue #15 / #5 comment 6661106383). |
| v6 | `bank-hard.json` (official gate path; draft, pre-run) + parallel `bank-hard-v6.json` | 77 unique tasks, one per template; dedup guard max pairwise ratio 0.575 on task content; C correct sets at varied positions (`c_position_dist_v6.json`, no leading-prefix leak, asserted at build); K lines==fields; semantic checkers in `harness/parb_check_v6.py` (no single-keyword pass/fail; E batteries executed in sandboxed subprocess); gold self-test 77/77 perfect via `scripts/gold_selftest_v6.py`; checker-keyword injection OFF by default (`STRATA_CHECKER_INJECT` opt-in reproduces v5 behaviour). Builder `harness/parb_bank_v6.py` computes every reference deterministically. No arm has run against v6 yet — refs/checkers/hashes first (issue #15). |

Dedup guard and position/line-count assertions run inside the builder (must exit 0); `MANIFEST.sha256` pins all v6 inputs.

### v6 dual artifacts (draft)
- Official gate path: `bank-hard.json` (cats A4 B4 C6 D9 E30 F3 G6 H4 I3 J4 K4) scored by `harness/parb_check.py` / `parb_loop.py`.
- Parallel redesign (not wired into gate_run): `bank-hard-v6.json` + `harness/parb_check_v6.py` + gold self-test; different cat mix.
- Keyword injection: `STRATA_CHECKER_INJECT` default OFF (`gate_v35_inject_off_test.py`).
- Dedup: `scripts/dedup_hard_bank.py` on `bank-hard.json`.


## Freeze rule enforcement (issue #15, Hermes)

The official hard-v5 gate remains: bank-hard.json (sha16 32953591ba2a6c51) + parb_check.py
(1c032ef022607d7b) + parb_loop.py (f5f5b78ab46a0f0c), byte-identical to the v5 audit tree.
A parallel draft redesigned these files in place (v5 rewording + reworked G/H/F/D checkers);
that work is preserved as `harness/parb_check_draft.py` for discussion, NOT as the frozen
gate: issue #15 requires v5 unchanged as history and v6 as a new bank. v6 = `bank-hard-v6.json`
+ `harness/parb_check_v6.py` (77 unique templates, gold self-test 77/77, MANIFEST.sha256).
Reviewers: dispute this split on issue #15 rather than by in-place edits.
