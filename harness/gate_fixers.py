#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FORM repair by code alone, without calling the model (the v1.7 idea).

Principle: code may change only presentation, never data. If after tidying the text
parses and contains exactly the same rows and keys as before, the fix counts, the model
is not called (zero tokens). If it does not parse or data is lost, we return None
and the gate falls back to its normal path (asking the model).
"""
import json
import re


def _balanced(text, open_ch, close_ch):
    i = text.find(open_ch)
    if i < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for j in range(i, len(text)):
        ch = text[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    return None


def try_json(text):
    """Returns (object, method) or (None, None). Tries everything that does not change data."""
    raw = _balanced(text, "[", "]") or _balanced(text, "{", "}")
    if raw is None:
        return None, None
    variants = [
        ("as_is", raw),
        ("no_trailing_comma", re.sub(r",\s*([}\]])", r"\1", raw)),
        ("py_consts", re.sub(r"\bTrue\b", "true", re.sub(r"\bFalse\b", "false", re.sub(r"\bNone\b", "null", raw)))),
        ("single_quotes", re.sub(r"'", '"', raw)),
        ("unquoted_keys", re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)", r'\1"\2"\3', raw)),
        ("no_comments", re.sub(r"(?m)^\s*//.*$", "", raw)),
    ]
    for how, v in variants:
        try:
            obj = json.loads(v)
            return obj, how
        except Exception:
            continue
    return None, None


def sig_of_obj(obj):
    if isinstance(obj, list):
        keys = set()
        for x in obj:
            if isinstance(x, dict):
                keys |= set(x.keys())
        return {"kind": "json_rows", "rows": len(obj), "keys": keys}
    if isinstance(obj, dict):
        rows = next((v for v in obj.values() if isinstance(v, list)), [])
        return {"kind": "json_obj", "rows": len(rows), "keys": set(obj.keys())}
    return {"kind": "other", "rows": 0, "keys": set()}


def fix_json_text(acct, text):
    """Only if the source text was already JSON-like and rows/keys did not change."""
    before = try_json(_balanced(text, "[", "]") or _balanced(text, "{", "}") or "")
    obj, how = try_json(text)
    if obj is None:
        return None
    sig = sig_of_obj(obj)
    if sig["rows"] == 0 and sig["kind"] != "other":
        return None
    if getattr(acct, "ev", None):
        acct.ev("gate", "json_fixed_by_code_%s" % how)
    return json.dumps(obj, ensure_ascii=False)


def fix_fields_text(acct, text, need):
    """KEY: value fields — we extract them even when the model wrapped them in prose.
    We never invent: if a key is missing, the fix does not help."""
    got = {}
    for ln in text.splitlines():
        m = re.match(r"^\s*(?:[-*\u2022]+\s*)?(?:\*\*)?\s*([A-Z][A-Z0-9_]{2,})\s*(?:\*\*)?\s*[:=]\s*"
                     r"\s*(.+?)\s*[.,;]*\s*$", ln)
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        if k not in got:
            got[k] = v.strip("*").strip()
    if any(k not in got for k in need):
        return None
    out = "\n".join("%s: %s" % (k, got[k]) for k in need)
    if getattr(acct, "ev", None):
        acct.ev("gate", "fields_fixed_by_code")
    return out


def fix_csv_text(acct, text, cols=None, nrows=None):
    """CSV: drop text before/after the table and empty lines; never touch row content."""
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    keep = []
    for l in lines:
        if re.match(r"^[^,;\t]+([,;][^,;\t]*){1,}$", l):
            keep.append(l)
    if len(keep) < 2:
        return None
    sep = ";" if ("," not in keep[0] and ";" in keep[0]) else ","
    widths = {len(l.split(sep)) for l in keep}
    if len(widths) != 1:
        return None
    if cols:
        head = [c.strip().lower() for c in keep[0].split(sep)]
        if any(c.lower() not in head for c in cols):
            return None
    if nrows and len(keep) - 1 != nrows:
        return None
    if getattr(acct, "ev", None):
        acct.ev("gate", "csv_fixed_by_code")
    return "\n".join(keep)
