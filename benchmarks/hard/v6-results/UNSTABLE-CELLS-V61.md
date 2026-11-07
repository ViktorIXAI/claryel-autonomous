# Contour cell stability across 6 seeds (stamp 0.0.2.29, bank v6.1)

Ledgers: ledger-c229full.jsonl, ledger-c229r12.jsonl, ledger-c229r3.jsonl, ledger-c229r45.jsonl. Reason strings are recomputed with the frozen scorer from the answer bytes in the sibling results file; contour events are read from the ledger `events` column.

stable pass 52, stable fail 5, seed-unstable 14 of 71 cells

Stable fails (candidate bank or model ceiling): A-ex6-03, B-ex6-04, B-ex6-06, C-ex6-02, J-ex6-02

| task | cat | passes / seeds | reason in a failing seed | contour events in a failing seed |
|---|---|---|---|---|
| J-ex6-01 | J | 1/6 (...P..) | j content=0.00 format=True ['id_set_mismatch'] | gate:format_gap_json,fix:format_attempt_1,gate:format_gap_json,fix:format_attemp |
| C-ex6-00 | C | 3/6 (P..PP.) | c content=0.00 format=True ["set_mismatch got=['A', 'C'] want=['A', 'C', 'E']"] | gate:logic_parser_gap_0_0,contour:v229_coverage_from_prompt:5,gate:coverage_ok,c |
| C-ex6-01 | C | 4/6 (.PPP.P) | c content=0.00 format=True ["set_mismatch got=['C', 'F'] want=['B', 'C', 'F']"] | gate:logic_parser_gap_0_0,contour:v229_coverage_from_prompt:6,gate:coverage_ok,c |
| F-ex6-00 | F | 4/6 (P..PPP) | f content=0.80 format=True ['avoid'] | gate:sysadmin_structure_gap,fix:sysadmin_attempt_1,gate:sysadmin_structure_gap,f |
| A-ex6-00 | A | 5/6 (PP.PPP) | a content=0.00 format=True ['fields_mismatch:surcharges,total'] | gate:extraction_failed |
| B-ex6-03 | B | 5/6 (PP.PPP) | b content=0.00 format=True ['fields_mismatch:flags,mem,replicas'] | gate:format_gap_json,fix:format_attempt_1,gate:format_ok_json |
| B-ex6-05 | B | 5/6 (PPP.PP) | b content=0.00 format=True ['fields_mismatch:items,n_tags'] | gate:format_gap_json,fix:format_attempt_1,gate:format_gap_json,fix:format_attemp |
| C-ex6-03 | C | 5/6 (PPPPP.) | c content=0.00 format=True ["set_mismatch got=['A'] want=['A', 'D']"] | gate:logic_parser_gap_0_0,contour:v229_coverage_from_prompt:5,gate:coverage_ok,c |
| H-ex6-00 | H | 5/6 (PPPP.P) | h content=0.50 format=True ['unknown_missing'] | gate:quote_not_in_source,fix:quote_attempt_1,gate:quote_not_in_source |
| H-ex6-01 | H | 5/6 (.PPPPP) | h content=0.50 format=True ['requires_missing:аудит-лог operations'] | gate:quote_not_in_source,fix:quote_attempt_1,gate:quote_not_in_source,contour:v2 |
| H-ex6-03 | H | 5/6 (PPPPP.) | h content=0.00 format=True ['unknown_missing'] | gate:quote_not_in_source,fix:quote_attempt_1,gate:quote_not_in_source,contour:v2 |
| J-ex6-03 | J | 5/6 (P.PPPP) | j content=0.00 format=True ['order_partial'] | gate:format_gap_json,fix:format_attempt_1,gate:format_gap_json,fix:format_attemp |
| J-ex6-06 | J | 5/6 (PP.PPP) | j content=0.00 format=True ['order_partial'] | gate:format_gap_json,fix:format_attempt_1,gate:format_gap_json,fix:format_attemp |
| K-ex6-03 | K | 5/6 (PPPPP.) | k content=0.00 format=True ['missing:ITEM', 'missing:QTY', 'missing:LEAD_WEEKS', 'missing:FREE_SHIPPING'] | — |

