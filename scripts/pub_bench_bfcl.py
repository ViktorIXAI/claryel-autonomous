#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BFCL v4 single-turn AST-match checker (contract `bfcl-ast-v1`).

Pins the question files and their `possible_answer/` golds from the UPSTREAM repository
tree (the standalone `berkeley-nest/berkeley-function-call-leaderboard` repo is gone;
the suite lives in `ShishirPatil/gorilla` under `berkeley-function-call-leaderboard/`,
pinned at commit `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8` - the same checkpoint an
independent external harness (google-deepmind/gbench) byte-pins as current upstream).
Naming correction, stated before any arm ran: the ladder line said "BFCL v3"; the
fetchable, maintained suite carries the `BFCL_v4_*` prefix (the suite renumbered and
added multi-turn / memory / web-search categories that are OUTSIDE this item's
question-only scope). Pinned scope: the five single-turn non-live categories
`simple_python` (400), `multiple` (200), `parallel` (200), `parallel_multiple` (200),
`irrelevance` (240) - 1240 entries, gold calls in the sibling `possible_answer/` files
(irrelevance has no gold file BY DESIGN: the expected behaviour is to emit NO call).

Contract `bfcl-ast-v1` (this file is the contract; a change means a new contract id):
  extraction: strip fenced blocks; parse the remaining text with `ast`; a candidate call
    is any `ast.Call` whose function is a plain or dotted name EQUAL to one of the
    function names provided in the task's own docs (a call to a name that was never
    offered is ignored as prose noise, never matched).
  matching: the model's call multiset must equal the gold call multiset (order-free).
    One model call matches one gold call iff same name AND:
      - every parameter present in the gold call is provided (keyword, or positional
        mapped through the docs' `properties` order) with a value equal to one of the
        gold's allowed values (the `possible_answer` files wrap each parameter value in
        a list of ACCEPTED values; equality is structural with int==float (bool excluded)
        and list==tuple; strings compare exactly), AND
      - a gold parameter whose name is not in the call's own doc properties is SKIPPED:
        it is an upstream gold quirk (2 of 1240 entries), unverifiable by construction,
        AND
      - a gold parameter whose accepted-value list contains the empty string is OPTIONAL
        and may be omitted (this `""` marker is the upstream convention, 624 parameters
        over 444 entries), AND
      - a parameter the gold provides but the model omits is tolerated ONLY when the
        parameter carries a schema `default` and the gold's accepted values contain it, AND
      - every parameter the model provides beyond the gold's is tolerated ONLY when it is
        not in `required` and its value equals the schema `default`.
  irrelevance: gold is the empty call list - a correct answer contains no call to a
    provided function; prose (with or without an abstain sentence) is correct.

The file refuses to score anything until its self-test passes. Usage:
  pub_bench_bfcl.py selftest
  pub_bench_bfcl.py <tasks.jsonl> <answers.jsonl> [--verdicts OUT.jsonl]
                                        [--limit N] [--offset N] [--call-note TEXT]
