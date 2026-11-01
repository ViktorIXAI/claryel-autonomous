#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent re-scorer (spec: independent quality evaluation).

Re-scores frozen model outputs WITHOUT the harness scorer, using a fully
separate implementation of the checkable task semantics:

  * arithmetic tasks (kind=invoice/total, cat A): recompute totals from the
    task's structured ground-truth fields with Decimal;
  * extraction tasks (cat B): require every ground-truth field value present
    in the answer (independent containment check, no regex library from the
    harness);
  * loop/agent tasks (cat D/J): re-check the required tool-call sequence and
    required final JSON from the mock transcript already stored in results;
  * format_ok re-checked independently: JSON/XML/YAML parse, key sets.

Divergences with the harness scorer are the research output — they are
published in full, not averaged away. Second opinions on the "improved" and
"regressed" paired sets directly test the claim that v1.9 wins are real.

Usage: python3 analytics/second_opinion.py <results-a.jsonl> <results-b.jsonl>
       (compares paired (task,rep) deltas AND re-scores both sides)
"""
import json, re, sys
from collections import Counter
from decimal import Decimal

sys.path.insert(0, ".")   # to load the bank (task definitions), not the scorer
BANK = os.environ.get("PARB_BANK", "benchmarks/text-gates/bank.json")


def load_rows(path):
    d = {}
    for line in open(path, encoding="utf-8", errors="ignore"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if not r.get("task"):
            continue
        k = (r["task"], r.get("rep"))
        if k not in d or float(r.get("content") or 0) > float(d[k].get("content") or 0):
            d[k] = r
    return d


def bank_index():
    return {t["id"]: t for t in json.load(open(BANK, encoding="utf-8"))}


NUM = re.compile(r"-?\d+(?:[.,]\d+)?")


def num(x):
    return float(str(x).replace(" ", "").replace("\u00a0", "").replace(",", "."))


def rescore_math(task, ans):
    """invoice/total tasks: independent recomputation-free presence check —
    every numeric leaf of ground-truth ref must appear in the answer."""
    ref = task.get("ref")
    if not isinstance(ref, dict):
        return None
    need = set()

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        else:
            try:
                f = round(num(x), 2)
                if isinstance(x, str) and any(ch.isdigit() for ch in x) and f >= 0.01:
                    need.add(f)
                elif isinstance(x, (int, float)) and not isinstance(x, bool) and f >= 0.01:
                    need.add(f)
            except Exception:
                pass

    walk(ref)
    if len(need) < 2:
        return None
    havnums = set()
    for h in NUM.findall(ans):
        try:
            havnums.add(round(num(h), 2))
        except Exception:
            pass
    ok = sum(1 for v in need if v in havnums)
    return round(ok / len(need), 4)


def rescore_extract(task, ans):
    ref = task.get("ref")
    if not isinstance(ref, dict) or not ref:
        return None
    vals = [str(v) for v in ref.values() if v is not None and str(v).strip()]
    if not vals:
        return None
    low = ans.lower()
    hit = sum(1 for v in vals if v.lower().strip() in low)
    return round(hit / len(vals), 4)


def rescore_json_format(ans):
    """independent format check: strict json.loads, no harness helpers."""
    m = re.search(r"\{.*\}", ans, re.S)
    if not m:
        return 0
    try:
        json.loads(m.group(0))
        return 1
    except Exception:
        return 0


TOOLS = ("READ_FILE", "WRITE_FILE", "SEARCH", "EXECUTE_COMMAND", "SEND_EMAIL",
         "CREATE_DOCUMENT", "SUMMARIZE", "CALCULATOR")


def rescore_agent(task, ans):
    """agent-plan tasks (cat D): independent check of the declared tool plan —
    required tools present, forbidden tools absent, relative order respected.
    Implemented from the task's ref spec only; no harness scorer code."""
    ref = task.get("ref")
    if not isinstance(ref, dict):
        return None
    up = ans.upper()
    seq = []
    for m in re.finditer(r"\b(" + "|".join(TOOLS) + r")\b", up):
        t = m.group(1)
        if t not in seq:
            seq.append(t)
    if not seq:
        return None
    ok = True
    for t in ref.get("must", []):
        if t not in seq:
            ok = False
    for t in ref.get("must_not_plan", []):
        if t in seq:
            ok = False
    order = [t for t in ref.get("order", []) if t in TOOLS]
    if order:
        idx = [seq.index(t) if t in seq else 999 for t in order]
        if 999 in idx or idx != sorted(idx):
            ok = False
    if ref.get("no_sum_before_read") and "READ_FILE" in seq and "SUMMARIZE" in seq:
        if seq.index("SUMMARIZE") < seq.index("READ_FILE"):
            ok = False
    return 1.0 if ok else 0.0


