# Bank v6.2 defect changelog — every changed byte, with evidence

Date: 2026-11-07 (host clock). Owner directive of 2026-11-07 delegates measurement-stack
decisions to the agent: corrections ship as a NEW version with published arithmetic and
execution proofs; `0.0.2.x` contour and the published v6.1 bytes are never patched in place.

## Version identity

| file | sha16 | size | role |
|---|---|---|---|
| `benchmarks/hard/bank-hard-v6.json` | `9ec86dfca4a6f85f` | 120,519 B | v6.1, published, **bytes untouched** (verified again at v6.2 build time) |
| `benchmarks/hard/bank-hard-v6.2.json` | `3c866ea7daae611c` | 120,569 B | v6.2, this changelog |
| run-workspace `bank.json` (v6.1 line) | `f4553aab304f60d7` | — | the bank every published v6.1-row quoted below ran on |

Seed protocol unchanged (task `seed` fields byte-identical; run seeds stay
`gseed = int(sha256(task|rep)[:8], 16) % 999983`). Scorer contract unchanged: the frozen
`harness/parb_check_v6.py` scorers (`check_json_obj` with `deep_eq`/EPS for A, `check_C_v6`
exact-set for C, `check_K_v6` token/stem for K) are byte-identical — v6.2 corrects bank data,
not scoring. Task count 77, all ids unchanged.

Reproduce: `python3 scripts/build_bank_v62.py && python3 scripts/verify_bank_v62.py`.
The builder re-derives every new gold at build time from the shipped task bytes (A's
constants parsed from its own prompt text; C's options evaluated on the build CPython),
so a CI re-run reproduces the exact output bytes. `verify_bank_v62.py` fail-closes if the
v6.1 file moves, if any task beyond the three named ones differs, if any field beyond
`ref`/`prompt` differs, or if a gold stops re-deriving.

## 1. A-ex6-03 — reference replaced (prompt untouched)

Changed bytes (`ref` object only):

```
"net": 7629.26,  ->  "net": 6230.1,
"social": 1254.0, ->  "social": 2090.0,
"tax": 616.74     ->  "tax": 1179.9
```

Evidence (from `bank-defect-v61-queue.md`, re-computed): the prompt states база = gross =
9500.0 and no other base. Its own chain gives
`social = min(0.22 x 9500.0, 6100) = 2090.0`;
`tax = 0.19 x (9500.0 - 2090.0 - 1200) = 0.19 x 6210.0 = 1179.9`;
`net = 9500.0 - 2090.0 - 1179.9 = 6230.1`. The v6.1 gold `social=1254.0` implies a hidden
base of 5700.0 that appears nowhere in the prompt, and the v6.1 gold is not even
self-consistent (`0.19 x (9500-1254-1200) = 1338.74 != 616.74`). 0/89 published rows across
every arm ever passed the old gold. The new gold is the faithful execution of the printed
chain; float values are stored 2-decimal-rounded as in every other A task and compare via
`deep_eq` EPS.

Rejected alternative: print "22% от базы 5700" in the prompt — rejected because it edits the
prompt corpus (invalidates every stored A-ex6-03 answer for paired rescoring) while the
prompt as shipped is unambiguous and fair; only the gold was wrong.

## 2. C-ex6-02 — reference replaced (prompt untouched)

Changed bytes (`ref.letters`):

```
"letters": ["C"]  ->  "letters": ["A", "B", "C", "D"]
```

Evidence: the four shipped snippets, executed on CPython (the runtime the task is about):
`A: sorted({3,2,1,1}) -> [1, 2, 3]`; `B: list(set([1,2,3,3])) -> [1, 2, 3]`;
`C: sorted([3,1,2]) -> [1, 2, 3]`; `D: [3,2,1][::-1][:3] -> [1, 2, 3]`. Every option prints
the target, so `want=["C"]` is refuted by executing the task's own text; 0/89 published rows
ever passed. The new gold is exactly the executed truth table, which is what the question
asks ("какой вариант печатает [1, 2, 3]?"). Disclosure: B's result depends on CPython's
small-int set iteration order (an implementation detail); the task is defined on CPython,
and the executed-truth-table rule makes the gold checkable by running the shipped code —
`verify_bank_v62.py` re-executes it on every run.

Rejected alternative: rewrite an option so it genuinely does not print (e.g.
`B: sorted({3,2,1}, reverse=True)`) — rejected because it edits the prompt corpus; with the
prompt untouched, all 89 published C-ex6-02 answer rows remain re-scorable against the new
gold (the 24 rows answering `A,B,C,D` flip to pass; `A,C,D` and `C,D` blocks stay genuine
misses of B).

## 3. K-ex6-03 — prompt gains the value form (reference untouched)

Changed bytes (`prompt`, one appended parenthetical on the field-spec line):

```
...\nПоля: ITEM, QTY, LEAD_WEEKS, FREE_SHIPPING"
 -> ...
\nПоля: ITEM, QTY, LEAD_WEEKS, FREE_SHIPPING (FREE_SHIPPING: yes/no)"
```

Evidence: the frozen scorer stems/substrings gold token `yes`, which has no >=4-char token,
so Russian forms `да` / `бесплатная` could never bridge to it; exactly 9/91 published rows
lost 0.25 on `value:FREE_SHIPPING` (forms `бесплатная` x4, `да` x3, `true` x2). The prompt
now states the required value form, making the gold contract-derivable. `ref` stays
`["кресла Oslo", "200", "14", "yes"]` byte-identical.

Rejected alternative: change the gold token to a Russian form — rejected because any single
token still leaves the other language's forms failing; the ambiguity is in the prompt, so the
prompt is where the fix belongs. NOTE: this is the one v6.2 change that edits a prompt, so
K-ex6-03 answer rows recorded under v6.1 are labelled PRE-v6.2 (prompt-consumed, not
comparable) in any future paired table; A/C rows stay fully comparable.

## Explicitly NOT changed in v6.2

- `C-ex6-00` / `C-ex6-01`: documented as NOT defects (published reach limit of the
  prompt-stated-rule family). In-prompt policy wording is a separate owner-commanded
  decision, deliberately left out of this version — one substantive change per defect, and
  the two cells do not block the line.
- every other task byte: verified (raw diff of the re-serialized v6.1 vs v6.2 touches only
  the five lines listed above; `verify_bank_v62.py` asserts exactly this).
- every scorer file, every ledger/answer artifact, the contour harness.

## What comes next (queued, not in this commit)

1. Re-score every published arm under v6.2 references (stored answer bytes vs new golds)
   into `benchmarks/hard/v6-results/rescore-v62/` with a per-cell delta table — expected
   to flip only A-ex6-03/C-ex6-02 cells that executed their own stated rules.
2. Four-arm cadence re-run (contour line `0.0.2.43` / raw ChatGPT / Grok / bare basalt) on
   v6.2 with fresh seed-matched reps — raw-arm improvement is the fairness check that the
   bank got fairer. This requires a v6.2 workspace build (the ws builder currently pins
   `bank-hard-v6.json`); that is the next measurement-stack step, never a silent bank swap.