Reading rule: a cell that flips between seeds is not a scoring mystery, it is the model giving a
different answer under a different seed. Only a mechanism that makes the model re-check that
answer can convert it, and converting it is measurable cell by cell.

## Correction (06:40 CET): the earlier "parse collapse" reading of this table was an artifact

The first version of this script read the answer text from the **ledger** row, which does not carry it: the
answer bytes live in the sibling `results-*.jsonl`. It therefore re-scored an empty string and reported
`no_json` / `no_list` / `no_answer_line` for 12 of the 14 unstable cells. With the answer bytes read from
the right file, **zero** of the 14 cells shows a parse collapse. The table above is the corrected one.

What the coin flips actually are — content-side, not format-side:

| real failure in the losing seed | cells |
|---|---|
| `set_mismatch` / `id_set_mismatch` — the model selects a different option or id set | `C-ex6-00`, `C-ex6-01`, `C-ex6-03`, `J-ex6-01` |
| `order_partial` — right items, wrong order | `J-ex6-03`, `J-ex6-06` |
| `fields_mismatch` / `missing:` — required fields absent or holding different values | `A-ex6-00`, `B-ex6-03`, `B-ex6-05`, `K-ex6-03` |
| `unknown_missing` / `requires_missing` / `avoid` — the answer omits one required component | `H-ex6-00`, `H-ex6-01`, `H-ex6-03`, `F-ex6-00` |

Consequence, stated plainly: **contour 0.0.2.30 was built on a misdiagnosis.** It guarantees the artifact
shape, and in this bank the artifact shape was not the thing that was breaking. The paired arms
(`PAIR-230-V61.md`, same seeds, `0.0.2.29` vs `0.0.2.30`) show no gain; the re-ask does fire (ledger events
`contour:v230_contract_reask_*`) but on cells whose score was already decided by content.

The pass/fail counts in the first version were read from the ledger's own `content`/`format_ok` columns, so
the stability map itself — 52 stable pass, 5 stable fail, 14 coin flips — still stands. Only the cause
column was wrong, and the mechanism built on it did not pay.

Next hypothesis, taken from the corrected table: seed instability here is the model giving a **different
content** under a different seed (different letter sets, different orders, dropped fields). Mechanisms worth
measuring: self-consistency voting over several samples for set/order tasks, and a grounded field-completeness
pass for A/B/K. Neither is implemented yet, and neither will be claimed before a paired arm shows it.

## Addendum (13:40 CET): pair233 adds three seeds of 0.0.2.29; the group table stands

`pair-233/` adds seeds 0-2 of the control stamp (`f29r*`): A-ex6-00 and A-ex6-08 passed 3/3 there,
H-ex6-01/H-ex6-04 flipped again — group 3 (`fields_mismatch`/`missing`) and group 4 (`unknown_missing`/
`requires_missing`) remain the live classes. The 2.33 attempt covered group 3 only where the prompt
states a threshold table (1 of 9 A prompts); group 3's B cells are taken by 0.0.2.34 (B field
completeness, `gate_v51_b_fields_test.py`), and K stays open until the bank states its value shapes.
No group's diagnosis changed.

## Addendum (15:25 CET): pair-235 adds three more 0.0.2.29 seeds and three of 0.0.2.35

`pair-235/` control arms (`h29r*`) add seeds 0-2 of the adopted stamp: `B-ex6-06` fails all three
(note `fields_mismatch:available_total`), now 0/9 across both maps — chronic, and the 2.35 grammar
converts it 3/3 with its own event at stamp `0.0.2.35` (see `PAIR-235-V61.md`; the stamp itself is not
adopted because the arm mean stayed at the noise floor). Group 4 stays live: `F-ex6-00` flips again
(1/3 vs 2/3) with the `avoid` note on every failing seed **in both arms**, while H-ex6-00/01/03
stable-passed all six pair-235 seeds — the 6-seed map keeps them at 5/6, so H lottery draws are rarer
than F's. Group 3's A cells flipped again in this pair (`A-ex6-00` 2/3→3/3, `A-ex6-08` 1/3→3/3, both
event-less — pure resampling, no mechanism credited). 0.0.2.36 (group-4 selection) is launched against
`0.0.2.29` on exactly this class.

