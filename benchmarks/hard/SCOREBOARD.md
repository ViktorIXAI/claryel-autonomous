# Hard-bank scoreboard

> **Label:** the 70/77 contour figure below is **score under v5 checkers only** (bank archive `bank-hard-v5.json`). Do not cite it as contour-vs-bare superiority. See PROTOCOL.md and issue #15.


Current authoritative table lives in `audit-20261105/README.md`
(final hard-v5, commit-pinned, reproducible via `scripts/audit_hard_v5.py`).

## Hard v5, rep0 (FINAL, 2026-11-05 audit)


> **WATERMARK (owner retraction 2026-11-05):** these totals are historical outputs of the flawed v5 checkers — **INVALID FOR RANKING** (issue #15 adjudication contract, point 6i). No comparative-superiority claim may be drawn from them.

| arm | strict (official) |
|---|---|
| contour 0.0.2.12 + Basalt (local) | 70/77 = 90.9% |
| gpt-6.1-sol xhigh (raw) | 56/77 = 72.7% |
| grok-4.7 (raw) | 54/77 = 70.1% |
| basalt raw | 45/77 = 58.4% |

## History (PRELIMINARY — superseded by the audit)

Scoreboards written only in commit messages before 2026-11-05 were
provisional: they applied the contour loop-D scorer to single-shot arms
(-2 basalt, -2 grok at worst) and one entry claimed H-guard point gains
that an A/B rescore showed to be zero. Both corrected in
`audit-20261105/README.md`; nothing was changed in the answers themselves.

| era | contour 2.12 | codex | grok | basalt raw |
|---|---|---|---|---|
| bank v-next (G docs missing) | invalid G rows | invalid G rows | invalid G rows | invalid G rows |
| bank v-next fixed | 67/77 | 53/77 | 53/77 | 46/77 |
| bank v5 (final) | 70/77 | 56/77 | 54/77 | 45/77 |
