# -*- coding: utf-8 -*-
"""Contour 0.0.2.32: self-consistency and the artifact-shape guarantee are FROZEN to their own stamps.

Both mechanisms were measured negative on the paired arms they were published with — 0.0.2.30 cost
-1.3 cells, 0.0.2.31 cost -2.7 cells and 2.5x the energy (`PAIR-230-V61.md`, `PAIR-231-V61.md`). A later
stamp must not silently inherit a feature that lost: `contour_at_least` would have carried both into every
future arm. Registration of a behaviour is therefore paired with an explicit adoption state, and a rejected
behaviour stays available only at the exact stamp where it was measured, so that stamp remains reproducible.

`harness/gate_v49_feature_adoption_test.py` is the contract: a stamp inherits only adopted behaviour.
"""

# Measured-negative contour behaviours: registered in CONTOUR_FEATURES for the record, and enabled only at
# the revision where the measurement was made. Key = feature name, value = the single revision it belongs to.
REJECTED_FEATURES = {
    "contract_shape_guarantee": (2, 30),
    "selfconsistency_vote": (2, 31),
    # 0.0.2.36 group-4 lottery selection measured pair-236 (PAIR-236-V61.md): 6 fires across three paired
    # seeds, ZERO converted scoreboard cells; the H class turned out content-BIASED (every strict re-sample
    # omits the same component — the 2.31 failure mode), and the arm mean was −1.0. Frozen to its own stamp.
    "g4_lottery_selection": (2, 36),
}

# 0.0.2.32 / 0.0.2.33 measured UNRESOLVABLE on bank v6.1 (+1.3 cells each, below the ~2-cell floor of the
# same comparison): `j_prompt_rerank` (PAIR-232-V61.md) and `a_table_arith` (PAIR-233-V61.md, zero live
# fires: the candidate model answered its target cell correctly in every seed, so the arm delta contained
# no on-target cells). A behaviour inherits only if its measurement resolved it — an unadopted feature
# stays enabled at its own stamp alone, so it cannot ride into a later candidate's measurement.
UNADOPTED_FEATURES = {
    "j_prompt_rerank": (2, 32),
    # 2.33 measured unresolvable ONLY because its arms never produced an on-target cell (zero live
    # fires — the mechanism never saw a failing seed to repair). pair-237's adopted line produced two:
    # A-ex6-00 lost seeds 1-2 with fields_mismatch:surcharges,total, and the frozen grammar replays to
    # 1.00 strict with its event on exactly those published bytes (PAIR-237-V61.md). RE-LANDED from
    # 0.0.2.38 as that stamp's single candidate change (gate_run
    # `A_TABLE_ARITH = CONTOUR_REVISION == (2, 33) or contour_at_least(2, 38)`) under the pre-registered
    # pair-238 rule. If pair-238 does not hold the clean pattern, the flag freezes again at 2.38.
    "a_table_arith": (2, 33),
    # 0.0.2.34 measured -1.0 cells at three seeds with ZERO live fires in either grammar: the config
    # grammar accepts 1 of 7 B prompts (no-op, the model was already prompt-equal), the echo grammar
    # matches 1 and refuses on every saved answer for one extra model key, and the two B cells that
    # actually lose sit outside both grammars (`PAIR-234-V61.md`). The B cells are bit-identical
    # between arms: the delta is pure resampling and the mechanism reached zero work.
    "b_field_complete": (2, 34),
    # 0.0.2.35 measured pair-235: the mechanism is confirmed on-target — `contour:v235_b_table_total`
    # fired in all three candidate seeds, converted its only bank target (B-ex6-06) 0/3 -> 3/3 with the
    # event on every converted row and zero extra model calls. But the paired arm mean moved +2.0,
    # exactly AT the ~2-cell resolution floor of this comparison, and four off-target cells flipped with
    # no 2.35 event, breaking the pre-registered clean pattern. The cell-level claim passed; the
    # arm-level claim did not resolve above noise, and the pre-registered decision rule freezes the
    # stamp. Adoption is withheld as a LINE decision, not a mechanism verdict: the repair stays
    # reproducible at stamp 0.0.2.35 and re-adoption is a one-flag owner call (`PAIR-235-V61.md`).
    # RE-LANDED from 0.0.2.37 as that stamp's single candidate change (PAIR-236 decision): the entry above
    # still freezes the 2.35 measurement to 2.35; 2.37 re-enables the gate explicitly (gate_run
    # `B_TABLE_AGGREGATE = CONTOUR_REVISION == (2, 35) or contour_at_least(2, 37)`) under the pre-registered
    # pair-237 rule. MEASURED pair-237: the all-or-nothing pattern held exactly and 0.0.2.37 is ADOPTED as
    # the new control line (PAIR-237-V61.md); the 2.35 measurement entry above stays the historical record.
    "b_table_aggregate": (2, 35),
}