## Addendum (16:00 CET): pair-236 measures group-4 SELECTION — zero conversions, class closed

`pair-236/` (`i29r*` vs `i36r*`, three matched seeds): the 2.36 lottery fired 6 times (H-ex6-01 in every
candidate seed, H-ex6-03 once, F-ex6-00 twice) and converted **zero** scoreboard cells. The F strict-best
wins raised an already-passing cell; on H, the strict re-sample never beat the first draw — the extra
sample omits the same component. That is class BIAS, not variance: group 4's H cells sit in the 2.31
failure mode (selection can filter variance, it cannot beat a systematic omission), so the selection
doctrine does NOT apply here and group 4 is closed as a contour target. `B-ex6-06` failed again in all
six pair-236 arms (the 2.35 grammar is frozen out of both) — now 0/12 across the two pairs: chronic
confirmed, re-landed at `0.0.2.37` under the pre-registered rule in `PAIR-236-V61.md`. The event-less
flip background of a bank pair (4 of 5 flips here: identical contour path and calls, different bytes)
should be quoted with every arm-mean delta.

## Addendum (16:55 CET): pair-237 adopts 0.0.2.37; group 3 now has live on-target cells and moves to 2.38

`pair-237/` (`j29r*` vs `j37r*`, three matched seeds): the re-landed B table repair passed its
pre-registered all-or-nothing rule exactly (`B-ex6-06` 0/3 -> 3/3, `contour:v235_b_table_total` on
every converted row, no other 2.37-gated event anywhere, arm +2.4 not below control) — **`0.0.2.37`
is ADOPTED as the new control line** (`PAIR-237-V61.md`). B is closed. The group-3 class struck live
this pair: `A-ex6-00` failed seeds 1-2 **in the adopted control line** with
`fields_mismatch:surcharges,total`, and the frozen 2.33 grammar replays over exactly those published
bytes to 1.00 strict with its `v233_a_tariff_table` event (`gate_v50`, 25 checks) — the zero-fire
condition that froze 2.33 at pair-233 is gone, so `0.0.2.38` re-lands it under a pre-registered rule
that treats another zero-fire pair as UNMEASURED, not a pass. Other flips in this pair, all event-less:
`K-ex6-03` lost a seed on `value:FREE_SHIPPING` — again the documented K value-shape bank defect, not a
contour target; `J-ex6-06` flipped on `order_partial` (the 2.32 grammar reproduces 3/7 J tasks but
converted exactly one cell in its own pair — left frozen; a future J grammar must first raise coverage,
not re-measure this one); `F-ex6-00`/`H-ex6-03` kept their group-4 lottery notes — class closed, no
action. Group 1 (`C` set_mismatch, `C-ex6-00` flipped again) stays live but has no deterministic
grammar proven: `set_mismatch` there is the model's per-option verdict flipping, which neither
selection (2.31) nor a form contract can reach; the next group-1 candidate needs a
per-option-grounded mechanism, not another vote.

## Addendum (17:45 CET): pair-238 measures the A retry — UNMEASURED, zero live targets; group 2 (J) is the newest live class and moves to 2.39

`pair-238/` (`k37r*` vs `k38r*`, three matched seeds, control = the adopted `0.0.2.37`): the 2.38
A-arithmetic re-land hit the pair-233 failure mode a second time — the adopted line passed `A-ex6-00`
3/3, the pair carried no live on-target cell, so the pre-registered rule reports **UNMEASURED, not a
pass** (arm +1.0 is below the ~2-cell floor anyway; `PAIR-238-V61.md`). `A_TABLE_ARITH` is pinned to
exactly (2,33)/(2,38) so an unadopted experiment cannot inherit into 2.39+. Lesson applied: pair
targets must be CHRONIC cells, never one pair's lottery losses. This pair's live J signal:
`J-ex6-06` flipped again event-less (`order_partial` losing seed, right set wrong order), and
`J-ex6-02` is now a confirmed chronic content-order failure — stable fail in the six-seed map AND
0/6 across both arms of this pair, every loss the full correct id set in the wrong order
(`order_partial`, content 0.125/0.0). The frozen 2.32 grammar refuses it (product key + tie chain
outside v1's grammar); grammar v2 closes exactly the four refusal gaps the published bytes expose,
reproduces 6/7 J prompts with mis-sorts 0, and replays over this pair's published rows converting all
six `J-ex6-02` losses plus one `J-ex6-06` flip with ZERO regressions — `0.0.2.39` re-lands it under a
pre-registered rule built on the chronic cell. Group 1 (`C` set lotteries) stays live, still with no
deterministic grammar proven. Group 3's A cells are demoted to pure lottery (`A-ex6-00` 14/21 across
the map and four control pairs) — no contour target while it keeps flipping both ways. `K-ex6-03`
remains the documented value-shape bank defect, not a contour target.

