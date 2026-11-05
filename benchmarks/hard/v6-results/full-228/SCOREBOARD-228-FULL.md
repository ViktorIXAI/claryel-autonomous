# Contour 0.0.2.28 full arm (77 tasks, hard bank v6)

Run tag `c228full`, one rep, fresh seeds per task (hash of task|rep), pinned scorer and
bank as in `benchmarks/hard/MANIFEST.sha256`. Artifacts in this directory: `results-c228full.jsonl`
(answer bytes), `ledger-c228full.jsonl` (per-row scores and contour events), `c228full.log`,
`run-record-c228full.json`, `pair-225-228.txt`.

| view | value |
|---|---|
| plain strict (71 single-shot) | **61/71** |
| loop strict (6 loop-D) | 5/6 |
| model calls | 129 |
| wall | 1020 s (endpoint shared with other arms during this run; latency is not comparable to idle arms) |

Per-category strict (77 incl. loop): A 8/9 B 5/7 C 5/8 D 8/9 E 10/10 F 6/6 G 6/6 H 5/5 I 6/6 J 3/7 K 4/4.

Against the previous measured stamp (0.0.2.25, `full-225/`): plain 56 -> **61**, loop 4 -> 5.
Paired by task: 6 wins, 0 losses, 71 ties, exact sign-test p=0.0312. Every win is a
mechanism the stamp introduced, visible in the ledger:

- `A-ex6-01`, `A-ex6-02`, `A-ex6-04` — 0.0.2.27 computes the arithmetic from the numbers in
  the prompt (invoice+VAT, FX, proration) instead of trusting the model's own math.
- `G-ex6-03` — 0.0.2.26 overwrites a `conflict: true` answer whose clauses/values disagree
  with the prompt-derived pair.
- `H-ex6-02` — 0.0.2.28 fills `requires`/`unknown` from an explicit prompt signature constraint.
- `D-ex6-l2` — loop resample noise, no contour event on either side.

Still failing (plain): A-ex6-03, B-ex6-04, B-ex6-06, C-ex6-01, C-ex6-02, C-ex6-03, J-ex6-01, J-ex6-02, J-ex6-03, J-ex6-06. Loop losses: D-ex6-l3.

Contour events in this arm: gate:format_gap_json x24, gate:json_fixed_by_code_as_is x12, gate:format_repaired_by_code x12, fix:format_attempt_2 x12, gate:sysadmin_structure_gap x12, gate:quote_not_in_source x10.

## Honest bounds
- One rep. The p=0.0312 comes from a 6-0 paired sign test on the same tasks, so it is not a
  resample test: the same seeds could produce a different split. A repeat of 0.0.2.28 on an
  idle endpoint is owed before this number is quoted as the level.
- 0.0.2.26/0.0.2.27 were published as offline replay evidence; their first full-arm evidence
  is this run. `LADDER.md` marks which stamps have their own arm.
- A-03 is deliberately not touched by 0.0.2.27: its prompt formula contradicts the bank
  reference (bank defect, logged in `REVIEW-INBOX.md`).
