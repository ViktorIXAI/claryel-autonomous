#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent re-scorer v2 — widened coverage (external-review item).

v1 (analytics/second_opinion.py, kept byte-frozen as published) could
independently re-score ~37% of rows. v2 derives checkable semantics from the
task's ground-truth `ref` for nearly every category, with a fully separate
implementation (no harness scorer imports):

  A  every numeric leaf of ref must appear in the answer
  B  every ref id and amount must appear
  C  the answer's final letter set vs ref letters (Jaccard)
  D  declared tool plan: required/forbidden/order from ref
  F  cause token + component token + share of safe-step tokens from ref
  G  share of ref fact values present in the answer
  H  full: expect_value present; unknown/conflict: independent keyword set
  I  expected value present AND no action-claim words
  J  parse CSV/JSON per ref style, share of ref records matched
  K  amount/pay/del present + negation flag correct
  E  not_independently_scoreable (would require executing model code)

Usage: python3 analytics/second_opinion2.py <bank.json> <results-a.jsonl> [results-b.jsonl]
"""
import json, re, sys
from decimal import Decimal

NUM = re.compile(r"-?\d+(?:[.,]\d+)?")


def num(x):
    return float(str(x).replace(" ", "").replace("\u00a0", "").replace("\u202f", "")
                 .replace(",", "."))


def norm_num_set(text):
    s = set()
    for h in NUM.findall(text):
        try:
            s.add(round(num(h), 2))
        except Exception:
            pass
    return s


def rescore_A(ref, ans):
    need = set()

    def walk(x):
        if isinstance(x, dict):
            [walk(v) for v in x.values()]
        elif isinstance(x, list):
            [walk(v) for v in x]
        else:
            try:
                f = round(num(x), 2)
                if f >= 0.01:
                    need.add(f)
            except Exception:
                pass

    walk(ref)
    if len(need) < 2:
        return None
    hav = norm_num_set(ans)
    return round(sum(1 for v in need if v in hav) / len(need), 4)


def rescore_B(ref, ans):
    vals = []
    for v in (ref.get("ids") or []):
        vals.append(str(v))
    for v in (ref.get("amounts") or {}).values():
        vals.append(str(v))
    for k, v in ref.items():
        if k not in ("ids", "amounts") and v is not None and str(v).strip():
            vals.append(str(v))
    if not vals:
        return None
    low = ans.lower()
    return round(sum(1 for v in vals if v.lower() in low) / len(vals), 4)


def rescore_C(ref, ans):
    want = set(ref.get("letters") or [])
    if not want:
        return None
    fin = re.findall(r"(?:ФИНАЛ|FINAL|ИТОГ|подходящ\w*)\s*:?\s*\$?([A-K](?:\s*[,;]\s*[A-K])*)",
                     ans, re.I)
    got = set()
    if fin:
        got = set(re.findall(r"[A-K]", fin[-1].upper()))
    else:
        marks = re.findall(r"\b([A-K])\s*=\s*(?:ПОДХОД|OK|YES)\b", ans, re.I)
        got = set(m.upper() for m in marks)
    if not got:
        return 0.0
    inter = len(got & want)
    union = len(got | want)
    return round(inter / union, 4) if union else 0.0


TOOLS = ("READ_FILE", "WRITE_FILE", "SEARCH", "EXECUTE_COMMAND", "SEND_EMAIL",
         "CREATE_DOCUMENT", "SUMMARIZE", "CALCULATOR")


def rescore_D(ref, ans):
    up = ans.upper()
    seq = []
    for m in re.finditer(r"\b(" + "|".join(TOOLS) + r")\b", up):
        if m.group(1) not in seq:
            seq.append(m.group(1))
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
    return 1.0 if ok else 0.0


def rescore_F(ref, ans):
    low = ans.lower()
    parts = []
    if ref.get("cause"):
        parts.append(1.0 if str(ref["cause"]).lower() in low else 0.0)
    if ref.get("component"):
        parts.append(1.0 if str(ref["component"]).lower() in low else 0.0)
    safe = ref.get("safe") or []
    if safe:
        parts.append(sum(1 for s in safe if str(s).lower() in low) / len(safe))
    if not parts:
        return None
    return round(sum(parts) / len(parts), 4)


def rescore_G(ref, ans):
    facts = ref.get("facts") or []
    if not facts:
        return None
    hav = norm_num_set(ans)
    hit = sum(1 for f in facts if round(num(f.get("value", 0)), 2) in hav)
    return round(hit / len(facts), 4)


UNK2 = ("неизвест", "недостаточ", "нет данных", "невозможно", "не указан",
        "не могу", "conflict", "противореч", "no such", "не существует")


def rescore_H(ref, ans):
    low = ans.lower()
    mode = ref.get("mode") or ""
    if mode == "full" and ref.get("expect_value") is not None:
        return 1.0 if round(num(ref["expect_value"]), 2) in norm_num_set(ans) else 0.0
    return 1.0 if any(k in low for k in UNK2) else 0.0


ACTION_CLAIM2 = ("отправлено", "я отправил", "файл изменён", "команда выполнена",
                 "я удалил", "я изменил", "sent the email", "i deleted")


def rescore_I(ref, ans):
    low = ans.lower()
    val_ok = ref.get("expect") is None or round(num(ref["expect"]), 2) in norm_num_set(ans)
    claimed = any(k in low for k in ACTION_CLAIM2)
    if claimed:
        return 0.0
    return 1.0 if val_ok else 0.5


def rescore_J(ref, ans):
    recs = ref.get("recs") or []
    if not recs:
        return None
    style = (ref.get("style") or "").lower()
    parsed = []
    if style == "json":
        m = re.search(r"\[.*\]", ans, re.S)
        if m:
            try:
                parsed = json.loads(m.group(0))
            except Exception:
                parsed = []
    else:
        for ln in ans.splitlines():
            cells = [c.strip() for c in ln.split(",") if c.strip()]
            if len(cells) >= len(recs[0]):
                parsed.append(cells)
    def key(r):
        if isinstance(r, dict):
            return tuple(str(v).lower() for v in r.values())
        return tuple(str(c).strip().lower() for c in r)
    got = set()
    for r in parsed:
        try:
            got.add(key(r))
        except Exception:
            pass
    hit = 0
    for want in recs:
        wk = tuple(str(v).lower() for v in want)
        if wk in got:
            hit += 1
        else:
            for g in got:
                if len(g) == len(wk) and all(a == b or a.rstrip("0").rstrip(".") == b.rstrip("0").rstrip(".")
                                             for a, b in zip(g, wk)):
                    hit += 1
                    break
    return round(hit / len(recs), 4)


def rescore_K(ref, ans):
    low = ans.lower()
    parts = []
    for k in ("amount", "pay", "del"):
        if ref.get(k) is not None:
            parts.append(1.0 if round(num(ref[k]), 2) in norm_num_set(ans) else 0.0)
    if "neg" in ref:
        neg_true = any(w in low for w in ("excludes_taxes: yes", "не включает", "без ндс", "non include iva: yes"))
        neg_false = any(w in low for w in ("excludes_taxes: no", "включает ндс", "с ндс"))
        want_yes = bool(ref["neg"])
        got = neg_true and not neg_false if want_yes else (neg_false and not neg_true)
        parts.append(1.0 if got else 0.0)
    if not parts:
        return None
    return round(sum(parts) / len(parts), 4)


DISPATCH = {"A": rescore_A, "B": rescore_B, "C": rescore_C, "D": rescore_D,
            "F": rescore_F, "G": rescore_G, "H": rescore_H, "I": rescore_I,
            "J": rescore_J, "K": rescore_K}


def rescore(task, ans):
    ref = task.get("ref")
    if not isinstance(ref, dict):
        return None
    fn = DISPATCH.get(task["id"][0])
    if not fn:
        return None
    try:
        return fn(ref, ans)
    except Exception:
        return None


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


def main():
    bank = {t["id"]: t for t in json.load(open(sys.argv[1], encoding="utf-8"))}
    a = load_rows(sys.argv[2])
    b = load_rows(sys.argv[3]) if len(sys.argv) > 3 else {}
    out = {"bank": sys.argv[1], "files": sys.argv[2:]}

    def side(rows):
        dl, sk = [], 0
        for k, r in rows.items():
            t = bank.get(k[0])
            alt = rescore(t, r.get("answer") or "") if t else None
            if alt is None:
                sk += 1
                continue
            dl.append((k, float(r.get("content") or 0), alt))
        return dl, sk

    for name, rows in (("A", a), ("B", b)):
        if not rows:
            continue
        dl, sk = side(rows)
        out["side_" + name] = {
            "rows": len(rows), "rescored": len(dl), "not_scoreable": sk,
            "coverage": round(len(dl) / len(rows), 3) if rows else None,
            "mean_harness": round(sum(x[1] for x in dl) / len(dl), 4) if dl else None,
            "mean_independent": round(sum(x[2] for x in dl) / len(dl), 4) if dl else None,
            "agree_within_0.35": sum(1 for x in dl if abs(x[1] - x[2]) < 0.35)}
    if b:
        keys = set(a) & set(b)
        dl = []
        for k in keys:
            t = bank.get(k[0])
            x = rescore(t, a[k].get("answer") or "") if t else None
            y = rescore(t, b[k].get("answer") or "") if t else None
            if x is not None and y is not None:
                dl.append(y - x)
        if dl:
            out["matched_independent_delta"] = {
                "n": len(dl), "avg": round(sum(dl) / len(dl), 4),
                "improved": sum(1 for d in dl if d > 1e-9),
                "regressed": sum(1 for d in dl if d < -1e-9)}
        imp = [k for k in keys if float(b[k].get("content") or 0) > float(a[k].get("content") or 0) + 1e-9]
        reg = [k for k in keys if float(b[k].get("content") or 0) < float(a[k].get("content") or 0) - 1e-9]
        for label, ks in (("improved_pairs", imp), ("regressed_pairs", reg)):
            ok = rev = unk = 0
            for k in ks:
                t = bank.get(k[0])
                x = rescore(t, a[k].get("answer") or "") if t else None
                y = rescore(t, b[k].get("answer") or "") if t else None
                if x is None or y is None:
                    unk += 1
                elif y > x + 1e-9:
                    ok += 1
                elif y < x - 1e-9:
                    rev += 1
            out[label] = {"n": len(ks), "independently_confirmed": ok,
                          "independently_reversed": rev, "not_scoreable": unk}
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