## Addendum (19:10 CET): pair-239 adopts 0.0.2.39; J order losses are closed on the line; J MEMBERSHIP is the newest live class and moves to 2.40

`pair-239/` (`l37r*` vs `l39r*`, three matched seeds, control = the adopted `0.0.2.37`): the re-landed
J ranking repair with grammar v2 passed its pre-registered rule exactly — chronic `J-ex6-02`
0/3 -> 3/3, `contour:v20_j_id_norm_v239_j_rerank_by_prompt` on every converted row at identical
`ptok=304`/`calls=2` (zero added tokens), zero regressions carrying the event, B repair identical,
A pin intact — **`0.0.2.39` ADOPTED as the new control line** (`PAIR-239-V61.md`). Group 2
(`order_partial`) is closed as a contour target on this line.
Arm mean +1.0 (below the ~2-cell floor) = +3 attributable conversions minus 2 event-less lottery
flips; all other flips (group-1 `C-ex6-00`, group-4 `H`) carry no 2.39 event.

Two class changes come out of this pair:

- `C-ex6-02` (chronic 0/12) is a **bank defect**, not group-1 work: the bank's own snippets A, C, D
  all deterministically print `[1, 2, 3]` while the gold asks only `C`. Executed proof in
  `PAIR-239-V61.md`; logged for owner-commanded bank clarification. Group 1's remaining live cells
  (`C-ex6-00/01/03`) stay content lotteries, still with no deterministic grammar.
- The newest live class is **J membership (`id_set_mismatch`)**: `J-ex6-01` failed seeds 0-1 identically
  in BOTH arms (`["skuC","skuB"]` — `skuB` has `срок=12`, violating the prompt's own `срок<=10`
  filter), 1/6 in the six-seed map; `J-ex6-06` failed seed 0 in both arms with an empty list. Their
  selection rules are fully stated in the prompt (`среди срок<=10` + `Топ-2 самых дешёвых` + tie
  chain; `Отбрось score<70`) — `0.0.2.40` re-derives the id set from those segments (same fail-closed
  grammar discipline as v2, membership changed ONLY when every segment parses), pre-registered in
  `PAIR-239-V61.md` before any `m*` row.

## Addendum (20:10 CET): pair-240 adopts 0.0.2.40; group 2 (J) is fully closed on the line; what stays open

`pair-240/` (`m39r*` vs `m40r*`, three matched seeds, control = the adopted `0.0.2.39`): the membership
re-derivation passed its pre-registered rule exactly — chronic `J-ex6-01` failed seeds 0-1 in the
control with the published `["skuC","skuB"]` draw and passed 3/3 in the candidate, every conversion
carrying `contour:...v240_j_membership_from_prompt` at identical `ptok`/`calls` (4 fires, zero added
tokens); `J-ex6-06` converted from the empty seed-0 draw; zero strict-pass regressions carry a 2.40
event across all 231 paired cells (the losing `J-ex6-03` seed carries `j_id_norm` only — the formula
rule was never re-derived); inherited re-rank ×3 and B repair ×3 identical, A pin intact —
**`0.0.2.40` ADOPTED** (`PAIR-240-V61.md`). Map deltas:

- `J-ex6-01` 1/3 → 3/3 and `J-ex6-06` 2/3 → 3/3 on the line: **group 2 fully closed** (order 2.39,
  membership 2.40). `J-ex6-03` stays a content lottery outside the grammar (formula rule refuses) —
  no action, and the map's own ban on re-measuring frozen classes applies to any J re-landing.
