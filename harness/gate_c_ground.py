# -*- coding: utf-8 -*-
"""Rule-grounded membership for category C (hard bank v6), contour 0.0.2.41.

Category C asks 'which of the lettered options satisfy the stated rule'. From 0.0.2.29 the
coverage contract reads the option letters from the task text and builds the answer line from the
model's OWN per-option verdicts; the corrected stability map shows the remaining seed instability
there is one flipped verdict: `set_mismatch got=['A'] want=['A','D']` (C-ex6-03 — the only
failure of the 2.29+ line in ~40 published C rows) and `got=['A','C']` / `got=['C','F']`
(C-ex6-00/01, judgment tasks whose rule the prompt does NOT state).

0.0.2.41 grounds the membership ONLY where the prompt states a rule the code can evaluate — the
same legitimacy class as the J membership change at 0.0.2.40 (filter/top-K stated in full):
zero model tokens, the reference is never read, the derived letters are always option letters of
this same prompt, and a rule the grammar only half-understands REFUSES and touches nothing.

Two shapes, deliberately narrow:

A. threshold conjunction — a rule clause introduced with «когда» containing ONLY predicates of
   the form `<col> >= N` (lowercase ascii column) or `>= M <unit>` (мин/сек time units); the
   question must ask for the options that SATISFY the condition. An option is in the set iff its
   own text states exactly one value for EVERY predicate and satisfies ALL of them. An option
   silent on a predicate, or double-stating a value or a duration, refuses the whole prompt: a
   partial evaluation would silently add or drop one letter — the exact failure this fights.
B. truth table — «Таблица истинности: когда <formula> истинно?» over single-letter variables,
   AND/OR/NOT/parentheses (precedence NOT > AND > OR); every option must be a full assignment
   `a=1,b=0` or the word никогда/всегда; the set collects the options the formula makes true.

Every other C prompt (policy/battery/JSON-spec judgment tasks, python snippets, reason-bearing
options, uppercase columns like `RAM>=32`) parses nothing and is left byte-identical.
`rule_coverage()` states per bank how many C prompts parse BEFORE any arm runs.
"""
from __future__ import annotations

import re

# ---- shape A: threshold conjunction ----
# lowercase-ascii columns only: `RAM>=32` (C-ex6-07) stays outside the grammar on purpose — its
# options do not restate the column per option, and half-parsing it would guess.
_RULE_PRED = re.compile(r"\b([a-z][a-z0-9_]{1,})\s*(>=|≥|не менее|не меньше|больше или равно)\s*(\d+(?:[.,]\d+)?)")
_RULE_TIME = re.compile(r"(>=|≥|не менее|не меньше|больше или равно)\s*(\d+(?:[.,]\d+)?)\s*(минут\w*|мин|minute[s]?|sec\w*|секунд\w*|сек|hour\w*|час\w*)", re.I)
_RULE_WHEN = re.compile(r"\bкогда\b", re.I)
_RULE_Q = re.compile(r"наруша|подходящ|подходят\b|истинно|верны", re.I)
_OPTS = re.compile(r"(?m)^\s*([A-H])[:\-)]\s*(.*)$")
_INCL = (">=", "≥", "не менее", "не меньше", "больше или равно")

# one minutes(+optional trailing seconds) expression, e.g. «30 минут», «4 минуты 59 секунд»
_TIMEVAL = re.compile(r"\b(\d+)\s*(минут\w*|мин|minute[s]?)\s*(?:(\d+)\s*(?:сек\w*|second[s]?)?)?", re.I)
# one bare seconds expression, e.g. «45 секунд»
_TIMEVAL_SEC = re.compile(r"\b(\d+)\s*(?:сек\w*|second[s]?)\b", re.I)

# ---- shape B: truth table ----
_TT_Q = re.compile(r"[Тт]аблица истинности:\s*когда\s+(.+?)\s+истинно\??", re.S)
_TT_ASSIGN = re.compile(r"^\s*([a-z])\s*=\s*([01])\s*$")
_TT_NEVER = re.compile(r"^\s*(никогда|never)\s*$", re.I)
_TT_ALWAYS = re.compile(r"^\s*(всегда|always)\s*$", re.I)
_TT_TOK = re.compile(r"\s*(&&|\band\b|\|\||\bor\b|\bnot\b|!|~|\(|\)|[a-z])", re.I)


def _num(s):
    return float(s.replace(",", "."))


def _secs(value, unit):
    u = unit.lower()
    if u.startswith("мин") or u.startswith("minute"):
        return value * 60
    if u.startswith("сек") or u.startswith("sec"):
        return value
    return None  # hour units and anything else stay out of the grammar


def _option_secs(text):
    """The one duration this option states, in seconds; None if it states none or two."""
    mv = _TIMEVAL.search(text)
    rest = text
    if mv:
        secs = int(mv.group(1)) * 60 + (int(mv.group(3)) if mv.group(3) else 0)
        rest = text[:mv.start()] + " " + text[mv.end():]
        if _TIMEVAL_SEC.search(rest) or _TIMEVAL.search(rest):
            return None  # a second duration in the same option is ambiguous -> refuse
        return secs
    ms = _TIMEVAL_SEC.search(text)
    if ms:
        rest = text[:ms.start()] + " " + text[ms.end():]
        if _TIMEVAL_SEC.search(rest) or _TIMEVAL.search(rest):
            return None
        return int(ms.group(1))
    return None


