#!/usr/bin/env python3
"""Contract for contour 0.0.2.31 — plurality vote on set/order answers, no peeking allowed.

The corrected stability map (UNSTABLE-CELLS-V61.md) says the coin-flip cells are content-side: under a
different seed the model picks a different letter set (C) or a different id list (J). This mechanism asks
two more samples of the SAME prompt and lets the plurality answer win. Two properties are contractual:

1. selection only — the winner is always one of the model's own answers, nothing is edited or merged;
2. no peeking — the extra samples are asked with the original message list only, and the voting code never
   sees the reference answer, so it cannot be an answer-lookup dressed up as a mechanism.

A tie, a singleton or a set the model never expressed leaves the first answer alone.
"""
import importlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PARB_ROOT", os.getcwd())


def load(version):
    os.environ["PARB_GATE_VERSION"] = version
    os.environ.pop("STRATA_CHECKER_INJECT", None)
    import gate_run as G
    importlib.reload(G)
    return G


fails = []
ran = [0]


def check(name, cond, detail=""):
    ran[0] += 1
    print("%-62s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        fails.append(name)


class StubAcct:
    def __init__(self):
        self.fixes = 0
        self.blocks = 0
        self.code_ms = 0.0
        self.events = []

    def ev(self, kind, msg):
        self.events.append("%s:%s" % (kind, msg))

    def add(self, r, useful=True):
        pass


def row(text):
    return {"text": text, "ptok": 5, "ctok": 9, "ttft": 0.1, "finish": "stop", "err": None, "el": 0.2}


# --- version axis first (reload mutates one module object) ------------------------------------
OLD = load("0.0.2.30")
check("vote off at 0.0.2.30", OLD.SELFCONSIST is False)
check("old stamp never asks extra samples", OLD.selfconsistency_vote(StubAcct(), "J", row('["a"]'), [], 1)["text"] == '["a"]')

G = load("0.0.2.31")
check("vote on at 0.0.2.31", G.SELFCONSIST is True)
check("only set/order categories vote", G.SELFCONSIST_CATS == ("C", "J"))

# --- what counts as an expressed set ----------------------------------------------------------
check("C answer line expresses letters", G._answer_set("C", "разбор\nОТВЕТ: A, C") == ("A", "C"))
check("C bare letters express a set", G._answer_set("C", "A, C") == ("A", "C"))
check("C prose with no letters expresses nothing", G._answer_set("C", "подходит первый") is None)
check("J id list expresses a list", G._answer_set("J", '["v2", "v3", "v5"]') == ("v2", "v3", "v5"))
check("J object does not count", G._answer_set("J", '{"ids": ["v2"]}') is None)
check("J list of objects does not count", G._answer_set("J", '[{"id": "v2"}]') is None)

# --- the vote --------------------------------------------------------------------------------
MSGS = [{"role": "user", "content": "Выбери top-3 по убыванию. Верни JSON-список id: v1..v5"}]
GOLD_MARK = "v2, v3, v5 -- reference"


def scripted(texts):
    calls = []

    def _ask(acct, msgs, seed, mt=512):
        calls.append((msgs, seed))
        return row(texts[len(calls) - 1])
    return _ask, calls


ask, calls = scripted(['["v2", "v3", "v5"]', '["v2", "v3", "v5"]'])
G.ask_ladder = ask
acct = StubAcct()
r = G.selfconsistency_vote(acct, "J", row('["v2", "v4"]'), MSGS, 100)
check("plurality replaces a lone answer", json.loads(r["text"]) == ["v2", "v3", "v5"])
check("exactly two extra samples", len(calls) == 2, "calls=%d" % len(calls))
check("extra samples use the ORIGINAL message list only", all(m == MSGS for m, _ in calls))
check("seeds are distinct from the original", sorted(s for _, s in calls) == sorted(
    [100 + 1 * G._SC_CONST, 100 + 2 * G._SC_CONST]))
check("vote event", "contour:v231_selfconsist_J_vote_taken" in acct.events)
check("no reference text reaches the model in the vote", not any(GOLD_MARK in m[-1]["content"] for m, _ in calls))

ask2, calls2 = scripted(['["v2", "v4"]', '["v2", "v4"]'])
G.ask_ladder = ask2
acct2 = StubAcct()
r2 = G.selfconsistency_vote(acct2, "J", row('["v2", "v4"]'), MSGS, 100)
check("unanimous keeps the first answer", json.loads(r2["text"]) == ["v2", "v4"])
check("unanimous event", "contour:v231_selfconsist_J_unanimous" in acct2.events)

ask3, _ = scripted(['["v1", "v2"]', '["v3", "v4"]'])
G.ask_ladder = ask3
acct3 = StubAcct()
r3 = G.selfconsistency_vote(acct3, "J", row('["v2", "v4"]'), MSGS, 100)
check("three different sets -> no majority, first answer kept", json.loads(r3["text"]) == ["v2", "v4"])
check("no-majority event", "contour:v231_selfconsist_J_no_majority" in acct3.events)

ask4, _ = scripted(['["v2", "v3", "v5"]', '["v1"]'])
G.ask_ladder = ask4
acct4 = StubAcct()
r4 = G.selfconsistency_vote(acct4, "J", row('["v2", "v3", "v5"]'), MSGS, 100)
check("plurality equal to the original changes nothing", json.loads(r4["text"]) == ["v2", "v3", "v5"])
check("plurality-is-original event", "contour:v231_selfconsist_J_plurality_is_original" in acct4.events)

ask5, _ = scripted(["", ""])
G.ask_ladder = ask5
acct5 = StubAcct()
r5 = G.selfconsistency_vote(acct5, "J", row("проза без списка"), MSGS, 100)
check("nothing expressible -> no vote, first answer kept", r5["text"] == "проза без списка")
check("no-expressible-set event", "contour:v231_selfconsist_J_no_expressible_set" in acct5.events)

# --- end-to-end on a real bank task under the frozen scorer -----------------------------------
import parb_check_v6 as CK  # noqa: E402
bank = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "benchmarks", "hard", "bank-hard-v6.json"), encoding="utf-8"))
jt = next(t for t in bank if t["cat"] == "J")
gold = json.dumps(jt["ref"])
one_wrong = '["%s", "%s"]' % (jt["ref"][0], "zz-not-in-prompt")
G.ask_ladder = lambda acct, msgs, seed, mt=512: row(gold)
accte = StubAcct()
re_ = G.selfconsistency_vote(accte, "J", row(one_wrong), MSGS, 7)
c0, f0, d0 = CK.CHECKS["J"](jt, one_wrong)
c1, f1, d1 = CK.CHECKS["J"](jt, re_["text"])
check("real J task: lone wrong answer scores below the voted one",
      c0 < c1 and c1 == 1.0, "single=%.2f voted=%.2f" % (c0, c1))

print()
print("%d checks, %d fail" % (ran[0], len(fails)))
raise SystemExit(1 if fails else 0)