`--limit/--offset` select the pre-registered cross-arm slice from the SAME pinned task file, so
the digest row keeps the full-file tasks sha16 (a sliced task file would silently mint a second
bench id; `pub_bench_score.py` uses the same convention). Selection only - it cannot move a
verdict. `--call-note` names the slice in the row's call column, because a head slice of this
file is category-pure and that has to be visible next to the percent.
"""
import ast
import hashlib
import json
import os
import re
import sys

BFCL_CHECKER = "bfcl-ast-v1"
GORILLA_SHA = "6ea57973c7a6097fd7c5915698c54c17c5b1b6c8"
CATEGORIES = ["simple_python", "multiple", "parallel", "parallel_multiple", "irrelevance"]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pub_bench_score import call_label, digest_row, write_digest  # noqa: E402  (one digest format)

PROMPT_TMPL = (
    "You will be given one or more function definitions in JSON. Based on the user "
    "request, output one function call per required action in Python syntax, using "
    "ONLY these functions, e.g. name(arg=value). Put each call on its own line. Do "
    "not output code fences, comments or explanations alongside the calls. If the "
    "request cannot be fulfilled with the given functions, reply in plain prose that "
    "no given function can be used, and output no call.\n\n"
    "### Functions:\n%s\n\n### User request:\n%s"
)


def build_prompt(functions, request):
    return PROMPT_TMPL % (json.dumps(functions, ensure_ascii=False), request)


def strip_code(ans):
    blocks = re.findall(r"```(?:python)?\n(.*?)```", ans or "", re.S)
    return ("\n\n".join(blocks) if blocks else (ans or "")).strip()


def _val_eq(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_val_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, set) and isinstance(b, set):
        return a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_val_eq(a[k], b[k]) for k in a)
    return a == b


def lit(node):
    """ast literal -> python value; non-literals are incomparable (never equal)."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        out = [lit(e) for e in node.elts]
        if any(o is _INCOMPARABLE for o in out):
            return _INCOMPARABLE
        return tuple(out)
    if isinstance(node, ast.Set):
        out = {lit(e) for e in node.elts}
        return _INCOMPARABLE if _INCOMPARABLE in out else frozenset(out)
    if isinstance(node, ast.Dict):
        out = {}
        for k, v in zip(node.keys, node.values):
            kk, vv = lit(k), lit(v)
            if kk is _INCOMPARABLE or vv is _INCOMPARABLE:
                return _INCOMPARABLE
            if not isinstance(kk, (str, int, float, tuple)):
                return _INCOMPARABLE
            out[kk] = vv
        return out
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        v = lit(node.operand)
        if v is _INCOMPARABLE or not isinstance(v, (int, float)) or isinstance(v, bool):
            return _INCOMPARABLE
        return -v if isinstance(node.op, ast.USub) else v
    return _INCOMPARABLE


class _Incomparable:
    pass


_INCOMPARABLE = _Incomparable()


def _call_name(node):
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    parts = []
    while isinstance(f, ast.Attribute):
        parts.append(f.attr)
        f = f.value
    if isinstance(f, ast.Name):
        parts.append(f.id)
        return ".".join(reversed(parts))
    return None


def _span_end(text, paren_i):
    """Index just past the ')' matching text[paren_i]=='('; None if unbalanced."""
    depth, i, n = 0, paren_i, len(text)
    quote = None
    while i < n:
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
        continue
    return None


def _scan_line_calls(line):
    """Parse each balanced `name(...)` span in a prose line as an eval expression."""
    trees, consumed_upto = [], 0
    for m in re.finditer(r"[A-Za-z_][\w.]*[ \t]*\(", line):
        if m.start() < consumed_upto:
            continue
        pi = line.index("(", m.start())
        end = _span_end(line, pi)
        if end is None:
            continue
        seg = line[m.start():end]
        try:
            trees.append(ast.parse(seg, mode="eval"))
            consumed_upto = end
        except SyntaxError:
            # nested inner span may still be valid: do not consume, the regex finds it
            continue
    return trees


def extract_calls(ans, provided_names):
    """Candidate calls = ast.Call nodes whose name was offered by the task docs.
    Parse order: whole text, then per line, then per balanced call span in a line."""
    text = strip_code(ans)
    trees = []
    try:
        trees.append(ast.parse(text))
    except SyntaxError:
        for line in text.splitlines():
            line = line.strip().rstrip(",;")
            if not line:
                continue
            try:
                trees.append(ast.parse(line))
            except SyntaxError:
                trees.extend(_scan_line_calls(line))
    calls = []
    for t in trees:
        for node in ast.walk(t):
            if isinstance(node, ast.Call):
                name = _call_name(node)
                if name in provided_names:
                    args = [(lit(a), None) for a in node.args]
                    kwargs = [(kw.arg, lit(kw.value)) for kw in node.keywords]
                    calls.append((name, args, kwargs))
    return calls


def _map_args(name, args, kwargs, doc_props):
    """Positionals mapped through the docs' properties order; keywords by name."""
    named = {}
    for i, (v, _) in enumerate(args):
        if i >= len(doc_props):
            return None
        named[doc_props[i]] = v
    for k, v in kwargs:
        if k is None or k in named or k not in doc_props:
            return None
        named[k] = v
    return named


