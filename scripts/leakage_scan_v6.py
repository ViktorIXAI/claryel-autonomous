"""v6 leakage lint (issue #15 gate: 'no gold value inside the prompt').

For every task: the serialized reference must not appear verbatim in the
prompt; for computed-answer categories (J/K/B/A/I) the full serialized gold
must not appear; the literal instruction-side markers 'expected'/'ожидаемый
ответ' must not appear in any prompt. Reports per-task verdicts; exit 0 only
if zero leaks.
"""
import json
import sys

bank = json.load(open("benchmarks/hard/bank-hard-v6.json", encoding="utf-8"))
bad = 0
for t in bank:
    pr = t["prompt"]
    ref = t["ref"]
    rs = json.dumps(ref, ensure_ascii=False, sort_keys=True)
    hits = []
    if rs in pr:
        hits.append("ref_json_in_prompt")
    if t["cat"] in ("J", "K") and isinstance(ref, list):
        for item in ref:
            s = json.dumps(item, ensure_ascii=False)
            if t["cat"] == "J" and len(ref) >= 2 and s in pr and not any(str(x) in pr and x == item for x in ()):
                pass
        # J gold is an ordered id list: the ordered sequence must not be quoted in prompt
        seq = ",".join(map(str, ref))
        if seq in pr.replace(" ", "") and t["cat"] == "J":
            hits.append("ordered_gold_in_prompt")
    low = pr.lower()
    for marker in ("expected", "ожидаемый ответ", "правильный ответ"):
        if marker in low:
            hits.append("answer_marker:" + marker)
    if hits:
        bad += 1
        print("LEAK", t["id"], hits)
print("LEAKAGE SCAN v6: %d tasks, %d leaks" % (len(bank), bad))
sys.exit(0 if bad == 0 else 1)
