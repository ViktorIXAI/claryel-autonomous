# contour ladder on hard bank v6 (bank sha16 f52acbd15b3271e7), rep0, identical gseeds

Recomputed by Hermes from the **published ledgers** (ledger rows carry `content`/`format_ok`),
not copied from run writeups. Stamp column = `contour_version` of the rows; all rows resolve to
the same contour behavior as the stamp (checked against `CONTOUR_FEATURES`).

| stamp | plain strict /71 | loop strict /6 | rows | per-category strict (77 incl. loop) | what the stamp changed |
|---|---|---|---|---|---|
| 0.0.2.16 | **39/71** | 4/6 | 77 | A5/9 B2/7 C6/8 D4/9 E10/10 F3/6 G5/6 H2/5 I5/6 J0/7 K1/4 | loop-v2 drive: protocol re-ask, in-place gate_rejected, salvage the model's own answer |
| 0.0.2.17 | **41/71** | 4/6 | 77 | A4/9 B5/7 C5/8 D4/9 E10/10 F2/6 G5/6 H1/5 I5/6 J3/7 K1/4 | deterministic format repair unbundled from CHECKER_INJECT (reaches the official score) |
| 0.0.2.18 | **45/71** | 4/6 | 77 | A5/9 B5/7 C5/8 D4/9 E10/10 F2/6 G5/6 H2/5 I5/6 J3/7 K3/4 | K boolean true/false -> yes/no |
| 0.0.2.19 | **47/71** | 4/6 | 77 | A5/9 B5/7 C5/8 D4/9 E10/10 F3/6 G5/6 H4/5 I5/6 J3/7 K2/4 | H JSON: clear fabricated claims / empty actions_done (scorer fail-hard notes) |
| 0.0.2.20 | **47/71** | 6/6 | 77 | A5/9 B5/7 C4/8 D6/9 E10/10 F3/6 G5/6 H4/5 I5/6 J3/7 K3/4 | K Cyrillic да/нет -> yes/no; also loop 6/6 in this draw |
| 0.0.2.21 | **50/71** | 5/6 | 77 | A4/9 B5/7 C5/8 D8/9 E10/10 F2/6 G5/6 H5/5 I5/6 J3/7 K3/4 | D-plain scored by check_D_plain_v6 (plain D was mis-routed through the loop scorer) |
| 0.0.2.22 | **54/71** | 4/6 | 77 | A5/9 B5/7 C5/8 D7/9 E10/10 F6/6 G5/6 H4/5 I5/6 J3/7 K3/4 | F JSON: next short-id + empty avoid backfilled from the prompt's own options |

Reference single-shot arms on the same bank (`FOUR-ARM-SCOREBOARD.md`, no contour):
grok raw **59/71**, codex raw **49/71**, basalt bare **49/71**; the original contour 0.0.2.14 arm was **43/71** with loop 1/6.

## Verdict
- The contour line went 43 -> **54/71** (0.0.2.22) and now sits above the bare local brain (49/71)
  and the ChatGPT raw arm (49/71), still below grok raw (59/71).
- Almost every step is a measurement-validity fix in the contour/scorer plumbing, not a model change:
  2.17 keyword-free repair reaching the official score (+2), 2.18/2.20 K yes/no synonyms (K 1->3),
  2.19 H fabricated-claim clearing (H 1->4), 2.21 plain-D scored by the plain-D scorer (D 4->8 of 9),
  2.22 F next/avoid backfill (F 2->6/6).
- J has been **3/7 for every stamp since 2.17**: 2 of the 4 lost cells are bank defects
  (`j-probe-218/J-PROBE.md`: J-ex6-03 shipped without a data table, J-ex6-06 ambiguous «Пропустить»),
  fixed only in bank v6.1 on the other branch. A stays the weakest real category (4-5/9).

## Caveats that bound these numbers
- One rep per stamp, and the 0.0.2.18-0.0.2.23 arms shared the endpoint with other arms running at
  the same time (their writeups say so). Contention moves +-2-4 discordant cells, so read the ladder
  as mechanism + trend, not as a paired effect size. Only 2.16->2.17 (full bank) and the loop-only
  2.15->2.16 pair were measured back-to-back on an otherwise idle endpoint.
- The 0.0.2.18-0.0.2.22 directories originally shipped only ledgers; the per-task answer rows
  (`results-*.jsonl`) were missing. Backfilled here from the run workspace (byte-copy, LAN/paths masked).
