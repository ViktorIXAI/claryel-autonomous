# Scoring protocol (hard bank family)

Three scoring modes are kept permanently distinct. Reports must name the
mode; historical scores are never silently re-judged — a contract change
requires a new bank/scorer version plus a migration note.

| mode | format required? | category D judged by | applies to |
|---|---|---|---|
| `strict_loop` | yes | agent-loop scorer (`parb_loop.check_D_loop` for v5; `parb_check_v6.check_D_loop_v6` for v6): requires structured step traces | contour arm (its answers ARE agent loops); NOT fair for single-shot chat arms |
| `strict_plain` | yes | plain plan scorer (`parb_check.check_D` / `parb_check_v6.check_D_plain_v6`) on final text | OFFICIAL mode for single-shot (raw) arms |
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
| v5 | `bank-hard-v5.json` (archive) and historical `bank-hard.json` at commit of v5 audit | **IMMUTABLE.** Contour **70/77** and the raw-arm scores in `SCOREBOARD.md` / `audit-20261105/` are **score under v5 checkers only**. Pins: `MANIFEST.v5.sha256` (`bank-hard.json` / `bank-hard-v5.json` sha16 `32953591ba2a6c51`, `parb_check.py` `1c032ef022607d7b`, `parb_loop.py` `f5f5b78ab46a0f0c`). Not evidence of contour-vs-bare superiority (issue #15 / #5 comment 6661106383). |
| v6 | **`bank-hard-v6.json` only** + **`harness/parb_check_v6.py`** | Official v6 gate artifacts. 77 unique tasks (A9 B7 C8 D9 E10 F6 G6 H5 I6 J7 K4). Semantic/structural checkers (no single-keyword pass/fail). Category **G is short-context** (`[SHORT-CONTEXT]` docs; score only `conflict`/`clauses`/`values`). Category **E** batteries execute **only** via `e_sandbox.run_docker` (fail-closed if docker unavailable; never bare subprocess). Gold self-test 77/77 via `scripts/gold_selftest_v6.py`. Builder `harness/parb_bank_v6.py`. Pins: `MANIFEST.v6.sha256` (bank + scorer + builder + shim + gold + suites + sandbox). No arm has run against v6 yet — refs/checkers/hashes first (issue #15). |

Dedup guard and position/line-count assertions run inside the builder (must exit 0); `MANIFEST.v6.sha256` pins all v6 inputs. `harness/verify_manifest.py` must PASS; a deliberately altered pinned file must FAIL (negative test).

### v6 artifacts (issue #15 P0)
- Gate path: `benchmarks/hard/bank-hard-v6.json` scored by `harness/parb_check_v6.py`.
- Sandbox: `harness/e_sandbox.py` (`run_docker` default for E; `--network=none`, pids-limit, read-only).
- Workspace shim: `scripts/build_hard_v6_ws.py` writes `check_v6_shim.py` → `parb_check_v6`.
- Keyword injection: `STRATA_CHECKER_INJECT` default OFF (`gate_v35_inject_off_test.py`).
- Adversarial suite: `scripts/semantic_suite_v6.py` (C tokenized IDs; G field-only; H structured uncertainty; D-loop consume-once; E sandbox negatives).
- Dry-run (no models): `scripts/dry_run_same_scorer_v6.py` — one v6 scorer import across 4 arms; path+sha256 per arm per category (11 + D plain/D loop).

## Freeze rule enforcement (issue #15)

The official hard-**v5** gate remains immutable: `bank-hard.json` (sha16 `32953591ba2a6c51`) + `parb_check.py` (`1c032ef022607d7b`) + `parb_loop.py` (`f5f5b78ab46a0f0c`), byte-identical to the v5 audit tree. Do not mutate these files in place.

**v6** is a new bank: `bank-hard-v6.json` + `parb_check_v6.py` only. Reviewers: dispute this split on issue #15 rather than by in-place edits of v5.