def _match_call(gold_name, gold_args, model, funcs):
    """model = (name, args, kwargs) vs one gold call dict {param: [accepted values]}."""
    name, args, kwargs = model
    if name != gold_name:
        return False
    doc = funcs.get(name) or {}
    props = list((doc.get("parameters") or {}).get("properties") or {})
    required = set((doc.get("parameters") or {}).get("required") or [])
    defaults = {k: p.get("default", _INCOMPARABLE)
                for k, p in ((doc.get("parameters") or {}).get("properties") or {}).items()}
    named = _map_args(name, args, kwargs, props)
    if named is None:
        return False
    for p, accepted in gold_args.items():
        if p not in props:
            continue  # upstream gold quirk: not in this call's docs, unverifiable
        if p in named:
            if not any(_val_eq(named[p], a) for a in accepted):
                return False
        else:
            if any(isinstance(a, str) and a == "" for a in accepted):
                continue  # upstream "" marker: this parameter is optional
            d = defaults.get(p, _INCOMPARABLE)
            if d is _INCOMPARABLE or not any(_val_eq(d, a) for a in accepted):
                return False
    for p, v in named.items():
        if p in gold_args:
            continue
        if p in required:
            return False
        d = defaults.get(p, _INCOMPARABLE)
        if d is _INCOMPARABLE or not _val_eq(v, d):
            return False
    return True


def score_entry(task, answer):
    """-> (ok: bool, why: str). task carries `functions` (docs) and `gold`."""
    funcs = {f["name"]: f for f in task["functions"]}
    gold = task["gold"]
    if isinstance(gold, dict):
        gold = [gold]
    models = extract_calls(answer, set(funcs))
    if len(models) != len(gold):
        return False, "calls=%d gold=%d" % (len(models), len(gold))
    used = [False] * len(models)
    for gc in gold:
        (gname, gargs), = gc.items()
        hit = -1
        for i, m in enumerate(models):
            if not used[i] and _match_call(gname, gargs, m, funcs):
                hit = i
                break
        if hit < 0:
            return False, "unmatched gold call %s" % gname
        used[hit] = True
    return True, ""


