# contour ladder on hard bank v6 (rep0, identical gseeds)

Bank source of truth `benchmarks/hard/bank-hard-v6.json` sha16 `9ec86dfca4a6f85f`. Every arm in
this ladder ran against the generated workspace copy `bank.json` (re-serialized, therefore a
different hash): sha16 `f52acbd15b3271e7`, the identity pinned in `v6-results/README.md` and
printed by `scripts/build_hard_v6_ws.py` at build time. Bank **v6.1** (J defect fixes, see
`BANK-V61.md`) re-pins the workspace to a new hash and is NOT part of this ladder.

Recomputed by `scripts/ladder_v6.py` from the **published ledgers** (ledger rows carry
`content`/`format_ok`) — not copied from run writeups. Every row also has its per-task
answer bytes in the same directory (`results-*.jsonl`), so any cell can be re-scored.

| stamp | plain strict /71 | loop strict /6 | rows | per-category strict (77 incl. loop) | what the stamp changed |
|---|---|---|---|---|---|
| 0.0.2.16 | **39/71** | 4/6 | 77 | A5/9 B2/7 C6/8 D4/9 E10/10 F3/6 G5/6 H2/5 I5/6 J0/7 K1/4 | loop-v2 drive: protocol re-ask, in-place gate_rejected, salvage the model's own answer |
| 0.0.2.17 | **41/71** | 4/6 | 77 | A4/9 B5/7 C5/8 D4/9 E10/10 F2/6 G5/6 H1/5 I5/6 J3/7 K1/4 | deterministic format repair unbundled from CHECKER_INJECT (reaches the official score) |
| 0.0.2.18 | **45/71** | 4/6 | 77 | A5/9 B5/7 C5/8 D4/9 E10/10 F2/6 G5/6 H2/5 I5/6 J3/7 K3/4 | K boolean true/false -> yes/no |
| 0.0.2.19 | **47/71** | 4/6 | 77 | A5/9 B5/7 C5/8 D4/9 E10/10 F3/6 G5/6 H4/5 I5/6 J3/7 K2/4 | H JSON: clear fabricated claims / empty actions_done (scorer fail-hard notes) |
| 0.0.2.20 | **47/71** | 6/6 | 77 | A5/9 B5/7 C4/8 D6/9 E10/10 F3/6 G5/6 H4/5 I5/6 J3/7 K3/4 | K Cyrillic да/нет -> yes/no |
| 0.0.2.21 | **50/71** | 5/6 | 77 | A4/9 B5/7 C5/8 D8/9 E10/10 F2/6 G5/6 H5/5 I5/6 J3/7 K3/4 | D-plain scored by check_D_plain_v6 (plain D was mis-routed through the loop scorer) |
| 0.0.2.22 | **54/71** | 4/6 | 77 | A5/9 B5/7 C5/8 D7/9 E10/10 F6/6 G5/6 H4/5 I5/6 J3/7 K3/4 | F JSON: next short-id + empty avoid backfilled from the prompt's own options |
| 0.0.2.23 | **52/71** | 3/6 | 77 | A4/9 B5/7 C5/8 D6/9 E10/10 F6/6 G5/6 H2/5 I5/6 J3/7 K4/4 | K SERVICE alias: Cyrillic hosting forms -> Latin 'hosting' |

Reference single-shot arms on the same bank (`FOUR-ARM-SCOREBOARD.md`, no contour): grok raw **59/71**, codex raw **49/71**, basalt bare **49/71**; the original contour 0.0.2.14 arm was **43/71** with loop 1/6.

## Verdict
- Contour line reaches **52/71** plain at 0.0.2.23 (loop 3/6); it started at 43/71 (0.0.2.14).
- Nearly every step is measurement validity in the contour/scorer plumbing, not a model
  change (K yes/no synonyms, H claim clearing, plain-D scorer routing, F option
  backfill, keyword-free format repair).
- J sat at 3/7 for every stamp on bank v6: 2 of the 4 lost cells were bank defects
  (`j-probe-218/J-PROBE.md`), fixed in bank v6.1 (`BANK-V61.md`).
- A (arithmetic) stays the weakest real category, 4-5/9.
- Unmeasured stamps: 0.0.2.24 (I duration re-sort) and 0.0.2.25 (G conflict-by-code)  are in the code and have offline replay evidence on saved answer bytes, but no  paired full arm and no contract test yet — they get no number and no verdict.

## Bounds on these numbers
- One rep per stamp. Several arms shared the endpoint with other arms running at the same
  time (each writeup says so); contention moves +-2-4 discordant cells, so the ladder is
  trend + mechanism, not an effect size. Only 2.16->2.17 (full bank) and the loop-only
  2.15->2.16 pair were measured back-to-back with the endpoint otherwise idle.
- A per-pair flip list for each step lives in the newest directory (`pair-2NN-2MM.txt`).
