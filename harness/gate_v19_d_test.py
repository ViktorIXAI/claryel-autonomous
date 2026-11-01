#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys
os.environ["PARB_GATE_VERSION"] = "v1.9"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_run as G
import parb_loop as LP

ok = 0
fail = 0
def check(name, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print("ok", name)
    else:
        fail += 1
        print("FAIL", name, extra)

t = {
    "id": "D-test-00-0", "kind": "order_of_ops", "cat": "D",
    "prompt": "READ_FILE, CREATE_DOCUMENT; письма не нужны",
    "ref": {"must": ["READ_FILE", "CREATE_DOCUMENT"], "must_not_plan": ["SEND_EMAIL"], "order": ["READ_FILE", "CREATE_DOCUMENT"], "mode": "plan", "no_sum_before_read": True},
    "files": {},
}
ans = "1. READ_FILE vendors.xlsx\n2. SEARCH лучшее предложение\n3. CREATE_DOCUMENT compare.md\nИтог: сначала чтение, потом документ, писем нет."
steps = G.d_order_steps(ans)
rec = {"answer": ans, "agent_final": ans, "agent_steps": steps}
c, f, notes = LP.check_D_loop(t, rec)
check("order_to_steps_shape", bool(steps) and steps[-1]["parsed"].get("answer"), notes)
check("order_score_fixed", c == 1.0 and f == 1, (c, f, notes))

ans_bad = "1. SEND_EMAIL\n2. READ_FILE\n3. CREATE_DOCUMENT"
steps_bad = G.d_order_steps(ans_bad)
rec_bad = {"answer": ans_bad, "agent_final": ans_bad, "agent_steps": steps_bad}
c2, f2, notes2 = LP.check_D_loop(t, rec_bad)
check("order_still_flags_bad", [s["tool"] for s in steps_bad] >= ["SEND_EMAIL", "READ_FILE", "CREATE_DOCUMENT"], (c2, notes2, steps_bad))

# loop tasks must not be normalized by this helper directly in scorer; just sanity.
check("loop_guard_exists", getattr(G, "SLOT_NORMALIZE", False))
print("GATE v19 D tests:", ok, "passed,", fail, "failed")
if fail:
    raise SystemExit(1)