def selftest():
    T = []

    def task(name_extra=None, **kw):
        d = json.loads(json.dumps({  # synthetic doc mirroring the real shape
            "name": "calculate_triangle_area",
            "description": "area",
            "parameters": {"type": "dict",
                           "properties": {"base": {"type": "integer"},
                                          "height": {"type": "integer"},
                                          "unit": {"type": "string", "default": "units"}},
                           "required": ["base", "height"]}}))
        f = [d]
        if name_extra:
            f.append(json.loads(json.dumps({
                "name": "triangle_properties.get",
                "description": "props",
                "parameters": {"type": "dict",
                               "properties": {"a": {"type": "integer"}, "b": {"type": "integer"},
                                              "unit": {"type": "string", "default": "units"}},
                               "required": ["a", "b"]}})))
        t = {"id": "t", "functions": f, "gold": kw.get("gold", [{"calculate_triangle_area":
             {"base": [10], "height": [5], "unit": ["units", ""]}}])}
        return t
    t = task()
    checks = [
        ("exact simple", t, "calculate_triangle_area(base=10, height=5, unit=\"units\")", True),
        ("optional omitted (gold contains default)", t,
         "calculate_triangle_area(base=10, height=5)", True),
        ("num equality", t, "calculate_triangle_area(base=10, height=5.0, unit='units')", True),
        ("wrong value", t, "calculate_triangle_area(base=11, height=5)", False),
        ("wrong unit not in accepted", t, "calculate_triangle_area(base=10, height=5, unit='m')", False),
        ("accepted alternative", t, "calculate_triangle_area(base=10, height=5, unit='')", True),
        ("extra required-shaped param", t, "calculate_triangle_area(base=10, height=5, unit='units', z=1)", False),
        ("positionals via doc order", t, "calculate_triangle_area(10, 5)", True),
        ("prose call to un-offered name ignored", t,
         "I would use helper(1,2); calculate_triangle_area(base=10, height=5)", True),
        ("un-offered call ONLY", t, "helper(1,2)", False),
        ("dotted name match", task(name_extra=True),
         "triangle_properties.get(a=1, b=2)", False),  # gold still triangle area -> no match
        ("fenced block", t, "```python\ncalculate_triangle_area(base=10, height=5)\n```", True),
    ]
    ot = json.loads(json.dumps(task()))
    ot["functions"][0]["parameters"]["properties"]["unit"].pop("default", None)
    ot["gold"] = [{"calculate_triangle_area":
                   {"base": [10], "height": [5], "unit": ["feet", ""]}}]
    checks += [
        ('optional "" marker: omission ok', ot, "calculate_triangle_area(base=10, height=5)", True),
        ('optional "" marker: wrong provided value fails', ot,
         "calculate_triangle_area(base=10, height=5, unit='m')", False),
        ('optional "" marker: accepted value ok', ot,
         "calculate_triangle_area(base=10, height=5, unit='feet')", True),
    ]
    gd = json.loads(json.dumps(task()))
    gd["gold"] = [{"calculate_triangle_area":
                   {"base": [10], "height": [5], "unit": ["units"], "zz": [1]}}]
    checks += [
        ("gold param not in docs is skipped", gd,
         'calculate_triangle_area(base=10, height=5, unit="units")', True),
    ]
    pt = {"id": "p", "functions": [
        {"name": "math_toolkit.sum_of_multiples",
         "parameters": {"properties": {"lower_limit": {}, "upper_limit": {}, "multiples": {}},
                        "required": ["lower_limit", "upper_limit", "multiples"]}},
        {"name": "math_toolkit.product_of_primes",
         "parameters": {"properties": {"count": {}}, "required": ["count"]}}],
        "gold": [{"math_toolkit.sum_of_multiples": {"lower_limit": [1], "upper_limit": [1000],
                                                    "multiples": [[3, 5]]}},
                 {"math_toolkit.product_of_primes": {"count": [5]}}]}
    checks += [
        ("two calls, order-free", pt,
         "math_toolkit.product_of_primes(count=5)\nmath_toolkit.sum_of_multiples(1, 1000, [3, 5])", True),
        ("nested list equality vs tuple", pt,
         "math_toolkit.sum_of_multiples(lower_limit=1, upper_limit=1000, multiples=(3, 5))\n"
         "math_toolkit.product_of_primes(count=5)", True),
        ("missing one of two", pt, "math_toolkit.product_of_primes(count=5)", False),
        ("one extra", pt, "math_toolkit.product_of_primes(count=5)\n"
         "math_toolkit.sum_of_multiples(1, 1000, [3, 5])\nmath_toolkit.product_of_primes(count=5)", False),
    ]
    it = {"id": "i", "functions": [{"name": "determine_body_mass_index",
                                    "parameters": {"properties": {"h": {}}, "required": ["h"]}}],
          "gold": []}
    checks += [
        ("irrelevance abstain prose", it, "No given function can be used for this request.", True),
        ("irrelevance calls anyway", it, "determine_body_mass_index(h=1.8)", False),
    ]
    ok = 0
    for label, tt, ans, want in checks:
        got, why = score_entry(tt, ans)
        ok += (got == want)
        if got != want:
            print("SELFTEST FAIL %s: got %s want %s (%s)" % (label, got, want, why))
    print("SELFTEST %d/%d" % (ok, len(checks)))
    return ok == len(checks)


PINNED_FILES = {  # sha16 of the fetched upstream files at GORILLA_SHA (fail closed on drift)
    "BFCL_v4_simple_python.json": "82dd63ba502eb252",
    "BFCL_v4_multiple.json": "aef168155ebd74b7",
    "BFCL_v4_parallel.json": "19f51a82eff42e5d",
    "BFCL_v4_parallel_multiple.json": "8863ea8433239f55",
    "BFCL_v4_irrelevance.json": "2b6ed4c2e992cdcf",
    "pa-BFCL_v4_simple_python.json": "90cd5bc653690ee8",
    "pa-BFCL_v4_multiple.json": "244e00ce9395df94",
    "pa-BFCL_v4_parallel.json": "8a6aa19c1adddc6a",
    "pa-BFCL_v4_parallel_multiple.json": "5ebf24f458c1f163",
}


