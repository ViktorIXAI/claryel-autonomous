#!/usr/bin/env python3
"""0.0.2.8 engine-stall guard tests.

Rule under test: a response that produced nothing without an HTTP error is a serve
stall, not a wrong answer. It is retried once with the identical sample, flagged on
the row, and a serve that stalls too often stops the run.
"""
import importlib.util
import os
import sys

os.environ["PARB_GATE_VERSION"] = "0.0.2.8"
BASE = os.path.dirname(os.path.abspath(__file__))


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(BASE, filename))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


GG = load_module("gate_engine_guard", "gate_engine_guard.py")
GR = load_module("gate_run", "gate_run.py")

fails = 0


def check(name, cond, extra=""):
    global fails
    if cond:
        print("ok", name)
    else:
        fails += 1
        print("FAIL", name, extra)


# 1. What counts as a stall.
check("empty stream with no usage block is a stall",
      GG.is_stalled("", None, None, None) is True)
check("20 s refusal with zero tokens is a stall",
      GG.is_stalled("", None, 0, 0) is True)
check("HTTP error is not a stall (it is already an error)",
      GG.is_stalled("", "URLError: timed out", None, None) is False)
check("any text is not a stall",
      GG.is_stalled("ОК", None, 900, 3) is False)
check("usage reported means the engine ran",
      GG.is_stalled("", None, 900, 0) is False)

# 2. Rolling rate: armed only on a full window, and strictly above the threshold.
tr = GG.StallTracker(rate=0.25, window=4)
for v in (True, True, True):
    tr.add(v)
check("incomplete window never aborts a run", tr.unfit() is False, tr.verdict())
tr.add(True)
check("4/4 stalls abort", tr.unfit() is True, tr.verdict())
tr2 = GG.StallTracker(rate=0.25, window=4)
for v in (True, False, False, False):
    tr2.add(v)
check("1/4 at threshold 25% does not abort", tr2.unfit() is False, tr2.verdict())
tr3 = GG.StallTracker(rate=0.25, window=4)
for v in (True, True, False, False):
    tr3.add(v)
check("2/4 aborts", tr3.unfit() is True, tr3.verdict())

# 3. ask_ladder retries the identical sample once, then flags the row.
calls = []


def stub_stall(msgs, mt, seed):
    calls.append((mt, seed))
    return {"text": "", "ptok": None, "ctok": None, "ttft": None, "finish": None,
            "el": 20.0, "err": None, "stalled": True}


real_call = GR.call
GR.call = stub_stall
acct = GR.Acct()
r = GR.ask_ladder(acct, [{"role": "user", "content": "x"}], 77, mt=512)
GR.call = real_call
check("stalled request retried exactly once", len(calls) == 2, str(calls))
check("retry keeps the identical seed", calls[0][1] == calls[1][1] == 77, str(calls))
check("row left flagged as stalled", r["stalled"] is True)
check("stall events recorded",
      "engine:stalled_retry" in acct.events and "engine:stalled" in acct.events,
      str(acct.events))

# 4. A recovered retry is recorded as recovered, not as a stall.
calls2 = []


def stub_recover(msgs, mt, seed):
    calls2.append((mt, seed))
    if len(calls2) == 1:
        return {"text": "", "ptok": None, "ctok": None, "ttft": None, "finish": None,
                "el": 20.0, "err": None, "stalled": True}
    return {"text": "ОК", "ptok": 900, "ctok": 3, "ttft": 1.2, "finish": "stop",
            "el": 1.5, "err": None, "stalled": False}


GR.call = stub_recover
acct2 = GR.Acct()
r2 = GR.ask_ladder(acct2, [{"role": "user", "content": "x"}], 77, mt=512)
GR.call = real_call
check("recovered retry scores normally", r2["stalled"] is False and r2["text"] == "ОК", r2)
check("recovery event recorded", "engine:stalled_recovered" in acct2.events, str(acct2.events))

# 5. Every run records the conditions it was measured under.
summary = {"canonical_version": "0.0.2.8", "release_line": "0.0", "contour_version": "2.8",
           "contour_behavior": "2.7", "contour_changed_at_this_release": False}
rec = GG.run_record("P2005", "qwen3.8-flash-next-iq3_s",
                    "http://strata-modelhost:8080/v1/chat/completions", summary, "2.7",
                    health={"loaded": True}, git_sha="abc1234", plan_tasks=681)
check("run record names both version axes",
      rec["contour_version"] == "0.0.2.8" and rec["contour_behavior"] == "2.7"
      and rec["contour_changed_at_this_release"] is False, str(rec))
check("run record keeps serve health and plan size",
      rec["serve_health"] == {"loaded": True} and rec["plan_tasks"] == 681, str(rec))
check("run record states the stall policy",
      rec["stall_policy"]["retry"] == 1 and rec["stall_policy"]["rate"] == 0.25, str(rec))
check("health url derived from the chat endpoint",
      GG.health_url("http://strata-modelhost:8080/v1/chat/completions")
      == "http://strata-modelhost:8080/health",
      GG.health_url("http://h:8080/v1/chat/completions"))

# 6. Measurement-only change: the contour behavior must not move with 0.0.2.8.
import gate_versioning as GV
check("0.0.2.8 keeps contour behavior 2.7", GV.format_behavior("0.0.2.8") == "2.7",
      str(GV.summary("0.0.2.8")))
check("0.0.2.8 flags no contour change",
      GV.summary("0.0.2.8")["contour_changed_at_this_release"] is False)
check("0.0.2.7 still resolves to its own behavior", GV.format_behavior("0.0.2.7") == "2.7")

print("GATE v28 STALL tests:", "PASS 10/10" if fails == 0 else f"FAIL {fails}")
sys.exit(1 if fails else 0)
