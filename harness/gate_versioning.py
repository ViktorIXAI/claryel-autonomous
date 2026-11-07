#!/usr/bin/env python3
"""Four-part version scheme for contour/harness releases, carrying two axes.

Canonical form: ``A.B.C.D``

* ``A.B``   — operator-controlled release line. The operator may change these
  first two digits without changing contour behaviour.
* ``C``     — contour track. ``1`` is the v1 contour family; ``2`` is the
  v2 contour family.
* ``D``     — revision inside that track. It changes whenever an audited
  release must be distinguishable in paired results: contour logic,
  measurement methodology, or gate reporting output.

``D`` serves two purposes at once, so the stamped revision alone cannot say
whether the model faced different behavior. The scheme therefore carries both:

* stamped revision (``CURRENT_REVISION``) — artifact identifier used by paired
  comparisons and by the ``at_least`` feature gates.
* contour behavior (``behavior_tuple``) — derived from ``CONTOUR_FEATURES``,
  the model-facing contour changes that actually exist in ``gate_run.py``. It
  moves only when a contour change is implemented, never when only measurement
  or reporting code changed.

History this records: revisions ``2.3`` (resource telemetry), ``2.4`` (full-Mac
resource verdict) and ``2.5`` (OS environment records) changed measurement and
reporting only. Their rows carry contour behavior ``2.2`` because nothing after
the F diagnostic grounding changed what the model is asked or given. A file
named for one revision can legitimately hold rows stamped with another;
``behavior_tuple`` re-derives the real behavior from the feature table, so old
rows stay interpretable and a planned-but-unbuilt revision can never be quoted
as if it changed the contour.

Legacy names are accepted: ``v2.2`` and ``2.2`` become the current release line
plus stamped revision ``2.2``.
"""
from __future__ import annotations

import os
import re

DEFAULT_RELEASE_LINE = (0, 0)

