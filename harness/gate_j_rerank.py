# -*- coding: utf-8 -*-
"""Ranking repair for category J (hard bank v6), contour 0.0.2.32 (v1 grammar) / 0.0.2.39 (v2 grammar).

v1 (2.32) stays byte-identical: called with v2=False it parses exactly what it parsed at stamp 0.0.2.32.
The v2 grammar (2.39) closes the four coverage gaps that made v1 refuse 4 of 7 bank J prompts — each gap
found on PUBLISHED pair bytes, not invented (PAIR-238-V61.md): the ё spelling of cheap-words (`дешёвых`),
genitive column forms and the `при равенстве <col>` lead that names the primary key (J-ex6-01, J-ex6-04),
a unique prefix column match (`срок` for `срок_дней`, J-ex6-01), and an explicit product key over two
prompt-table columns (`по произведению severity*probability`, J-ex6-02) with a fully-stated tie chain.
Every v2 extension keeps the same contract: an unresolved name, an ambiguous column, a formula or a
tie clause it cannot parse returns None and touches nothing.

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
# v2 (0.0.2.39): the product of two prompt-table columns is a supported primary key, so the word
# "произведение" no longer refuses on its own — but a bare formula (`Балл = ...`), averages or weights
# still refuse, and a product whose column names or tie chain cannot be parsed refuses too.
_OUT_OF_GRAMMAR_V2 = re.compile(r"формул|средн|взвеш|=\s", re.I)
_PROD = re.compile(r"произведени[юиее]*\s+([A-Za-zА-Яа-яЁё_]+)\s*[*xх×]\s*([A-Za-zА-Яа-яЁё_]+)", re.I)
_TIE_LEAD = re.compile(r"при\s+равенстве\s+([A-Za-zА-Яа-яЁё_]+)", re.I)


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


def _direction(rule, v2=False):
    """Direction of the PRIMARY key only: text before the first tie-break marker."""
    head = _TIE.split(rule)[0]
    d = "desc" if re.search(r"убыв|нисходящ|самы[ыхе]+ (больш|дорог|высок)", head, re.I) else ""
    asc_words = r"возраст|восходящ|самы[ыхе]+ (дешев|дешёв|мал|низк|коротк|ранн)" if v2 \
        else r"возраст|восходящ|самы[ыхе]+ (дешев|мал|низк|коротк|ранн)"
    a = re.search(asc_words, head, re.I)
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


def _match_col(word, cols, v2):
    """Resolve one rule word to exactly one table column: exact, stem, then (v2) unique prefix.
    Anything ambiguous or unresolved returns None; the CALLER decides whether that refuses the rule."""
    exact = [c for c in cols if c and c.lower() == word.lower()]
    if len(exact) == 1:
        return exact[0]
    near = [c for c in cols if c and _stem_match(word, c)]
    if len(near) == 1:
        return near[0]
    if v2 and not exact and not near:
        pfx = [c for c in cols if c and c.lower().startswith(word.lower())]
        if len(pfx) == 1:
            return pfx[0]
    return None


def _key_column(rule, cols, v2=False):
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
    if v2:
        # v2a: a bare inflected column mention in the PRIMARY clause (before any tie marker),
        # e.g. "по возрастанию цены" naming column `цена_мес`. Only the primary clause is scanned so a
        # tie-break column can never be mistaken for the primary key.
        head = _TIE.split(rule)[0]
        hits2 = []
        for w in re.findall(r"[A-Za-zА-Яа-яЁё_]{2,}", head):
            m = _match_col(w, cols, True)
            if m and m not in hits2:
                hits2.append(m)
        if len(hits2) == 1:
            return hits2[0]
        # v2b: the tie lead names the primary key — "при равенстве ЦЕНЫ" only makes sense when the
        # primary sort is by that column (J-ex6-01 never says the word for price anywhere else).
        lead = _TIE_LEAD.search(rule)
        if lead:
            m = _match_col(lead.group(1), cols, True)
            if m:
                return m
    if len(cols) == 1:
        return cols[0]
    return None


def _tie_chain(rule, cols, direction_primary):
    """v2 (0.0.2.39): parse the FULL tie-break chain the prompt states: 'при равенстве — по severity
    (убыв.), затем id'. Every tie segment must resolve to a column+direction, an id clause, or the
    chain is refused — a half-parsed chain would silently reorder correct answers. Returns None on any
    unparseable segment, [] when the rule states no tie marker (the v1 default id-asc tie stays)."""
    parts = _TIE.split(rule)
    if len(parts) == 1:
        return []
    chain = []
    for seg in parts[1:]:
        clause = re.split(r"[—–:]", seg, 1)[-1] if re.search(r"[—–:]", seg) else seg
        low = clause.lower()
        if re.search(r"\bid\b|алфавит", low):
            chain.append(("id", "asc"))
            continue
        d = "desc" if re.search(r"убыв|больш", low) else (
            "asc" if re.search(r"возраст|меньш|ранн|коротк", low) else None)
        if d is None:
            return None
        col = None
        for w in re.findall(r"[A-Za-zА-Яа-яЁё_]{2,}", clause):
            m = _match_col(w, cols, True)
            if m:
                if col is not None and m != col:
                    return None
                col = m
        if col is None:
            return None
        if col == direction_primary:
            col = "id"
        chain.append((col, d))
    return chain


def rank_from_prompt(prompt, answer_ids, v2=False, membership=False):
    """Re-rank the model's own ids by the prompt's table and rule. None = do not touch the answer.
    v2=False is the frozen 0.0.2.32 grammar; v2=True adds the 0.0.2.39 coverage extensions, every one
    of them fail-closed. membership=True (0.0.2.40, pair-240) is the SAME parse run for a membership
    replacement instead of a pure permutation: an empty model list is then allowed (the drawn answer
    collapsed to `[]`), and a top-K truncation whose boundary is a genuine tie that the stated chain
    cannot separate refuses — choosing WHICH row wins a tie the rule never resolved would be the
    contour inventing membership, exactly what the contract forbids. Callers at stamps below 2.40 keep
    membership=False and the byte-identical old behaviour."""
    parsed = parse_table(prompt)
    if parsed is None:
        return None
    cols, rows = parsed
    by_id = {rid: rec for rid, rec in rows}
    if (not answer_ids and not membership) or any(a not in by_id for a in answer_ids):
        return None
    rule = rule_part(prompt)
    if (_OUT_OF_GRAMMAR_V2 if v2 else _OUT_OF_GRAMMAR).search(rule):
        return None
    direction = _direction(rule, v2=v2)
    if direction is None:
        return None
    # The column named by the FILTER clause is not the sort column. Removing the filter text first is what
    # keeps "Отбрось score<70; отсортируй по дате" from sorting by score.
    key_text = re.sub(r"[A-Za-zА-Яа-яЁё_]+\s*(?:>=|<=|>|<)\s*\d+(?:\.\d+)?", " ", rule)
    prod = _PROD.search(rule) if v2 else None
    primary = None
    if prod:
        a = _match_col(prod.group(1), cols, True)
        b = _match_col(prod.group(2), cols, True)
        if a is None or b is None:
            return None
        if any(not isinstance(r[1].get(c), float) for r in rows for c in (a, b)):
            return None
        primary = ("prod", a, b, direction)
        key_col = None
    else:
        key_col = _key_column(key_text, cols, v2=v2)
        if key_col is None:
            return None
        primary = ("col", key_col, direction)
    if v2:
        chain = _tie_chain(rule, cols, key_col)
        if chain is None:
            return None
    else:
        chain = []

    universe = [rid for rid, _ in rows]
    fm = re.search(r"([A-Za-zА-Яа-яЁё_]+)\s*(>=|<=|>|<)\s*(\d+(?:\.\d+)?)", rule)
    if fm:
        near = [c for c in cols if _stem_match(fm.group(1), c)]
        name = near[0] if len(near) == 1 else None
        if name is None and v2:
            pfx = [c for c in cols if c and c.lower().startswith(fm.group(1).lower())]
            name = pfx[0] if len(pfx) == 1 else None
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
        v = by_id[rid].get(key_col)
        if isinstance(v, str):
            return v
        return -v if direction == "desc" else v

    if not v2:
        ordered = sorted(universe, key=lambda rid: (key(rid), rid))
    else:
        def sortk(rid):
            out = []
            spec = primary
            if spec[0] == "prod":
                va, vb = by_id[rid][spec[1]], by_id[rid][spec[2]]
                out.append(-(va * vb) if spec[3] == "desc" else va * vb)
            else:
                v = by_id[rid].get(spec[1])
                out.append(v if isinstance(v, str) else (-v if spec[2] == "desc" else v))
            for col, d in chain:
                if col == "id":
                    out.append(rid)
                else:
                    v = by_id[rid].get(col)
                    out.append(v if isinstance(v, str) else (-v if d == "desc" else v))
            out.append(rid)
            return tuple(out)
        ordered = sorted(universe, key=sortk)
    top = re.search(r"(?:топ|top)[- ]?(\d+)", rule, re.I)
    # 0.0.2.40 membership mode: a SET replacement is only ever rule-declared. When the stated rule has
    # neither a filter segment nor a top-K segment, nothing in the prompt selects which rows belong in
    # the answer, so a membership CHANGE (or deriving an answer from an empty draw) would be the contour
    # inventing membership — refuse and touch nothing. A pure permutation of the model's own set stays
    # allowed: that is the adopted 2.39 repair and must not be lost at 2.40.
    if membership and fm is None and top is None and (
            not answer_ids or set(ordered) != set(answer_ids)):
        return None
    if top:
        k = int(top.group(1))
        if membership and v2 and len(ordered) > k:
            # 0.0.2.40: a membership replacement must not be decided by the contour's own invented
            # id tie-break. Compare the RULE-STATED sort value at the truncation boundary (the
            # always-appended final rid is excluded; a chain segment on `id` still separates).
            def rule_key(rid):
                return sortk(rid)[:-1]
            if rule_key(ordered[k - 1]) == rule_key(ordered[k]):
                return None
        ordered = ordered[:int(top.group(1))]
    return ordered


def rule_coverage(bank, v2=False, membership=False):
    """Before any arm runs: which J tasks this grammar reproduces, and which it refuses.

    membership=True (0.0.2.40) states the SET-derivation coverage on single-shot tasks: the derived id
    set must equal the gold set exactly (order judged by the v2 re-rank separately); a derivation that
    misses the set is a MIS-DERIVATION and the contract test requires zero of them.
    """
    out = []
    for t in bank:
        if t["cat"] != "J":
            continue
        if membership and t.get("mode") == "loop":
            continue
        got = rank_from_prompt(t["prompt"], t["ref"] if isinstance(t["ref"], list) else [],
                               v2=v2 or membership, membership=membership)
        if membership:
            ref = set(t["ref"]) if isinstance(t["ref"], list) else set()
            out.append((t["id"], "derives" if got is not None and set(got) == ref else (
                "refuses" if got is None else "MIS-DERIVES: %s" % got)))
        else:
            out.append((t["id"], "reproduces" if got == list(t["ref"]) else (
                "refuses" if got is None else "MIS-SORTS: %s" % got)))
    return out