def _threshold_set(prompt, opts):
    """Shape A. Return the sorted letter tuple the rule admits, or None to refuse."""
    if not _RULE_WHEN.search(prompt):
        return None
    preds = [(m.group(1), m.group(2), _num(m.group(3))) for m in _RULE_PRED.finditer(prompt)]
    times = [(m.group(1), _num(m.group(2)), m.group(3)) for m in _RULE_TIME.finditer(prompt)]
    if not preds or len(times) != 1:
        return None
    # the question (first line containing '?') must ask for options satisfying the condition
    q = ""
    for ln in prompt.splitlines():
        if "?" in ln:
            q = ln
            break
    if not q or not _RULE_Q.search(q):
        return None
    top, tval, tunit = times[0]
    tsec = _secs(tval, tunit)
    if tsec is None:
        return None
    picked = []
    seen = set()
    for letter, text in opts:
        if letter in seen:
            return None
        seen.add(letter)
        ok = True
        for col, op, val in preds:
            # option-side value may state the column singular or plural: rule-side 'endpoints'
            # must match option-side '1 endpoint' as well as '2 endpoints'
            stem = col[:-1] if col.endswith("s") and len(col) >= 5 else col
            colre = re.compile(r"(\d+(?:[.,]\d+)?)\s+" + re.escape(stem) + r"s?\b", re.I)
            vals = [m.group(1) for m in colre.finditer(text)]
            if len(vals) != 1:
                return None  # silent or double-stated on this column -> whole prompt refuses
            ov = _num(vals[0])
            if op in _INCL and not (ov >= val):
                ok = False
        secs = _option_secs(text)
        if secs is None:
            return None
        if top in _INCL and not (secs >= tsec):
            ok = False
        if ok:
            picked.append(letter)
    return tuple(sorted(picked))


def _tt_eval_factory(formula):
    """Tiny recursive-descent parser (NOT > AND > OR). Returns (fn, variables) or None."""
    toks = []
    i = 0
    while i < len(formula):
        m = _TT_TOK.match(formula, i)
        if not m:
            if formula[i].isspace():
                i += 1
                continue
            return None
        toks.append(m.group(1).lower())
        i = m.end()
    if not toks:
        return None
    variables = {t for t in toks if re.fullmatch(r"[a-z]", t)}
    if not variables or len(variables) > 6:
        return None
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def atom(a):
        t = peek()
        if t is None:
            raise ValueError
        if t in ("not", "!", "~"):
            pos[0] += 1
            return not atom(a)
        if t == "(":
            pos[0] += 1
            v = or_(a)
            if peek() != ")":
                raise ValueError
            pos[0] += 1
            return v
        if re.fullmatch(r"[a-z]", t):
            pos[0] += 1
            return a[t] == 1
        raise ValueError

    def and_(a):
        v = atom(a)
        while peek() in ("and", "&&"):
            pos[0] += 1
            r = atom(a)  # never short-circuit: the right side must be CONSUMED either way
            v = v and r
        return v

    def or_(a):
        v = and_(a)
        while peek() in ("or", "||"):
            pos[0] += 1
            r = and_(a)
            v = v or r
        return v

    def fn(a):
        pos[0] = 0
        v = or_(a)
        if pos[0] != len(toks):
            raise ValueError
        return v

    probe = {v: 0 for v in variables}
    try:
        fn(probe)
    except (ValueError, KeyError):
        return None
    return fn, variables


def _truth_table_set(prompt, opts):
    m = _TT_Q.search(prompt)
    if not m:
        return None
    ev = _tt_eval_factory(m.group(1))
    if not ev:
        return None
    fn, variables = ev
    varlist = sorted(variables)
    n = len(varlist)
    sat = 0
    for mask in range(1 << n):
        if fn({v: (mask >> i) & 1 for i, v in enumerate(varlist)}):
            sat += 1
    letters = []
    for letter, text in opts:
        parts = [p.strip() for p in (text or "").split(",")]
        assign = {}
        full = True
        for p in parts:
            pm = _TT_ASSIGN.match(p)
            if not pm:
                full = False
                break
            if pm.group(1) in assign:
                return None  # same variable twice -> ambiguous, refuse
            assign[pm.group(1)] = int(pm.group(2))
        if full:
            if set(assign) != set(varlist):
                return None  # partial assignment: the row is not fully stated, refuse
            if fn(assign):
                letters.append(letter)
            continue
        if _TT_NEVER.match(text or ""):
            if sat == 0:
                letters.append(letter)
            continue
        if _TT_ALWAYS.match(text or ""):
            if sat == (1 << n):
                letters.append(letter)
            continue
        return None  # an option this shape cannot read -> whole prompt refuses
    return tuple(sorted(letters))


