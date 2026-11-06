#!/usr/bin/env python3
"""Contract for contour 0.0.2.30 — the artifact shape is part of the contract.

The six-seed stability map (UNSTABLE-CELLS-V61.md) showed that 12 of 14 seed-unstable cells died on a
total parse collapse (`no_json` / `no_list` / `no_answer_line`) with no contour repair event in the losing
seed. 0.0.2.30 takes one shape-only re-ask and, if that still fails, salvages the model's own text
deterministically. Two properties are contractual here:

1. no content invention: every salvaged string is a substring of what the model already produced;
2. no scorer leakage: the re-ask instruction is a fixed shape string that quotes no gold value, no
   scorer field name and no checker keyword (issue #15 keeps the official score keyword-free).

The frozen scorer is imported unchanged and must accept the salvaged artifact.
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


# importlib.reload mutates the single gate_run module object, so the version-dependent assertions have to
# run while that module is loaded at the version they describe: 0.0.2.29 first (gate off), then 0.0.2.30.
OLD = load("0.0.2.29")
check("gate off at 0.0.2.29", OLD.CONTRACT_GUARANTEE is False)
check("old stamp leaves a collapsed answer alone",
      OLD.contract_guarantee(StubAcct(), "A", {"text": "ответ такой", "err": None}, [], 1)["text"] == "ответ такой")

G = load("0.0.2.30")
check("gate on at 0.0.2.30", G.CONTRACT_GUARANTEE is True)

# --- shape detector ---------------------------------------------------------------------------
check("prose has no json object", G._contract_shape_missing("A", "Давай так: риск высокий") == "json_object")
check("json object satisfies A", G._contract_shape_missing("A", '{"total": 10}') is None)
check("dict is not a list for J", G._contract_shape_missing("J", '{"a": 1}') == "json_list")
check("list satisfies J", G._contract_shape_missing("J", '[{"id": "c1"}]') is None)
check("prose has no field lines for K", G._contract_shape_missing("K", "хостинг дорогой") == "field_lines")
check("field lines satisfy K", G._contract_shape_missing("K", "SERVICE: hosting\nTAX: no") is None)
check("C needs the answer line", G._contract_shape_missing("C", "A, C") == "answer_line")
check("C accepts the answer line", G._contract_shape_missing("C", "разбор\nОТВЕТ: A, C") is None)
check("empty answer detected", G._contract_shape_missing("A", "   ") == "empty")

# --- salvage never invents --------------------------------------------------------------------
PROSE_A = ('Коллега, считал так: итого 120 евро, вот итог:\n'
           '{"net": 100, "vat": 20, "total": 120}\n'
           'Проверяй сам.')
salv, ev = G._contract_salvage("A", PROSE_A)
check("A salvage extracts the model's own object", json.loads(salv) == {"net": 100, "vat": 20, "total": 120}, ev)
check("A salvage adds no facts (substring)", salv in PROSE_A)
PROSE_J = "Вот список:\n[{\"id\": \"c1\", \"sum\": 5}, {\"id\": \"c2\", \"sum\": 7}]\nготово."
salv_j, ev_j = G._contract_salvage("J", PROSE_J)
check("J salvage prefers the list", isinstance(json.loads(salv_j), list) and len(json.loads(salv_j)) == 2, ev_j)
check("J salvage is a substring", salv_j in PROSE_J)
salv_k, ev_k = G._contract_salvage("K", "SERVICE: hosting\nTAX: no\nи вообще дорого")
check("K salvage keeps the field lines", salv_k == "SERVICE: hosting\nTAX: no", ev_k)
check("no artifact means no salvage", G._contract_salvage("A", "просто текст без структуры")[1] is None)
check("broken json is not salvaged into a guess", G._contract_salvage("A", '{"net": 100,')[1] is None)

# --- the re-ask path --------------------------------------------------------------------------
CALLS = []


def canned_ok(acct, msgs, seed, mt=512):
    CALLS.append(msgs[-1]["content"])
    return {"text": '{"net": 100, "total": 120}', "ptok": 5, "ctok": 9, "ttft": 0.1,
            "finish": "stop", "err": None, "el": 0.2}


G.ask_ladder = canned_ok
acct = StubAcct()
r = G.contract_guarantee(acct, "A", {"text": "итого 120, без формата", "err": None}, [], 7)
check("shape-only re-ask recovers the artifact", json.loads(r["text"])["total"] == 120)
check("exactly one re-ask", len(CALLS) == 1)
check("re-ask event recorded", "contour:v230_contract_reask_json_object" in acct.events)
check("re-ask success event", "contour:v230_contract_reask_ok" in acct.events)
BANNED = ("эталон", "правильный ответ", "checker", "expected", "gold", "net", "total", "hosting")
check("re-ask hint quotes no gold value or scorer keyword",
      not any(b in CALLS[0].lower() for b in BANNED), CALLS[0][:40])


def canned_bad(acct, msgs, seed, mt=512):
    return {"text": "и снова проза без структуры", "ptok": 5, "ctok": 9, "ttft": 0.1,
            "finish": "stop", "err": None, "el": 0.2}


G.ask_ladder = canned_bad
acct2 = StubAcct()
r2 = G.contract_guarantee(acct2, "A", {"text": 'проза\n{"net": 1}\nконец', "err": None}, [], 7)
check("failed re-ask falls back to deterministic salvage", json.loads(r2["text"]) == {"net": 1})
check("salvage event recorded", "contour:v230_contract_salvage_block" in acct2.events)

acct3 = StubAcct()
r3 = G.contract_guarantee(acct3, "A", {"text": "совсем без структуры", "err": None}, [], 7)
# Rule when nothing works: the model's own first answer is kept verbatim and the failure is reported.
# Choosing between two collapsed answers would be a coin flip; inventing structure would be a lie.
check("nothing to salvage keeps the model's own text verbatim", r3["text"] == "совсем без структуры")
check("unresolved event recorded", "contour:v230_contract_unresolved" in acct3.events)

# --- end-to-end against the real bank and the real scorer --------------------------------------
# Real bank tasks only: the artifact shape under test is the scorer's own requirement, not a fixture
# guess. This also documents what salvage can and cannot do: it rescues an answer that contains the
# artifact somewhere, and it refuses an answer that has no artifact at all.
import parb_check_v6 as CK  # noqa: E402
_bank = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    "benchmarks", "hard", "bank-hard-v6.json"), encoding="utf-8"))
jt = next(t for t in _bank if t["cat"] == "J")
gold_j = json.dumps(jt["ref"])

c0, f0, d0 = CK.CHECKS["J"](jt, "Разобрался, рейтинг будет по убыванию, не переживай.")
check("real J task: an answer with no artifact fails format in the frozen scorer", not f0, str(d0)[:40])

G.ask_ladder = lambda acct, msgs, seed, mt=512: {
    "text": "Рейтинг по убыванию: %s" % gold_j, "ptok": 5, "ctok": 9, "ttft": 0.1,
    "finish": "stop", "err": None, "el": 0.2}
acctj = StubAcct()
rj = G.contract_guarantee(acctj, "J", {"text": "Разобрался, рейтинг будет по убыванию, не переживай.",
                                       "err": None}, [], 11)
cj, fj, dj = CK.CHECKS["J"](jt, rj["text"])
check("real J task: guarantee path yields an artifact the frozen scorer passes",
      bool(fj) and cj == 1.0, "content=%.2f %s" % (cj, str(dj)[:40]))

ct = next(t for t in _bank if t["cat"] == "C" and isinstance(t.get("ref"), dict) is False
          or (t["cat"] == "C" and t["id"] == "C-ex6-02"))
letters = ct["ref"] if isinstance(ct["ref"], list) else ct["ref"].get("letters", [])
cc0, cf0, cd0 = CK.CHECKS["C"](ct, "первый ближе всего, наверное A")
check("real C task: prose without the answer line fails in the frozen scorer", not cf0, str(cd0)[:40])
G.ask_ladder = lambda acct, msgs, seed, mt=512: {
    "text": "ОТВЕТ: " + ", ".join(letters), "ptok": 5, "ctok": 4, "ttft": 0.1,
    "finish": "stop", "err": None, "el": 0.2}
acctc = StubAcct()
rc = G.contract_guarantee(acctc, "C", {"text": "первый ближе всего, наверное A", "err": None}, [], 13)
ccc, ccf, ccd = CK.CHECKS["C"](ct, rc["text"])
check("real C task: guarantee path yields the answer line the frozen scorer passes",
      bool(ccf) and ccc == 1.0, "%s -> content=%.2f %s" % (rc["text"][:24], ccc, str(ccd)[:40]))

print()
print("%d checks, %d fail" % (ran[0], len(fails)))
raise SystemExit(1 if fails else 0)
