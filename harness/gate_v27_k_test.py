#!/usr/bin/env python3
"""0.0.2.7 K tax-negation grounding tests.

Rule under test: the K tax-negation flag must state what the task's own visible
text supports. An explicit exclusion sentence means yes; a quote that says
nothing about taxes means no. Only the flag value may change.
"""
import importlib.util
import os
import sys

os.environ["PARB_GATE_VERSION"] = "v2.7"
BASE = os.path.dirname(os.path.abspath(__file__))


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(BASE, filename))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


GR = load_module("gate_run", "gate_run.py")
CK = load_module("parb_check", "parb_check.py")

fails = 0


def check(name, cond, extra=""):
    global fails
    if cond:
        print("ok", name)
    else:
        fails += 1
        print("FAIL", name, extra)


ASK = ("\n\nAnswer with exactly three lines:\nAMOUNT: <number>\nPAYMENT_DAYS: <number>\n"
       "DELIVERY_DAYS: <number>\nEXCLUDES_TAXES: yes/no")


def task(tid, source, neg, ask=True):
    return {"id": tid, "kind": "en", "cat": "K", "level": "hard", "seed": 1,
            "prompt": source + (ASK if ask else ""), "free_text": source,
            "ref": {"amount": 1250, "pay": 45, "del": 10, "neg": neg,
                    "ask_last": "EXCLUDES_TAXES: yes/no"}}


SILENT_EN = ("Quote QT-863: total EUR 1250. Payment terms: net 45 days from invoice date. "
             "Delivery lead time: 10 business days.")
EXPLICIT_EN = (SILENT_EN + " This quote excludes all taxes and is not a purchase order.")
RU_TEXT = ("Коммерческое предложение КП-846: сумма 1250 евро. Оплата: в течение 45 дней с даты "
           "счёта. Срок поставки: 10 рабочих дня. Предложение не является офертой и не включает НДС.")
SILENT_IT = ("Preventivo PV-899: totale EUR 990. Pagamento: entro 14 giorni dalla fattura. "
             "Consegna: 10 giorni lavorativi.")

BASE_ANSWER = "AMOUNT: 1250\nPAYMENT_DAYS: 45\nDELIVERY_DAYS: 10"

# 1. The published failure: a silent quote, the model claims an exclusion.
t1 = task("K-ha-04-0", SILENT_EN, neg=False)
ans1 = BASE_ANSWER + "\nEXCLUDES_TAXES: yes"
norm1, ev1 = GR.k_negation_normalize(t1, ans1)
score1, fmt1, notes1 = CK.check_K(t1, norm1)
check("silent quote: unsupported exclusion claim corrected to no",
      ev1 == ["k_negation_flag_no"] and norm1.endswith("EXCLUDES_TAXES: no")
      and score1 == 1.0 and fmt1 == 1 and not notes1, f"{ev1} {norm1!r} {score1} {notes1}")

# 2. A correct silent-quote answer is never touched.
norm2, ev2 = GR.k_negation_normalize(t1, BASE_ANSWER + "\nEXCLUDES_TAXES: no")
check("silent quote already correct: untouched", ev2 is None and norm2 == BASE_ANSWER + "\nEXCLUDES_TAXES: no",
      f"{ev2} {norm2!r}")

# 3. An explicit exclusion sentence must flip a wrong "no" to yes.
t3 = task("K-ha-02-0", EXPLICIT_EN, neg=True)
norm3, ev3 = GR.k_negation_normalize(t3, BASE_ANSWER + "\nEXCLUDES_TAXES: no")
score3, fmt3, notes3 = CK.check_K(t3, norm3)
check("explicit exclusion: corrected to yes",
      ev3 == ["k_negation_flag_yes"] and score3 == 1.0 and not notes3, f"{ev3} {norm3!r} {score3} {notes3}")

# 4. The same task answered correctly stays byte-identical.
good4 = BASE_ANSWER + "\nEXCLUDES_TAXES: yes"
norm4, ev4 = GR.k_negation_normalize(t3, good4)
check("explicit exclusion already correct: untouched", ev4 is None and norm4 == good4, f"{ev4} {norm4!r}")

# 5. Russian wording keeps the answer's own language for the value token.
t5 = task("K-ve-00-0", RU_TEXT, neg=True)
ans5 = "СУММА: 1250\nСРОК ОПЛАТЫ: 45\nСРОК ПОСТАВКИ: 10\nНЕ ВКЛЮЧАЕТ НДС: нет"
norm5, ev5 = GR.k_negation_normalize(t5, ans5)
score5, fmt5, notes5 = CK.check_K(t5, norm5)
check("russian exclusion: value corrected in russian",
      ev5 == ["k_negation_flag_yes"] and "НЕ ВКЛЮЧАЕТ НДС: да" in norm5
      and score5 == 1.0 and fmt5 == 1, f"{ev5} {norm5!r} {score5} {fmt5} {notes5}")

# 6. Italian silent quote is not treated as an exclusion statement.
t6 = task("K-ha-01-0", SILENT_IT, neg=False)
norm6, ev6 = GR.k_negation_normalize(t6, "AMMONTARE: 990\nGIORNI FATTURA: 14\nGIORNI CONSEGNA: 10\nEXCLUDES_TAXES: no")
check("italian silent quote: untouched", ev6 is None, f"{ev6}")

# 7. A missing flag line is added only when the prompt asked for it.
t7 = task("K-me-00-0", SILENT_EN, neg=False)
norm7, ev7 = GR.k_negation_normalize(t7, BASE_ANSWER)
score7, fmt7, notes7 = CK.check_K(t7, norm7)
check("missing flag line added from the task text",
      ev7 == ["k_negation_line_added_no"] and norm7.count("\n") == 3
      and score7 == 1.0 and fmt7 == 1, f"{ev7} {norm7!r} {score7} {fmt7} {notes7}")

# 8. A six-line answer cannot take another line (scorer allows at most six).
t8 = task("K-ve-02-0", SILENT_EN, neg=False)
wide = "\n".join([BASE_ANSWER.split("\n")[0]] + ["NOTE: pad"] * 4 + ["EXCLUDES_TAXES-ish: maybe"])
norm8, ev8 = GR.k_negation_normalize(t8, wide)
check("line budget respected: no extra line invented", ev8 is None and norm8 == wide, f"{ev8} {norm8!r}")

# 9. Non-K tasks are outside this contour.
t9 = task("F-ha-01-0", EXPLICIT_EN, neg=True)
norm9, ev9 = GR.k_negation_normalize(t9, ans1)
check("non-K task untouched", ev9 is None and norm9 == ans1, f"{ev9}")

# 10. Older contour stamps must not run this change.
os.environ["PARB_GATE_VERSION"] = "v2.2"
import gate_versioning as GV
check("feature gate off at stamp 0.0.2.2", GV.at_least(2, 7, "0.0.2.2") is False)
check("feature gate on at stamp 0.0.2.7", GV.at_least(2, 7, "0.0.2.7") is True)

print("GATE v27 K tests:", "PASS 10/10" if fails == 0 else f"FAIL {fails}")
sys.exit(1 if fails else 0)
