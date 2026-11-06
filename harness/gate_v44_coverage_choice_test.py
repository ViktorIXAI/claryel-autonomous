#!/usr/bin/env python3
"""Contract for contour 0.0.2.29 — category C (coverage_choice) plumbing.

hard bank v6.1 ships C tasks WITHOUT a top-level n_cand, so coverage_gate short-circuited to a
plain ask_ladder: no per-candidate verdicts, and the returned text was either prose or bare
letters, never the answer line the task itself demands. 0.0.2.29 derives the option letters from
the task text and emits "ОТВЕТ: <letters>" built only from the model's own ПОДХОД verdicts.
The frozen scorer is imported unchanged and must accept the contour's line.
"""
import os
import sys
import importlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PARB_ROOT", os.getcwd())


def load(version):
    os.environ["PARB_GATE_VERSION"] = version
    os.environ.pop("STRATA_CHECKER_INJECT", None)
    import gate_run as G
    importlib.reload(G)
    return G


fails = []


def check(name, cond, detail=""):
    print("%-60s %s %s" % (name, "PASS" if cond else "FAIL", detail))
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


PROMPT = ("Выбери ПОДХОДЯЩИЕ варианты. Формат ответа: строка 'ОТВЕТ: ' с буквами через "
          "запятую по возрастанию; если ни один не подходит — 'ОТВЕТ: NONE'.\n"
          "A: первое\nB: второе\nC: третье\nD: четвёртое\n")
TASK = {"id": "C-ex6-02", "cat": "C", "kind": "c", "prompt": PROMPT,
        "ref": {"letters": ["C"], "n_cand": 4}}
VERDICTS = "A=НЕ ПОДХОД\nB=НЕ ПОДХОД\nC=ПОДХОД\nD=НЕ ПОДХОД\nФИНАЛ: C"


def canned(text):
    def _ask(acct, msgs, seed, mt=512):
        return {"text": text, "ptok": 10, "ctok": 20, "ttft": 0.1,
                "finish": "stop", "err": None, "el": 0.2}
    return _ask


G28 = load("0.0.2.28")
check("2.28: COVERAGE_FROM_PROMPT off", getattr(G28, "COVERAGE_FROM_PROMPT", False) is False)
G28.ask_ladder = canned(VERDICTS)
r28 = G28.coverage_gate(StubAcct(), dict(TASK), 1, [])
check("2.28: task without n_cand keeps the plain ladder text",
    r28["text"] == VERDICTS, repr(r28["text"][:30]))
check("2.28: helper keeps the old bare-letter answer",
      G28.coverage_answer_line(TASK, {"C", "A"}, "raw") == "A,C")

G29 = load("0.0.2.29")
check("2.29: COVERAGE_FROM_PROMPT on", G29.COVERAGE_FROM_PROMPT is True)
check("2.29: checker-keyword injection still OFF", G29.CHECKER_INJECT is False)
G29.ask_ladder = canned(VERDICTS)
acct = StubAcct()
r29 = G29.coverage_gate(acct, dict(TASK), 1, [])
check("2.29: option letters derived from the task text",
      any(e.startswith("contour:v229_coverage_from_prompt:4") for e in acct.events),
      str(acct.events[:2]))
check("2.29: per-candidate coverage protocol ran", "gate:coverage_ok" in acct.events,
      str(acct.events[:4]))
check("2.29: answer line follows the task's own contract", r29["text"] == "ОТВЕТ: C",
      repr(r29["text"]))
check("2.29: empty verdict set becomes NONE, not prose",
      G29.coverage_answer_line(TASK, set(), "рассуждения модели") == "ОТВЕТ: NONE")
check("2.29: task without an ОТВЕТ contract is left alone",
      G29.coverage_answer_line({"prompt": "просто перечисли"}, {"B"}, "raw") == "B")

import parb_check_v6 as CK

c, f, notes = CK.check_C_v6(TASK, r29["text"])
check("frozen scorer accepts the 2.29 line (format + content)",
      f is True and c == 1.0, "c=%s fmt=%s %s" % (c, f, notes))
c2, f2, n2 = CK.check_C_v6(TASK, "Разбираем варианты.\nA, B, C, D")
check("frozen scorer still punishes prose (nothing relaxed)", c2 == 0.0,
      "c=%s fmt=%s %s" % (c2, f2, n2))
print("ALL PASS" if not fails else "FAILED: %s" % fails)
sys.exit(1 if fails else 0)