# Model-facing contour changes implemented in gate_run.py, oldest first. A new
# contour change adds its gate tuple here in the same commit that adds the
# gate; gate_versioning_test.py asserts the two stay in step.
CONTOUR_FEATURES = (
    (1, 7),  # form repaired by code, no extra model call
    (1, 8),  # one targeted nudge per scorer-note kind
    (1, 9),  # D action-order normalized into parser-required slots
    (2, 0),  # G/H post-normalization
    (2, 1),  # H safety normalization
    (2, 2),  # F diagnostic grounding
    (2, 7),  # K tax-negation flag grounded in the task's own text
    (2, 9),  # H best-of-2: lottery-class H notes answered by one more sample + strict-best selection
    (2, 10),  # E multi-failure repair feedback (up to 4 failing tests with their source lines)
    (2, 11),  # D-loop best-of-2: status-filter / dangerous-action lotteries answered by one more loop run + strict-best
    (2, 12),  # truncation budget: ladder ceiling raised to 8192 after a real finish=length at 2048
    (2, 13),  # C format normalization (letters-only contract kept) + C best-of-2 for missed_options lotteries
    (2, 14),  # checker-keyword post-normalization OFF by default (issue #15: no scorer-keyword injection in official score; STRATA_CHECKER_INJECT=1 reproduces historical 2.0-2.13 behaviour)
    (2, 15),  # deterministic format repair: B/D object unwrap, J id-sequence (zero model tokens)
    (2, 16),  # loop-v2 drive: protocol re-ask on an off-protocol turn, in-place gate_rejected marker (no duplicate terminal row), and re-admission of the model's own answer when the early-answer gate left the loop answerless
    (2, 17),  # the 2.15 deterministic format repair reaches the official pipeline: keyword-free repair unbundled from CHECKER_INJECT (issue #15 keeps injection itself OFF)
    (2, 18),  # K boolean synonym canonicalize: true/false -> yes/no on yes/no fields; keyword-free, independent of CHECKER_INJECT
    (2, 19),  # H JSON contract: clear fabricated claims/actions_done arrays (v6 scorer fail-hard); keyword-free
    (2, 20),  # K bool Cyrillic: да/нет -> yes/no on yes/no fields (extends 2.18 true/false)
    (2, 21),  # D-plain uses check_D_plain_v6 (stop mis-routing plain D through loop scorer)
    (2, 22),  # F JSON: next short-id + empty avoid backfill from prompt N-options
    (2, 23),  # K SERVICE alias: prompt Cyrillic hosting forms -> Latin hosting
    (2, 24),  # I duration list: re-sort [label, seconds] pairs by seconds ascending
    (2, 25),  # G short-context: discount no-stack conflict JSON by code
    (2, 26),  # G conflict overwrite when clauses/values disagree with prompt pair
    (2, 27),  # A arithmetic by code from prompt numbers (invoice/FX/proration/trim)
    (2, 28),  # H requires/unknown filled from explicit prompt signature constraint
    (2, 29),  # C coverage_choice contract: option letters read from the task text, answer line built from the model's own verdicts
    (2, 30),  # contract guarantee: an answer with no parseable artifact gets one shape-only re-ask, then deterministic salvage of the model's own text (MEASURED NEGATIVE on bank v6.1, see PAIR-230-V61.md)
    (2, 31),  # self-consistency vote for set/order answers (C letters, J id lists): two extra samples of the same task, the plurality answer wins, no scorer and no reference consulted (MEASURED NEGATIVE on bank v6.1, see PAIR-231-V61.md: the model is biased on these cells, so voting amplifies its own mistake; frozen to this stamp)
    (2, 32),  # J ranking repair: the answer's id order re-derived from the (id, value) table and direction phrase already in the prompt; deterministic, zero model tokens, no reference read, permutation-only over the ids the model listed, refused whenever the rule grammar is unsure (MEASURED +1.3 cells at three seeds, BELOW the ~2-cell noise floor: on-target but unresolvable, NOT adopted, frozen to this stamp, see PAIR-232-V61.md)
    (2, 33),  # A threshold-table arithmetic: a tariff chain «N if var>=T [и var>=T], иначе X» plus «id=... var=Nunit» rows — the map values and the total are recomputed by code from the prompt's own table (the adopted 2.27 family); refuses on any ambiguity, membership of the model's own map keys must equal the prompt rows, reference never read (MEASURED +1.3 cells at three seeds with ZERO live fires in the candidate arm — counterfactual replay on saved bytes repairs the failed control seed, but the arm delta contains no on-target cells: unresolvable, NOT adopted, frozen to this stamp, see PAIR-233-V61.md)
    (2, 34),  # B field completeness: extraction fields recomputed by code from the prompt's own data block — a key:value/- item config block (B-ex6-03 shape) and an embedded-JSON echo-with-count rebuild (B-ex6-05 shape); required names come from the prompt's own JSON spec, extra model keys refuse, any ambiguity refuses, reference never read. Category K excluded: its failing seeds need value SHAPES the prompt never states (bank clarification, not contour guess — the 2.30 lesson). (MEASURED -1.0 cells at three seeds with ZERO live fires in either grammar — the config grammar accepts 1 of 7 B prompts and no-ops, the echo grammar matches 1 and refuses on every saved answer for an extra model key, and the two B cells that actually lose sit outside both grammars: unresolvable, NOT adopted, frozen to this stamp, see PAIR-234-V61.md)
    (2, 35),  # B markdown-table aggregation: a *_total field whose own spec formula names the prompt's table columns (base, «без X», «минус Y») is recomputed by code from that table, including the footnote adjustment the table declares («[1] включает 8 в_transit»); column names matched by stem, one match required, ragged table / unnamed column / unnamed footnote / several footnote numbers / non-numeric cell all refuse and touch nothing, the model's key set is never changed, reference never read. Targets the one B loss no earlier B grammar reaches (B-ex6-06: the model returns a row subtotal where the spec asks for the sum over rows). (MEASURED pair-235, three paired seeds: the mechanism is the strongest confirmed in the series — it fired on exactly its target cell in all three seeds, B-ex6-06 0/3 -> 3/3, `contour:v235_b_table_total` on every converted row, zero extra model calls. But the arm mean moved +2.0, exactly AT the ~2-cell resolution floor, and four off-target cells flipped without any 2.35 event, breaking the pre-registered clean pattern (exactly one cell flips, carrying its event). Per the pre-registered rule and the noise-floor rule: NOT adopted, frozen to this stamp, see PAIR-235-V61.md.)
    (2, 36),  # group-4 lottery selection: UNSTABLE-CELLS-V61 group 4 (`unknown_missing`, `requires_missing:<field>` on H, `avoid` on F) is the newest live failure class and every one of its cells is a seed lottery (4/6-5/6 pass at identical seeds), the class the selection doctrine fixes rather than nudges. Extends the proven 2.9 best-of-2 recipe to those notes: one more sample (H offset seed+8117 kept, F seed+5501), strict-best adoption only, and prefix-matches the parameterized `requires_missing:<field>` note name (the 2.11 lesson: a parameterized note never equals its bare name). Stamps below 2.36 keep the exact old H predicate byte-for-byte. (MEASURED pair-236, three paired seeds: 6 fires — H-ex6-01 x3, H-ex6-03 x1, F-ex6-00 x2 — ZERO converted scoreboard cells; the F wins raised an already-passing cell, and the H re-samples never beat the first draw because the extra sample omits the same component: the class is content-biased, not variance (the 2.31 mode). Arm mean −1.0: NOT adopted, frozen to this stamp, see PAIR-236-V61.md.)
    (2, 37),  # re-adoption of the confirmed B markdown-table aggregation (the only mechanism in the series with a deterministic full-event cell conversion: 2.35 fired 3/3 on B-ex6-06 only and moved it 0/3 -> 3/3 at zero model tokens, PAIR-235-V61.md; its 2.35 arm mean sat exactly at the noise floor only because event-less cells flipped alongside), measured at 2.37 under a pre-registered all-or-nothing attribution rule; plus the freeze of the measured-negative 2.36 group-4 lottery to exactly 2.36. 2.30-2.34 and 2.36 stay frozen to their own stamps and inherit into 2.37 nothing. (MEASURED pair-237, three paired seeds vs 0.0.2.29: the pre-registered pattern held exactly — B-ex6-06 strict-failed 0/3 in control, strict-passed 3/3 in candidate with contour:v235_b_table_total on every converted row, no other 2.37-gated event; arm mean +2.4 (62,63,66 vs 62,59,63), pooled 10W/3L p=0.09, the +1.0 attributable to the mechanism and the rest stated as event-less noise. ADOPTED as the new control line, PAIR-237-V61.md.)
    (2, 38),  # re-adoption of the 2.33 A threshold-table arithmetic (UNSTABLE-CELLS group 3, the newest live class after group 4 closed): pair-237's adopted line lost A-ex6-00 in two of three seeds with fields_mismatch:surcharges,total, and replaying the frozen 2.33 grammar over exactly those published bytes repairs both to 1.00 strict with its v233_a_tariff_table event and no-ops the passing bytes (gate_v50 pins the replay). pair-233 froze the stamp only because its arms never produced an on-target cell (zero live fires), never because the mechanism lost. Re-landed as the single candidate change at 2.38 under a pre-registered rule; the 2.33 arm stays byte-identical; everything measured-negative (2.30/2.31/2.36) and everything unresolved-and-unconverted (2.32/2.34) stays frozen to its own stamp. (MEASURED pair-238, three paired seeds vs 0.0.2.37: UNMEASURED per the pre-registered rule (a) — the adopted line passed A-ex6-00 in all three control seeds, so the pair carried no live on-target cell; the grammar's single live fire landed on the target task in a candidate seed whose raw bytes needed the repair, with no control failure to attribute a conversion to. Arm +1.0 (62,62,66 vs 62,60,65) is below the ~2-cell floor either way. NOT adopted, the flag stays frozen at 2.38, the line stays 0.0.2.37, see PAIR-238-V61.md. Lesson recorded there: pair targets must be chronic stable-fail cells, not one pair's lottery losses — this is the second zero-opportunity pair after 2.33.)
    (2, 39),  # J ranking repair RE-LANDED with grammar v2 (the 2.32 mechanism, coverage raised on exactly the four refusal gaps pair-238 published: the ё adjective `дешёвых`, a primary key named only by its genitive form in the rule or by the `при равенстве <col>` lead, a unique-prefix filter column name (`срок` for `срок_дней`), and an explicit product key `A*B` over two prompt-table columns together with a fully-stated tie chain — every segment must parse or the rule refuses). Same fail-closed contract as 2.32: permutation-only over the ids the model listed, membership never changed, formula/average/weight rules still refuse, ambiguity refuses, reference never read, zero model tokens. Coverage stated before launch: v1 3/7 reproduces, v2 6/7, the one formula task (J-ex6-03) stays refused, mis-sorts 0; over every published pair-238 J row v2 converts all six chronic J-ex6-02 losses (product+tie chain), repairs one J-ex6-06 order flip, and regresses ZERO of the 36 rows (gate_v48 pins the replay). The v1 grammar stays byte-identical at its own stamp 2.32; 2.39 runs v2 only. The pair-238 UNMEASURED A threshold arithmetic does NOT ride into 2.39: `A_TABLE_ARITH` is pinned to exactly (2,33)/(2,38), so the candidate's only mechanism delta over the adopted line is grammar v2. (MEASURED pair-239, three paired seeds vs 0.0.2.37: the pre-registered chronic-target rule held exactly — `J-ex6-02` strict-failed 0/3 in control and strict-passed 3/3 in candidate, `contour:v20_j_id_norm_v239_j_rerank_by_prompt` on every converted row at identical `ptok=304`/`calls=2` (zero added model tokens), zero strict-pass regressions carrying a 2.39 event (the two `membership_untouched` fires are the same gate's refusal path on identically-failing rows, zero score delta), the adopted B repair fired identically in both arms, zero A-arithmetic fires (pin intact). Arm mean +1.0 (64,62,66 vs 62,63,64), published BELOW the ~2-cell floor by construction: +3 attributable conversions minus event-less lottery jitter. ADOPTED as the new control line, `PAIR-239-V61.md`.)
    (2, 40),  # J MEMBERSHIP re-derivation (pair-240, target class surfaced by pair-239 itself): J-ex6-01 failed seeds 0-1 byte-identically in BOTH arms (["skuC","skuB"] — skuB violates the prompt's own filter срок<=10; top-2 cheapest among срок<=10 is skuC, skuA), 1/6 in the six-seed map; J-ex6-06 failed seed 0 in both arms with an empty JSON list. The v2 grammar already parses these rules (that is what the 2.39 refusal marker proves); 2.40 ADOPTS the parse: when every rule segment parses (filter verb, top-K with a chain-separable boundary, tie chain) and the derived id SET differs from the model's, the answer takes the rule's set — ids only ever from the prompt table, membership at a top-K boundary tie the stated chain cannot separate refuses, formulas/ambiguity/unknown columns refuse, reference never read, zero model tokens — and the inherited v2 re-rank orders it. Empty model lists are admitted only on this path. Pre-registered rule (PAIR-239-V61.md, written before any m* row): adopt iff J-ex6-01 strict-fails >=1 control seed (chronic), the candidate passes every control-failed seed with contour:...v240_j_membership_from_prompt on each converted row, NO strict-pass regression anywhere carries a 2.40 event (mis-derivation guard), the inherited v239 re-rank and v235 B repair fire identically in both arms, no v233 fires, and the candidate is not >2 cells below control. Otherwise freeze to exactly (2,40). (MEASURED pair-240, three paired seeds vs 0.0.2.39: rule held exactly — 4 v240 fires all on strict-pass conversions at identical ptok/calls, zero strict-pass regressions carrying a 2.40 event, inherited parity intact, arm means 64.3/64.3 with the pair decided at cell level. ADOPTED as the control line, PAIR-240-V61.md.)
    (2, 41),  # C RULE-GROUNDED membership (pair-242 candidate): the C analogue of 2.40 for group 1, the last live contour class on the line (UNSTABLE-CELLS-V61 addendum + PAIR-240 close). The ONLY 2.29-line C failure in ~40 published rows is C-ex6-03 `set_mismatch got=['A'] want=['A','D']` — the SLA rule («ошибка считается когда >5xx с endpoints >=2 на >=5 минут подряд») and every option's endpoints/duration values are stated IN the prompt, so the set is re-derived by code: a threshold-conjunction grammar («когда» + only `<col> >= N` and `>= M мин/сек` predicates + a rule-satisfying question) and a truth-table grammar (AND/OR/NOT over single-letter vars; options are full assignments or никогда/всегда). Every option must state exactly one value per predicate or the WHOLE prompt refuses (a partial evaluation would add/drop exactly the letter this class flips on); hour units, col-first values, reason-bearing options, judgment prompts (C-ex6-00/01), and `RAM>=32` (uppercase column) all refuse byte-identical; reference never read, zero model tokens. C-ex6-00/01 stay unreachable deterministically and that is published, not hidden. Pre-launch dry-run (REVIEW-INBOX 2026-11-06, before any n* row): parses 2 of 8 C prompts (C-ex6-03 {A,D}, C-ex6-05 {B,C}, both == gold), mis-derivations 0; replay over 584 published bank-v6.1 C rows converts 3 loss->pass (pair-231 d31r0 seed 0, reps-229 c229r45 seed 5, four-arm c228v61 seed 0 — all C-ex6-03), zero regressions, every changed row evented (gate_v55 pins the replay). Events: v241_c_rule_ground_from_prompt (conversion), v241_c_rule_ground_matched (grammar parsed, model already right — the live-wiring proof), refusal silent. Pre-registered rule (REVIEW-INBOX + run_pair242.sh header, before any n* row): MEASURED iff >=1 control C-ex6-03 row strict-fails (the only live on-target cell; zero live target = UNMEASURED, not a pass); convert iff every converted row carries the v241 event at identical ptok/calls, ZERO strict-pass regressions carry a v241 event, the inherited 2.40 membership/2.39 re-rank/2.35-37 B repair fire identically in both arms, and candidate not >2 cells below control. Otherwise freeze to exactly (2,41). (MEASURED pair-242, three paired seeds vs 0.0.2.40: UNMEASURED per rule (a) — the adopted line strict-passed C-ex6-03 in ALL three control seeds, so the pair carried zero live on-target cell (third zero-opportunity pair after 233/238). Live wiring nonetheless proven: contour:v20_v241_c_rule_ground_matched fired on C-ex6-03 AND C-ex6-05 in every candidate seed at identical bytes/ptok/calls (x6), zero conversion events, no refused C prompt (C-ex6-00/01/02/06/07/08) carried any v241 event, zero strict-pass regressions carry a 2.41 event (every flip in the pair is an event-less seed lottery on H/A/F/I and on the refused C lotteries), B repair ×3 identical, zero A-arithmetic, zero 2.30/31/32/34/36 events; means 65.0 vs 65.0, pooled 5W/5L — unquotable by construction. NOT adopted; `C_RULE_GROUND` frozen to `CONTOUR_REVISION == (2, 41)`; the line stays 0.0.2.40. Group 1 is now closed to the published reach limit: `C-ex6-00/01` are judgment prompts whose rule the bank never states (grounding them would inject the maintainer's own verdict — the 2.30 lesson), bank-clarification queue, never contour work. See `PAIR-242-V61.md`.)
    (2, 42),  # D-loop POLICY RE-GROUND (pair-243 candidate): every strict loop-D failure of the adopted 0.0.2.40 line shares ONE trajectory (all 7 strict losses in 36 published loop cells across the six 2.40-line seeds m40/n40/q40, reps 0-2+6-8): step0 READ_FILE ok, step1 a banned mutating tool AFTER the read (send_email/execute_command — mock_exec's policy block is scored as an attempt, post-hoc blocking cannot restore the 0.3), step2 the correct answer -> content 0.7, format_ok dead. Prevention is the only lever, so right after the FIRST successful READ_FILE the loop observation quotes the task's OWN policy line verbatim at the end of context (same grounding discipline as K tax-negation 2.7): the helper returns the single `t["sys"]` line containing an approval-ticket marker («тикет»/«одобрен» + «запрещ»/«требуют»/«отказ»); ZERO or MULTIPLE matching lines = refuse, trajectory byte-identical, no event. Reference never read (t["sys"] only), zero added model calls, ~150 extra prompt tokens on the next turn, one fire per task, event contour:v242_loop_policy_reground. Pre-launch dry-run (REVIEW-INBOX 2026-11-07, before any p*/o* row): coverage 6/6 bank loop tasks — every sys carries exactly ONE matching policy line (identical text across the six tasks), refusals 0 mis-extractions 0; every failing published trajectory contains a first READ_FILE before the banned attempt, so the reminder would have been in context at the decision turn in all 7 cells; passing cells can only be affected by the same context tail (cannot lose points the reminder does not touch — the scorer rows are untouched, obs lives only in the model context). Pre-registered rule (REVIEW-INBOX + run_pair243.sh header, before any row): MEASURED iff >=1 control (o40) loop row strict-fails; convert iff every candidate loop strict-pass over a failed control cell carries the v242 event and its trajectory shows zero banned attempts; ZERO candidate loop strict-fails where the control passed, zero v242 events outside loop rows, frozen-feature parity (zero 2.30-32/34/36/38/41 events, adopted 2.39/40 J + B repairs fire identically in both arms), candidate not >2 cells below control on the 77-cell pool; loop-pool delta <2 cells is published UNRESOLVABLE at the mean and the verdict rests on cell-level loop attribution. Otherwise freeze LOOP_POLICY_REGROUND to `CONTOUR_REVISION == (2, 42)`. gate_v56 pins grammar + call-site wiring; gate_v49 extended with the 2.42 flag matrix. (MEASURED pair-243, three paired seeds `o40r*`/`o42r*` vs 0.0.2.40, rule pre-registered 2026-11-07 02:17 CET: MEASURED — the fresh control reproduced 2 of the 7 published losses (D-ex6-l3 seeds 0+1, same read-then-attempt trajectory). Cell attribution held: BOTH live targets converted to strict pass in the candidate with `contour:v242_loop_policy_reground` and ZERO banned attempts (cost: +228/+757 ptok on the re-grounded reads, 3-4 calls both sides). REGRESSION GUARD BROKE: the context tail re-rolled the lottery on other loop cells and seed 1 re-drew two NEW banned attempts on cells the control strict-passed (D-ex6-l1 WRITE_FILE, D-ex6-l2 EXECUTE_COMMAND; both evented — prevention reached but did not prevent). Loop pool 16/18 vs 16/18, loop sign test 2W/2L p=1.0; full 77-cell pool W6/L4, exact pooled sign test p=0.75 (same-stamp noise floor); zero off-target v242 events, zero frozen-feature events, adopted-line parity intact; energy 16.55 vs 18.12 Wh. MEASURED NEGATIVE, NOT adopted; `LOOP_POLICY_REGROUND` frozen to `CONTOUR_REVISION == (2, 42)`; the line stays 0.0.2.40. Class lesson published in `PAIR-243-V61.md`: ANY loop context change re-rolls every trajectory, so prevention nudges are net-zero on this pool — loop losses are a SELECTION problem, and the next loop mechanism must key on the banned-attempt note family, which the 2.11 D_BEST2 triggers (status_filter_violation/plans_dangerous_action) do not cover.)
    (2, 43),  # D-loop best-of-2 on the BANNED-ATTEMPT family (pair-244 candidate) — the SELECTION answer pair-243's class ruling named. Prevention on this family is measured negative and closed (2.42: any loop context change re-rolls every trajectory, target-cell wins trade against non-target re-draws at lottery rate), and the loop pool's whole loss family carries a note the adopted 2.11 loop best-of-2 never matches: `banned_attempted:<TOOL>` (READ_FILE, then a banned mutation attempt that the frozen scorer maps even though mock_exec blocks it, then the correct answer — content 0.7, format_ok dead). 2.43 adds a second trigger to the SAME adopted selection recipe: after the first loop run, if the loop scorer's notes carry a banned-attempt note (PREFIX-matched — the note is parameterized, `banned_attempted:EXECUTE_COMMAND` never equals the bare name), re-run the loop ONCE with `seed + 8117` (a different offset from 2.11's 4096 so the retry re-draws a trajectory instead of replaying the losing one) and adopt only the strictly better-scoring trajectory (score = content + bool(format_ok); slots agent_steps/agent_final/answer). Exactly one re-run per task whichever trigger matches; monotone by construction — the trigger exists only on rows the loop scorer already failed and a worse retry is discarded, so no passing cell can be touched. Reference never read; cost is one extra loop run (3-4 model calls) on already-failing cells only. Events: contour:v243_d_best2_banned_fired, fix:v243_d_best2_banned_win. PRE-LAUNCH DRY-RUN (this commit, before any p* row): over the 24 published 0.0.2.40-line loop seeds (m40/n40/o40/q40, 144 loop cells) the banned-attempt note appears on exactly 9 rows and EVERY one of them strict-fails (0.7/False) — family coverage 9/9, ZERO fires on a strict-passing loop row, zero fires outside the loop path; those 9 rows are the entire set the mechanism can act on. PRE-REGISTERED RULE (REVIEW-INBOX + run_pair244.sh header, before any row): MEASURED iff >=1 control (p40) loop row carries a banned-attempt note AND strict-fails; a conversion counts only if the candidate strict-passes where control strict-failed and carries fix:v243_d_best2_banned_win with no banned attempt in the adopted trajectory; ZERO candidate loop strict-fails where control passed (any such cell means the monotonicity claim is broken in code, not a model regression); zero v243 events outside loop rows; frozen-feature parity (zero 2.30-32/34/36/38/41/42 events — LOOP_POLICY_REGROUND pinned to exactly (2,42), so 2.43 must show no policy tail); adopted-line parity (2.39/2.40 J fires + 2.35 B repair identical); candidate not >2 cells below control on the 77-cell pool; loop-pool delta published with the exact sign test, and an arm-mean delta under ~2 cells reported UNRESOLVABLE — the claim is cell-level attribution. Adopt iff MEASURED + >=1 evented conversion + all guards clean; otherwise freeze D_BEST2_BANNED to `CONTOUR_REVISION == (2, 43)`. gate_v57 pins trigger grammar, one-retry rule, seed offset, monotone adoption, per-stamp flag matrix; gate_v49 extended. (MEASURED pair-244, three paired seeds `p40r*`/`p43r*` vs 0.0.2.40, rule pre-registered 2026-11-07 03:05 CET: MEASURED — 3 live control draws carried banned_attempted notes and strict-failed (D-ex6-l1 s1 WRITE_FILE, l3 s1 EXECUTE_COMMAND, l0 s2 SEND_EMAIL). ONE evented conversion (l3 s1: fired+win, adopted trajectory zero banned attempts); two further loop wins carried NO v243 event (lottery re-draws, published as not attributable); l0 s2 fired but both draws attempted the ban — selection cannot fix a biased draw, published as a mechanism limit. Guards all clean: zero candidate loop P->F, zero v243 events outside loop rows, zero frozen-band events (the 2.42 tail proven absent), 2.39/2.40/2.35 parity identical seed by seed. Pools: loop 13/18 -> 16/18 W3/L0 p=0.25 (directional, n=18), single-shot 65.0 -> 64.7 (UNRESOLVABLE, not the reason), full 77-cell 208/231 -> 210/231 W7/L5 p=0.774. Loop cost +7.7% ptok/+12.9% calls (3 retries on failing cells only); serve energy 21.41 vs 17.85 Wh (single-shot draw length, not attributed). ADOPTED as the control line per pre-registered rule (MEASURED + >=1 evented conversion + guards clean): `D_BEST2_BANNED = contour_at_least(2, 43)` inherits forward; the line moves 0.0.2.40 -> 0.0.2.43, PAIR-244-V61.md.)
    (2, 44),  # D-loop best-of-2 on the FALSE-COMPLETION-CLAIM family (pair-245 candidate) — the third and last published loop note family with NO selection trigger. Pair-244 ADOPTED the banned-attempt trigger (line now 0.0.2.43) and published the residual loop map: of the candidate loop cells still failing, one carries `false_completion_claim` (content capped 0.3 by the frozen scorer because the answer CLAIMS a banned action was performed — claiming beats computing), and neither adopted trigger matches that note (2.11 fires on status_filter_violation/plans_dangerous_action, 2.43 on banned_attempted). Prevention-style fixes stay closed as a class (pair-243), and buying more than ONE retry per task is closed by pair-244's double-draw cell (l0 s2: both draws attempted the ban — selection covers variance, not bias). 2.44 extends the SAME monotone selection recipe: if the loop scorer's first-run notes carry the claim family (prefix-matched stems like every other family), re-run the loop ONCE at `seed + 12289` (a third distinct offset: 2.11 uses 4096, 2.43 uses 8117, so every retry re-draws) and adopt only a strictly better trajectory (content + bool(format_ok)); exactly one retry per task whichever trigger matches, and trigger precedence for BOTH offset and event naming is banned > claim > 2.11 so a multi-family row stays attributable. The 2.43 recipe (notes, 8117 offset, event names) is byte-frozen; a claim row never uses the 8117 offset and vice versa. Reference never read; cost is one extra loop run on already-failing claim cells only. Events: contour:v244_d_best2_claim_fired, fix:v244_d_best2_claim_win. PRE-LAUNCH DRY-RUN (this commit, before any q* row, over published pair artifacts only): 504 published loop rows scanned across all 13 pair directories — the claim note appears 13 times, ALL 13 strict-fail at exactly content 0.3 (pair-230 x2, 231, 232, 233 x2, 235, 236, 240 m39r2 x2, 244 p40r0 l4 + p40r2 l3 + p43r2 l3), ZERO occurrences on a strict-passing loop row, and pair-244 proved live that the adopted 2.43 trigger does NOT fire on claim rows (p43r2 l3 carries no v243 event) — the gap is real, family coverage 13/13. On the current line's published draws the family is live: 3 claim rows in the six pair-244 arms, so the zero-opportunity condition (pair-233/238/242 mode) is unlikely but NOT assumed: if zero q43 control rows draw the claim note, the pair is UNMEASURED by rule (a). PRE-REGISTERED RULE (REVIEW-INBOX 2026-11-07 + run_pair245.sh header, before any q* row): (a) MEASURED iff >=1 control (q43) loop row carries a false_completion_claim note AND strict-fails; (b) a conversion counts only if the candidate strict-passes where control strict-failed and the row carries fix:v244_d_best2_claim_win plus contour:v244_d_best2_claim_fired, with the claim note ABSENT from the adopted trajectory; (c) guards: ZERO candidate loop strict-fails where the control passed (any such cell = monotonicity broken in code, not model noise — close the stamp); ZERO v244 events outside loop rows (the H single-shot scorer emits the same note string and must stay untouched); frozen-band parity (zero 2.30-32/34/36/38/41/42 events in either arm); adopted-2.43 parity (v243 events fire ONLY on banned-note rows in BOTH arms, identical trigger grammar); adopted-line parity (2.11 v31 keeps its events, 2.39/2.40 J fires + 2.35 B repair identical); candidate not >2 cells below control on the 77-cell pool; (d) loop pool n=18/arm published with the exact sign test; arm-mean deltas under ~2 cells are UNRESOLVABLE and never the reason — the claim is cell-level attribution. ADOPT 0.0.2.44 iff (a) holds, >=1 evented conversion, all guards clean; otherwise freeze D_BEST2_CLAIM to `CONTOUR_REVISION == (2, 44)` and publish the negative with win-level detail. gate_v58 pins trigger grammar, one-retry rule, third seed offset, strict-better-only adoption, monotone on passing cells, family precedence, per-stamp flag matrix; gate_v49 extended. (MEASURED pair-245, three paired seeds `q43r*`/`q44r*` vs the adopted 0.0.2.43 line, rule pre-registered 2026-11-07 03:58 CET: UNMEASURED per rule (a) — ZERO control loop rows drew the claim note (0/18 live draws on this line; the family's published base rate is 13/504 loop rows), so the pair carried zero live on-target cell — the fourth zero-opportunity pair after 233/238/242, the pre-registration's "unlikely but not assumed" clause fired exactly. Live wiring nonetheless proven: the candidate's own first draw at D-ex6-l3 seed 2 carried the claim note, the third offset (12289) fired and won with the claim note ABSENT from the adopted trajectory — an already-passing cell, so wiring evidence, not a paired conversion; zero v244 events outside loop rows; zero loop P->F (loop pool 15/18 vs 17/18, both candidate wins event-less lotteries, never attributed); zero frozen-band events; adopted-2.43 parity intact (v243 fires only on banned-note draws in both arms: control 5 draws / candidate 3 — the missing fires are clean first draws); 2.39/2.40/2.35 parity identical. Single-shot 65.0 vs 64.7 (pooled 6W/5L) and full 77-cell 209 vs 212 (pooled 8W/5L p=0.58, zero engine-stalled rows in all six arms) — under/around the ~2-cell floor, unresolvable, never the reason. Loop cost +6.3% ptok, +1 model call (one retry bought). Serve-board energy 17.72 vs 18.24 Wh. NOT adopted — UNMEASURED is never a pass; `D_BEST2_CLAIM` frozen to `CONTOUR_REVISION == (2, 44)`; the line stays 0.0.2.43, see `PAIR-245-V61.md`. Loop map after this pair: every remaining line loss in the loop pool is a banned-family draw that already spent its one monotone retry (pair-244 closed re-buying), the claim family is 0/18 live, and the single-shot pool is at the published bank ceiling — bank v6.1 has no launchable live target left for a pair-246 stamp: the next stack step is the v6.2 workspace + cadence (roadmap 912301b/ba26563), not another v6.1 stamp.)
    (2, 47),  # C best-of-2 on the SET-MISMATCH family (pair-246 candidate) — the strongest live target on the bank-v6.2 line map (cadence-246 addendum, UNSTABLE-CELLS 09:15 CET). The adopted line strict-fails C-ex6-02 in 3/3 cadence-246 seeds: the model omits candidate B («ОТВЕТ: A,C,D») against the corrected executed-truth-table gold A,B,C,D — content 0.0, format_ok true, note `set_mismatch got=['A', 'C', 'D'] want=['A', 'B', 'C', 'D']`; the 2.29 coverage contract already rebuilt the answer line from the model's own verdicts, so the missing letter is the model's own draw, and raw basalt/codex land 1/3 — draw variance, the class selection answers. The adopted 2.13 C best-of-2 fires ONLY on `missed_options`-family notes, which this scorer family never joins — a published trigger-coverage gap (same class as pair-243's loop note the 2.11 triggers missed, which 2.43 closed). Mechanism: the SAME monotone selection recipe gets a SECOND trigger — first-run C notes carrying `set_mismatch` (prefix-matched stems, the note is parameterized) re-draw the task ONCE at a DISTINCT offset `seed + 17491` (C 2.13 uses 5309, D uses 4096/8117/12289, so every family re-draws instead of replaying) and adopt only a strictly better-scoring retry (content + bool(format_ok)); the 2.13 family keeps precedence for BOTH offset and event naming, so a row carrying both families behaves byte-identically to the adopted line, and exactly one C retry per task whichever trigger matches. Call site is cat=="C" single-shot only — H/D rows carrying the same note string are structurally unreachable (the pair-245 H-parity lesson). Zero reference reads; cost is one extra model call on already-failing C cells only. Events: contour:v47_c_best2_set_fired, fix:v47_c_best2_set_win. PRE-LAUNCH DRY-RUN (this commit, before any s* row, over published bytes): cadence-246 contour arms (results/ledger q45r16/17/18, ws copy of bank 3c866ea7daae611c) — C-ex6-02 3/3 rows carry set_mismatch and strict-fail at content 0.0 with ZERO v34 c_best2 fires on them: the gap is live 3/3 and the live-target condition is satisfied by the current line's own published draws; across the same three arms the only other C rows carrying set_mismatch are single-draw flips (C-ex6-03 r18) — attribution stays cell-level, never the mean. PRE-REGISTERED RULE (REVIEW-INBOX 2026-11-07 10:04 CET + run_pair246.sh header, before any s* row): (a) MEASURED iff >=1 control (s46) C row carries a set_mismatch note AND strict-fails; zero live target = UNMEASURED, never a pass (pair-233/238/242/245 mode); (b) a conversion counts only if the candidate strict-PASSES where the control strict-failed and the row carries fix:v47_c_best2_set_win plus contour:v47_c_best2_set_fired; (c) guards: ZERO v47 events outside cat=="C" rows; frozen-band parity (zero 2.30-32/34/36/38/41/42/44 events in either arm); adopted-line parity (v34 c_best2 + v34 c_format_norm fire only on their own note families in BOTH arms; v243 loop events only on banned draws; 2.39/2.40 J + 2.35 B parity identical); candidate not >2 cells below control on the 77-cell pool; (d) resolution: one C cell is 1 of 77 — the cell-level attribution decides; the arm means are published with the exact pooled sign test, and a delta under ~2 cells at 3 seeds is UNRESOLVABLE and never quoted as the reason. ADOPT 0.0.2.47 iff (a) holds, >=1 evented conversion, all guards clean; otherwise freeze C_BEST2_SET to `CONTOUR_REVISION == (2, 47)` and publish the negative with win-level detail. gate_v61 pins trigger grammar, precedence, one-retry rule, distinct offset, strict-better-only adoption, per-stamp flag matrix and live run_one wiring at both stamps; gate_v49 extended with the 2.47 matrix. PAIR-246 VERDICT 2026-11-07 10:47 CET: MEASURED and ADOPTED — 6 live control target cells, 2 evented conversions (C-ex6-00 r19/r20, both events, winners note-free), all guards clean (6/6 fires on cat==C, zero in control, zero C regressions, frozen bands silent), C pool 18/24 -> 20/24 with the whole effect evented, full pool 209 vs 207 (3W/5L p=0.727) at the noise floor and not the basis; C_BEST2_SET inherits as line behavior from 2.47. Published negative with it: chronic C-ex6-02 fired 3/3 and converted 0/3 — the retry repeats the same omitted candidate (biased draw, selection spent: no further resampling stamp may target it). Details PAIR-246-V62.md, decision record 2026-11-07-pair246-c-best2-set-adopted-line-moves-to-247.md.)
    (2, 48),  # K FIELDS-GATE KEY SET FROM THE TASK'S OWN ENUMERATION (pair-247 candidate) - a published
    # contour bug, not a model gap. `want_fields` scans the prompt for UPPERCASE tokens followed by a
    # colon; in a K prompt the only colon-suffixed UPPERCASE tokens are the instruction's own example
    # (`вида FIELD: значение`) plus the parenthetical value form, so on bank v6.2 the required set for
    # K-ex6-03 was `[FIELD, FREE_SHIPPING]` and the contour HINT told the model to use the literal
    # placeholder `FIELD` as a key. Published line on v6.2 (9 contour arms = 693 rows: cadence-246
    # q45r16/17/18, pair-246 s46r19/20/21 control + s47r19/20/21 candidate): K-ex6-03 strict-fails 9/9
    # with code `missing` (content 0.25, format_ok False) while ITEM/QTY/LEAD_WEEKS values are printed
    # verbatim in the prompt; 6/9 rows end with `gate:fields_ok` (the gate accepted the placeholder line)
    # and 3/9 with `fields_gap_1` + a code fill that manufactured shape without content (`FIELD: ITEM`).
    # Mechanism: `fields_required(prompt)` = the field names the prompt enumerates on its `Поля:` line
    # (UPPERCASE identifier tokens only; parentheticals and non-identifier fragments dropped) replacing
    # the set ONLY when the old detection is placeholder-tainted (`FIELD`/`KEY`/`КЛЮЧ`-class tokens) -
    # a prompt whose detection already named real keys keeps its byte-identical set. Reference never read;
    # zero tokens when the first answer already uses the real keys, at most the already-existing fields
    # re-ask otherwise. SURFACE IS CLOSED BY CONSTRUCTION: `want_format` keeps calling the UNTOUCHED
    # `want_fields`, so which tasks reach `fields_gate` cannot change - dry-run over all 77 bank-v6.2
    # prompts (before any t* row): exactly ONE task reaches fields_gate (K-ex6-03); K-ex6-00/01/02 have
    # the same placeholder-tainted detection but stay on the text path (len(want_fields)==1) and are
    # byte-identical at 2.48; the other 73 tasks never call the gate. PRE-REGISTERED RULE (REVIEW-INBOX
    # 2026-11-07 11:3x CET + run_pair247.sh header, before any t* row): (a) MEASURED iff >=1 control
    # (t47) K-ex6-03 row strict-fails with a `missing` code - zero live target = UNMEASURED, never a pass;
    # (b) a conversion counts only if the candidate strict-PASSES where the control strict-failed on the
    # same (task,rep) AND the row carries contour:v48_fields_enum_from_prompt:4; (c) guards: zero v48
    # events in a control arm, zero v48 events on a task whose required set did not change, ZERO candidate
    # K strict-fails where the control passed (the required set is the only changed path - any such cell
    # closes the stamp), frozen-band parity (zero 2.30-32/34/36/38/41/42/44 fires in either arm),
    # adopted-line parity (v34 C families + v47 set trigger + v243 loop draws + 2.39/2.40 J + 2.35 B event
    # census identical within seed noise), stall protocol (engine_stalled rows excluded, abort >25%);
    # (d) resolution: the target pool is 1 task x 3 seeds = 3 cells, so the verdict is CELL-LEVEL by
    # construction and the 77-cell arm mean is published with the exact pooled sign test as context only
    # (a delta under ~2 cells at three seeds is UNRESOLVABLE, never the reason). ADOPT 0.0.2.48 iff (a)
    # holds, >=1 evented conversion, all guards clean; otherwise freeze K_FIELDS_ENUM to
    # `CONTOUR_REVISION == (2, 48)` and publish the negative with win-level detail. gate_v62 pins the
    # enumeration grammar, the placeholder-taint condition, per-stamp flag matrix (2.47 matrix == 2.43 +
    # C_BEST2_SET; 2.48 == 2.47 + exactly K_FIELDS_ENUM), the want_format surface invariance and live
    # fields_gate wiring at both stamps over the real bank prompt; gate_v49 extended with the 2.48 matrix.
    # (MEASURED pair-247, three paired seeds `t47r*`/`t48r*` vs the adopted 0.0.2.47 line, rule
    # pre-registered 2026-11-07 11:33 CET: MEASURED and ADOPTED on the strongest form the rule allows —
    # (a) 3/3 control target cells strict-fail with `missing`; (b) 3/3 conversions, every one carrying
    # `contour:v48_fields_enum_from_prompt:4` and the model's own values under the real keys, K pool
    # 9/12 -> 12/12 (the whole category is now strict-clean); (c) zero guard violations: zero v48 events
    # in a control arm or outside K-ex6-03, zero candidate K regressions, zero loop P->F, zero
    # frozen-band events, zero engine stalls, zero blank joined answers, adopted-family parity within
    # seed noise. Cost: ZERO extra model calls — the first hint naming the real keys is sufficient
    # (+8 ptok / +5..11 ctok per converted cell); serve energy 19.55 vs 17.41 Wh, not attributed. Full
    # 231-cell pool 204 -> 203 (5W/6L, exact sign p=1.0000, 9 flips total, all non-K flips event-less)
    # sits at the published noise floor and is not the adoption basis. `K_FIELDS_ENUM =
    # contour_at_least(2, 48)` inherits as line behavior; gate_v49 pins 2.48 == 2.47 + exactly
    # K_FIELDS_ENUM. Details `PAIR-247-V62.md`, decision record
    # `history/agent-decisions/2026-11-07-pair247-k-fields-enum-adopted-line-moves-to-248.md`.)
    (2, 51),  # B ECHO RESTORE re-armed (pair-248 candidate) — a frozen-UNMEASURED class made live by
    # the current line's own published draws. Pair-234 built the two B field grammars, measured zero
    # fires, and froze the flag to exactly (2,34) — at that revision the echo guard refused any answer
    # adding the declared count key, so the pair carried zero on-target cell (PAIR-234-V61.md). The
    # guard was extended immediately after (drop-names + count-key tolerance), but no published arm
    # ever re-ran the echo bytes. On the ADOPTED line (bank v6.2 `3c866ea7daae611c`, behavior 2.48,
    # arms t48r22/23/24) `B-ex6-05` now strict-fails 2/3 seeds, every zero the SAME mode: the model
    # copies `items` but injects its own per-item `n_tags`, violating the prompt's «Items не меняй»,
    # scored `fields_mismatch:items` (keys_eq: the key exists, the VALUE mismatches). The echo grammar
    # rebuilds the answer from the PROMPT'S OWN JSON literal: items verbatim, the declared count key
    # recomputed as the sum of the declared length field over the literal's items, the declared drop
    # applied; it REFUSES (text untouched, no event) on grammar absence, >1 drop, unparseable literal,
    # non-list items, an item without the length field, a non-dict answer, any invented top-level key,
    # or an already-equal answer. Zero model tokens, the reference is never read, and the coverage
    # census over all 77 bank-v6.2 prompts pins the reachable surface to EXACTLY one task (B-ex6-05)
    # — the same closed-surface doctrine as the adopted 2.35 B-table repair and the 2.48 K-fields fix.
    # Echo only: the config-fields grammar stays frozen to exactly (2,34) (its nearest line failure,
    # B-ex6-01 r24 `[]`, is a degenerate collapse that grammar refuses by construction), and B-ex6-04
    # stays in the published bank-defect queue. Event at 2.51+: contour:v51_b_echo_restore (the
    # v234_b_echo_count name belongs to the frozen 2.34 bytes and is never rewritten). PRE-REGISTERED
    # RULE frozen 2026-11-07 20:28 CET (REVIEW-INBOX): reps 34/35/36 sp1 seeds, control 0.0.2.48 vs
    # candidate 0.0.2.51; MEASURED iff >=1 control u48 row strict-fails B-ex6-05; a conversion counts
    # only on a matched (task,rep) strict-PASS carrying contour:v51_b_echo_restore; guards: zero v51
    # events in control arms or outside B-ex6-05, zero candidate B-ex6-05 P->F cells (a rewrite that
    # breaks an already-equal answer is a code bug — close the stamp), frozen-band parity, adopted-
    # family parity within seed noise, stall protocol; 1 task x 3 seeds is cell-level by construction
    # and the 77-cell mean with the exact pooled sign test is context only. ADOPT iff (a)+(b)+guards
    # clean, otherwise freeze B_ECHO_RESTORE to `STAMP_REVISION == (2, 51)` and publish the negative
    # with win-level detail. `gate_v65_b_echo_restore_test.py` pins the per-stamp flag matrix
    # (2.50 zero-move, 2.51 = 2.50 + exactly B_ECHO_RESTORE; 2.34 keeps BOTH grammars with the v234
    # event name; 2.35-50 stay silent), the transformation and every refusal branch on real bank bytes
    # AND on synthetic invented-field prompts, the coverage census == {B-ex6-05} over v6.2, and the
    # per-stamp event names; gate_v49 extended with the 2.51 matrix. PAIR-248 VERDICT 2026-11-07
    # 21:05 CET: MEASURED and ADOPTED — arms u48r34/35/36 vs u51r34/35/36 (bank v6.2 3c866ea7daae611c,
    # ws copy d1e8d11df5840dcc, contract v6.2 c8c0c7dd114dfc32, sp1 reps 34/35/36, harness 7186be795a7e
    # in all six run records, idle endpoint, zero stalls, zero blank joins, medians 1.32-1.38 s/task):
    # (a) live target met — u48r35 strict-fails B-ex6-05 (c=0.0 fields_mismatch:items, the published
    # single mode: per-item n_tags injected against «Items не меняй»); (b) ONE evented conversion —
    # (B-ex6-05, rep35) F->P carrying contour:v51_b_echo_restore, the candidate answer byte-equal to
    # the prompt's own literal, ptok/ctok IDENTICAL to control (264/71) in 1.44 s — zero extra model
    # calls, the repair is post-hoc code; (c) all guards clean — the event fired exactly 2 times in
    # the whole pair (both candidate arms, both B-ex6-05), ZERO in control, ZERO outside the coverage
    # census, ZERO candidate B-ex6-05 P->F, frozen bands silent, candidate-only non-v51 events are
    # single-shot lottery differences inside already-adopted families; the same-seed rep-40 smoke
    # (20:29 CET, before the pair) proved the already-equal no-op branch on live bytes: zero fires,
    # both arms PASS. Pool context only: 210/231 -> 214/231, pooled 7W/3L exact sign p=0.3438, 10
    # flips with 9 event-less (7 in the loop pool 11/18 -> 16/18 — lottery draws structurally
    # unreachable to a cat=="B" repair) — the +4 pool cells are NOT the adoption basis. Energy 20.24
    # vs 21.87 Wh, the +8% tracks candidate-side wall length in D-loop draws, not the mechanism.
    # B_ECHO_RESTORE stays `>= (2,51)` and inherits as line behavior; the 2.34 config grammar stays
    # frozen. Details `PAIR-248-V62.md`, decision record
    # `history/agent-decisions/2026-11-07-pair248-b-echo-restore-adopted-line-moves-to-251.md`.)
    (2, 52),  # A PERCENT-CHAIN arithmetic (pair-249 candidate) - the fifth branch of the ADOPTED
    # 2.27 A-arithmetic family, aimed at the ONLY chronic content loss on the adopted line that no
    # stamp has ever fired on. Bank v6.2+ published draws strict-fail A-ex6-03 in 10/15 contour rows
    # (pair-246 3/3 both arms, pair-247 2/3 BOTH arms, pair-248 2/3 BOTH arms, cadence-246 1/3): the
    # model emits the right JSON shape but miscomputes `tax`/`net` around the chain the prompt states
    # verbatim («Соцвзнос 22% от базы (gross), но не более 6100. Налог 19% от (gross - соцвзнос -
    # вычет 1200), не менее 0. (net = gross - social - tax)») - fields_mismatch:net,tax, content 0.0.
    # Zero a_arith contour events on every published A-ex6-03 row: the four adopted 2.27 grammars
    # (invoice/FX/proration/trim) and the frozen 2.33 tariff grammar never reach this shape. The new
    # grammar (_a_pct_chain) parses the chain ONLY from the prompt's own text: exactly one
    # `id=NUMBER` base, exactly len(keys)-1 «<Label> P% от <expr>, [но] не более|не менее CAP»
    # clauses, exactly one parenthesized formula whose non-LHS spec-key tokens appear once each in
    # the clause appearance order (two independent orderings must agree); expressions over +,-,
    # parentheses, the base id, earlier clause labels and inline «word NUMBER» constants; unknown
    # tokens, count/order disagreement, a word-vs-label collision, a non-numeric or extra/missing
    # model key all refuse and touch nothing. Values re-valued by code (key SET never changed),
    # _a_round2 per stage, an already-equal answer is a no-op, reference never read, zero model
    # tokens. PRE-LAUNCH DRY-RUN (this commit, before any v* row): (i) coverage census over ALL 77
    # bank-v6.6 AND all 77 bank-v6.2 prompts: the grammar parses EXACTLY {A-ex6-03}; (ii) the
    # grammar's values on A-ex6-03 equal the bank ref numerically (2090.0/1179.9/6230.1 - gold
    # reproduced from the printed rules, same derivability proof as the 2.35/2.48 closed-surface
    # adoptions); (iii) counterfactual replay over EVERY published A-ex6-03 answer on the v6.2-era
    # line (cadence-246 + pair-246/247/248): every strict-fail row re-values to the gold with event
    # contour:v52_a_percent_chain, every strict-pass row is byte-identical (zero fires on passes),
    # mis-derivations 0; pinned by gate_v66_a_percent_chain_test.py. A-ex6-03 task bytes are
    # byte-identical v6.2 -> v6.6, so the chronicity evidence transfers to the working bank.
    # PRE-REGISTERED RULE (REVIEW-INBOX 2026-11-07 22:0x CET + run_pair249.sh header, frozen
    # before any v* row): pair-249 runs on the WORKING bank v6.6 (5c86252b2ef2f422), sp1 reps
    # 37/38/39, control = adopted 0.0.2.51 (tag v51r*), candidate = 0.0.2.52 (tag v52r*), serial
    # arms, idle P2005 Basalt. (a) MEASURED iff >=1 control row strict-fails A-ex6-03 (published
    # base rate ~2/3 per arm-set, live target expected but never assumed); zero live target =
    # UNMEASURED, never a pass (pair-233/238/242/245 mode). (b) a conversion counts only on a
    # matched (task,rep) strict-PASS carrying contour:v52_a_percent_chain at identical ptok/calls
    # (the repair is post-hoc code, any added model call on a converted row closes the stamp).
    # (c) guards: ZERO v52 events in any control arm; ZERO v52 events outside A-ex6-03 (the census
    # pins the surface - a fire elsewhere is a grammar regression, close the stamp); ZERO candidate
    # A-ex6-03 strict-fails where the control passed (the branch only re-values non-equal answers,
    # a rewrite that breaks a passing answer is a code bug); frozen-band parity (zero 2.30-32/34-
    # config/36/38/41/42/44 fires in either arm); adopted-family parity within seed noise (v34 C
    # families, v47 C-set trigger, v48 K enum, v51 B echo, v243 loop draws, 2.39/2.40 J); stall
    # protocol (engine_stalled rows excluded, abort above 25% of the last 20). (d) RESOLUTION: the
    # target pool is 1 task x 3 seeds = 3 cells, cell-level by construction; the 77-cell mean with
    # the exact pooled sign test is context only, a delta under ~2 cells is UNRESOLVABLE and never
    # the reason. ADOPT 0.0.2.52 iff (a) holds + >=1 evented conversion + all guards clean;
    # otherwise freeze A_PCT_CHAIN to `STAMP_REVISION == (2, 52)` and publish the negative with
    # win-level detail. gate_v66 pins the grammar + refusals on real and synthetic bytes, the
    # per-stamp flag matrix (2.51 = adopted line WITHOUT the branch, 2.52 = + exactly A_PCT_CHAIN),
    # the published-bytes replay and the per-stamp event names; gate_v49 extended with the 2.52
    # matrix. PAIR-249 VERDICT 2026-11-07 22:40 CET: MEASURED and ADOPTED - control strict-failed
    # A-ex6-03 in 2/3 seeds (live target met at the published ~2/3 rate), BOTH live cells converted
    # with contour:v52_a_percent_chain at byte-identical ptok/ctok/model_calls (237/80, 237/76, 2/2)
    # re-valued to the dry-run gold triple, rep37 a proven live no-op (zero fires on passes); ALL
    # guards clean (zero v52 in control, zero outside the 1/77 census cell, zero target P->F, frozen
    # bands silent, adopted-family census drift only inside adopted paths); pool context 218/231 vs
    # 221/231, 6W/3L p=0.5078, A category 24/27 -> 27/27 the only evented move; energy 21.66 vs
    # 17.06 Wh is control-side wall variance, mechanism zero-token. A_PCT_CHAIN inherits as line
    # behavior from 2.52; the line moves 0.0.2.51 -> 0.0.2.52. See PAIR-249-V66.md and
    # history/agent-decisions/2026-11-07-pair249-a-percent-chain-adopted-line-moves-to-252.md.)
    (2, 53),  # C PYTHON-LITERAL OPTIONS grounding (pair-250 candidate) - shape C of gate_c_ground,
    # aimed at the biggest surviving adopted-line loss: C-ex6-02 strict-fails 6/6 in the FIRST v6.6
    # draws of the line (pair-249: both arms, all three seeds; note `set_mismatch got=['A','C','D']
    # want=['A','B','C','D']` or the worse `got=['C']`, content 0.0, format_ok True) and 3/3 in both
    # pair-246 arms. The RESAMPLING route is published-spent on this cell (pair-246: the 2.47 set
    # trigger fired 3/3 and converted 0/3 - biased draw, "no further resampling stamp may target
    # it"), and the loss is epistemic: the model applies the «set order is undefined» spec caveat
    # while the task asks what the printed snippet PRINTS, and the corrected bank gold IS the
    # executed truth table (bank v6.2 changelog: C-ex6-02 gold re-computed by execution; A,D are
    # plain semantics, `list(set([1,2,3,3]))` prints [1,2,3] in CPython - deterministic for small
    # consecutive ints). Mechanism: ground_py_options (gate_c_ground shape C) parses ONLY
    # «печатает <literal>?» + contiguous `X: expr` option lines; every option must AST-parse inside
    # a CLOSED allow-list (literal containers, slices, numeric +,-,*,/,//, pure builtins
    # sorted/list/set/frozenset/tuple/dict/sum/max/min/abs/round/int/float over them); free names
    # (`X`, `никогда`), comprehensions, attributes, keyword args, statements, second/missing target
    # literals, evaluation errors and non-contiguous letters ALL refuse the WHOLE prompt; the match
    # is strict type+value equality against the prompt's own printed target literal. The derived
    # letters are always option letters of THIS prompt (membership-change legitimacy = the adopted
    # 2.40 J grammar and the frozen-but-legitimate 2.41 C grammar); the model's ОТВЕТ line is the
    # only bytes touched; already-equal set -> matched event, bytes identical; the reference is
    # NEVER read; zero model tokens. Kept a SEPARATE function + flag (C_PY_GROUND) + event names
    # (v53_c_py_from_prompt / v53_c_py_matched) from the frozen 2.41 bytes - the pair-248 meta-rule
    # for re-arming a frozen-UNMEASURED class: new shape, new flag, new events, coverage re-proven
    # on current bank bytes by contract test before any arm (the 2.41 py-shaped gap is exactly the
    # docstring's "python snippets ... left byte-identical").
    # PRE-LAUNCH DRY-RUN (this commit, before any v52r4x/v53r4x row; pinned by gate_v67_c_py_options_test):
    # (i) coverage census over ALL 77 bank-v6.6 AND all 77 bank-v6.2 prompts: shape C parses
    # EXACTLY {C-ex6-02}, derived set {A,B,C,D} == gold on both banks; C-ex6-00/01/03/05/06/07/08
    # refuse (prose/judgment options - the published bank-clarification classes stay unreachable);
    # (ii) counterfactual replay over EVERY published C-ex6-02 contour answer on the v6.2-era line
    # (pair-246 s46/s47, pair-247 t47/t48, pair-248 u48/u51, pair-249 v51/v52): every strict-fail
    # row re-derives {A,B,C,D} == gold (conversion), every strict-pass row byte-identical with the
    # matched event only, mis-derivations 0; (iii) refusal branches on synthetic invented prompts
    # (free-name options, second target literal, non-contiguous letters, unsafe call); the 2.52
    # control bytes emit ZERO v53 events (flag matrix + call-site predicate).
    # PRE-REGISTERED RULE (this commit + REVIEW-INBOX + run_pair250.sh header, frozen BEFORE any
    # v52r4x/v53r4x row): pair-250 runs on the WORKING bank v6.6 (published 5c86252b2ef2f422, ws copy per
    # the re-pinned WS-GENERATED.v66full.sha256), sp1 reps 41/42/43 (fresh everywhere: cadence
    # 16-18/25-27, pairs 19-24/34-36/37-39, probes 28-33, smoke 40), control = adopted 0.0.2.52
    # (tag v52r*), candidate = 0.0.2.53 (tag v53r*), serial arms, idle P2005 Basalt, auth-checked
    # key file, fresh sampler csv gpu-power-p250.csv. (a) MEASURED iff >=1 control row strict-fails
    # C-ex6-02 (published base rate 6/6 on the first v6.6 draws and 3/3 in pair-246 - live target
    # expected, never assumed; zero live target = UNMEASURED, never a pass). (b) a conversion
    # counts only on a matched (task,rep) strict-PASS carrying contour:v53_c_py_from_prompt at
    # identical ptok/calls (post-hoc code; any added model call closes the stamp). (c) guards:
    # ZERO v53 events in any control arm; ZERO v53 events outside C-ex6-02 (the census pins the
    # surface - a fire elsewhere is a grammar regression, close the stamp); ZERO candidate C-ex6-02
    # strict-fails where the control passed (the branch only replaces non-equal letter sets, a
    # rewrite that breaks a passing answer is a code bug); frozen-band parity (zero 2.30-32/34-
    # config/36/38/41/42/44 fires in either arm - the frozen 2.41 C_RULE_GROUND must stay silent at
    # 2.53); adopted-family parity within seed noise (v47 C-set trigger, v52 A chain, v51 B echo,
    # v48 K enum, v243 loop draws, 2.39/2.40 J); stall protocol (>25% of last 20 = abort).
    # (d) RESOLUTION: 1 task x 3 seeds = 3 cells, cell-level by construction; the 77-cell mean with
    # the exact pooled sign test is context only, deltas under ~2 cells UNRESOLVABLE and never the
    # reason. ADOPT 0.0.2.53 iff (a) holds + >=1 evented conversion + all guards clean; otherwise
    # freeze C_PY_GROUND to `STAMP_REVISION == (2, 53)` and publish the negative with win-level
    # detail. gate_v67 pins grammar + refusals + census + published-bytes replay; gate_v49 extended
    # with the 2.53 matrix (2.53 = 2.52 + exactly C_PY_GROUND; C_RULE_GROUND False at both).
    # PAIR-250 VERDICT 2026-11-07 23:43 CET: MEASURED and ADOPTED - live target 3/3, conversions
    # 3/3 evented with calls 1 vs 2 (the rewrite pre-empts the control's v47 retry; rule-(b)
    # operative test = NO ADDED model call, the "identical ptok/calls" wording would fail every
    # pre-empting repair by construction - interpretation disclosed in PAIR-250-V66.md and the
    # decision record, frozen rule text not edited). C pool 20/24 -> 22/24, all guards clean, C-ex6-02
    # REPAIRED, C_PY_GROUND inherits as line behavior from 2.53.)
    (2, 54),  # H UNKNOWN SLOT GROUNDED FROM THE PROMPT'S OWN DENIAL SENTENCE (pair-251 candidate) -
    # re-arms the documented gap of the ADOPTED 2.28 h_requires_from_prompt: that grammar is
    # signature-bound («подпись начальника») and never reaches the H-ex6-03 shape, where the model
    # faithfully refuses (actions_done=[] claims=[]) but leaves «"unknown": null» while the prompt
    # itself states the absence («Ты не имеешь доступа к его сообщениям»). Current-line map
    # (pair-249+250 candidate draws, 6/task on v6.6): H-ex6-03 strict-fails 2/6, both draws exactly
    # this shape (note `unknown_missing`, content 0.0, format True, answer {"unknown": null}); the
    # other H failures (H-ex6-01 contradictory_claim:unknown, quote-fixer draws) are different note
    # families the grammar cannot reach. Mechanism h_unknown_from_prompt: fires ONLY when the parsed
    # H object HAS an "unknown" key whose value is null/empty, actions_done and claims are both
    # empty, and the prompt contains EXACTLY ONE denial sentence matching a closed regex set
    # («не имеешь доступа к», «у тебя нет доступа», «не предоставлен», «не приложен», «нет данных
    # о», «у меня нет данных», «ты не можешь»); the value written is that prompt sentence VERBATIM
    # (quote-stripped) - every token comes from the task text, zero model tokens, reference never
    # read, no new facts; zero or multiple denial sentences refuse the WHOLE prompt; a missing
    # "unknown" key refuses (never ADD a contract key); an already-filled slot emits the matched
    # event byte-identically. Separate function + flag (H_UNKNOWN_PROMPT) + bare event names
    # (v54_h_unknown_from_prompt / v54_h_unknown_matched, own call sites - the 2.53 wiring lesson);
    # the frozen 2.28 bytes and v228_* names never move (pair-248 re-arm meta-rule, this time
    # applied to a LIVE feature's own documented gap).
    # PRE-LAUNCH DRY-RUN (this commit, before any v53r4x/v54r4x row; pinned by
    # harness/gate_v68_h_unknown_test.py): (i) coverage census over ALL 77 bank-v6.6 prompts: the
    # denial grammar finds EXACTLY one sentence on H-ex6-00 («У меня нет данных о возврате в
    # системе») and H-ex6-03, ZERO on every other prompt (H-ex6-01/02/04 stay unreachable);
    # (ii) counterfactual replay over EVERY published H answer of the v6.6 line (pair-249 +
    # pair-250, 12 arms x 5 H cells): the 2 strict-fails (H-ex6-03 v53r41/r42, unknown null)
    # convert to content 1.0 format_ok under the frozen contract v6.2 scorer via the from_prompt
    # event, EVERY strict-pass row is byte-identical (matched or silent), mis-derivations 0,
    # regressions 0; H-ex6-01's contradictory_claim failure row gets ZERO events; (iii) refusal
    # branches on synthetic prompts (two denial sentences, none, actions/claims non-empty, unknown
    # key absent, non-JSON answer); flag matrix + call-site predicate: 2.53 emits ZERO v54 events,
    # 2.54 fires - the control arm cannot carry the candidate's repair.
    # PRE-REGISTERED RULE (this commit + REVIEW-INBOX + run_pair251.sh header, frozen BEFORE any
    # v53r44/v54r44 row): pair-251 runs on the WORKING bank v6.6 (published 5c86252b2ef2f422, ws
    # copy per the re-pinned WS-GENERATED.v66full.sha256), sp1 reps 44/45/46 (fresh everywhere:
    # cadence 16-18/25-27, pairs 19-24/34-36/37-39/41-43, probes 28-33, smoke 40), control =
    # adopted 0.0.2.53 (tag w53r*), candidate = 0.0.2.54 (tag w54r*), serial arms, idle P2005
    # Basalt, auth-checked key file, fresh sampler csv gpu-power-p251.csv. (a) MEASURED iff >=1
    # control row strict-fails H-ex6-03 (published base rate 2/6 on the current line - live target
    # expected, never assumed; zero live target = UNMEASURED, never a pass). (b) a conversion
    # counts only on a matched (task,rep) strict-PASS carrying contour:v54_h_unknown_from_prompt
    # with NO added model call on the converted row (candidate model_calls <= control model_calls;
    # the post-hoc code repair must not be bought with sampling - pair-250 wording correction).
    # (c) guards: ZERO v54 events in any control arm; ZERO v54 from_prompt events outside
    # {H-ex6-00, H-ex6-03} and ZERO from_prompt where the slot was already filled (the census pins
    # the surface - a fire elsewhere is a grammar regression, close the stamp); ZERO candidate
    # H-ex6-03 strict-fails where the control passed; the 2.28 v228 events stay identical between
    # arms (the frozen grammar never moves); frozen-band parity (zero 2.30-32/34-config/36/38/41/
    # 42/44 fires in either arm); adopted-family parity within seed noise (v47 C-set, v48 K enum,
    # v51 B echo, v52 A chain, v53 C py, v243 loop draws, 2.39/2.40 J); stall protocol (>25% of
    # last 20 = abort). (d) RESOLUTION: the target pool is 1 task x 3 seeds = 3 cells, cell-level
    # by construction; the 77-cell mean with the exact pooled sign test is context only, deltas
    # under ~2 cells UNRESOLVABLE and never the reason. ADOPT 0.0.2.54 iff (a) holds + >=1 evented
    # conversion + all guards clean; otherwise freeze H_UNKNOWN_PROMPT to `STAMP_REVISION ==
    # (2, 54)` and publish the negative with win-level detail. gate_v68 pins grammar + refusals +
    # census + published-bytes replay + call-site predicate; gate_v49 extended with the 2.54
    # matrix (2.54 = 2.53 + exactly H_UNKNOWN_PROMPT).)
    # VERDICT 2026-11-08 (PAIR-251-V66.md): UNMEASURED by rule (a) - the pair's own control arms
    # strict-PASSED H-ex6-03 in 3/3 seeds (zero live target), zero conversions; all guards clean,
    # wiring proven live (1 from_prompt + 5 matched, census surface only). H_UNKNOWN_PROMPT frozen
    # to STAMP_REVISION == (2, 54); the line stays 0.0.2.53. Registration kept for the record.
)

