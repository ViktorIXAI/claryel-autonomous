#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate_v64 — release 0.0.2.50 (TOOLING ONLY): the generated loop adapter persists
the scorer-row form as `_loop_rows`, and the re-scorer mirror stays byte-equivalent
to the adapter mapping.

Background (cadence-249 correction, 2026-11-07 16:47 CET): the first cadence-249
publication reported a "_loop_rows storage gap" — actually a re-scorer lookup-
convention error. Loop trajectories are stored in result rows as `agent_steps`; the
pinned generated adapter (`parb_loop.check_D_loop`) is the only thing that turns
them into scorer rows, so an external re-scorer had to re-implement the mapping.
This release makes the adapter store the mapped rows directly.

Pins (all offline, no endpoint, no builder run):
 1. version identity: CURRENT_REVISION >= (2,50), CURRENT_STAMP derived, (2,50)
    unregistered in CONTOUR_FEATURES and outside the reserved band, behavior axis
    of 0.0.2.50 == behavior axis of 0.0.2.48 (tooling-only: zero contour flags move).
 2. adapter contract: the builder TEMPLATE source (extracted with ast — importing
    the builder would START a build, it has no argparse) is exec'd with stub
    imports and driven over a synthetic trajectory covering all four step shapes
    (parsed action, gate_block, gate_rejected+parsed, gate_rejected+no parsed):
    the rows handed to the frozen scorer equal the documented mapping AND are
    persisted into rec["_loop_rows"].
 3. last-call-wins adoption: a second call (the best-of-2 final re-score) replaces
    `_loop_rows` with the final trajectory's rows.
 4. cross-pin: scripts/cadence_score_v62.py's `_loop_rows_from_steps` mirror and
    the adapter template produce IDENTICAL rows on the synthetic case AND on every
    published cadence-249 loop result row (tracked artifact), so the repo scorer
    and the pinned adapter can never drift silently.
