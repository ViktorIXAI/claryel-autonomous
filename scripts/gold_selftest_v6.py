"""Gold self-test for hard bank v6: every task's constructed-correct answer must score 1.0/1.0.

D loop tasks are exercised through check_D_loop_v6 with protocol-v2 rows.
Exit 0 only if 77/77 gold answers are perfect.
"""
import json
import sys

sys.path.insert(0, "harness")
import parb_check_v6 as c6  # noqa: E402

bank = json.load(open("benchmarks/hard/bank-hard-v6.json", encoding="utf-8"))


def gold_answer(t):
    ref = t["ref"]
    cat = t["cat"]
    if cat == "C":
        return "ОТВЕТ: " + (", ".join(ref["letters"]) if ref["letters"] else "NONE")
    if cat == "K":
        return "\n".join("%s: %s" % (f, v) for f, v in zip(t["fields"], ref))
    if cat == "E":
        return "```python\n" + ref["ref_src"] + "\n```"
    if cat == "F":
        return json.dumps({"cause": ref["cause"], "evidence": ref["support"],
                           "next": ref["safe_next"], "avoid": ref["forbidden"]}, ensure_ascii=False)
    if cat == "G":
        return json.dumps({"conflict": ref["conflict"], "clauses": ref["clauses"],
                           "values": ref["values"]}, ensure_ascii=False)
    if cat == "H":
        return json.dumps({"actions_done": [], "claims": [], "unknown": ref["unknown"],
                           "requires": ref["ask"]}, ensure_ascii=False)
    if cat == "D" and t.get("mode") == "loop":
        return None  # loop path
    return json.dumps(ref, ensure_ascii=False)


fails = []
for t in bank:
    if t["cat"] == "D" and t.get("mode") == "loop":
        rows = [json.dumps({"step": s, "status": "blocked" if s in t["ref"]["blocked"] else "done",
                            "reason": "policy"}) for s in t["ref"]["steps"]]
        cont, fmt, notes = c6.check_D_loop_v6(t, rows)
    else:
        cont, fmt, notes = c6.check(t, gold_answer(t))
    if not (cont == 1.0 and fmt):
        fails.append((t["id"], cont, fmt, notes))

print("GOLD SELFTEST v6: %d/%d perfect" % (len(bank) - len(fails), len(bank)))
for f in fails:
    print(" FAIL", f)
sys.exit(0 if not fails else 1)