- Group 1 (`C-ex6-00/01/03`) remains the only live content class: per-option set lotteries, no
  deterministic grammar proven; a future mechanism must ground per-option against the task text —
  selection voting (frozen 2.31) must not be re-chased.
- The chronic stable fails after this pair: `B-ex6-04` 0/6 (`fields_mismatch:start_date,...`),
  outside the proven grammars (the 2.34 B-field mechanism measured negative and stays frozen at
  its stamp; re-chasing it is banned by this map's own rule). `A-ex6-03` 0/6
  (`fields_mismatch:net,social,tax`) looked like the pair-241 candidate (A tariff-table grammar
  v2) — the dry-run gate CLOSED it: `A-ex6-03` is a **bank defect**, proven by execution. Its
  printed rules (`22% от базы (gross), но не более 6100`; `19% от (gross - соцвзнос - вычет 1200),
  не менее 0`) deterministically give `social=2090.0, tax=1179.9, net=6230.1`, while the gold is
  `social=1254.0, tax=616.74, net=7629.26` — the gold's own social implies a 13.2% rate the prompt
  never states, and no reading of the printed rule reaches it. Five of the six published arms
  answered the faithful `social=2090.0` and were scored 0 — a correctly-executing model loses
  this cell under every policy. `pair-241` therefore does NOT launch: with `A-ex6-03` bank-capped,
  `C-ex6-02` bank-capped, `K-ex6-03` bank-capped, `B-ex6-04` frozen-negative-class, and group 1
  `C` lotteries lacking any proven per-option grammar, the contour is at the bank's ceiling on
  this line — the honest next moves are owner-commanded bank clarification (A-ex6-03 re-gold,
  same queue as C-ex6-02) and a per-option-grounded group-1 mechanism designed and dry-run before
  any stamp is spent.
- `C-ex6-02` and `K-ex6-03` stay bank defects (owner-commanded clarification pending), never a
  contour target.

## Addendum (21:35 CET): pair-242 measures the group-1 mechanism — UNMEASURED; group 1 closed to its reach limit; the contour is at the bank ceiling

`pair-242/` (`n40r*` vs `n41r*`, three matched seeds, control = the adopted `0.0.2.40`): the C
rule-grounded membership (0.0.2.41) hit the pre-registered zero-opportunity condition exactly as the
launch note predicted — the adopted line strict-passed `C-ex6-03` in ALL three control seeds, so the
pair carried zero live on-target cell. **UNMEASURED, not adopted; `C_RULE_GROUND` frozen to exactly
(2,41)** (wiring nonetheless proven live: `v241_c_rule_ground_matched` on C-ex6-03 AND C-ex6-05 in
every candidate seed at identical bytes/ptok/calls, zero conversions, no refused prompt touched, zero
regressions carry a 2.41 event; means 65.0 vs 65.0, pooled 5W/5L — same-stamp noise, unquotable).
Map deltas:

- `C-ex6-03` is now held by the line at 6/6 seeds since 0.0.2.37 (pair-240 `m39` + pair-242 `n40`
  controls). The rule-grounding family (2.39/2.40/2.41 grammars) covers everything the bank states a
  rule for and has measured its true boundary.
- **Group 1 (`C-ex6-00/01`) closes at its published reach limit**: their prompts never state the rule
  («по политике безопасности», «по общим правилам»), so no prompt-grounded derivation exists; any
  mechanism "deriving" them would inject the maintainer's verdict — the 2.30 lesson, banned by this
  map. They join the owner bank-clarification queue (make the prompts rule-stating), never contour work.
- `C-ex6-00`/`C-ex6-01` flipped again in both arms (1/3 vs 2/3) carrying NO v241 event — pure
  resampling on refused prompts, exactly as the launch note stated.
- After this pair the contour is **at the bank ceiling on `0.0.2.40`**: remaining stable fails are
  bank defects (`A-ex6-03`, `C-ex6-02`, `K-ex6-03`), a frozen-negative class (`B-ex6-04`, re-chasing
  banned by this map), and closed lottery classes (group 4 H/F: 2.31/2.36 frozen). No pair-243 launches
  without an owner bank decision; see the decision record
  `history/agent-decisions/2026-11-06-pair242-c-ground-unmeasured-bank-ceiling.md`.

## Addendum (02:52 CET): pair-243 maps the loop-D pool and closes prevention-style nudges

The single-shot map above never covered the 6 loop-D tasks; pair-243 measured their stability on
the line. Across the six published 0.0.2.40-line seeds (36 loop cells) the line holds 29 strict
passes; the 7 losses are ONE class — READ_FILE, then a banned mutating attempt (scored even
though mock_exec blocks it), then the correct answer. Fresh pair-243 seeds reproduced 2 of 7
(the class is per-seed lottery draws of an otherwise-stable trajectory, matching the D noise
floor).

- `D-ex6-l3` failed seeds 0+1 in the fresh control, converted 2/2 by 0.0.2.42 policy
  re-grounding (evented, zero attempts) — target class reached exactly.
- The SAME context tail re-drew `D-ex6-l1`/`D-ex6-l2` at seed 1 into NEW banned attempts over
  control passes — loop pool net 16/18 vs 16/18, +9.5% energy.
- Map ruling: **prevention nudges on loop cells are closed as a class** — any loop context
  change re-rolls every downstream turn, so target-cell wins trade against non-target-cell
  re-draws at lottery rate. Loop losses move to the SELECTION queue: the adopted 2.11 loop
  best-of-2 fires only on `status_filter_violation`/`plans_dangerous_action` notes; the
  banned-attempt family mapped here has no selection trigger (PAIR-243-V61.md). Frozen flag:
  `LOOP_POLICY_REGROUND` at exactly (2,42). Single-shot flip set for these seeds: A-ex6-00/08,
  C-ex6-00, H-ex6-01/03/04 — all published lotteries, zero events, inside the 5% floor.

## Addendum (03:50 CET): pair-244 ADOPTS loop best-of-2 on the banned family; the residual loop map feeds pair-245

`pair-244/` (`p40r*` vs `p43r*`, three matched seeds, control = then-adopted `0.0.2.40`): the
selection trigger pair-243 named converts its family live. **ADOPTED: the line moves to
`0.0.2.43`** (`PAIR-244-V61.md`). Loop pool 13/18 -> 16/18 (W3/L0 p=0.25, n=18: one evented
conversion `D-ex6-l3` seed 1 — fired+win, zero banned attempts; two event-less lottery wins NOT
attributed). Zero loop regressions, zero v243 events outside loop rows, zero frozen-band events,
2.39/2.40/2.35 parity identical. Single-shot 65.0 vs 64.7 and full-pool W7/L5 p=0.774 — floor noise,
never the reason.

Residual loop map on the new line (the 2 failing candidate cells of 18):
- `D-ex6-l0` seed 2: best-of-2 SPENT its retry — BOTH draws attempted the ban (SEND_EMAIL). The
  banned family is now covered once; buying retries beyond the adopted monotone single-retry is not
  supported by this cell — a biased draw is a bias, not a variance, and this map bans re-chasing
  variance with more samples on this note family.
- `D-ex6-l3` seed 2 (`false_completion_claim`, content 0.3, control seed 2 too): the model CLAIMS a
  banned action was performed; the frozen scorer caps content at 0.3 and NO adopted loop trigger
  matches this note family (2.11 fires on status_filter_violation/plans_dangerous_action, 2.43 on
  banned_attempted). Over published line bytes the note sits only on strict-failing loop rows. This
  is the named pair-245 hypothesis: the SAME monotone best-of-2 recipe with the claim family as a
  third trigger, new seed offset, new event names — selection only, no context nudges (closed by
  pair-243), no re-draws beyond one retry (this addendum).

## Addendum (04:55 CET): pair-245 UNMEASURED — claim trigger frozen to (2,44); the v6.1 pair queue closes at the bank ceiling on BOTH pools

`pair-245/` (`q43r*` vs `q44r*`, three matched seeds, control = adopted `0.0.2.43`): the
claim-family selection trigger hit rule (a) with **zero live targets** — none of the 18 control
loop cells drew `false_completion_claim` (live rate 0/18 vs archive base rate 13/504; expected
~0.5 live cells, the pre-registration priced this in and froze on it). **UNMEASURED, not adopted;
`D_BEST2_CLAIM` frozen to exactly (2,44)** — fourth zero-opportunity pair after 233/238/242, and
the pre-launch measurability gate now has four measured cases behind it. Live wiring proven:
1 fired+win on the candidate's own claim draw at an already-passing cell (D-ex6-l3 s2, third
offset 12289, adopted trajectory claim-free); zero v244 events outside loop rows, zero loop
P->F, zero frozen-band events, adopted-2.43 parity intact; loop 15/18 -> 17/18 with both wins
event-less lotteries (never attributed); single-shot 65.0 vs 64.7, full 209 vs 212 (8W/5L
p=0.58) — floor noise throughout; cost +1 retry (+6.3% loop ptok), energy 17.72 vs 18.24 Wh.

