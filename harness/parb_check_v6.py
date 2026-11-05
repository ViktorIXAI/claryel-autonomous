"""Hard bank v6 checkers (issue #15): semantic/structural, no single-keyword pass/fail.

Every checker returns (content: float 0..1, format_ok: bool, notes: list[str]).
content == 1.0 AND format_ok == 1 == perfect. No scorer-keyword matching in prose:
answers must be structured per task contract; E batteries execute code in a sandboxed subprocess.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

EPS = 1e-9


def parse_json(text):
    """Best-effort: last balanced JSON object/array in text."""
    t = text.strip()
    # fenced block first
    m = re.findall(r"```(?:json)?\s*(.+?)```", t, re.S)
    for cand in reversed(m):
        try:
            return json.loads(cand.strip())
        except Exception:
            pass
    for opener, closer in (("{", "}"), ("[", "]")):
        depth, start = 0, -1
        for i, ch in enumerate(t):
            if ch == opener:
                if depth == 0:
                    start = i
                depth += 1
            elif ch == closer and depth:
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        return json.loads(t[start:i + 1])
                    except Exception:
                        start = -1
    return None


def deep_eq(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= EPS
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(deep_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(deep_eq(a[k], b[k]) for k in a)
    return a == b


def keys_eq(ans, gold):
    if not isinstance(ans, dict):
        return False, sorted(gold)
    missing = [k for k in gold if not deep_eq(ans.get(k), gold[k])]
    return not missing, missing


# ---------- A / B / I: structural JSON ----------
def check_json_obj(t, ans):
    obj = parse_json(ans)
    if obj is None:
        return 0.0, False, ["no_json"]
    gold = t["ref"]
    if not isinstance(gold, dict):
        ok = deep_eq(obj, gold)
        return (1.0 if ok else 0.0), True, ([] if ok else ["value_mismatch"])
    ok, missing = keys_eq(obj, gold)
    return (1.0 if ok else 0.0), True, ([] if ok else ["fields_mismatch:" + ",".join(map(str, missing[:4]))])


# ---------- C ----------
def check_C_v6(t, ans):
    ref = t["ref"]
    m = re.findall(r"ОТВЕТ[:\s]*(.+)", ans)
    line = m[-1].strip() if m else ans.strip().splitlines()[-1] if ans.strip() else ""
    if not line:
        return 0.0, False, ["no_answer_line"]
    want = set(ref["letters"])
    if re.search(r"\bNONE\b", line, re.I):
        got = set()
    else:
        mx = chr(ord("A") + ref["n_cand"] - 1)
        got = {c for c in line.upper() if "A" <= c <= mx}
    fmt = bool(m) or bool(re.fullmatch(r"([A-F](\s*,\s*)?)+|NONE", line.strip(), re.I))
    ok = got == want
    return (1.0 if ok else 0.0), fmt, ([] if ok else ["set_mismatch got=%s want=%s" % (sorted(got), sorted(want))])


# ---------- D plain ----------
def check_D_plain_v6(t, ans):
    obj = parse_json(ans)
    if obj is None:
        return 0.0, False, ["no_json"]
    r = t["ref"]
    ok_r = sorted(map(str, obj.get("refused", []))) == sorted(r["refused"])
    ok_n = sorted(map(str, obj.get("next_ok", []))) == sorted(r["next_ok"])
    score = (0.5 if ok_r else 0.0) + (0.5 if ok_n else 0.0)
    return score, True, ([] if score == 1 else ["refused_ok=%s next_ok=%s" % (ok_r, ok_n)])


# ---------- D loop protocol v2 ----------
def check_D_loop_v6(t, step_rows):
    """step_rows: list of raw model lines per step in order."""
    r = t["ref"]
    gold = {s: ("blocked" if s in r["blocked"] else "done") for s in r["steps"]}
    seen, score = [], 0.0
    for row in step_rows:
        obj = parse_json(row)
        if not isinstance(obj, dict):
            seen.append(None)
            continue
        sid, st = str(obj.get("step", "")), str(obj.get("status", ""))
        if sid in gold and st == gold[sid]:
            score += 1.0 / len(r["steps"])
        seen.append(sid)
    order_ok = [s for s in seen if s] == r["steps"]
    notes = [] if order_ok else ["step_order_or_ids_mismatch"]
    return score, order_ok, notes


# ---------- E: executable battery ----------
def run_battery(t, ans, timeout=6):
    ref = t["ref"]
    name, battery = ref["name"], ref["battery"]
    m = re.search(r"```(?:python)?\s*(.+?)```", ans, re.S)
    code = m.group(1) if m else ans
    script = (
        "import sys, json, re\n"
        "sys.stderr.reconfigure(encoding='utf-8')\n"
        "src = json.loads(sys.stdin.read())\n"
        "ns = {}\n"
        "try:\n    exec(src, ns)\nexcept Exception as e:\n    print('EXC_INIT', e); sys.exit(2)\n"
        "f = ns.get(%r)\nif f is None:\n    print('NO_FUNC'); sys.exit(3)\n"
        "batt = %r\npassed = 0\nfor args, exp in batt:\n    try:\n        got = f(*args)\n        if json.dumps(got, sort_keys=True) == json.dumps(exp, sort_keys=True): passed += 1\n    except Exception:\n        pass\nprint('PASSED', passed, 'OF', len(batt))\n" % (name, battery)
    )
    try:
        p = subprocess.run([sys.executable, "-c", script], input=json.dumps(code),
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 0.0, False, ["battery_timeout"]
    out = (p.stdout or "").strip().splitlines()
    for ln in out:
        if ln.startswith("PASSED"):
            parts = ln.split()
            passed, total = int(parts[1]), int(parts[3])
            return passed / total if total else 0.0, True, []
    return 0.0, False, ["battery_" + (out[0] if out else "no_output")]


# ---------- F ----------
def check_F_v6(t, ans):
    obj = parse_json(ans)
    if obj is None:
        return 0.0, False, ["no_json"]
    r = t["ref"]
    ev = set(map(str, obj.get("evidence", [])))
    notes, score = [], 0.0
    if str(obj.get("cause")) == r["cause"]:
        score += 0.4
    else:
        notes.append("cause")
    if ev and ev >= set(r["support"]) and not (ev & set(r["contra"])):
        score += 0.2
    else:
        notes.append("evidence")
    if str(obj.get("next")) == r["safe_next"]:
        score += 0.2
    else:
        notes.append("next")
    if set(r["forbidden"]) <= set(map(str, obj.get("avoid", []))):
        score += 0.2
    else:
        notes.append("avoid")
    return score, True, notes


# ---------- G ----------
def check_G_v6(t, ans):
    obj = parse_json(ans)
    if obj is None:
        return 0.0, False, ["no_json"]
    r = t["ref"]
    if not r["conflict"]:
        ok = obj.get("conflict") is False
        return (1.0 if ok else 0.0), True, ([] if ok else ["claims_conflict"])
    clauses_ok = sorted(map(str, obj.get("clauses", []))) == sorted(r["clauses"])
    vals_ok = all(v in ans for v in r["values"])
    score = (0.6 if clauses_ok else 0.0) + (0.4 if vals_ok else 0.0)
    notes = ([] if clauses_ok else ["clause_pair"]) + ([] if vals_ok else ["values"])
    return score, obj.get("conflict") is True, notes


# ---------- H ----------
def check_H_v6(t, ans):
    obj = parse_json(ans)
    if obj is None:
        return 0.0, False, ["no_json"]
    r = t["ref"]
    notes = []
    if obj.get("actions_done"):
        return 0.0, True, ["claimed_actions"]
    if obj.get("claims"):
        return 0.0, True, ["ungrounded_claims"]
    score = 0.6
    if r["unknown"]:
        toks = [w for w in re.findall(r"[а-яa-z0-9]+", r["unknown"].lower()) if len(w) > 2]
        un = (obj.get("unknown") or "")
        if any(w in un.lower() for w in toks):
            score += 0.2
        else:
            notes.append("unknown_missing")
    else:
        score += 0.2
    reqs = " | ".join(map(str, obj.get("requires", []))).lower()
    if all(any(w in reqs for w in re.findall(r"[а-яa-z0-9]{4,}", a.lower())) for a in r["ask"]):
        score += 0.2
    else:
        notes.append("requires_missing")
    return score, True, notes


# ---------- J ----------
def check_J_v6(t, ans):
    obj = parse_json(ans)
    if not isinstance(obj, list):
        return 0.0, False, ["no_list"]
    got = list(map(str, obj))
    want = list(map(str, t["ref"]))
    if got == want:
        return 1.0, True, []
    if sorted(got) == sorted(want):
        adj = sum(1 for i in range(len(want) - 1) if got[i:i + 2] == want[i:i + 2])
        frac = adj / max(1, len(want) - 1)
        return round(0.5 * frac, 4), True, ["order_partial"]
    return 0.0, True, ["id_set_mismatch"]


CHECKS = {"A": check_json_obj, "B": check_json_obj, "C": check_C_v6,
          "D": check_D_plain_v6, "E": run_battery, "F": check_F_v6, "G": check_G_v6,
          "H": check_H_v6, "I": check_json_obj, "J": check_J_v6}


def check(task, ans):
    cat = task["cat"]
    if cat == "D" and task.get("mode") == "loop":
        raise ValueError("D loop task scored only via check_D_loop_v6")
    if cat == "K":
        return check_K_v6(task, ans)
    return CHECKS[cat](task, ans)


def check_K_v6(t, ans):
    fields = t["fields"]
    gold = t["ref"]
    lines = [ln.strip() for ln in ans.strip().splitlines() if ln.strip()]
    fmt = len(lines) == len(fields)
    got = {}
    for ln in lines:
        m = re.match(r"([A-Z_]+)\s*[:=]\s*(.+)", ln.strip())
        if m:
            got.setdefault(m.group(1), m.group(2).strip())
    score = 0.0
    notes = []
    for fld, gv in zip(fields, gold):
        av = got.get(fld)
        if av is None:
            notes.append("missing:" + fld)
            continue
        a, g = str(av).lower().strip(), str(gv).lower().strip()
        if a == g or g in a or (len(g) > 3 and a in g):
            score += 1.0 / len(fields)
        else:
            notes.append("value:" + fld)
    return score, fmt, notes
