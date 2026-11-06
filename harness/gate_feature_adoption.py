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