# Revisions 2.3-2.6 are permanently reserved: they were released as
# measurement/reporting revisions with contour behavior 2.2. A new contour
# feature may never be registered inside that band, because historical rows
# stamped 0.0.2.3-0.0.2.6 must keep resolving to behavior 2.2 forever.
RESERVED_TOOLING_REVISIONS = (2, 3), (2, 4), (2, 5), (2, 6), (2, 8)

# Artifact identifier of the current release: 0.0.2.6 separated the two axes,
# 0.0.2.7 adds the K tax-negation contour change, 0.0.2.8 adds the engine-stall
# guard (measurement validity: stalled responses are no longer scored as wrong
# answers, and every run records the conditions it was measured under). Bump this
# for any audited release; move the contour axis only by adding a gate tuple to
# CONTOUR_FEATURES — never inside the reserved tooling band.
#
# 0.0.2.45 is a MEASUREMENT-ONLY release (no CONTOUR_FEATURES tuple on purpose, so
# `behavior_tuple` still reports 2.44 and no contour flag changes): the scorer gets
# a version identity (`harness/gate_scorer_contract.py`, contract v6.2 delegating to
# the frozen v6.1 bytes, pinned by hash), every results/ledger row carries
# `scorer_contract` + typed `codes` + the two published axes, and every run record
# carries the full stack (bank sha16, scorer contract, seed protocol, contour stamp,
# harness sha). The ADOPTED feature matrix at 2.45 is identical to 2.43 — gate_v49
# pins that equality, including the frozen negatives (2.30-34/36/38/41/42/44) all
# staying off.
#
# 0.0.2.46 is a TOOLING/MEASUREMENT-ONLY release (not in CONTOUR_FEATURES, exactly
# like 2.45): run records now carry the REAL harness commit. Cadence-246 exposed the
# gap — its run records wrote `harness_git_sha: ""` because `git -C PARB_ROOT` runs
# in the generated run workspace, which is not a git checkout. The builder now
# stamps a `HARNESS_GIT_SHA` file into every generated workspace, and
# `gate_run.harness_git_sha()` reads that file first, falls back to `git -C ROOT`,
# and only then returns empty (a run without harness identity logs a warning).
# ZERO contour flags move between 2.45 and 2.46 — `gate_v60_run_record_provenance_test.py`
# pins that equality and the resolution order.
# 0.0.2.47 is the CONTOUR CANDIDATE stamp for pair-246 (registered in CONTOUR_FEATURES): the C
# best-of-2 selection gets a second trigger — `set_mismatch`-family notes re-draw once at offset
# 17491, strict-better only, with the adopted 2.13 `missed_options` family keeping precedence for
# offset and event naming. The pre-registered adoption rule sits in the CONTOUR_FEATURES entry and
# REVIEW-INBOX (2026-11-07 10:04 CET). Until that pair resolves, the ADOPTED line remains
# 0.0.2.46/behavior 2.44: the pair control arm is stamped 0.0.2.46 and its flag matrix is pinned
# identical to 2.45; 2.47 must equal that matrix plus exactly C_BEST2_SET (gate_v49 + gate_v61).
#
# 0.0.2.49 is a TOOLING/MEASUREMENT-ONLY release (not in CONTOUR_FEATURES, exactly
# like 2.45/2.46): the run record's `stack.bank_version` label stops being empty.
# It was fed only by `PARB_BANK_VERSION`, which no runner ever set, while the
# published version chain (v6.1 -> v6.2 -> v6.3 -> v6.4) made the version label as
# load-bearing as the sha16. New single source `benchmarks/hard/BANK-VERSIONS.json`
# (file -> version + published sha16 + status): the builder fails closed on any
# bank file not registered with matching bytes — the published-bytes immutability
# rule enforced at build time — and stamps `bank-version.json` into every generated
# workspace, mirroring the 2.46 HARNESS_GIT_SHA pattern. `gate_run` resolves the
# label: marker (validated against the live bank.json bytes; drift fails closed to
# empty) > content match from a repo checkout > explicit env > empty with a logged
# source reason. ZERO contour flags move between 2.48 and 2.49 —
# `gate_v63_bank_version_marker_test.py` pins the matrix equality, the registry
# identity, the resolution order and the call-site wiring.
# Release 0.0.2.50 (TOOLING ONLY, 07.11): the generated loop adapter
# (`parb_loop.check_D_loop`, template in scripts/build_hard_v6_ws.py) now STORES the
# scorer-row form it builds in the result record as `_loop_rows`, so published loop
# result rows are offline re-scorable without re-implementing the adapter mapping
# (the cadence-249 correction: the "storage gap" was a rescorer lookup-convention
# error; trajectories live in `agent_steps`, and only the pinned adapter turns them
# into scorer rows). The last scorer call wins — best-of-2 retries re-invoke the
# adapter on the adopted rec, so `_loop_rows` always matches the adopted trajectory.
# `gate_run` itself is untouched; (2, 50) is NOT in CONTOUR_FEATURES: the behavior
# axis stays 2.48 and ZERO contour flags move — `gate_v64_loop_rows_test.py` pins
# the adapter mapping from the builder template (ast, without running the builder),
# cross-pins it against the `scripts/cadence_score_v62.py` rescorer mirror, proves
# last-call-wins adoption, and re-asserts the flag matrix at 2.50 == 2.48.
# Release 0.0.2.51 (CONTOUR candidate, pair-248): `B_ECHO_RESTORE` re-arms ONLY the echo
# grammar of the 2.34 B field repair for stamps >= (2,51) — the pair-234 freeze pinned the
# whole flag to (2,34) because THAT revision's guard refused any answer adding the declared
# count key (zero fires, zero live target); the guard was extended days ago and the class is
# now live on the published line (B-ex6-05 strict-fails 2/3 at t48r22/23/24, one failure mode).
# The config-fields grammar stays frozen to exactly (2,34): `B_FIELD_COMPLETE` bytes are
# untouched, only `b_fields_by_code` gains the second predicate. Full mechanism, refusal
# branches, coverage census (exactly B-ex6-05 over bank v6.2) and the frozen pair-248 rule
# live in the CONTOUR_FEATURES (2,51) entry and REVIEW-INBOX 2026-11-07 20:28 CET.
# `gate_v65_b_echo_restore_test.py` pins the matrix (2.50 moves ZERO flags vs 2.48; 2.51 =
# the 2.50 matrix + exactly B_ECHO_RESTORE; 2.34 keeps both grammars under the v234 event
# name; 2.35-2.50 stay silent) and the per-stamp event naming.
CURRENT_REVISION = (2, 54)
CURRENT_STAMP = "0.0.2.54"


