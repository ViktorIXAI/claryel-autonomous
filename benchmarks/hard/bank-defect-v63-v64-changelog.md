# Bank defect changelog: v6.2 -> v6.3 -> v6.4 (B-ex6-04, two independent unstated-contract defects)

Date: 2026-11-07 (host clock). Predecessor file stays byte-frozen and published:
`bank-hard-v6.2.json` sha16 `3c866ea7daae611c`. Every correction below is a NEW file, never an
in-place edit (repo rule: published bytes of a version are immutable).

## Version chain and identity

| bank | file | sha16 | content delta |
|---|---|---|---|
| v6.2 | `bank-hard-v6.2.json` | `3c866ea7daae611c` | frozen, unchanged |
| v6.3 | `bank-hard-v6.3.json` | `73f7a04d57473545` | v6.2 + one field (`B-ex6-04.prompt`, stated year) |
| v6.4 | `bank-hard-v6.4.json` | `85a0cd0dd6fa1fab` | v6.3 + one field (`B-ex6-04.prompt`, value-form hint) |

All 77 gold (`ref`) bytes, seeds and distractor clauses are byte-identical across v6.2/v6.3/v6.4
(asserted by `scripts/verify_bank_v63.py` and `scripts/verify_bank_v64.py`, both PASS). One
substantive change per version.

## Defect 1 (fixed in v6.3): gold year never stated in the prompt

`B-ex6-04` gold demands `start_date = "2026-04-01"`, but the v6.2 prompt dates the letter only as
`3 марта` / `1 апреля` — the year appears nowhere. 0/15 strict fails on the published contour line
(cadence-246 q45r16-18, pair-246 s46/s47 r19-21, pair-247 q43/q44 r22-24), and the raw arms split
on luck: bare basalt 3/3 pass on cadence-246 (guessed the year from model priors), codex 0/3 and
grok 0/3 (both explicitly say the year is not stated). An unstated gold atom, not a model gap.

Exactly one changed line (the `Письмо:` prompt line of `B-ex6-04`):

```diff
-... подписан 3 марта, старт работ 1 апреля, ...
+... подписан 3 марта 2026, старт работ 1 апреля 2026, ...
```

The year is re-derived at build time from the shipped gold (`ref["start_date"][:4]`), never typed,
so the stated year provably equals the gold year and no gold byte moves. `verify_bank_v63.py`:
exactly one changed task/field, every gold and seed byte identical, distractor clause untouched.

Probe verdict (REVIEW-INBOX 12:20 CET, rule frozen 12:16 CET before any row): v6.3 arm
`p63r22/23/24` = **0/3 strict** — the year fix works (`2026-04-01` in all three rows) but all
three then fail on defect 2. Condition (i) of the pre-registered rule failed, so v6.3 stays
**PROVISIONAL** (published as the intermediate version; it never became the working bank).

## Defect 2 (fixed in v6.4): value-form of `penalty_per_week` unspecified

The gold is the string `"2%"`; the v6.2/v6.3 JSON spec lists `"penalty_per_week"` with no
value-form example, so `"2%"`, `2` and `0.02` all look valid to every arm. Predicted mechanically
before it was probed: the upgraded `scripts/bank_derivability_audit.py` `type_form` check (a
percent-shaped gold string whose JSON spec gives no quoted value-form example) fires on exactly
this field in v6.2 and v6.3 and on no other A/B/K task.

Exactly one changed line (same prompt line):

```diff
-... "budget_eur":число,"penalty_per_week"}.
+... "budget_eur":число,"penalty_per_week":"число% (например 5%)"}.
```

The hint is derived from the gold's unit; the example value `5%` is deliberately NOT the gold
(`2%` never appears as an example — the leak guard fails the build if it does).
`verify_bank_v64.py`: one changed field, all gold/seed bytes identical over 77 tasks, v6.3's
stated year intact, no leak.

Derivability audit census (candidate unstated gold atoms, A/B/K): **39 (v6.2) -> 38 (v6.3) ->
37 (v6.4)**; B-ex6-04 now has zero candidates.

## v6.4 probe (rule frozen 12:20 CET in REVIEW-INBOX before any `p64` row)

Contour `0.0.2.48` (harness `3ae462167529`), `PARB_SUBSET=B-ex6-04`, sp1 seeds 861061/593370/188460
(reps 22/23/24), serial on the idle P2005 endpoint, fresh workspaces per bank, bank identity in
every run record (ws copies: v6.2 `d1e8d11df5840dcc`, v6.3 `42bf2ecf69558dc2`, v6.4
`7788cc288922b9a4`). Scorer contract v6.2 `c8c0c7dd114dfc32`; strict = `content == 1.0 and format_ok`.

| bank | rows | strict | what the answer said |
|---|---|---|---|
| v6.2 control | p62r22/23/24 | 0/3 | `start_date 2024-04-01` (year unstated, wrong prior) |
| v6.3 | p63r22/23/24 | 0/3 | `start_date 2026-04-01` (fix 1 works) but `penalty_per_week: 2` (number) |
| v6.4 | p64r22/23/24 | **3/3 PASS** | `2026-04-01` and `"2%"` — exact gold on every seed |

All nine rows carry the identical contour event chain (`gate:format_gap_json`,
`json_fixed_by_code_as_is`, `format_repaired_by_code`, `fix:format_attempt_2`,
`contour:v20_obj_unwrap`, fix=1 calls=2): the contour side is byte-identical across arms, the only
moved input is the bank prompt. Ledger cost: ptok 292 (v6.2) / 312 (v6.3) / 330 (v6.4); seconds
per row in `bank-probe-634/`. No GPU sampler was run for a 6-row probe and **no Wh claim is made**
(the p64 arms carry only `start.epoch`; durations come from the PGR logs).

**Verdict (rule applied as written):** >=2/3 strict on v6.4 (got 3/3), 0/3 fresh controls on v6.2
AND v6.3 at identical seeds in the same session, verify PASS, audit delta exactly the two
B-ex6-04 atoms => **bank v6.4 `85a0cd0dd6fa1fab` becomes the WORKING hard bank**; `B-ex6-04`
leaves the defect queue; no contour stamp was ever aimed at it (correctly — a stamp aimed at a
defective cell is UNMEASURED by construction). Published arms measured under v6.2 bytes are not
re-scored here: the B-ex6-04 prompt moved, so old v6.2 numbers stay under v6.2 identity; the four
raw arms' fairness re-check under v6.4 runs as the pre-registered probe in
`REVIEW-INBOX.md` 12:56 CET.