def build(fetch_dir, out_path):
    """Build the pinned tasks.jsonl from a fetched directory; refuse on any pin drift."""
    for name, want in PINNED_FILES.items():
        p = os.path.join(fetch_dir, name)
        got = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
        if got != want:
            print("PIN DRIFT %s: got %s want %s" % (name, got, want))
            sys.exit(1)
    n_out = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for cat in CATEGORIES:
            golds = {}
            pa = os.path.join(fetch_dir, "pa-BFCL_v4_%s.json" % cat)
            if os.path.exists(pa):
                for l in open(pa, encoding="utf-8"):
                    if l.strip():
                        e = json.loads(l)
                        golds[e["id"]] = e["ground_truth"]
            n = 0
            for l in open(os.path.join(fetch_dir, "BFCL_v4_%s.json" % cat), encoding="utf-8"):
                if not l.strip():
                    continue
                e = json.loads(l)
                assert len(e["question"]) == 1 and len(e["question"][0]) == 1, e["id"]
                msg = e["question"][0][0]
                assert msg["role"] == "user" and msg["content"].strip(), e["id"]
                row = {"id": e["id"], "bench": "bfcl", "category": cat,
                       "prompt": build_prompt(e["function"], msg["content"]),
                       "functions": e["function"],
                       "gold": golds.get(e["id"], [])}
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                n += 1
            print("built %s: %d rows" % (cat, n))
            n_out += n
    print("wrote %s (%d rows, checker contract %s, source commit %s)"
          % (out_path, n_out, BFCL_CHECKER, GORILLA_SHA))


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "selftest":
        sys.exit(0 if selftest() else 1)
    if len(sys.argv) >= 2 and sys.argv[1] == "build":
        if len(sys.argv) != 4:
            print("usage: pub_bench_bfcl.py build <fetch-dir> <out.tasks.jsonl>")
            sys.exit(2)
        build(sys.argv[2], sys.argv[3])
        sys.exit(0)
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    if not selftest():
        print("refusing to score: checker self-test failed")
        sys.exit(1)
    tasks = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
    limit, offset = None, 0
    for i, a in enumerate(sys.argv):
        if a == "--limit":
            limit = int(sys.argv[i + 1])
        elif a == "--offset":
            offset = int(sys.argv[i + 1])
    if offset or limit is not None:
        tasks = tasks[offset:(offset + limit) if limit is not None else None]
        print("slice: offset %d, limit %s -> %d tasks of the pinned file"
              % (offset, limit, len(tasks)))
    ans = {}
    for l in open(sys.argv[2], encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        ans.setdefault(r["id"], r)
    verdicts, miss, cat = [], 0, {}
    for t in tasks:
        a = ans.get(t["id"])
        if a is None or not (a.get("answer") or "").strip():
            miss += 1
            continue
        ok, why = score_entry(t, a["answer"])
        verdicts.append({"id": t["id"], "ok": ok, "why": why})
        c = t.get("category", "?")
        cat[c] = (cat.get(c) or [0, 0])
        cat[c][1] += 1
        cat[c][0] += 1 if ok else 0
    n, ok = len(verdicts), sum(1 for v in verdicts if v["ok"])
    if not n or miss > 0.05 * len(tasks):
        print("refusing: %d scored, %d missing of %d (>5%% missing or empty arm)"
              % (n, miss, len(tasks)))
        sys.exit(1)
    for c in sorted(cat):
        w, m = cat[c]
        print("%-18s %3d/%3d = %5.1f%%" % (c, w, m, 100.0 * w / m))
    print("bfcl %d/%d = %.1f%% (AST-match, checker %s)" % (ok, n, 100.0 * ok / n, BFCL_CHECKER))
    out = sys.argv[sys.argv.index("--verdicts") + 1] if "--verdicts" in sys.argv else None
    if out:
        with open(out, "w", encoding="utf-8") as f:
            for v in verdicts:
                f.write(json.dumps(v, ensure_ascii=False) + "\n")
    sha = hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest()[:16]
    model = next((a.get("model") for a in ans.values() if a.get("model")), "unknown")
    temp = next((a.get("temp") for a in ans.values() if a.get("temp") is not None), None)
    note = sys.argv[sys.argv.index("--call-note") + 1] if "--call-note" in sys.argv else ""
    note = ("; " + note) if note else ""
    row = digest_row("bfcl", model, len(tasks), sha,
                     "%s%s; checker %s" % (call_label(list(ans.values()), temp), note, BFCL_CHECKER),
                     ok, n)
    print("-> %s" % os.path.basename(write_digest(row)))


if __name__ == "__main__":
    main()