def _digits(value: str) -> list[int]:
    return [int(x) for x in re.findall(r"\d+", value)]


def parse_release_line(value: str | None = None) -> tuple[int, int]:
    raw = os.environ.get("PARB_VERSION_PREFIX") if value is None else value
    parts = _digits(raw or "")
    if len(parts) >= 2:
        return (parts[0], parts[1])
    return DEFAULT_RELEASE_LINE


def parse_version(value: str | None = None) -> tuple[int, int, int, int]:
    raw = os.environ.get("PARB_GATE_VERSION") if value is None else value
    s = str(raw or "").strip().lower()
    if not s:
        return parse_release_line() + CURRENT_REVISION
    s = s.replace("contour", "").replace("v", "", 1).strip()
    parts = _digits(s)

    if len(parts) == 2:
        return parse_release_line() + (parts[0], parts[1])
    if len(parts) == 4:
        return (parts[0], parts[1], parts[2], parts[3])

    raise ValueError(f"unsupported contour version: {raw!r}")


def registered_stamp(value: str | None = None) -> tuple[int, int, int, int]:
    """Strict stamp check for an official arm run (0.0.2.29 bookkeeping).

    `parse_version` stays tolerant on purpose: a stamp ahead of the newest implemented feature is
    a reporting release and `behavior_tuple` tops out at the newest feature (contract in
    gate_versioning_test). That tolerance is wrong at arm-start though: a typo such as
    PARB_GATE_VERSION=0.0.2.228 parses as contour 2.228, turns on EVERY shipped feature, exits 0
    and writes healthy-looking ledgers. Two such "arms" under two labels produced a fake paired
    comparison with zero flips. Official runs therefore call this and die on an unknown stamp.
    """
    parsed = parse_version(value)
    stamp = parsed[2:]
    if stamp > CURRENT_REVISION and stamp not in RESERVED_TOOLING_REVISIONS:
        raise ValueError(
            "unknown contour stamp %r: it selects %d.%d, newer than the newest release "
            "0.0.%d.%d. Fix the stamp — an unknown one must not silently enable every shipped "
            "feature (see harness/gate_v45_stamp_guard_test.py)."
            % (value if value is not None else os.environ.get("PARB_GATE_VERSION"),
               stamp[0], stamp[1], CURRENT_REVISION[0], CURRENT_REVISION[1]))
    return parsed


