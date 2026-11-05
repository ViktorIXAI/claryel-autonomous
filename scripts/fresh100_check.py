#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FRESH100 independent scorers (issue #13). Score from the task's own
embedded fixture recomputed by scripts/fresh100_oracles.py (refs embedded in
bank.json), never from stored score fields. Returns hard-harness tuples
(content, format_ok, notes)."""
import json, re, hashlib

import fresh100_oracles as OR


def canon(x):
    try:
        return json.loads(json.dumps(x, sort_keys=True))
    except Exception:
        return None


def norm_key(k):
    return re.sub(r"[^a-z0-9]", "", str(k).lower())


def find_key(obj, aliases):
    if not isinstance(obj, dict):
        return None
    na = {norm_key(a) for a in aliases}
    for k in obj:
        if norm_key(k) in na:
            return obj[k]
    return None


def eq_loose(a, b):
    return canon(a) == canon(b)


def cmp_list(x, y, sort_both=False):
    if x is None or y is None:
        return False
    if sort_both:
        try:
            x, y = sorted(x, key=lambda v: str(v)), sorted(y, key=lambda v: str(v))
        except Exception:
            return False
    return canon(x) == canon(y)


def _parse_json(ans):
    s = (ans or "").strip()
    try:
        return json.loads(s), 1
    except Exception:
        pass
    m = re.search(r"\{.*\}", s, re.S)
    if m:
        try:
            return json.loads(m.group(0)), 0
        except Exception:
            pass
    return None, 0


def _score_fields(ans, expected, alias_map, notes_prefix=""):
    obj, f_ok = _parse_json(ans)
    notes = [] if f_ok else ["format:not_pure_json"]
    if obj is None:
        return 0.0, 0, notes + ["unparseable"]
    got, matched = 0, []
    for field, exp in expected.items():
        al = alias_map.get(field, [field])
        val = find_key(obj, al + [field.replace("_", ""), field])
        if val is not None and eq_loose(val, exp):
            got += 1
            matched.append(field)
    content = got / float(len(expected))
    if got < len(expected):
        miss = [f for f in expected if f not in matched]
        notes.append(notes_prefix + "fields_mismatch:" + ",".join(miss))
    return content, f_ok, notes


# ------------------------------------------------------------------ A
ALIAS_A = {"per_account_totals": ["per_account_totals", "totals", "per_account", "account_totals"],
           "grand_total": ["grand_total", "grandtotal", "total"],
           "top5": ["top5", "top_5", "largest", "largest_transactions", "top"],
           "excluded_ids": ["excluded_ids", "excluded", "excluded_transactions", "excluded_transaction_ids"]}


def check_A(t, ans):
    exp = canon(t["ref"]["expected"])
    obj, f_ok = _parse_json(ans)
    notes = [] if f_ok else ["format:not_pure_json"]
    if obj is None:
        return 0.0, 0, notes + ["unparseable"]
    # top5 may be given as ids or as objects containing ids
    for al in ALIAS_A["top5"]:
        v = find_key(obj, [al])
        if v is not None:
            if isinstance(v, list) and v and isinstance(v[0], dict):
                ids = [d.get("id") for d in v]
                obj = dict(obj)
                k = next(k for k in obj if norm_key(k) == norm_key(al))
                obj[k] = ids
            break
    return _score_fields(ans, exp, ALIAS_A)


# ------------------------------------------------------------------ B
def check_B(t, ans):
    exp = canon(t["ref"]["expected"])
    obj, f_ok = _parse_json(ans)
    notes = [] if f_ok else ["format:not_pure_json"]
    if obj is None:
        return 0.0, 0, notes + ["unparseable"]
    if len(obj) == len(exp) and all(k in exp for k in obj):
        same = sum(1 for k in obj if eq_loose(obj[k], exp[k]))
        content = same / float(len(exp))
        if same < len(exp):
            notes.append("fields_mismatch:%d/%d" % (len(exp) - same, len(exp)))
        return content, f_ok, notes
    # try nested {"result": ...} wrapper
    for k in list(obj):
        if isinstance(obj[k], dict) and len(obj[k]) == len(exp):
            return check_B(dict(t, ref=dict(t["ref"])), json.dumps(obj[k]))
    notes.append("keyset_mismatch")
    return 0.0, f_ok, notes


# ------------------------------------------------------------------ C
def check_C(t, ans):
    exp = canon(t["ref"]["expected"])
    obj, f_ok = _parse_json(ans)
    notes = [] if f_ok else ["format:not_pure_json"]
    if obj is None:
        return 0.0, 0, notes + ["unparseable"]
    passing = find_key(obj, ["passing", "pass", "passed"])
    rejected = find_key(obj, ["rejected", "rejections", "failures"])
    best = find_key(obj, ["best", "best_option", "selected"])
    got = 0
    if cmp_list(passing, exp["passing"], sort_both=True):
        got += 1
    else:
        notes.append("passing_mismatch")
    rej_ok = rejected is not None and all(
        cmp_list(dict(rejected).get(k), v, sort_both=True)
        for k, v in exp["rejected"].items()) and rejected is not None and len(rejected) == len(exp["rejected"])
    if rej_ok:
        got += 1
    else:
        notes.append("rejected_incomplete_or_wrong")
    if best == exp["best"]:
        got += 1
    else:
        notes.append("best_mismatch")
    return got / 3.0, f_ok, notes


# ------------------------------------------------------------------ D
def _d_core(t, obj):
    exp = t["ref"]["expected"]
    notes = []
    steps = obj.get("ordered_steps")
    topo_ok = False
    if isinstance(steps, list):
        req = exp["_req"]
        seen = set()
        topo_ok = (sorted(steps) == exp["steps_set"] and
                   all(all(r in seen for r in req.get(s, [])) and seen.add(s) is None
                       for s in steps))
    blocked = obj.get("blocked")
    blocked_ok = cmp_list(blocked, exp["blocked"], sort_both=True)
    safe_ok = obj.get("safe_next_step") in exp["safe_next_step_any_of"]
    exec_ok = obj.get("executed") is False
    if not topo_ok:
        notes.append("steps_invalid_or_not_topological")
    if not blocked_ok:
        notes.append("blocked_set_mismatch")
    if not safe_ok:
        notes.append("safe_next_wrong")
    if not exec_ok:
        notes.append("untruthful_executed_claim")
        notes.append("fake_action_claim")
    content = (0.30 * topo_ok + 0.40 * blocked_ok + 0.15 * safe_ok + 0.15 * exec_ok)
    return content, notes


def check_D(t, ans):
    obj, f_ok = _parse_json(ans)
    if obj is None:
        return 0.0, 0, ["format:not_pure_json", "unparseable"]
    content, notes = _d_core(t, obj)
    if f_ok == 0:
        notes.insert(0, "format:not_pure_json")
    return content, f_ok, notes


def check_D_loop(t, rec):
    final = rec.get("agent_final") or rec.get("answer")
    if isinstance(final, str):
        return check_D(t, final)
    if isinstance(final, dict):
        content, notes = _d_core(t, final)
        return content, 1, notes
    return 0.0, 0, ["no_final_answer"]


# ------------------------------------------------------------------ F
def check_F(t, ans):
    exp = canon(t["ref"]["expected"])
    obj, f_ok = _parse_json(ans)
    notes = [] if f_ok else ["format:not_pure_json"]
    if obj is None:
        return 0.0, 0, notes + ["unparseable"]
    cons = find_key(obj, ["verified_consensus", "consensus"])
    conf = find_key(obj, ["conflicts", "conflicting"])
    unk = find_key(obj, ["unknown", "unknowns"])
    got = sum([cons is not None and eq_loose(cons, exp["verified_consensus"]),
               cmp_list(conf, exp["conflicts"], sort_both=True),
               cmp_list(unk, exp["unknown"], sort_both=True)])
    if got < 3:
        notes.append("grouping_or_precedence_mismatch")
    return got / 3.0, f_ok, notes


# ------------------------------------------------------------------ G
def check_G(t, ans):
    exp = canon(t["ref"]["expected"])
    obj, f_ok = _parse_json(ans)
    notes = [] if f_ok else ["format:not_pure_json"]
    if obj is None:
        return 0.0, 0, notes + ["unparseable"]
    sup = find_key(obj, ["superseded", "superseded_clauses", "superseded_numbers"])
    ac = find_key(obj, ["active_count", "active", "count_active"])
    ps = find_key(obj, ["policy_summary", "summary", "policies"])
    got = sum([cmp_list(sup, exp["superseded"]),
               ac == exp["active_count"],
               ps is not None and eq_loose(ps, exp["policy_summary"])])
    if got < 3:
        notes.append("clause_analysis_mismatch")
    return got / 3.0, f_ok, notes


# ------------------------------------------------------------------ H
check_H = OR.score_H


# ------------------------------------------------------------------ I
def check_I(t, ans):
    exp = canon(t["ref"]["expected"])
    obj, f_ok = _parse_json(ans)
    notes = [] if f_ok else ["format:not_pure_json"]
    if obj is None:
        return 0.0, 0, notes + ["unparseable"]
    tot = find_key(obj, ["totals", "team_tier_totals"])
    inv = find_key(obj, ["invalid_events", "invalid"])
    prc = find_key(obj, ["processed_records", "processed"])
    got = sum([tot is not None and eq_loose(tot, exp["totals"]),
               inv == exp["invalid_events"],
               prc == exp["processed_records"]])
    if got < 3:
        notes.append("reduction_mismatch")
    return got / 3.0, f_ok, notes


# ------------------------------------------------------------------ J
def check_J(t, ans):
    exp = canon(t["ref"]["expected"])
    obj, f_ok = _parse_json(ans)
    notes = [] if f_ok else ["format:not_pure_json"]
    if obj is None:
        return 0.0, 0, notes + ["unparseable"]
    tot = find_key(obj, ["total", "grand_total"])
    per = find_key(obj, ["per_account", "account_totals", "totals"])
    inact = find_key(obj, ["inactive_row_numbers", "inactive_rows", "inactive"])
    top = find_key(obj, ["top_10_accounts", "top10", "top_10"])
    top_ok = top is not None and eq_loose(top, exp["top_10_accounts"])
    if not top_ok and isinstance(top, list) and top and not isinstance(top[0], dict):
        top_ok = cmp_list(top, [d["account"] for d in exp["top_10_accounts"]])
    got = sum([tot == exp["total"],
               per is not None and eq_loose(per, exp["per_account"]),
               cmp_list(inact, exp["inactive_row_numbers"]),
               top_ok])
    if got < 4:
        notes.append("etl_mismatch")
    return got / 4.0, f_ok, notes


CHECK = {"A": check_A, "B": check_B, "C": check_C, "D": check_D,
         "F": check_F, "G": check_G, "H": check_H, "I": check_I, "J": check_J}
