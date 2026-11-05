#!/usr/bin/env python3
"""Contract v36 (contour 2.15): deterministic format repair, zero model tokens.

1. B/D-plain answer wrapped in a one-element list -> plain JSON object, content kept.
2. J decorated items (objects with id) -> bare id sequence; already-bare lists untouched.
3. The repair is inert below revision (2, 15) and must never alter non-JSON answers.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_versioning as V
import gate_run as G

# gate the behavior on the revision axis
orig = V.CURRENT_REVISION
try:
    V.CURRENT_REVISION = (2, 14)
    a, ev = G.post_normalize_answer("B", {"mode": "plain"}, '[{"a": 1}]')
    assert a == '[{"a": 1}]' and ev is None, "2.14 must not repair"
    V.CURRENT_REVISION = (2, 15)

    a, ev = G.post_normalize_answer("B", {"mode": "plain"}, '[{"a": 1}]')
    assert json.loads(a) == {"a": 1} and ev == ["obj_unwrap"], "B unwrap failed"

    a, ev = G.post_normalize_answer("D", {"mode": "plain"}, '[{"step": "x"}]')
    assert json.loads(a) == {"step": "x"} and ev == ["obj_unwrap"], "D unwrap failed"

    a, ev = G.post_normalize_answer("D", {"mode": "loop"}, '[{"action": "x"}]')
    assert a == '[{"action": "x"}]' and ev is None, "loop answers must never be unwrapped"

    a, ev = G.post_normalize_answer("J", {"mode": "plain"},
                                    '[{"id": "b", "why": "x"}, {"id": "a"}]')
    assert json.loads(a) == ["b", "a"] and ev == ["j_id_norm"], "J id-norm failed"

    a, ev = G.post_normalize_answer("J", {"mode": "plain"}, '["b", "a"]')
    assert a == '["b", "a"]' and ev is None, "bare J list must pass through"

    a, ev = G.post_normalize_answer("A", {"mode": "plain"}, "plain prose answer")
    assert a == "plain prose answer" and ev is None, "non-JSON answer must not be touched"

    # wrapped object in a fenced block still repairs
    a, ev = G.post_normalize_answer("B", {"mode": "plain"}, '```json\n[{"a": 1}]\n```')
    assert json.loads(a) == {"a": 1} and ev == ["obj_unwrap"], "fenced unwrap failed"
finally:
    V.CURRENT_REVISION = orig
print("CONTRACT v36 OK: 2.15 format repair active, inert at 2.14, loop/prose/bare untouched")