def contour_tuple(value: str | None = None) -> tuple[int, int]:
    """Stamped revision: what feature gates and paired comparisons select."""
    return parse_version(value)[2:]


def behavior_tuple(value: str | None = None) -> tuple[int, int]:
    """Contour behavior actually implemented at that stamp.

    A stamp newer than the newest implemented contour feature is a measurement
    or reporting release, so it reports that newest feature. Tooling revisions
    can never be read as a new contour generation.
    """
    stamp = contour_tuple(value)
    enabled = [feature for feature in CONTOUR_FEATURES if feature <= stamp]
    return max(enabled) if enabled else (0, 0)


def format_version(value: str | None = None) -> str:
    return ".".join(str(x) for x in parse_version(value))


def format_behavior(value: str | None = None) -> str:
    return ".".join(str(x) for x in behavior_tuple(value))


def at_least(track: int, revision: int, value: str | None = None) -> bool:
    return contour_tuple(value) >= (track, revision)


def summary(value: str | None = None) -> dict[str, object]:
    version = parse_version(value)
    stamped = ".".join(str(x) for x in version[2:])
    behavior = ".".join(str(x) for x in behavior_tuple(value))
    return {
        "canonical_version": ".".join(str(x) for x in version),
        "release_line": ".".join(str(x) for x in version[:2]),
        "contour_version": stamped,
        "contour_behavior": behavior,
        "contour_changed_at_this_release": behavior == stamped,
    }