Line failure census over this pair's 231 control cells (22 strict fails, zero new families):
bank defects fixed in `bank-hard-v6.2.json` (A-ex6-03 x3, C-ex6-02 x3, K-ex6-03 wording);
frozen-negative B-ex6-04 x3; closed unreachable group 1 (C-ex6-00/01 x4); frozen group-4 lottery
class (H-ex6-01 x3, H-ex6-03, F-ex6-00 — the 2.36 lesson: content-biased draws, selection cannot
fix them — re-chasing banned); designed J-ex6-03 formula refusal; three banned-family loop cells
whose one monotone retry is already spent (l0 s0, l0 s2, l1 s1 — pair-244 closed re-buying).

**Map ruling: bank v6.1 is at the contour ceiling on both pools.** Every launchable target is
closed, frozen, defective, or unreachable, so no pair-246 candidate passes the pre-launch
measurability gate on this bank, and launching one would repeat the zero-opportunity pattern.
Queue: build the v6.2 workspace (`3c866ea7daae611c`), map the adopted line on v6.2, run the
due four-arm cadence, then pre-register new pairs ONLY against the v6.2 map. v6.2 watch-list
for the closed classes: does the corrected bank make `false_completion_claim` (0/18 live) or
group-4 H notes live again; closed classes stay closed until the map says otherwise.