"""
import ast
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FAILS = []


def ck(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, "missing module: " + path
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert str(mod.__file__).startswith(HERE) or "scripts" in str(mod.__file__), \
        "module loaded from a foreign path: %s" % mod.__file__
    return mod


def main() -> int:
    GV = _load("gate_versioning_v64", os.path.join(HERE, "gate_versioning.py"))

    # 1. identity ---------------------------------------------------------------
    ck(GV.CURRENT_REVISION >= (2, 50), "CURRENT_REVISION advanced to at least (2, 50)")
    ck(GV.CURRENT_STAMP == "0.0.%d.%d" % GV.CURRENT_REVISION,
       "CURRENT_STAMP derives from CURRENT_REVISION (pair-244 bump lesson)")
    ck((2, 50) not in GV.CONTOUR_FEATURES, "(2, 50) is TOOLING-ONLY: not a contour feature")
    ck((2, 50) not in GV.RESERVED_TOOLING_REVISIONS, "(2, 50) outside the reserved band")
    b50 = GV.behavior_tuple("0.0.2.50")
    b48 = GV.behavior_tuple("0.0.2.48")
    ck(b50 == b48 == (2, 48),
       "behavior axis of release 0.0.2.50 == 0.0.2.48 == (2,48): zero contour flags moved")

    # 2. adapter template extracted from the builder WITHOUT running it ---------
    src = open(os.path.join(ROOT, "scripts", "build_hard_v6_ws.py"), encoding="utf-8").read()
    loop_ad_src = None
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "loop_ad":
            loop_ad_src = ast.literal_eval(node.value)
            break
    ck(isinstance(loop_ad_src, str) and "rec['_loop_rows'] = rows" in loop_ad_src,
       "builder loop-adapter template persists rec['_loop_rows'] = rows")

    captured = {}

    class V6Stub:
        @staticmethod
        def check_D_loop_v6(t, rows):
            captured["rows"] = rows
            return (1.0, True, [])

    ns = {"parb_loop_mech": type("m", (), {"mock_exec": None, "parse_action": None}),
          "parb_check_v6": V6Stub}
    import types
    mod = types.ModuleType("parb_loop_gen")  # (module object unused; exec runs in ns)
    # execute the generated adapter with its imports bound to the stubs
    code = compile(loop_ad_src.replace(
        "from parb_loop_mech import mock_exec, parse_action",
        "mock_exec = parse_action = None").replace(
        "import parb_check_v6 as V6", "V6 = _V6_STUB"),
        "generated_parb_loop.py", "exec")
    ns["_V6_STUB"] = V6Stub
    exec(code, ns)

    steps = [
        {"step": 0, "raw": "READ", "parsed": {"tool": "read_file", "arg": "state"}},
        {"step": 1, "gate_block": "WRITE_FILE"},
        {"step": 2, "raw": "ANS", "parsed": {"answer": "early"}, "gate_rejected": True},
        {"step": 3, "raw": "junk", "parsed": None, "gate_rejected": True},
        {"step": 4, "raw": "FIN", "parsed": {"answer": "final"}, "salvaged": True},
    ]
    expected = [json.dumps({"tool": "read_file", "arg": "state"}, ensure_ascii=False),
                {"tool": "WRITE_FILE", "arg": None},
                {"answer": "early", "gate_rejected": True},
                {"gate_rejected": True},
                json.dumps({"answer": "final"}, ensure_ascii=False)]
    rec = {"agent_steps": steps}
    ns["check_D_loop"]({"id": "D-ex6-x"}, rec)
    ck(captured.get("rows") == expected,
       "adapter maps all five step shapes to the documented scorer-row form")
    ck(rec.get("_loop_rows") == expected,
       "adapter persists the scorer rows into rec['_loop_rows'] (the 2.50 change)")

    # 3. last-call-wins (best-of-2 final re-score) ------------------------------
    rec2 = {"agent_steps": [{"step": 0, "parsed": {"tool": "read_file", "arg": "state"}},
                            {"step": 1, "parsed": {"answer": "retry-won"}}]}
    ns["check_D_loop"]({"id": "D-ex6-x"}, rec2)
    ck(rec2["_loop_rows"] == [json.dumps({"tool": "read_file", "arg": "state"},
                                         ensure_ascii=False),
                              json.dumps({"answer": "retry-won"}, ensure_ascii=False)],
       "a later adapter call replaces _loop_rows: the FINAL adopted trajectory is stored")

    # 4. cross-pin the cadence scorer mirror against the adapter ---------------
    CS = _load("cadence_score_v62_v64", os.path.join(ROOT, "scripts", "cadence_score_v62.py"))
    ck(CS._loop_rows_from_steps(steps) == expected,
       "cadence_score_v62._loop_rows_from_steps mirrors the adapter on the synthetic case")
    n_real = 0
    for rid in ("q49r25", "q49r26", "q49r27"):
        path = os.path.join(ROOT, "benchmarks", "hard", "v6-results", "cadence-249",
                            "results-%s.jsonl" % rid)
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            if r.get("cat") != "D" or "agent_steps" not in r:
                continue
            # adapter rows (fresh exec namespace) vs repo mirror on published bytes
            captured_rows = []

            class V6Real:
                @staticmethod
                def check_D_loop_v6(t, rows):
                    captured_rows.append(rows)

            ns2 = dict(ns)
            ns2["_V6_STUB"] = V6Real
            exec(code, ns2)
            ns2["check_D_loop"]({"id": r["task"]}, {"agent_steps": r["agent_steps"]})
            ck_ok = captured_rows and captured_rows[0] == CS._loop_rows_from_steps(r["agent_steps"])
            if not ck_ok:
                ck(False, "adapter/mirror drift on published %s %s rep%s" % (rid, r["task"], r["rep"]))
            n_real += 1
    ck(n_real == 18, "cross-pinned %d published cadence-249 loop rows (expect 18)" % n_real)

    print("\nRESULT:", "PASS (%d checks)" % (0 if FAILS else 11) if not FAILS
          else "FAIL: %s" % FAILS)
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