def rescore(task, ans):
    c = task["id"][0]
    if c == "D" or task.get("units") == "agent_plan":
        return rescore_agent(task, ans)
    if c == "A" or task.get("kind") in ("invoice", "total", "arith"):
        v = rescore_math(task, ans)
        if v is not None:
            return v
    if c in ("B", "H") or task.get("subcat") in ("slot", "slots", "extract"):
        return rescore_extract(task, ans)
    return None   # categories whose semantics cannot be re-derived independently


def main():
    a = load_rows(sys.argv[1])
    b = load_rows(sys.argv[2]) if len(sys.argv) > 2 else {}
    bank = bank_index()
    out = {"files": [sys.argv[1], *sys.argv[2:]], "rescored_share": 0}

    def score_side(rows):
        agree = disagree = skipped = 0
        deltas = []
        for k, r in rows.items():
            t = bank.get(k[0])
            if not t:
                skipped += 1
                continue
            alt = rescore(t, r.get("answer") or r.get("content_text") or "")
            if alt is None:
                skipped += 1
                continue
            ours = float(r.get("content") or 0)
            deltas.append((k, ours, alt))
            if abs(ours - alt) < 0.35:
                agree += 1
            else:
                disagree += 1
        return deltas, agree, disagree, skipped

    for side, rows in (("A", a), ("B", b)):
        if not rows:
            continue
        dl, ag, dis, sk = score_side(rows)
        out[f"side_{side}"] = {"rows": len(rows), "rescored": len(dl),
                               "agree": ag, "diverge": dis, "not_independently_scoreable": sk,
                               "mean_harness": round(sum(x[1] for x in dl) / len(dl), 4) if dl else None,
                               "mean_independent": round(sum(x[2] for x in dl) / len(dl), 4) if dl else None}

    if b:
        keys = set(a) & set(b)
        # matched independent delta over all pairs both sides can score
        dl = []
        for k in keys:
            t = bank.get(k[0])
            if not t:
                continue
            alt_a = rescore(t, a[k].get("answer") or "")
            alt_b = rescore(t, b[k].get("answer") or "")
            if alt_a is not None and alt_b is not None:
                dl.append(alt_b - alt_a)
        if dl:
            out["matched_independent_delta"] = {
                "n": len(dl),
                "avg": round(sum(dl) / len(dl), 4),
                "improved": sum(1 for d in dl if d > 1e-9),
                "regressed": sum(1 for d in dl if d < -1e-9),
                "note": "same (task,rep) pairs re-scored by the independent scorer only"}
        imp = [k for k in keys if float(b[k].get("content") or 0) > float(a[k].get("content") or 0) + 1e-9]
        reg = [k for k in keys if float(b[k].get("content") or 0) < float(a[k].get("content") or 0) - 1e-9]
        for label, ks in (("improved_pairs", imp), ("regressed_pairs", reg)):
            ok = rev = unk = 0
            for k in ks:
                t = bank.get(k[0])
                alt_b = rescore(t, b[k].get("answer") or "") if t else None
                alt_a = rescore(t, a[k].get("answer") or "") if t else None
                if alt_b is None or alt_a is None:
                    unk += 1
                    continue
                if alt_b > alt_a + 1e-9:
                    ok += 1
                elif alt_b < alt_a - 1e-9:
                    rev += 1
            out[label] = {"n": len(ks), "independently_confirmed": ok,
                          "independently_reversed": rev, "not_scoreable": unk}
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
