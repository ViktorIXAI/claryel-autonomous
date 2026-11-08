# Claryel Autonomous Harness

**An open local-AI automation harness for measuring model tasks, answer
quality, latency, memory, power and cost on real machines.** The system runs a
frozen model against a fixed task bank, records every attempt, repairs safe
harness mistakes by code, and compares versions only with paired evidence.

This is a working engineering project, not a finished product. It publishes
accepted versions, rejected versions, broken runs and hardware limits. The
main question is practical: how much reliable local AI can be obtained on
affordable hardware without hiding failures?

```
same model  ·  same frozen task prompts  ·  same seeds
        only the software around the model changes
```

An AI agent developed and tested many harness changes under operator rules.
The operator set objectives, constraints, publication scope and final adoption
decisions. The agent's own work is itemized in [`docs/autonomy.md`](docs/autonomy.md);
its limits are in [`docs/limitations.md`](docs/limitations.md).

Status checked: 2026-11-08 (historical snapshot; version and run status require fresh verification)

The next stamp `0.0.2.57` (loop claim-family selection re-arm) is FROZEN UNMEASURED to
exactly 2.57 (2026-11-08, pair-257: the loop claim family's per-draw base rate is ~2.9%,
so a 3+3 loop pair carried zero live target; live wiring evidence published in `pair-257/`).
Working bank: v6.6 `5c86252b2ef2f422` — adopted-line bank baseline 97.4% (75.0/77 strict,
map-256); bank v6.7 `b4464127dc5b5b97` (six answer-byte-proven raw-fairness defects fixed,
found by the `raw_gold_disagreement` census) is PROVISIONAL pending its frozen probe rule
(REVIEW-INBOX 2026-11-08).

## Current version

