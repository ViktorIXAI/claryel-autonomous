#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for contour 0.0.2.48 (pair-247 candidate): K fields-gate key set from the
task's OWN enumeration.

The bug is published in the bank-v6.2 line artifacts, not hypothesized: `want_fields` scans the
prompt for UPPERCASE tokens followed by a colon, and in a K prompt the only such tokens are the
instruction's own example (`вида FIELD: значение`) plus a parenthetical value form. So for
K-ex6-03 the required key set was `[FIELD, FREE_SHIPPING]`, the contour hint told the model to use
the literal placeholder `FIELD` as a key, and the published line strict-fails that task 9/9 with
code `missing` (content 0.25) while the prompt prints every value the gold needs.

Checks (scripted brain, zero model calls, zero endpoint):
  1. enumeration grammar — real bank prompt, parentheticals, ` и ` separator, non-identifier and
     lowercase/Cyrillic fragments, no-enumeration prompt, idempotent dedup;
  2. placeholder-taint condition — a prompt whose old detection already named real keys keeps its
     set byte-identical at 2.48 (no silent gate change on the adopted line's passing cells);
  3. per-stamp flag matrix — the pair control 2.47 moves ZERO flags vs 2.46... (gate_v49 owns the
     full matrix; here: 2.48 == 2.47 + exactly K_FIELDS_ENUM, and at 2.47 `fields_required` is
     byte-identical to `want_fields` for every bank prompt);
  4. SURFACE INVARIANCE — `want_format` (which decides whether fields_gate runs at all) is
     identical at 2.47 and 2.48 over all 77 bank-v6.2 prompts, and exactly one prompt reaches the
     fields path;
  5. live `fields_gate` wiring at both stamps over the real bank prompt — at 2.47 the placeholder
     answer is accepted (`gate:fields_ok`, one call, no v48 event, hint names FIELD); at 2.48 the
     same first answer fails completeness, the event fires once with the new key count, the hint
     and the re-ask name the four real keys, exactly one re-ask is bought, and a complete second
     answer passes; a no-enumeration task at 2.48 stays byte-identical with zero events.
  6. versioning axes — (2,48) registered, CURRENT, behavior 2.48 only at the candidate stamp,
     registered_stamp() accepts it (the runner fail-closes otherwise).
"""
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("PARB_ROOT", os.getcwd())

BANK = HERE.parent / "benchmarks" / "hard" / "bank-hard-v6.2.json"


def load(ver):
    """Import THIS harness copy of gate_run at a given stamp (path forced: an older workspace
    copy on sys.path would silently measure a stale contour — the gate_v49 lesson)."""
    os.environ["PARB_GATE_VERSION"] = ver
    for m in ("gate_run", "gate_format_repair", "gate_loop_drive", "gate_versioning",
              "gate_j_rerank", "gate_c_ground", "parb_loop"):
        sys.modules.pop(m, None)
    spec = importlib.util.spec_from_file_location("gate_run", str(HERE / "gate_run.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gate_run"] = mod
    spec.loader.exec_module(mod)
    assert mod.__file__.startswith(str(HERE)), "shadowed contour copy: %s" % mod.__file__
    return mod


CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        print("FAIL: %s" % msg)
        raise SystemExit(1)


# ---------------------------------------------------------------- bank fixtures
bank = json.load(open(BANK, encoding="utf-8"))
BT = {t["id"]: t for t in bank}
K3 = BT["K-ex6-03"]["prompt"]
K0 = BT["K-ex6-00"]["prompt"]

# a synthetic prompt that already names real keys line-anchored (old detection is clean)
CLEAN_PROMPT = ("Заполни карточку. Каждая строка — отдельное поле.\n"
                "ARTICLE: —\nDELIVERY: —\nЗаказ №77, склад 4.")
# a synthetic prompt with an enumeration but NO placeholder token in the old set
ENUM_CLEAN_PROMPT = ("Дай строки КЛЮЧ: значение.\n"
                     "ITEM: —\nQTY: —\nТовар 'Oslo', 200 штук.")
# a synthetic prompt with an enumeration AND a placeholder token (the K shape, invented names)
SYN_K_PROMPT = ("Извлеки поля. Верни ровно 3 строк вида FIELD: значение, без пояснений.\n"
                "Заявка RFQ-1: 12 поддонов 'Krause', срок 5 недель.\n"
                "Поля: ITEM, QTY, LEAD_WEEKS (LEAD_WEEKS: число)")

PLACEHOLDER_KEYS = ("FIELD", "KEY", "КЛЮЧ", "КЛЮЧИ", "NAME", "ИМЯ")


class Acct:
    def __init__(self):
        self.events = []
        self.code_ms = 0.0
        self.fixes = 0

    def ev(self, kind, what):
        self.events.append("%s:%s" % (kind, what))


def stub_calls(mod, first, second=None):
    """Script the two brain entry points fields_gate uses; record hints and call count."""
    seen = {"ladder": [], "repair": [], "seeds": []}
    queue = [first] + ([second] if second is not None else [])

    def ask_ladder(acct, msgs, seed):
        seen["ladder"].append(msgs[-1]["content"])
        seen["seeds"].append(seed)
        txt = queue.pop(0) if queue else ""
        return {"text": txt, "ptok": 20, "ctok": 10, "ttft": 0.1, "finish": "stop",
                "err": None, "el": 0.3}

    def ask_repair(acct, msgs, hint, seed, prev=None):
        seen["repair"].append(hint)
        seen["seeds"].append(seed)
        txt = queue.pop(0) if queue else ""
        return {"text": txt, "ptok": 20, "ctok": 10, "ttft": 0.1, "finish": "stop",
                "err": None, "el": 0.3}

    mod.ask_ladder = ask_ladder
    mod.ask_repair = ask_repair
    return seen


g47 = load("0.0.2.47")
g48 = load("0.0.2.48")

# ---------------------------------------------------------------- 1. grammar
ck(g48.fields_enumeration(K3) == ["ITEM", "QTY", "LEAD_WEEKS", "FREE_SHIPPING"],
   "real K-ex6-03 prompt enumerates exactly its four fields: %s" % g48.fields_enumeration(K3))
ck("FREE_SHIPPING" in g48.fields_enumeration(K3),
   "the parenthetical value form never removes the enumerated key it names")
ck(g48.fields_enumeration(SYN_K_PROMPT) == ["ITEM", "QTY", "LEAD_WEEKS"],
   "invented field names parse with the same grammar (no bank-specific table)")
ck(g48.fields_enumeration("Поля: ITEM, QTY и ADDRESS\n") == ["ITEM", "QTY", "ADDRESS"],
   "` и ` separator handled")
ck(g48.fields_enumeration("Поля: item, Кол-во, 7, a1\n") == [],
   "lowercase / Cyrillic / numeric / short fragments never become keys")
ck(g48.fields_enumeration("Просто текст без перечисления полей") == [],
   "no enumeration line -> empty set")
ck(g48.fields_enumeration("Поля: ITEM, ITEM, QTY\n") == ["ITEM", "QTY"], "dedup, order kept")
ck(g48.fields_enumeration("") == [], "empty prompt -> empty set")

# ---------------------------------------------------------------- 2. taint condition
ck(g48.want_fields(CLEAN_PROMPT) == ["ARTICLE", "DELIVERY"],
   "fixture: old detection already names real keys")
ck(g48.fields_required(CLEAN_PROMPT) == g48.want_fields(CLEAN_PROMPT),
   "clean detection is never replaced even if the prompt is later extended")
ck(g48.want_fields(ENUM_CLEAN_PROMPT) == [] or
   not any(k in PLACEHOLDER_KEYS for k in g48.want_fields(ENUM_CLEAN_PROMPT)),
   "fixture ENUM_CLEAN has no placeholder token in the old set")
ck(g48.fields_required(ENUM_CLEAN_PROMPT) == g48.want_fields(ENUM_CLEAN_PROMPT),
   "no placeholder taint -> the required set is byte-identical at 2.48")
ck("FIELD" in g48.want_fields(SYN_K_PROMPT) and
   g48.fields_required(SYN_K_PROMPT) == ["ITEM", "QTY", "LEAD_WEEKS"],
   "placeholder-tainted set IS replaced by the enumeration: old=%s new=%s"
   % (g48.want_fields(SYN_K_PROMPT), g48.fields_required(SYN_K_PROMPT)))
# real bank: the K-ex6-03 old set keeps only its non-placeholder member
ck(g48.want_fields(K3) == ["FIELD", "FREE_SHIPPING"],
   "published detection for K-ex6-03 is [FIELD, FREE_SHIPPING]: %s" % g48.want_fields(K3))
ck(g48.fields_required(K3) == ["ITEM", "QTY", "LEAD_WEEKS", "FREE_SHIPPING"],
   "2.48 required set = enumeration + non-placeholder old keys: %s" % g48.fields_required(K3))

# ---------------------------------------------------------------- 3. per-stamp matrix
_FLAGS = [n for n in dir(g47) if n.isupper() and isinstance(getattr(g47, n), bool)]
ck(getattr(g47, "K_FIELDS_ENUM") is False, "the pair-247 trigger is OFF on the 2.47 control line")
ck(getattr(g48, "K_FIELDS_ENUM") is True, "the candidate trigger is ON at 2.48")
_diff = [f for f in _FLAGS if getattr(g48, f) != getattr(g47, f) and f != "K_FIELDS_ENUM"]
ck(not _diff, "2.48 = the 2.47 matrix + exactly K_FIELDS_ENUM (%s)" % _diff)
for t in bank:
    ck(g47.fields_required(t["prompt"]) == g47.want_fields(t["prompt"]),
       "at the control stamp 2.47 fields_required is byte-identical to want_fields (%s)" % t["id"])

# ---------------------------------------------------------------- 4. surface invariance
changed = sorted(t["id"] for t in bank
                 if g48.fields_required(t["prompt"]) != g48.want_fields(t["prompt"]))
ck(changed == ["K-ex6-00", "K-ex6-01", "K-ex6-02", "K-ex6-03"],
   "the required set changes only on the four K tasks that enumerate fields: %s" % changed)
_fmt48 = {t["id"]: g48.want_format(t["prompt"]) for t in bank}
live = sorted(i for i in changed if _fmt48[i] == "fields")
ck(live == ["K-ex6-03"],
   "of those, only K-ex6-03 actually reaches fields_gate — the LIVE surface is one task: %s" % live)
fmt47 = {t["id"]: g47.want_format(t["prompt"]) for t in bank}
fmt48 = {t["id"]: g48.want_format(t["prompt"]) for t in bank}
ck(fmt47 == fmt48, "want_format (which decides whether fields_gate runs at all) is invariant 2.47->2.48")
fields_tasks = sorted(i for i, f in fmt48.items() if f == "fields")
ck(fields_tasks == ["K-ex6-03"],
   "exactly one bank task reaches the fields path: %s" % fields_tasks)
for kid in ("K-ex6-00", "K-ex6-01", "K-ex6-02"):
    ck(fmt48[kid] == "text", "%s stays on the text path at 2.48 (gate never runs)" % kid)

# ---------------------------------------------------------------- 5. live fields_gate
PLACEHOLDER_ANSWER = "FIELD: кресло 'Oslo'\nFREE_SHIPPING: yes"
COMPLETE_ANSWER = "ITEM: кресла Oslo\nQTY: 200\nLEAD_WEEKS: 14\nFREE_SHIPPING: yes"
TASK3 = {"id": "K-ex6-03", "cat": "K", "kind": "k", "level": "ex6", "prompt": K3}
SYN_TASK = {"id": "K-ex6-99", "cat": "K", "kind": "k", "level": "ex6", "prompt": SYN_K_PROMPT}


def run_gate(mod, task, first, second=None):
    acct = Acct()
    seen = stub_calls(mod, first, second)
    out = mod.fields_gate(acct, task, 404001, [{"role": "user", "content": task["prompt"]}])
    return acct, seen, out


# control stamp: the placeholder answer is ACCEPTED (that is the published bug)
a, s, r = run_gate(g47, TASK3, PLACEHOLDER_ANSWER)
ck(r["text"] == PLACEHOLDER_ANSWER, "2.47 adopts the placeholder-shaped answer unchanged")
ck("gate:fields_ok" in a.events and not any(x.startswith("fix:") for x in a.events),
   "2.47 gate passes it with no re-ask: %s" % a.events)
ck(not any("v48" in x for x in a.events), "no v48 event at the control stamp")
ck(len(s["ladder"]) == 1 and not s["repair"], "exactly one brain call at 2.47")
ck("FIELD" in s["ladder"][0] and "LEAD_WEEKS" not in s["ladder"][0],
   "2.47 hint names the placeholder key, never the task's fields: %r" % s["ladder"][0])

# candidate stamp: same first answer now fails completeness, one re-ask buys the real keys
a, s, r = run_gate(g48, TASK3, PLACEHOLDER_ANSWER, COMPLETE_ANSWER)
ck("contour:v48_fields_enum_from_prompt:4" in a.events,
   "the wiring event fires once with the new key count: %s" % a.events)
ck(sum(1 for x in a.events if "v48" in x) == 1, "the event fires at most once per task")
ck("gate:fields_gap_3" in a.events, "three required keys are missing from the placeholder answer")
ck(len(s["ladder"]) == 1 and len(s["repair"]) == 1, "exactly one re-ask is bought at 2.48")
ck("ITEM" in s["ladder"][0] and "LEAD_WEEKS" in s["ladder"][0],
   "2.48 hint names the task's own fields: %r" % s["ladder"][0])
ck(all(("ITEM" in h and "QTY" in h and "LEAD_WEEKS" in h) for h in s["repair"]),
   "the re-ask names the real keys and the missing ones")
ck(r["text"] == COMPLETE_ANSWER and "gate:fields_ok" in a.events,
   "the complete answer passes the 2.48 gate: %s" % a.events)

# a complete first answer at 2.48 costs nothing extra
a, s, r = run_gate(g48, TASK3, COMPLETE_ANSWER)
ck(r["text"] == COMPLETE_ANSWER and "gate:fields_ok" in a.events
   and not any(x.startswith("fix:") for x in a.events)
   and len(s["ladder"]) == 1 and not s["repair"],
   "a compliant answer pays zero extra calls at 2.48: %s" % a.events)

# synthetic same-shape task (invented field names) behaves identically
a, s, r = run_gate(g48, SYN_TASK, "FIELD: поддоны 'Krause'\n", "ITEM: поддоны 'Krause'\nQTY: 12\nLEAD_WEEKS: 5\n")
ck("contour:v48_fields_enum_from_prompt:3" in a.events and r["text"].startswith("ITEM:"),
   "grammar is generic, not a K-ex6-03 lookup: %s" % a.events)

# a no-enumeration task at 2.48 is untouched (zero events, zero extra calls)
a, s, r = run_gate(g48, {"id": "K-ex6-98", "cat": "K", "kind": "k", "level": "ex6",
                         "prompt": CLEAN_PROMPT}, "ARTICLE: x\nDELIVERY: y\n")
ck(not any("v48" in x for x in a.events) and "gate:fields_ok" in a.events,
   "no enumeration + no placeholder taint -> byte-identical path at 2.48: %s" % a.events)

# control stamp reproduces the same synthetic behavior with zero v48 events
a47, s47, r47 = run_gate(g47, SYN_TASK, "FIELD: поддоны 'Krause'\n", "ITEM: x\n")
a48, s48, r48 = run_gate(g48, SYN_TASK, "FIELD: поддоны 'Krause'\n", "ITEM: x\n")
ck(not any("v48" in x for x in a47.events), "the control arm carries no v48 event")
ck(any("v48" in x for x in a48.events), "the candidate arm fires v48 on the same bytes")
ck("FIELD" in g47.fields_required(SYN_K_PROMPT) and "ITEM" not in g47.fields_required(SYN_K_PROMPT),
   "2.47 required set on the synthetic task stays placeholder-tainted")
import re as _re
_KEYLIST = lambda hint: set(x.strip() for x in _re.search(
    r"таких ключей: ([^.]+)\.", hint).group(1).split(","))
ck(all("ITEM" not in _KEYLIST(h) for h in s47["ladder"] + s47["repair"]),
   "2.47 never REQUIRES the task's real fields (worst case it asks to delete them): %s"
   % [sorted(_KEYLIST(h)) for h in s47["ladder"] + s47["repair"]])
ck(all({"ITEM", "QTY"} <= _KEYLIST(h) for h in s48["ladder"] + s48["repair"]),
   "2.48 requires the real fields in every hint: %s"
   % [sorted(_KEYLIST(h)) for h in s48["ladder"] + s48["repair"]])
ck("gate:fields_ok" in a47.events or not any("v48" in x for x in a47.events),
   "no v48 wiring on the control at all")
ck(any("fields_gap" in x for x in a48.events),
   "2.48 sees missing fields on the synthetic task: %s" % a48.events)

# ---------------------------------------------------------------- 6. versioning axes
import gate_versioning as GV
ck((2, 48) in GV.CONTOUR_FEATURES, "(2,48) registered in CONTOUR_FEATURES")
ck(GV.CURRENT_REVISION == (2, 48) and GV.CURRENT_STAMP == "0.0.2.48",
   "CURRENT bumped to the candidate stamp")
ck(GV.CURRENT_STAMP == "0.0.%d.%d" % GV.CURRENT_REVISION, "stamp string matches the revision")
ck(GV.behavior_tuple("0.0.2.47") == (2, 47) and GV.behavior_tuple("0.0.2.48") == (2, 48),
   "behavior axis moves only at the candidate stamp")
ck(GV.registered_stamp("0.0.2.48")[2:] == (2, 48), "registered_stamp accepts the candidate stamp")
ck((2, 48) not in GV.RESERVED_TOOLING_REVISIONS, "outside the reserved tooling band")

print("gate_v62 (K fields-gate key enumeration): %d checks PASS" % CHECKS)
