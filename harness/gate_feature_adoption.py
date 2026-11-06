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
}

# 0.0.2.32 / 0.0.2.33 measured UNRESOLVABLE on bank v6.1 (+1.3 cells each, below the ~2-cell floor of the
# same comparison): `j_prompt_rerank` (PAIR-232-V61.md) and `a_table_arith` (PAIR-233-V61.md, zero live
# fires: the candidate model answered its target cell correctly in every seed, so the arm delta contained
# no on-target cells). A behaviour inherits only if its measurement resolved it — an unadopted feature
# stays enabled at its own stamp alone, so it cannot ride into a later candidate's measurement.
UNADOPTED_FEATURES = {
    "j_prompt_rerank": (2, 32),
    "a_table_arith": (2, 33),
}