Contour gate line: `0.0.2.56` — ADOPTED on 2026-11-08 after pair-256 (loop best-of-3 on the
`banned_attempted` family — when the adopted 2.43 best-of-2 still leaves every candidate carrying
a banned attempt, the contour pays ONE further loop draw at seed+16234 and adopts it only if
strictly better than the best already held: monotone, fires only on already-failing loop rows,
never touches the 2.11/claim triggers, own `v56_*` events, the 2.43 first retry byte-untouched.
Loop-only pair on bank v6.6 with fresh matched seeds 55/56/57: the target `D-ex6-l0`
strict-failed 2/3 control seeds (`banned_attempted:SEND_EMAIL`, the v243 retry fired there without
a win — live target per the pre-launch mechanical gate) and BOTH converted with
`contour:v56_d_best3_banned_fired` + `fix:v56_d_best3_banned_win` on the row; loop pool 14/18 ->
18/18, W4/L0 with the two mechanism wins separated from two unevented resample wins published as
lottery flips; zero guard violations (no `v56` event in any control arm, none outside the banned
family, frozen band silent, v243 parity fired-5/won-3 identical across arms). Cost: +3..4 model
calls per conversion, energy delta inside window variance; `PAIR-256-V66.md`). The previous line
`0.0.2.55` was ADOPTED on 2026-11-08 after pair-252 (the D-plain answer-item
shortening — when the model's own `refused`/`next_ok` lists spell the prompt's own bracket-
enumeration entries, the contour shortens each item to the one-letter id the prompt itself declares:
a closed grammar over the prompt text (id table from its enumerations, list names from its JSON
spec, membership and list names never change; ungrounded, ragged or duplicated inputs refuse
byte-identical), zero model tokens, reference never read. The format-class `D-ex6-p2` — a CORRECT verdict scoring 0.0
because of spelled form, 2/12 line-era draws — strict-failed 1/3 control seeds (live target,
exactly the predicted rate) and converted 2/3 -> 3/3 with `contour:v55_d_id_normalized_from_prompt`
on the row at byte-identical ptok/ctok and model_calls 1 vs 1; census surface {D-ex6-p1, D-ex6-p2}
only, 5 further fires byte-identical `matched`, ZERO guard violations, loop pool untouched by the
grammar; `PAIR-252-V66.md`). The previous line `0.0.2.53` was ADOPTED on 2026-11-07 after pair-250 (the C python-literal
options gate — when a C task prints its own snippets and literal option expressions, the contour
EXECUTES them by code over a closed AST allow-list and rewrites only the ОТВЕТ line to the set
THIS prompt printed: the chronic `C-ex6-02` — a 27/27 loss across every published era — strict-failed
3/3 control seeds and all three converted with the event on the row and ZERO added model calls
(the rewrite even removes the control's selector retry there), C pool 20/24 -> 22/24 on bank
v6.6, zero guard violations; `PAIR-250-V66.md`). Its candidate `0.0.2.54` (pair-251, the H
`unknown` slot grounded from the prompt's own denial sentence) then measured **UNMEASURED**: the
pair's own control arms strict-PASSED the target `H-ex6-03` 3/3 — zero live target, zero
conversions, all guards clean, wiring proven live (1 `from_prompt` + 5 `matched`, census surface
only) — so it froze to exactly (2,54) and the line stayed `0.0.2.53` (`PAIR-251-V66.md`). Before it, `0.0.2.52` was ADOPTED after pair-249 (the A percent-chain
arithmetic — fifth branch of the 2.27 family: when a task prints its own percent chain (rate
clauses with cap/floor plus one formula), the contour recomputes the chain by code from the
prompt text and replaces only the model's numbers — the chronic `A-ex6-03` strict-failed 2/3
control seeds and both converted with the event on the row at byte-identical tokens, zero extra
model calls, A pool 24/27 -> 27/27 on bank v6.6, zero guard violations; `PAIR-249-V66.md`).
Before it, `0.0.2.51` was ADOPTED after pair-248 (the B echo restore — answer
rebuilt from the prompt's own JSON literal when the task says "same object, add a computed field,
don't touch items" — re-armed from the pair-234 grammar that was frozen UNMEASURED at (2,34) and
came back live on the adopted line itself: `B-ex6-05` strict-failed 2/3 seeds because the model
injected its own per-item `n_tags` against «Items не меняй»; 1/3 evented conversion (the other two
seeds the control already passed), answer byte-equal to the prompt literal, zero extra model calls,
zero guard violations, coverage census exactly 1/77; `PAIR-248-V62.md`). Before it, `0.0.2.48` was
adopted after pair-247 (K fields-gate key set taken
from the task's own `Поля:` enumeration instead of the instruction's placeholder token `FIELD`; the
target cell `K-ex6-03` had been failing 9/9 on our own line because the contour hint itself named the
placeholder key — 3/3 evented conversions, K pool 9/12 -> 12/12, zero guard violations, zero extra
model calls; `PAIR-247-V62.md`). Before it, `0.0.2.47` was adopted after pair-246 (C best-of-2 second
trigger on `set_mismatch`); between pair-244 and pair-246 the line was `0.0.2.43` with tooling-only
stamps `0.0.2.45/0.0.2.46`, and pair-245's `0.0.2.44` measured **UNMEASURED** and froze to exactly (2,44);
harness stamps are `0.0.2.x`; full
history in `versions/VERSIONS.md` and `benchmarks/hard/v6-results/LADDER.md`). `0.0.2.30` and `0.0.2.31`
measured **negative** against the former adopted `0.0.2.29`; `0.0.2.32` and `0.0.2.33` each measured
**+1.3 cells — below the ~2-cell noise floor, NOT adopted** (`PAIR-232-V61.md`; `PAIR-233-V61.md` — 2.33
additionally fired **zero times live**, so its arm delta contained no on-target cells at all, a direct
empirical lower bound on pure resampling); `0.0.2.34` measured **−1.0 cells with zero live fires in
either B grammar** — the model answered both of its target cells 6/6 in that pair, so the stamp had no
surface to act on (`PAIR-234-V61.md`); `0.0.2.35` is the **strongest mechanism evidence of the series** —
its table repair fired exactly on its target cell in all three candidate seeds and converted `B-ex6-06`
0/3 → 3/3 with its own event on every converted row and zero extra model calls — **but the arm mean moved
+2.0, exactly at the ~2-cell resolution floor, with four off-target flips carrying no 2.35 event: NOT
adopted, frozen to its own stamp** (`PAIR-235-V61.md`); `0.0.2.36` (group-4 best-of-2 selection) measured
**−1.0 with SIX fires and ZERO converted cells** — the F wins raised an already-passing cell, and on H the
extra sample reproduced the same omission: the class is content-biased, selection cannot fix it (the 2.31
lesson, `PAIR-236-V61.md`) — **NOT adopted, frozen to its own stamp**. All of 2.30/2.31/2.36 are frozen as
measured-negative and 2.32/2.34 as unresolved-without-conversion; none inherits into anything.
**`0.0.2.37` re-landed the 2.35 B table repair under a pre-registered all-or-nothing attribution rule and
passed it exactly** — `B-ex6-06` 0/3 → 3/3 with `contour:v235_b_table_total` on every converted row, no
other 2.37-gated event anywhere, arm 62/63/66 vs 62/59/63 (+2.4 mean, only the +1.0/seed target-cell
conversion attributable, the rest stated as event-less noise; pooled 10W/3L p=0.09): **ADOPTED as the new
control line** (`PAIR-237-V61.md`; decision record
`history/agent-decisions/2026-11-06-pair237-b-table-adopted-line-moves-to-237-and-238-launch.md`).
`0.0.2.38` re-landed the 2.33 A threshold-table arithmetic on that line and came back **UNMEASURED** —
the line passed `A-ex6-00` in all three control seeds, the pair carried no live on-target cell despite
one mechanism fire on that task in a candidate seed, so by its own pre-registered rule the stamp is not
adopted and `A_TABLE_ARITH` is pinned to exactly (2,33)/(2,38) (`PAIR-238-V61.md`; arms `k37r*` vs
`k38r*`). `0.0.2.39` re-lands the category-J ranking repair with **grammar v2** — v1 froze at 2.32
reaching 3 of 7 bank prompts, and the published bytes show exactly why the chronic victim `J-ex6-02`
(0/12 across the six-seed map and both pair-238 arms, every loss the right ids in the wrong order) was
never in reach; v2 closes those four named gaps, reproduces 6/7 with mis-sorts 0, and replays over
pair-238's published J rows converting seven losses with zero regressions. Paired arms `l37r*` vs
`l39r*` on three matched seeds **passed the pre-registered chronic-target rule exactly — `J-ex6-02`
0/3 → 3/3 with the re-rank event on every converted row at identical `ptok`/`calls`, zero regressions
carrying the event, B repair identical, A pin intact: `0.0.2.39` is ADOPTED as the new control line**
(arm mean +1.0, published below the ~2-cell floor by construction; `PAIR-239-V61.md`; decision record
`history/agent-decisions/2026-11-06-pair239-j-grammar-v2-adopted-line-moves-to-239-and-240-launch.md`).
`0.0.2.40` (J **membership** re-derivation from the prompt's own filter/top-K rule, the chronic
`J-ex6-01`/`J-ex6-06` `id_set_mismatch` class that pair surfaced) was pre-registered in
`PAIR-239-V61.md` and measured by pair-240 (`m39r*` vs `m40r*`), which **passed its pre-registered
rule exactly — chronic `J-ex6-01` strict-failed 2/3 control seeds and the candidate passed all three
with `contour:...v240_j_membership_from_prompt` at identical `ptok`/`calls`, `J-ex6-06` converted
from an empty draw, zero strict-pass regressions anywhere carry a 2.40 event (the mis-derivation
guard), the inherited re-rank and B repair fired identically, the A pin held — so `0.0.2.40` is
ADOPTED as the new control line** (arm means 64.3 vs 64.3, +0.0 and never the reason;
`PAIR-240-V61.md`; decision record
`history/agent-decisions/2026-11-06-pair240-j-membership-adopted-line-moves-to-240.md`). The J pair
logged `C-ex6-02` as a
**bank defect** — its gold `want=['C']` contradicts the task text (three of the four bank snippets
deterministically print `[1, 2, 3]`), so no contour mechanism chases that cell. Published arms
on the current hard bank v6.1: `full-229` (contour) and `four-arm-v61` (contour vs Grok vs ChatGPT vs
the same local model without contour).

## Headline results

Hard bank v6.1 — 71 single-shot + 6 loop tasks, frozen scorer, every number recomputed from published
answer bytes (`benchmarks/hard/v6-results/HEADTOHEAD-V61.md`):

- contour 0.0.2.29 on one 24 GB local GPU: six independent seeds published in
  `benchmarks/hard/v6-results/reps-229/`; on the common 61-cell set the contour band is
  53/52/50/55/53/51, mean 52.3
- ChatGPT (`gpt-6.1-sol`, xhigh) **50**, Grok 4.7 **54**, the same local weights with no contour **56**
- seed-averaged margins with a bootstrap over cells (`ARM-BANDS-V61.md`; contour 6 seeds, ChatGPT 3,
  bare basalt 5, Grok 3): vs ChatGPT **+12.0 cells, 95% CI +4.3..+19.8**; vs Grok **+8.3 cells,
  CI +1.8..+15.0**; vs bare basalt +5.9 cells, CI −0.5..+12.5 — **not resolved**, stated as such
- exact paired sign tests: vs ChatGPT **16W/3L p=0.0044**, vs Grok **12W/3L p=0.035**, vs bare basalt
  11W/4L p=0.118
- where the margin lives: contract-sensitive categories F/H/K **14 vs 6 / 6 / 1**; on the other 56 cells
  it is parity (49 vs 50 / 49 / 48, all p=1.00) — see `CATEGORY-SPLIT-V61.md`
- not a printing artifact: giving each raw arm the contour's deterministic repairer changes **0 cells**,
  and every cloud failure in F/H/K is content-side (`ABLATION-RAW-FIXERS.md`, `AUDIT-FHK-60.md`)
- two contour attempts measured **negative** and published as such: 0.0.2.30 artifact-shape guarantee
  (−1.3 cells) and 0.0.2.31 plurality vote on C/J (−2.7 cells, 2.5× energy — the model is biased here, not
  noisy, so voting amplifies its own mistake); a third, 0.0.2.32 J re-rank, landed **+1.3 — under the
  floor, unresolvable and not adopted** (`PAIR-232-V61.md`); a fourth, 0.0.2.33 A threshold-table
  arithmetic, also **+1.3 with zero live fires** — the candidate model answered its target cell correctly
  in every seed, so the pair measured nothing and +1.3 is a direct lower bound on pure resampling
  (`PAIR-233-V61.md`); a fifth, 0.0.2.34 B field completeness, **−1.0 with zero live fires** for the
  same reason (target cells 6/6 in both arms, `PAIR-234-V61.md`) — pairs 233/234 together bracket pure
  resampling at roughly ±1.3 cells around this scoreboard; a sixth, 0.0.2.35 B table aggregation, the
  strongest **cell-level** confirmation of the series (0/3→3/3 on its chronic target with its event, zero
  tokens) whose arm mean sat exactly at the floor with event-less flips (`PAIR-235-V61.md`); and a
  seventh, 0.0.2.36 group-4 best-of-2 selection, **−1.0 with six fires and zero converted cells** — the
  second sample reproduces the same component omission, so selection cannot beat a biased class
  (`PAIR-236-V61.md`); an eighth, 0.0.2.38's A-arithmetic re-land, **UNMEASURED — the adopted line
  passed its target cell 3/3 so the pair contained no live target at all**, the second zero-opportunity
  pair in the series and the reason pair hypotheses are now pinned to chronic stable-fail cells
  (`PAIR-238-V61.md`); a ninth candidate, 0.0.2.39 (J ranking repair with grammar v2, bank coverage
  3/7 → 6/7, mis-sorts 0, published-bytes replay converting seven losses with zero regressions), is the
  one that **resolved**: pair-239's chronic target was live, the conversion was fully evented at zero
  added tokens, and it was ADOPTED (`PAIR-239-V61.md`) — while its arm mean, +1.0, is still reported as
  below the floor and is not quoted as the reason; a tenth candidate, 0.0.2.40 (J **membership**
  re-derivation, coverage derives-gold 4/7 refuses 3/7, published-bytes replay converting 6 membership
  + 3 re-rank rows with zero regressions), also **resolved**: its chronic target was live, the conversion
  was fully evented at zero added tokens and the mis-derivation guard passed on all 231 paired cells, so
  it was ADOPTED (`PAIR-240-V61.md`) on an arm mean of +0.0 that is explicitly not the reason; an
  eleventh candidate, 0.0.2.41 (C rule-grounded membership — re-derive the letter set from the prompt's
  own threshold-conjunction/truth-table rule, parses 2 of 8 C prompts, published-bytes replay converting
  3 rows with zero regressions), was **UNMEASURED in pair-242**: the adopted line's control seeds all
  strict-passed its only live target `C-ex6-03`, so the pair carried no on-target cell (third
  zero-opportunity pair after 233/238), while the live wiring proved the grammar fires at zero tokens
  and zero regressions — the flag is therefore frozen to exactly (2,41) and the line stays `0.0.2.40`.
  Group 1 closes at its published reach limit: `C-ex6-00/01` are judgment prompts whose rule the prompt
  never states (bank-clarification queue, never contour guesses). After pair-242 the contour is **at the
  bank ceiling** on `0.0.2.40` — every remaining stable fail on the line is a bank defect
  (`A-ex6-03/C-ex6-02/K-ex6-03`), a frozen-negative class (`B-ex6-04`), or a closed lottery class, so no
  pair launches without owner-commanded bank clarification (`PAIR-242-V61.md`). A twelfth candidate,
  0.0.2.42 (D-loop **policy re-ground**: after the first successful read the observation quotes the
  task's own approval-policy line verbatim — prevention for the read-then-banned-attempt trajectory that
  accounts for all 7 strict loop-D losses of the line), launched under the owner's continuation rule
  because it targets NONE of the blocked bank cells (loop-D is contour-only headroom): **MEASURED
  NEGATIVE in pair-243** — the mechanism converted both live target cells (`D-ex6-l3` seeds 0+1, evented,
  zero attempts) but the context tail re-rolled the loop lottery and induced two NEW banned attempts on
  cells the control passed (`D-ex6-l1/l2` seed 1), loop pool 16/18 vs 16/18, full pool W6/L4 p=0.75 —
  the pre-registered zero-regression guard broke, so the flag is frozen to exactly (2,42) and the line
  stays `0.0.2.40`. Class lesson: any loop context change re-rolls every trajectory, so loop losses are
  a SELECTION target (the 2.11 best-of-2 family, trigger-gap published), never a prevention nudge
  (`PAIR-243-V61.md`). A thirteenth candidate, 0.0.2.43 (the SELECTION answer that gap named: loop
  best-of-2 on the `banned_attempted:<TOOL>` note family — one retry at seed+8117, strict-better only,
  monotone by construction): **MEASURED and ADOPTED in pair-244** on 2026-11-07 — 3 live control draws,
  exactly 1 evented conversion (fired+win, zero banned attempts in the adopted trajectory; two further
  loop wins carried NO event and are published as lottery, one fired draw lost because BOTH draws
  attempted the ban — selection covers variance, not bias), zero regressions, zero off-loop events,
  zero frozen-band events, line parity identical; loop pool 13/18 -> 16/18 (W3/L0 p=0.25,
  directional), means 65.0 vs 64.7 single-shot and 208 vs 210 of 231 full-pool — both under the
  resolution floor and explicitly not the reason (`PAIR-244-V61.md`): **`0.0.2.43` is ADOPTED as the
  new control line**. A fourteenth candidate, 0.0.2.44 (the same recipe on the last untriggered loop
  note family, `false_completion_claim` — claim-a-banned-action-did-happens caps content at 0.3;
  dry-run: 13 occurrences in 504 published loop rows, 13/13 strict-fails, zero on passing rows),
  pre-registered and measured in pair-245 vs the 0.0.2.43 line (REVIEW-INBOX 2026-11-07 03:58):
  **UNMEASURED — zero of the 18 control loop cells drew the claim note** (live 0/18 vs archive
  13/504), the fourth zero-opportunity pair after 233/238/242; UNMEASURED is never a pass, so it is
  NOT adopted and `D_BEST2_CLAIM` is frozen to exactly (2,44) (live smoke on the frozen tree: 2.43
  claim OFF / banned ON, 2.44 both ON, frozen bands OFF). Wiring was still proven live (one fired+win
  on the candidate's own claim draw at an already-passing cell, offset +12289, adopted trajectory
  claim-free; zero off-loop events, zero loop regressions, guards all clean), while pools — loop
  15/18 vs 17/18 with only event-less lottery wins, single-shot 65.0 vs 64.7, full 209 vs 212
  (8W/5L p=0.58) — sit at the floor throughout (`PAIR-245-V61.md`). **Queue ruling: bank v6.1 is at
  the contour ceiling on both pools** — the line's 22 remaining strict fails are all v6.2-fixed bank
  defects, frozen-negative classes, closed-unreachable prompts, a designed refusal, or retry-spent
  loop draws, so no pair-246 candidate passes the pre-launch measurability gate on this bank; the
  next launchable step is the v6.2 workspace + line map + the due four-arm cadence, and new pairs
  pre-register against the v6.2 map only (decision record
  `history/agent-decisions/2026-11-07-pair245-d-best2-claim-unmeasured-frozen-line-holds-243.md`).
  Resolution
  floor measured directly: the same
  stamp over the same seeds twice differs on 12 of 231 cells, so any contour delta under ~2 cells is
  reported as unresolvable (`PAIR-230-V61.md`, `PAIR-231-V61.md`, `PAIR-232-V61.md`, `PAIR-233-V61.md`)
- **Cadence-246 ran the due four-arm cadence on the corrected bank v6.2 (7 Nov)** — workspace
  `parb-v62-contour`, fresh seed-matched reps 16/17/18 pre-registered at 06:20 CET before any row.
  Contour (adopted 2.43 matrix, tooling release 0.0.2.45, bank `3c866ea7daae611c`, contract v6.2
  `c8c0c7dd114dfc32`) pools **166/183** on the 61-cell common set vs bare basalt **138** (40W/12L,
  p=1.3e-4), ChatGPT-codex **128** (47W/9L, p=2.6e-7), Grok **137** (37W/8L, p=1.5e-5): the margin
  replicates on the clarified bank and every raw arm now passes the two fixed golds A-ex6-03/K-ex6-03
  (3/3 each) — the owner's bank-fairness check passes. Rule (c) re-score from stored bytes: **zero**
  ledger-vs-bytes mismatches. Energy: contour 3 seeds 16.25 Wh vs 69.36 Wh for the raw same-model leg.
  The root cause of the long-frozen-negative cell **B-ex6-04** was established: its prompt never
  states the year the gold demands (contour work stays closed there; fix belongs to the next bank
  version); strongest next live target
  **C-ex6-02** (3/3 live control fails, no existing trigger family). The empty `harness_git_sha` in
  these run records was fixed the same day as tooling release **0.0.2.46** (run records now name the
  real harness commit; zero contour flags move). Artifacts `v6-results/cadence-246/`, writeup
  `CADENCE-246-V62.md`, scorer `scripts/cadence_score_v62.py`.
- **Pair-246 ran the pre-registered v6.2 pair the same morning (7 Nov)** — candidate `0.0.2.47`
  (C best-of-2 **second trigger** on the `set_mismatch` note family: the frozen v6.2 C scorer never
  emits `missed_options` for C, so the adopted 2.13 trigger had a structural coverage gap; one retry
  at `seed+17491`, strict-better only, `missed_options` keeps precedence, call site `cat == C`) vs
  control `0.0.2.46` (the adopted 2.43 matrix), bank v6.2, three fresh sp1 seeds, six serial arms on
  the idle endpoint. Rule pre-registered 10:04 CET before any row. Verdict: **MEASURED and ADOPTED** —
  6 live control target cells; 2 evented conversions (C-ex6-00 r19/r20, both v47 events, winners
  note-free); guards clean (6/6 fires on C, zero in control, zero C regressions, frozen bands
  silent); C pool 18/24 -> 20/24 with the whole effect evented, full pool 209 vs 207 (3W/5L
  p=0.727) at the noise floor and not the basis; energy 19.23 vs 18.85 Wh (−2%, noise). Direct
  negative result published with it: the chronic C-ex6-02 fired 3/3 and converted 0/3 — the retry
  repeats the same omitted candidate (biased draw, selection spent, no further resampling stamp may
  target it). `harness_git_sha` `1a590a1` named in all six run records — the 0.0.2.46 provenance fix
  proven live. **Adopted line moves to `0.0.2.47`** (`PAIR-246-V62.md`, decision record
  `history/agent-decisions/2026-11-07-pair246-c-best2-set-adopted-line-moves-to-247.md`, arms
  `v6-results/pair-246/`).
- **Bank v6.3 -> v6.4 closed the B-ex6-04 root cause the same day (7 Nov)** — cadence-246 had
  established the cell as a bank defect; it turned out to carry **two independent unstated-contract
  defects**. v6.3 (`73f7a04d57473545`) states the gold year in the prompt (derived from the gold,
  never typed); the pre-registered probe came back 0/3 — the year fix worked (`2026-04-01` in all
  three rows) and the rows then failed on the second defect: the gold `"2%"` (string) vs an
  unspecified value form, predicted mechanically by the new `scripts/bank_derivability_audit.py`
  `type_form` check before it was probed. v6.4 (`85a0cd0dd6fa1fab`) adds the value-form hint
  (`"число% (например 5%)"`, example deliberately not the gold, leak guard in the builder), one
  field again, all 77 golds byte-identical. Probe vs **fresh** 0/3 controls at identical sp1 seeds:
  v6.2 0/3, v6.3 0/3, **v6.4 3/3 strict** — verdict per the frozen rule: **v6.4 is the WORKING hard
  bank**, B-ex6-04 leaves the defect queue, v6.3 stays published as PROVISIONAL. Nine probe arms
  in `v6-results/bank-probe-634/` (contour event chains byte-identical across all nine — only bank
  bytes moved); byte-level changelog `bank-defect-v63-v64-changelog.md`; decision record
  `history/agent-decisions/2026-11-07-bank-v64-working-b-ex6-04-defect-closed.md`. A raw-arm
  fairness probe (owner rule "a fixed gold must lift the RAW arms") **passed 3/3 on every raw
  arm** under v6.4 — bare basalt 3/3 (no regression from its earlier year-guess), ChatGPT-codex
  and Grok flip 0/3 -> 3/3 with byte-exact answers — so the cell is **FAIR** and closed at the
  bank level with nothing claimed for the contour line (`fair-rows.md` in the probe dir).
- **Cadence-249 re-ran all four arms on bank v6.4 the same day (7 Nov)** and confirmed the
  bank **FAIR** on fresh independent seeds: the `B-ex6-04` lift signature reproduced exactly
  (codex/grok/contour 0/3 -> 3/3, basalt's year-guess 3/3 holds) and no raw pool regressed
  beyond the noise floor — every pool movement mapped to byte-identical categories or to the
  one corrected cell. Contour common set **170/183** vs basalt 144 (W31/L5, p=1.3e-5), codex
  131 (W43/L4, p=2.8e-9), grok 134 (W39/L3, p=5.6e-9) — contour > basalt > grok > codex holds
  on v6.4; the adopted 0.0.2.48 K-fields gate shows on brand-new seeds (K 12/12 vs 6/12 raw,
  K-ex6-03 3/3). Rule-(c) byte re-score: 0/183 mismatches. Retracted within the same hour
  (16:47 CET correction): the first publication reported a `_loop_rows` storage gap and
  non-replayable loop cells — that was a re-scorer lookup error; loop trajectories are stored
  (`agent_steps` + the pinned adapter mapping), all 18 loop cells now replay offline with
  0 ledger mismatches (strict 17/18 = the published column); only category E (docker battery)
  stays offline-non-replayable. Tooling
  fix shipped with the correction: the cadence scorer hardcoded its CSV arm label (now derived
  from run records) and now replays loop rows itself. Artifacts `v6-results/cadence-249/`, writeup `CADENCE-249-V64.md`,
  decision record `history/agent-decisions/2026-11-07-cadence249-v64-fair-contour-margin-holds.md`.
- **Bank v6.5 published as PROVISIONAL (7 Nov, 17:35-17:45 CET)** — closes the second
  defect from `bank-defect-b04.md`, open since v6.1: H-ex6-01's reference asks
  `requires: ["аудит-лог operations"]` but the prompt never names the artifact, so a
  faithful paraphrase is zeroed by the frozen scorer's stem matcher. One scenario
  sentence added (v6.5 `cd29d6ac94dc3267`, gold byte-identical, `scripts/verify_bank_v65.py`
  proves the ask becomes `_token_cover`-derivable only after the fix). Paired contour
  probe at 6 matched seeds: 5/6 vs 5/6 — the cell is a contour-line LOTTERY (the
  cadence-249 0/3-on-all-arms pattern was seed correlation), so the frozen rules keep
  v6.5 provisional; the derivability fix stands mechanically. Raw-arm fairness probe
  exposed DEFECT 2: basalt/codex/grok all 0/3 with every zero `ungrounded_claims` —
  the `"claims": [утверждения как факт]` field spec invites listing the partner's
  assertions while the hidden contract demands `[]`; v6.6 queued for that one field.
  Disclosure: the contour passes this cell via the `v219_h_clear_claims` repair, not
  model capability. Artifacts `v6-results/bank-probe-65/`, decision record
  `history/agent-decisions/2026-11-07-bank-v65-provisional-defect2.md`.
- **Bank v6.6 published and PROMOTED to working (7 Nov, 18:22-18:40 CET)** — closes
  defect 2 with exactly one field: the H-ex6-01 claims spec
  `[утверждения как факт]` -> `[только утверждения, подтверждённые твоим журналом; если
  подтверждений нет — пустой список]` (v6.6 `5c86252b2ef2f422`, gold byte-identical,
  `scripts/verify_bank_v66.py` PASS; v6.5 stays provisional with its frozen verdict).
  Rules frozen in REVIEW-INBOX before any row: raw fairness at the SAME matched reps
  28/29/30 — FAIR: ChatGPT-codex 0/3->3/3, Grok 0/3->3/3, bare basalt 0/3->2/3 (the
  surviving zero re-attributed from answer bytes to a NEW narrower mode, kept as an
  observation, not a defect); contour no-new-loss legs p66r28-30 3/3 PASS, conversion
  UNMEASURED by construction (controls passed), wiring live (`bank_version=v6.6
  source=marker`); answer-bytes bonus: `v219_h_clear_claims` fired 3/3 on v6.5 legs,
  0/3 on v6.6 — the model's own answer now satisfies the contract on this cell.
  Coverage limit published: the old fragment stays in H-ex6-00/02/03/04 until those
  cells show measured defects. Artifacts `v6-results/bank-probe-66/` (subset bytes
  `1b990aa6fc9a25dd`, per-row identity), changelog `bank-defect-v66-changelog.md`,
  decision record `history/agent-decisions/2026-11-07-bankv66-claims-spec-promoted.md`.
- **Derivability scanner versioned: audit-v2 released (7 Nov, 19:28-19:44 CET)** —
  `scripts/bank_derivability_audit_v2.py` (self-sha16 `ac4516f263e3e8f2`) stamps every
  census with scanner version + bank sha16 + scorer contract id, and adds H
  `ask`/`unknown` atom coverage that mirrors the frozen contract's own `_token_cover`
  matcher: on v6.1–v6.4 it mechanically flags exactly the published H-ex6-01 defect
  (`h_absent`), and v6.5/v6.6 come back H=0 — the class is now catchable at bank-build
  time with zero arms spent. audit-v1 stays byte-frozen and its chain recomputes
  exactly: 39 (v6.2) → 38 (v6.3) → 37 (v6.4–v6.6); v2 with `cats=ABK` reproduces v1's
  hit set on all six banks (`harness/audit_v2_scanner_test.py`, 27 checks, in CI).
  Queue effect: H-ex6-00/02/03/04 atoms are all directly nameable, so the census cannot
  license the queued H-family claims-fragment change by itself — it stays behind
  answer-byte arm evidence. Chain of record `benchmarks/hard/DERIVABILITY-CENSUS.md`,
  outputs `v6-results/audit-census-v2/`, no harness/contour bytes moved (stamp stays
  0.0.2.50, behavior 2.48).
- **Cadence-255 re-ran all four arms on bank v6.6 (8 Nov, 03:00-06:27 CET)**, due on both
  frozen clauses (5 measured stamps since cadence-249 AND two bank re-words). Bank FAIR:
  the fixed H-ex6-01 lifted all three raw arms 0/3 -> 3/3 on fresh reps 52-54 (v6.5-probe
  zeros were all `ungrounded_claims`), pooled raw totals hold (basalt 146, codex 135,
  grok 134 vs 144/131/134 at v6.4). Contour margin WIDENED: common 177 vs 146/135/134,
  pooled W/L 37/6, 46/4, 48/5, all p<2e-6; adopted gates hold on brand-new seeds
  (K-ex6-03, A-ex6-03 1/3 -> 3/3, C-ex6-02 0/3 -> 3/3, D-plain 9/9); rule-(c) byte
  re-score 0/201 mismatches; contour digest row `74.7/77 = 97.0%` of the whole bank
  (bank sha16 `590503cf` ws copy, stamp `0.0.2.55`). Grok transport death mid-leg
  (186 rc1 rows, expired oauth token) purged and retried clean per the done-set rule;
  `raw_v6.py` hardened the same window (`err` field, abort after 5 empty answers).
  Artifacts `v6-results/cadence-255/`, writeup `CADENCE-255-V66.md`, decision record
  `history/agent-decisions/2026-11-08-cadence255-v66-fair-margin-widened.md`. Next:
  rebuild the UNSTABLE-CELLS map on the 2.55 line before any new contour hypothesis.
- measured cost and energy (`COST-V61.md`, `ENERGY-METHOD.md`): contour arms cost **0.085-0.089 Wh per
  task** of measured GPU energy (two independent windows: 6.82 Wh and 13.02 Wh), the same model answering
  raw costs **0.468 Wh per task** — a ~5.4× energy difference at a *lower* score; ChatGPT/Grok arms took
  592 s / 1 812 s of answer time with their energy outside this machine's reach
- one-page version: `benchmarks/hard/v6-results/PROOF-V61.md`

## Research direction and testing philosophy

Claryel Autonomous is an open engineering research project, not a standalone product or an academic claim. Beyond controlled local-model benchmarks, we are exploring reliability across imperfect real-world tasks, including errors in instructions, execution, self-evaluation and scoring. Our longer-term direction is **Mix AI**: testing whether local and cloud systems can work together synergistically, with measured quality, safety and cost rather than assumed benefits.

Because models, inference engines, hardware and cloud services change rapidly, we preserve evidence for repeated retrospective analysis and may eventually test uncertainty-aware forecasts and scenarios. These remain open questions, not demonstrated capabilities. See [Research Direction and Testing Philosophy](docs/TESTING-PHILOSOPHY.md).

## Versioning and historical release snapshot

The following table documents an earlier release sequence; it is not a live latest-version claim. Consult `versions/VERSIONS.md` and dated experiment records for subsequent versions.


The version scheme is four digits: `A.B.C.D`.

| part | meaning | current value |
|---|---|---|
| `A.B` | operator release line; the operator changes these first two digits | `0.0` |
| `C` | contour track; `1` is the first contour family, `2` is the second | `2` |
| `D` | revision inside that track: a contour change or a measurement/reporting change | `7` for the K tax-negation contour change |

Every release carries two axes, and every artifact records both:

* **stamped revision** — the identifier used by paired comparisons and feature
  gates;
* **contour behavior** — the newest model-facing contour change that actually
  exists in the code. It moves only when the contour itself changed.

`0.0.2.3`, `0.0.2.4`, `0.0.2.5` and `0.0.2.6` changed measurement or reporting,
not the contour, so their contour behavior stays `0.0.2.2`. `0.0.2.7` is a real
contour change again. A revision number that has not been built does not exist:
nothing between `0.0.2.2` and `0.0.2.7` changed what the model was asked or
given.

Current mapping:

| canonical version | legacy name | contour behavior | meaning | status |
|---|---|---|---|---|
| `0.0.1.9` | `v1.9` | `0.0.1.9` | D action-order normalization | full accepted baseline |
| `0.0.2.0` | `v2.0` | `0.0.2.0` | G/H post-normalization | accepted on Mac pair; B2003 partial |
| `0.0.2.1` | `v2.1` | `0.0.2.1` | H safety normalization | full Mac pair used as baseline; full P3001 complete |
| `0.0.2.2` | `v2.2` | `0.0.2.2` | F diagnostic grounding | full Mac paired run accepted: +0.0438 overall, +0.3259 F, 0 regressions |
| `0.0.2.3` | — | `0.0.2.2` | resource telemetry and documentation policy | measurement release, contour unchanged |
| `0.0.2.4` | — | `0.0.2.2` | full-Mac resource/economic verdict | reporting release, contour unchanged |
| `0.0.2.5` | — | `0.0.2.2` | OS environment records and deterministic docs pass | reporting release, contour unchanged |
| `0.0.2.6` | — | `0.0.2.2` | contour behavior recorded next to the stamped revision in every artifact | measurement release, contour unchanged |
| `0.0.2.7` | — | `0.0.2.7` | K tax-negation flag grounded in the task's own text | candidate contour change; contract tests 10/10, paired A/B pending |
| `0.0.2.8` | — | `0.0.2.7` | engine-stall guard, per-run condition record | measurement release, contour unchanged |

Legacy `v1.x` and `v2.x` names still work as inputs. New reports should use the
canonical four-part form.

## Recorded operational status (historical)

The table below is a dated snapshot, not a live inventory of running jobs.


| item | status as of 2026-11-03 |
|---|---|
| P2005 targeted F smoke | complete; `0.0.2.1 -> 0.0.2.2`, 30 paired rows, 0 regressions |
| Mac targeted F smoke | complete; 30 paired rows, 0 regressions |
| P3001 targeted F smoke | complete; 30 paired rows, 0 regressions, perfect answers 3 -> 30 |
| Mac full `0.0.2.2` paired run | complete with resource telemetry; 2513 paired rows, +0.0438 overall, 0 regressions |
| P3032 full 178-task sweep | complete; adjusted mean 0.9867, adjusted perfect 94.9%, F 1.00 |
| P1005 post-GPU-swap quick sweep | complete; capacity-valid mean 0.9851, F 1.00; full paired A/B still pending |
| B2003 offline replay | complete; recorded F answers replayed through `0.0.2.2`, n=323 |
| P2005 full `0.0.2.1 -> 0.0.2.2` paired run | first attempt stopped: the serve stalled (86 of 298 joined keys on one side, 134 of 298 on the other returned no answer bytes), so its delta of -0.1319 was a box condition — on the 130 keys where both arms answered it was -0.0089; node parking floor raised to 3072 MiB and the pair is re-measured under the 0.0.2.8 stall guard |
| `0.0.2.7` K tax-negation contour | built and tested offline (10/10); paired A/B not started, no acceptance claimed |
| resource telemetry | permanent for full paired gates and hardware-class runs |
| OS environment records | every gate row, ledger row and telemetry header now records Ubuntu version, codename, Desktop/Server flavor and kernel |
| documentation freshness | daily policy added; scheduled check added |

<!-- BEGIN TERMINAL-BENCH-2026-11-04-STATUS -->
| [Terminal-Bench 4.0: independent one-pass run](experiments/terminal-bench/2026-11-04-p2005-tb4-66-verified/index.md) | in progress; 2 / 66 completed, 0 solved, 2 failed; not an official leaderboard run |
<!-- END TERMINAL-BENCH-2026-11-04-STATUS -->

<!-- BEGIN 2026-11-04-P2005-TB4-FAST5-BASELINE -->
| [tb4-fast5-baseline-20261104-070835](experiments/terminal-bench/2026-11-04-p2005-tb4-fast5-baseline/index.md) | 5-task sample; 4 / 5 completed, 1 solved, 3 failed; not an official leaderboard run |
<!-- END 2026-11-04-P2005-TB4-FAST5-BASELINE -->

## Historical measured results

The numbers below are paired where they compare versions. Raw means across
different plan mixes are not comparable.

### F diagnostic grounding, targeted subset

`0.0.2.1 -> 0.0.2.2`, same task, same repetition, same seed:

| machine | pairs | answer score | better | unchanged | worse |
|---|---:|---:|---:|---:|---:|
| P2005 | 30 | 0.7167 -> 1.0000 | 29 | 1 | 0 |
| Mac Studio | 30 | 0.7500 -> 1.0000 | 30 | 0 | 0 |
| P3001 | 30 | 0.7167 -> 1.0000 | 27 | 3 | 0 |

Recorded B2003 `0.0.2.1` F answers replayed offline through `0.0.2.2`:
n=323, every F task average becomes 1.0000.

### Resource and cost side of the answer

The P3001 RTX 3060 12 GB targeted F smoke with 1 Hz telemetry measured:

| metric | value |
|---|---:|
| answer mean | 0.9944 |
| perfect attempts | 29 / 30 |
| latency median | 5.88 s |
| latency p95 | 7.96 s |
| peak VRAM used | 11,385 MB of 12,288 MB |
| VRAM headroom | 903 MB |
| peak GPU power | 113.4 W |
| estimated GPU energy | 0.15 Wh per attempt |

The important engineering lesson: answer quality alone can look acceptable
while the 12 GB GPU is already near its safe memory boundary. This is why
resource telemetry is now part of the testing method.

## How to use it

The runner uses Python standard library only. It works with any OpenAI-compatible
endpoint:

```bash
git clone https://github.com/ViktorIXAI/claryel-autonomous
cd claryel-autonomous
./install.sh
cp config.example.sh config.sh
source config.sh
bash run_gate.sh
python3 harness/gate_report.py
```

Set `PARB_API`, `PARB_MODEL`, `PARB_KEY_FILE` and `PARB_BOX` in `config.sh`.
For full paired gates, also set `PARB_TELEM` to a JSONL path; `run_gate.sh`
then starts the resource collector automatically and stops it when the run
finishes.
Select a contour generation with `PARB_GATE_VERSION`, for example `0.0.2.2`.

For paired A/B work, keep the same plan, task bank, per-task seeds and machine
passport. The method is documented in
[`docs/reproduction-guide.md`](docs/reproduction-guide.md).

## Documentation policy

The landing page is maintained daily and checked by a script. It must remain
short, dated, structurally stable and free of inflated self-labeling. See
[`docs/documentation-policy.md`](docs/documentation-policy.md).

The daily check verifies:

- required README sections;
- a `Status checked:` date no older than one day;
- local links that still exist;
- forbidden public self-labels;
- version statements that point to the current versioning map.

## Source and citation policy

The operator reads scientific, economics and sociology articles and cites them
when useful. External sources are recorded as methods, context, comparisons or
warnings. They are not used as automatic proof of this repository's results.
See [`docs/source-policy.md`](docs/source-policy.md) and
[`sources/reading-list.md`](sources/reading-list.md).

## Where the evidence lives

**Everything is published on `main`** — code versions, every benchmark arm, scoreboards,
pair reports and decision records. No results live on side branches; if a branch other
than `main` is mentioned anywhere, it is scratch work and is not the record.

For the current hard-bank series (bank v6, 77 tasks): [`benchmarks/hard/v6-results/LADDER.md`](benchmarks/hard/v6-results/LADDER.md)
is the version-by-version ladder (contour 0.0.2.16 -> 0.0.2.23 measured arms, per-category
strict, verdict against the raw arms), `benchmarks/hard/v6-results/full-2NN/` holds each
arm's answers, ledgers, log and run-record, and `scripts/ladder_v6.py` regenerates the
ladder from those artifacts so no number in it is prose.


| area | location |
|---|---|
| version chronology | [`versions/VERSIONS.md`](versions/VERSIONS.md) |
| full results and summaries | [`results/summary-full.json`](results/summary-full.json) |
| independent second-opinion scorer | [`analytics/second_opinion.py`](analytics/second_opinion.py), [`results/independent-scorer.md`](results/independent-scorer.md) |
| hold-out bank | [`benchmarks/holdout/`](benchmarks/holdout/), [`results/holdout-mini.md`](results/holdout-mini.md) |
| resource telemetry | [`telemetry/README.md`](telemetry/README.md) |
| hardware passports | [`hardware/`](hardware/) |
| failures and rejected versions | [`history/failures/failures.md`](history/failures/failures.md) |
| agent decision log | [`history/agent-decisions/gate-versions.en.md`](history/agent-decisions/gate-versions.en.md) |
| open engineering and economic questions | [`docs/open-questions.md`](docs/open-questions.md) |

## Repository map

```text
docs/        operating policy, methodology, source policy, limitations, roadmap
harness/     runner, contour gates, validators, fixers, tests
benchmarks/  task banks, visual benchmarks, performance and privacy boundaries
versions/    version records, including rejected versions
history/     decision logs, failures, rollbacks, external inputs
hardware/    machine passports and measured hardware profiles
telemetry/   resource sampler, join tools, overhead notes
results/     summaries, paired deltas, independent validation notes
schemas/     schemas for runs, telemetry, hardware and experiments
analytics/   reproducible aggregation scripts
logs/        artifact index and samples
prompts/     contour prompts used in measured runs
experiments/ A/B runners and classification helpers
```

## What "self-improving" means here

The model weights are frozen. The measured improvement is the software around
the model: gates, validators, retries, repair paths, safety blocks and
measurement tooling. This is not a claim that the model's weights have learned
to improve themselves.

## Updates

Announcements are published on X: [@uctive](https://x.com/uctive).
Owner profile: [LinkedIn](https://www.linkedin.com/in/viktor-khudiakov-44a5447b).

MIT licensed. Keep the decision logs if you fork this: the failures and rejected
versions are as important as the accepted ones.