def ground_set_from_prompt(prompt):
    """Return the option-letter set the prompt's OWN stated rule admits, or None to touch nothing.

    Never reads any reference; reads only the task text. Fail-closed: two shapes only, and every
    ambiguity refuses the whole prompt. An empty tuple is a real verdict (nothing satisfies the
    rule); None means 'this grammar says nothing'.
    """
    if not prompt:
        return None
    opts = _OPTS.findall(prompt)
    if len(opts) < 2:
        return None
    tt = _truth_table_set(prompt, opts)
    if tt is not None:
        return tt
    return _threshold_set(prompt, opts)


def rule_coverage(bank):
    """Coverage statement over a bank's C rows, BEFORE any arm: prompt -> derived set or refuse."""
    out = []
    for t in bank:
        if not t["id"].startswith("C"):
            continue
        d = ground_set_from_prompt(t.get("prompt") or "")
        gold = tuple(sorted((t.get("ref") or {}).get("letters") or []))
        out.append((t["id"], d, gold, d is not None and d == gold))
    return out


# ---- shape C: printed Python-literal options (the C-ex6-02 class, contour 0.0.2.53) ----
# «какой вариант печатает [1, 2, 3]?» with option lines «X: <expr>». The grammar EXECUTES the
# task's own printed snippets under CPython semantics — the same epistemics the corrected bank
# gold used (executed truth table: bank v6.2 changelog; the model omits `list(set([1,2,3,3]))`
# by the spec-caveat hedge while the executed snippet prints [1, 2, 3]). A closed allow-listed
# subset only: literals, slices, numeric arithmetic, and pure builtins over them. ANY call
# outside the allow-list, ANY free name (options like `X` or «никогда»), any comprehension,
# attribute, statement or keyword argument, a missing/second/ambiguous target literal, an option
# that raises while evaluating, or non-contiguous option letters refuse the WHOLE prompt — a
# partial evaluation would silently add or drop exactly the letter this class flips on. The
# derived letters are always option letters of THIS prompt; the reference is never read; zero
# model tokens. Kept SEPARATE from ground_set_from_prompt so the frozen 2.41 flag can never
# reach this shape: the 2.41 bytes stay byte-frozen, this grammar fires only under its own flag.
import ast as _c_ast
import builtins as _c_builtins

_PYQ = re.compile(r"печатает\s*(\[[^\[\]]*\])\s*\?")
_PY_SAFE_CALLS = ("sorted", "list", "set", "frozenset", "tuple", "dict", "sum", "max", "min",
                  "abs", "round", "int", "float")


def _py_expr_ok(node):
    """Closed-subset validator: only the node kinds below may appear anywhere in the option."""
    if isinstance(node, (_c_ast.Expression, _c_ast.Constant, _c_ast.List, _c_ast.Tuple,
                         _c_ast.Set, _c_ast.Dict, _c_ast.Slice, _c_ast.Load)):
        return all(_py_expr_ok(c) for c in _c_ast.iter_child_nodes(node))
    if isinstance(node, _c_ast.UnaryOp):
        return (type(node.op).__name__ in ("UAdd", "USub")
                and type(node.operand) is _c_ast.Constant
                and type(node.operand.value) in (int, float))
    if isinstance(node, _c_ast.BinOp):
        return (type(node.op).__name__ in ("Add", "Sub", "Mult", "Div", "FloorDiv")
                and _py_expr_ok(node.left) and _py_expr_ok(node.right))
    if isinstance(node, _c_ast.Subscript):
        return _py_expr_ok(node.value) and _py_expr_ok(node.slice)
    if isinstance(node, _c_ast.Call):
        return (isinstance(node.func, _c_ast.Name) and node.func.id in _PY_SAFE_CALLS
                and not node.keywords and all(_py_expr_ok(a) for a in node.args))
    return False


def ground_py_options(prompt):
    """Return the option-letter set whose printed expression evaluates to the printed target,
    or None to touch nothing. Fail-closed on every uncertainty (see the shape-C header)."""
    if not prompt:
        return None
    q = _PYQ.findall(prompt)
    if len(q) != 1:
        return None
    try:
        target = _c_ast.literal_eval(q[0])
    except (ValueError, SyntaxError):
        return None
    opts = _OPTS.findall(prompt)
    if len(opts) < 2:
        return None
    letters = [o[0] for o in opts]
    if letters != [chr(ord("A") + i) for i in range(len(opts))]:
        return None
    env = {n: getattr(_c_builtins, n) for n in _PY_SAFE_CALLS}
    letters_hit = []
    for letter, expr in opts:
        try:
            tree = _c_ast.parse(expr, mode="eval")
        except (SyntaxError, ValueError):
            return None
        if not _py_expr_ok(tree):
            return None
        try:
            val = eval(compile(tree, "<opt>", "eval"), {"__builtins__": {}}, env)
        except Exception:
            return None
        if type(val) is type(target) and val == target:
            letters_hit.append(letter)
    return tuple(sorted(letters_hit))
