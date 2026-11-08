#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for the PARITY SHAPE RULE on the public line (2026-11-08).

A contour-parity row is admissible only when the arm's request SHAPE equals the bare arm's:
first token rung = the bare arm's max_tokens, the serve's default thinking state, the same
temperature, the same seed policy. `PARB_SHAPE=bare` is a call-parameter switch (it registers no
contour feature and enables no gate); this test pins three things by driving the REAL call sites
through a stubbed transport:

  1. frozen default (PARB_SHAPE unset): request bytes unchanged - sp1 seed, reasoning_effort
     none, enable_thinking false, first rung 512, and a real truncation still escalates;
  2. bare shape with PARB_LADDER=1200: exactly ONE request whose body keys are exactly the bare
     arm's keys, max_tokens 1200, no seed / reasoning_effort / chat_template_kwargs;
  3. the shape switch never touches the contour stamp or the feature registration.

Run: python3 harness/gate_shape_parity_test.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHILD = r"""
import importlib.util, json, os, sys
from pathlib import Path
HERE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("gate_run", HERE / "gate_run.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["gate_run"] = mod
spec.loader.exec_module(mod)
assert mod.__file__.startswith(str(HERE)), mod.__file__

CAPTURED = []

class _Resp:
    def __init__(self, finish):
        self.finish = finish
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def __iter__(self):
        yield (b'data: {"usage": {"prompt_tokens": 7, "completion_tokens": 3}, "choices": '
               b'[{"delta": {"content": "ANSWER: A"}, "index": 0}]}')
        yield ('data: {"choices": [{"delta": {}, "index": 0, "finish_reason": "%s"}]}'
               % self.finish).encode()
        yield b'data: [DONE]'

FINISH = "stop"


def _fake_urlopen(req, timeout=None):
    CAPTURED.append(json.loads(req.data.decode()))
    return _Resp(FINISH)

mod.urllib.request.urlopen = _fake_urlopen

# --- the real call site: ask_ladder with no explicit rung, as run_one does for category P ---
acct = mod.Acct()
r = mod.ask_ladder(acct, [{"role": "user", "content": "q"}], 12345)
first = {
    "keys": sorted(CAPTURED[0].keys()),
    "temperature": CAPTURED[0].get("temperature"),
    "max_tokens": CAPTURED[0].get("max_tokens"),
    "seed": CAPTURED[0].get("seed"),
    "chat_template_kwargs": CAPTURED[0].get("chat_template_kwargs"),
    "reasoning_effort": CAPTURED[0].get("reasoning_effort"),
    "stream": CAPTURED[0].get("stream"),
}
# --- truncation behaviour: a real finish=length must still walk the ladder ---
n_default = len(CAPTURED)
FINISH = "length"
r2 = mod.ask_ladder(acct, [{"role": "user", "content": "q"}], 12345)
rungs = [b["max_tokens"] for b in CAPTURED[n_default:]]

print(json.dumps({
    "shape_bare": mod.SHAPE_BARE,
    "first_rung": mod.FIRST_RUNG,
    "ladder": mod.LADDER,
    "stamp": mod.CONTOUR_VERSION,
    "behavior": mod.CONTOUR_BEHAVIOR,
    "first_request": first,
    "requests_first_call": len(CAPTURED[:1]),
    "rungs_on_truncation": rungs,
    "ladder_steps": acct.ladder,
    "finish": r.get("finish"),
    "err": r.get("err"),
}))
"""


def run(env_extra, stamp="0.0.2.56"):
    env = dict(os.environ)
    env["PARB_GATE_VERSION"] = stamp
    env.pop("PARB_SHAPE", None)
    env.pop("PARB_LADDER", None)
    env.pop("PARB_LADDER_TOP", None)
    env["PARB_KEY_FILE"] = ""
    env["PARB_API"] = "http://127.0.0.1:1/v1/chat/completions"
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-c", CHILD, str(HERE)], capture_output=True,
                       text=True, env=env, timeout=180)
    if p.returncode:
        raise SystemExit("child failed rc=%s\n%s\n%s" % (p.returncode, p.stdout, p.stderr))
    return json.loads(p.stdout.strip().splitlines()[-1])


BARE_KEYS = sorted(["model", "messages", "temperature", "max_tokens", "stream"])
FROZEN_KEYS = sorted(["model", "messages", "temperature", "max_tokens", "stream", "seed",
                      "reasoning_effort", "chat_template_kwargs"])

fails = []
total = 0


def check(name, cond, detail=""):
    global total
    total += 1
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  " + detail))
    if not cond:
        fails.append(name)


# 1. frozen default stays byte-identical for published arms
d = run({})
check("default: shape flag off", d["shape_bare"] is False)
check("default: first rung 512", d["first_rung"] == 512 and d["first_request"]["max_tokens"] == 512,
      json.dumps(d))
check("default: request keys unchanged", d["first_request"]["keys"] == FROZEN_KEYS,
      json.dumps(d["first_request"]))
check("default: seed pinned + thinking off", d["first_request"]["seed"] == 12345
      and d["first_request"]["chat_template_kwargs"] == {"enable_thinking": False}
      and d["first_request"]["reasoning_effort"] == "none", json.dumps(d["first_request"]))
check("default: truncation still escalates", d["rungs_on_truncation"][:2] == [512, 1024],
      json.dumps(d["rungs_on_truncation"]))
check("default: stamp unchanged", d["stamp"] == "0.0.2.56" and d["behavior"] == "2.56", json.dumps(d))

# 2. bare shape: one request, bare keys, rung = LADDER[0]
b = run({"PARB_SHAPE": "bare", "PARB_LADDER": "1200"})
check("bare: shape flag on", b["shape_bare"] is True)
check("bare: first rung = LADDER[0] = 1200", b["first_rung"] == 1200
      and b["first_request"]["max_tokens"] == 1200, json.dumps(b["first_request"]))
check("bare: request keys exactly the bare arm's", b["first_request"]["keys"] == BARE_KEYS,
      json.dumps(b["first_request"]))
check("bare: no seed / thinking / reasoning kwargs", b["first_request"]["seed"] is None
      and b["first_request"]["chat_template_kwargs"] is None
      and b["first_request"]["reasoning_effort"] is None, json.dumps(b["first_request"]))
check("bare: temperature 0.7, streamed", b["first_request"]["temperature"] == 0.7
      and b["first_request"]["stream"] is True)
check("bare: one request for an untruncated task", b["requests_first_call"] == 1,
      json.dumps(b))
check("bare: stamp unchanged by the shape switch", b["stamp"] == "0.0.2.56"
      and b["behavior"] == "2.56", json.dumps(b))
# a single-rung ladder never escalates beyond the bare arm's ceiling
check("bare: single rung never escalates", len(b["rungs_on_truncation"]) == 1
      and b["rungs_on_truncation"] == [1200], json.dumps(b["rungs_on_truncation"]))

# 3. bare shape with a real ladder keeps its own first rung (env honored, no silent 512)
b2 = run({"PARB_SHAPE": "bare", "PARB_LADDER": "1200,2400"})
check("bare+ladder: first request at 1200, escalates to 2400 only on truncation",
      b2["first_request"]["max_tokens"] == 1200 and b2["rungs_on_truncation"][:2] == [1200, 2400],
      json.dumps(b2))

print("\n%d/%d checks pass" % (total - len(fails), total))
sys.exit(1 if fails else 0)
