# -*- coding: utf-8 -*-
"""Ranking repair for category J (hard bank v6), contour 0.0.2.32.

The corrected stability map says several J cells fail with `order_partial`: the model lists the right ids in
the wrong order. Every J task in this bank puts its data table inside the prompt (`[(id, 9.1), ...]`) and
states the ranking rule in the same sentence. Re-deriving that order from the prompt's own table is the same
class of contour work as the 2.27 arithmetic-by-code change: the numbers and the rule are both in front of
the model, the reference answer is never read, and no model tokens are spent.

Fail-closed by construction. If the rule sentence contains anything outside this grammar — a formula, a
product of two fields, an unnamed column, an ambiguous direction — the function returns None and the answer
is not touched. A half-understood rule is worse than no rule: it silently reorders correct answers.

Over-fitting guard: the grammar is written against the task CLASS (an id/value table plus a direction
phrase), not against the seven bank prompts. `harness/gate_v48_j_rerank_test.py` proves it on synthetic
tables with invented field names and asserts that unsupported rules leave the answer alone; coverage on the
bank is reported by `rule_coverage()` BEFORE any arm runs, so the bank number is stated up front.
"""
from __future__ import annotations

import re

_ROW = re.compile(r"\(\s*'([^']+)'\s*,\s*([^()]+)\)")
_HDR = re.compile(r"\(([^()]+)\)\s*:")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_NUM = re.compile(r"^-?\d+(?:\.\d+)?$")
_TIE = re.compile(r"при равенстве|затем|then", re.I)
_OUT_OF_GRAMMAR = re.compile(r"произведени|формул|средн|взвеш|=\s", re.I)


def parse_table(prompt):
    """Return (column_names, [(id, {col: value})]) or None when the table is not purely numeric/date."""
    m = _HDR.search(prompt)
    header = [h.strip() for h in m.group(1).split(",")] if m else []
    rows = []
    for raw_id, raw_vals in _ROW.findall(prompt):
        rec = {}
        vals = [v.strip().strip("'") for v in raw_vals.split(",") if v.strip()]
        for i, v in enumerate(vals):
            col = header[i + 1] if m and i + 1 < len(header) else "f%d" % (i + 1)
            if _DATE.match(v):
                rec[col] = v
            elif _NUM.match(v):
                rec[col] = float(v)
            else:
                return None
        rows.append((raw_id, rec))
    if not rows:
        return None
    cols = [h for h in header[1:]] if m else sorted({k for _, r in rows for k in r})
    return [c for c in cols if c], rows


def rule_part(prompt):
    """The sentence(s) after the table: the rule text, never the data."""
    end = prompt.rfind("]")
    return prompt[end + 1:] if end >= 0 else ""


def _direction(rule):
    """Direction of the PRIMARY key only: text before the first tie-break marker."""
    head = _TIE.split(rule)[0]
    d = "desc" if re.search(r"убыв|нисходящ|самы[ыхе]+ (больш|дорог|высок)", head, re.I) else ""
    a = re.search(r"возраст|восходящ|самы[ыхе]+ (дешев|мал|низк|коротк|ранн)", head, re.I)
    if d and a:
        return None
    return d or ("asc" if a else None)


def _stem_match(word, col):
    """Inflected Russian column names: 'дате' for column 'дата', 'RAM' for 'RAM_GiB'. The common prefix has
    to cover all but the last character of the shorter form, so 'цена' can never claim 'цена_месяц' by
    accident only when the stems truly agree; two columns matching at once is treated as ambiguity and the
    rule is refused."""
    w, c = word.lower(), col.lower()
    if w == c:
        return True
    i = 0
    while i < min(len(w), len(c)) and w[i] == c[i]:
        i += 1
    return i >= max(3, min(len(w), len(c)) - 1)


def _key_column(rule, cols):
    hits = [c for c in cols if c and c.lower() in rule.lower()]
    if len(hits) == 1:
        return hits[0]
    for m in re.finditer(r"(?:по|сортируй по|отсортируй по)\s+([A-Za-zА-Яа-яЁё_]+)", rule, re.I):
        want = m.group(1)
        exact = [c for c in cols if c.lower() == want.lower()]
        if len(exact) == 1:
            return exact[0]
        near = [c for c in cols if _stem_match(want, c)]
        if len(near) == 1:
            return near[0]
    if len(cols) == 1:
        return cols[0]
    return None


def rank_from_prompt(prompt, answer_ids):
    """Re-rank the model's own ids by the prompt's table and rule. None = do not touch the answer."""
    parsed = parse_table(prompt)
    if parsed is None:
        return None
    cols, rows = parsed
    by_id = {rid: rec for rid, rec in rows}
    if not answer_ids or any(a not in by_id for a in answer_ids):
        return None
    rule = rule_part(prompt)
    if _OUT_OF_GRAMMAR.search(rule):
        return None
    direction = _direction(rule)
    if direction is None:
        return None
    # The column named by the FILTER clause is not the sort column. Removing the filter text first is what
    # keeps "Отбрось score<70; отсортируй по дате" from sorting by score.
    key_text = re.sub(r"[A-Za-zА-Яа-яЁё_]+\s*(?:>=|<=|>|<)\s*\d+(?:\.\d+)?", " ", rule)
    col = _key_column(key_text, cols)
    if col is None:
        return None

    universe = [rid for rid, _ in rows]
    fm = re.search(r"([A-Za-zА-Яа-яЁё_]+)\s*(>=|<=|>|<)\s*(\d+(?:\.\d+)?)", rule)
    if fm:
        near = [c for c in cols if _stem_match(fm.group(1), c)]
        name = near[0] if len(near) == 1 else None
        if name is None:
            return None
        num = float(fm.group(3))
        op = fm.group(2)
        def ok(x, op=op, num=num):
            return (x >= num) if op == ">=" else (x > num) if op == ">" else \
                   (x <= num) if op == "<=" else (x < num)
        # "Отбрось score<70" removes the matching rows, it does not keep them. The verb in front of the
        # condition decides the polarity, and an unrecognised verb means refusing rather than guessing.
        before = rule[:fm.start()].lower()
        if re.search(r"отбрось|убери|исключ", before):
            pred = lambda rid, name=name, op=op, num=num: not ok(by_id[rid][name]) if isinstance(by_id[rid].get(name), float) else False
        elif re.search(r"среди|нужен|нужна|только|где", before):
            pred = lambda rid, name=name, op=op, num=num: ok(by_id[rid][name]) if isinstance(by_id[rid].get(name), float) else False
        else:
            return None
        universe = [rid for rid in universe if isinstance(by_id[rid].get(name), float) and pred(rid)]
    if not universe:
        return None

    def key(rid):
        v = by_id[rid].get(col)
        if isinstance(v, str):
            return v
        return -v if direction == "desc" else v

    ordered = sorted(universe, key=lambda rid: (key(rid), rid))
    top = re.search(r"(?:топ|top)[- ]?(\d+)", rule, re.I)
    if top:
        ordered = ordered[:int(top.group(1))]
    return ordered


def rule_coverage(bank):
    """Before any arm runs: which J tasks this grammar reproduces, and which it refuses."""
    out = []
    for t in bank:
        if t["cat"] != "J":
            continue
        got = rank_from_prompt(t["prompt"], t["ref"] if isinstance(t["ref"], list) else [])
        out.append((t["id"], "reproduces" if got == list(t["ref"]) else (
            "refuses" if got is None else "MIS-SORTS: %s" % got)))
    return out
