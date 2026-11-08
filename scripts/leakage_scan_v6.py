"""v6 leakage lint (issue #15 gate: 'no gold value inside the prompt').

For every task: the serialized reference must not appear verbatim in the
prompt; for computed-answer categories (J/K/B/A/I) the full serialized gold
must not appear; the literal instruction-side markers 'expected'/'ожидаемый
ответ' must not appear in any prompt. Reports per-task verdicts; exit 0 only
if zero leaks. Optional argv[1] selects the bank JSON; with no argument it
stays on the historical v6.1 file so the standing invocation is unchanged.
scripts/bank_gate_census_v6.py imports leakage_scan(bank) to run the same
gate across every published bank version (owner directive 07.11: version
every element of the measurement stack).
"""
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BANK = os.path.join(_ROOT, "benchmarks", "hard", "bank-hard-v6.json")


def leakage_scan(bank):
    """Return [(task_id, hits), ...] for prompts that leak gold or answer markers."""
    out = []
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
            out.append((t["id"], hits))
    return out


def main():
    bank_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BANK
    bank = json.load(open(bank_path, encoding="utf-8"))
    leaks = leakage_scan(bank)
    for tid, hits in leaks:
        print("LEAK", tid, hits)
    print("LEAKAGE SCAN v6: %d tasks, %d leaks" % (len(bank), len(leaks)))
    return 0 if not leaks else 1


if __name__ == "__main__":
    sys.exit(main())