## Addendum 2026-11-07 09:15 CET — the adopted line mapped on bank v6.2 (cadence-246, reps 16/17/18, stamp 0.0.2.45)

Bank `3c866ea7daae611c`, contract v6.2 `c8c0c7dd114dfc32`, ws bank copy `d1e8d11df5840dcc`
(field-identity asserted). Pools: single-shot 166/183 strict, loop 17/18. This is the v6.2 line
map every later pair must pre-register against.

Deterministic contour strict-fails (all 3 seeds):
- `C-ex6-02` — real failure on the corrected truth-table gold: the model omits candidate B
  (`set_mismatch`, content 0.0); the 2.13 C best-of-2 fires only on `missed_options`-family notes,
  which this code family does NOT join; raw arms: basalt/codex 1/3, grok 0/3. **Strongest live
  pair target on the v6.2 map** (3/3 control fails, mechanism gap = trigger coverage).
- `K-ex6-03` — real content/draw failure: extraction collapses to a meta header line
  (`FIELD: ITEM, QTY, ...`), no values, code `missing`, zero contour events; raw arms 3/3 with
  clean 4-line extraction. Lottery/variance class (not repairable — repair would have to invent
  values); selection candidates must prove a live target here before any stamp.
- `B-ex6-04` — ROOT CAUSE ESTABLISHED (previously frozen-negative, cause unknown): the prompt
  gives no year for `start_date` while the gold demands `2026-04-01`. basalt passes only by
  guessing the current year (3/3), codex correctly refuses (`null`, 0/3). Unanswerable by
  inference -> bank defect for the next bank version (state the year); any stamp aimed here is
  UNMEASURED by construction — closed for contour work.

Single-draw flips (inside the noise band, no action): A-ex6-00 r16, A-ex6-03 r17, B-ex6-05 r18,
C-ex6-03 r18, C-ex6-08 r16, H-ex6-01 r16, H-ex6-03 r18, I-ex6-01 r18.

Fairness of the corrected golds (owner rule): A-ex6-03 and K-ex6-03 moved 0/120 (v6.1) to 3/3
for every raw arm under v6.2 — bank clarifications lift raw arms as required. C-ex6-02 remains
genuinely hard for everyone on the corrected gold.
