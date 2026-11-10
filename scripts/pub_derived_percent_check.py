#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Machine-check the quotable percents that carry no `PUB-DIGEST.md` row.

The digest table is the one table this line re-scores from shipped bytes (tick 9
closed that audit). The result documents quote a second class of numbers that no
digest row carries: pre-registered slice scores, per-category and per-difficulty
breakdowns, truncation censuses, and paired-join conversion rates. Those are just
as quotable and were only ever true by hand-maintenance.

This tool reads `benchmarks/public/DERIVED-PERCENTS.json` and, for every declared
entry, (1) recomputes the number OFFLINE from tracked artifacts with the pinned
checker, (2) requires the recomputed fraction+percent to equal the declared one,
and (3) requires the declared fraction to still appear in the named document.

It then runs the opposite direction: every `N/M = P %` citation in a result
document must be covered by a digest row, a registry entry, or an explicit
`not_recomputable_in_ci` record with a stated reason. A new unexplained percent
in a document is a finding, which is the point: the class cannot rot back into
prose-only maintenance.

Kinds and the fields each reads:
  subset      tasks, answers, offset, limit, checker_contract
              -> score the slice of the pinned task file against the arm's answers
  category    tasks, verdicts, field, value, optional filter{field:value}
              -> count passing verdict rows of that task group
  field_count rows, field, value
              -> count rows whose field equals value, over the rows in the file
  join        mode = symmetric_flip | flip_gain | keep_best_union
               base, base_key, other, other_key, optional restrict_ids
              -> paired-join conversion counts over shipped verdict sidecars

Nothing here writes a digest row, touches an arm byte, or calls a model. Exit 0
clean, 1 findings, 2 structural failure (missing artifact, unknown kind, checker
contract id drift). `SAH_PUB_DIR` overrides the public-benchmark directory for
the tamper controls in `harness/pub_derived_percent_test.py`.
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import NoReturn

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PUB = os.environ.get("SAH_PUB_DIR") or os.path.join(ROOT, "benchmarks", "public")
REGISTRY = "DERIVED-PERCENTS.json"

FRAC = re.compile(r"(\d{1,5})/(\d{1,5})(\s*=\s*\*{0,2})(\d{1,3}(?:\.\d)?)\s*%")
LOOSE = re.compile(r"\(\s*\d{1,5}/\d{1,5}\s+(?:loose|strict)\s*\)")
EXPECT = re.compile(r"^\s*(\d{1,5})/(\d{1,5})\s*=\s*(\d{1,3}(?:\.\d)?)\s*%\s*$")


def die(msg: str) -> NoReturn:
    sys.stderr.write("STRUCTURAL: %s\n" % msg)
    raise SystemExit(2)


def jl(path: str):
    if not os.path.exists(path):
        die("missing tracked artifact: %s" % path)
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def answers_of(path: str):
    ans = {}
    for r in jl(path):
        if "id" not in r:
            die("%s has a row without an id" % path)
        ans.setdefault(r["id"], r)
    return ans


def verdict_map(path: str, key: str):
    out = {}
    for r in jl(path):
        if key not in r:
            die("%s has no %r column (verdict row keys: %s)" % (path, key, sorted(r)))
        out[r["id"]] = bool(r[key])
    return out


# ---------------------------------------------------------------- kinds ----

def k_subset(e):
    cc = e.get("checker_contract")
    tasks = jl(os.path.join(PUB, e["tasks"]))
    off = int(e.get("offset", 0))
    lim = e.get("limit")
    sl = tasks[off:off + int(lim)] if lim else tasks[off:]
    ans = answers_of(os.path.join(PUB, e["answers"]))
    score = None
    if cc == "pub-checkers-v2":
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import pub_bench_score as S
        if S.CHECKER_CONTRACT != cc:
            die("pinned answer checker id moved: registry says %s, code says %s"
                % (cc, S.CHECKER_CONTRACT))
        if S.selftest() != 0:
            die("answer checker self-test failed - refusing to score")
        score = lambda t, a: S.check(t["checker"], t["gold"], a)
    elif cc == "bfcl-ast-v1":
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import pub_bench_bfcl as B
        if B.BFCL_CHECKER != cc:
            die("pinned AST checker id moved: registry says %s, code says %s"
                % (cc, B.BFCL_CHECKER))
        if not B.selftest():
            die("bfcl checker self-test failed - refusing to score")
        score = lambda t, a: B.score_entry(t, a)[0]
    else:
        die("unknown checker_contract %r in %s" % (cc, e.get("id")))
    if score is None:  # unreachable while die() raises; keeps the call site typed
        die("no scorer bound for checker_contract %r in %s" % (cc, e.get("id")))
    ok = miss = unscored = 0
    for t in sl:
        a = ans.get(t["id"])
        if a is None or not (a.get("answer") or "").strip():
            miss += 1
            continue
        r = score(t, a["answer"])
        if r is None:
            unscored += 1
        else:
            ok += 1 if r else 0
    if unscored:
        die("%s: %d tasks UNSCORED under %s - a derived percent over a partial "
            "denominator is refused" % (e["id"], unscored, cc))
    den = len(sl) - miss
    if miss > 0.05 * len(sl):
        die("%s: arm partial (%d/%d answers) - no percent" % (e["id"], den, len(sl)))
    return ok, den


def k_category(e):
    tasks = {t["id"]: t for t in jl(os.path.join(PUB, e["tasks"]))}
    flt = e.get("filter") or {}
    ok = den = 0
    for v in jl(os.path.join(PUB, e["verdicts"])):
        t = tasks.get(v["id"])
        if t is None:
            die("%s: verdict id %s is not in %s" % (e["id"], v["id"], e["tasks"]))
        if any(t.get(k) != val for k, val in flt.items()):
            continue
        if t.get(e["field"]) != e["value"]:
            continue
        den += 1
        ok += 1 if bool(v.get("ok", v.get("strict"))) else 0
    if not den:
        die("%s: no tasks match field=%s value=%s filter=%s"
            % (e["id"], e["field"], e["value"], flt))
    return ok, den


def k_field_count(e):
    rows = jl(os.path.join(PUB, e["rows"]))
    f = e["field"]
    hit = [r for r in rows if str(r.get(f)) == str(e["value"])]
    return len(hit), len(rows)


def k_join(e):
    mode = e.get("mode")
    base = verdict_map(os.path.join(PUB, e["base"]), e["base_key"])
    other = verdict_map(os.path.join(PUB, e["other"]), e["other_key"])
    restrict = None
    if e.get("restrict_ids"):
        restrict = {r["id"] for r in jl(os.path.join(PUB, e["restrict_ids"]))}
    if mode == "symmetric_flip":
        common = set(base) & set(other)
        if not common:
            die("%s: no common ids between the two verdict files" % e["id"])
        return sum(1 for i in common if base[i] != other[i]), len(common)
    if mode == "flip_gain":
        fails = {i for i in base if not base[i]}
        target = (fails & restrict) if restrict is not None else fails
        if not target:
            die("%s: empty target set" % e["id"])
        return sum(1 for i in target if other.get(i)), len(target)
    if mode == "keep_best_union":
        return sum(1 for i in base if base[i] or other.get(i)), len(base)
    die("unknown join mode %r in %s" % (mode, e.get("id")))


KINDS = {"subset": k_subset, "category": k_category,
         "field_count": k_field_count, "join": k_join}


# ------------------------------------------------------------- citations ---

def digest_citations():
    """Every fraction+percent the digest table prints (strict cell AND call cell)."""
    out = set()
    path = os.path.join(PUB, "PUB-DIGEST.md")
    for line in open(path, encoding="utf-8"):
        if not line.startswith("| ") or " = " not in line or "%" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6 or cells[0] == "bench":
            continue
        for col in (cells[5], cells[4]):
            for m in FRAC.finditer(LOOSE.sub("", col)):
                out.add((int(m.group(1)), int(m.group(2)), float(m.group(4))))
    return out


def doc_citations():
    out = []
    for name in sorted(os.listdir(PUB)):
        if not name.endswith("-RESULT.md"):
            continue
        text = open(os.path.join(PUB, name), encoding="utf-8").read()
        for i, line in enumerate(text.splitlines(), 1):
            for m in FRAC.finditer(LOOSE.sub("", line)):
                out.append((name, i, int(m.group(1)), int(m.group(2)), float(m.group(4))))
    return out


def main():
    reg = json.load(open(os.path.join(PUB, REGISTRY), encoding="utf-8"))
    entries = reg.get("entries") or []
    allow = reg.get("not_recomputable_in_ci") or []
    if not entries:
        die("%s declares no entries" % REGISTRY)

    print("registry: %s  entries=%d  excluded=%d"
          % (reg.get("contract", "?"), len(entries), len(allow)))
    findings = []
    seen_ids = set()
    for e in entries:
        for k in ("id", "doc", "kind", "expect"):
            if k not in e:
                die("registry entry without %r: %s" % (k, e))
        if e["id"] in seen_ids:
            die("duplicate registry id %s" % e["id"])
        seen_ids.add(e["id"])
        m = EXPECT.match(e["expect"])
        if not m:
            die("entry %s expect is not `N/M = P %%`: %r" % (e["id"], e["expect"]))
        en, ed, ep = int(m.group(1)), int(m.group(2)), float(m.group(3))
        kind = KINDS.get(e["kind"])
        if kind is None:
            die("entry %s has unknown kind %r" % (e["id"], e["kind"]))
        n, d = kind(e)
        pct = 100.0 * n / d if d else 0.0
        status = "ok"
        if (n, d) != (en, ed):
            status = "COUNT MISMATCH recomputed %d/%d" % (n, d)
            findings.append("%s: declared %s, recomputed %d/%d = %.1f %%"
                            % (e["id"], e["expect"], n, d, pct))
        elif abs(pct - ep) > 0.05:
            status = "PERCENT MISMATCH recomputed %.1f %%" % pct
            findings.append("%s: declared %s, recomputed %d/%d = %.1f %%"
                            % (e["id"], e["expect"], n, d, pct))
        doc = os.path.join(PUB, e["doc"])
        if not os.path.exists(doc):
            die("registry entry %s names a missing document %s" % (e["id"], e["doc"]))
        frac = "%d/%d" % (en, ed)
        if frac not in open(doc, encoding="utf-8").read():
            status = "QUOTE GONE from " + e["doc"]
            findings.append("%s: %s no longer appears in %s" % (e["id"], frac, e["doc"]))
        print("  %-34s %-11s %-18s %s" % (e["id"], e["kind"], "%d/%d = %.1f %%" % (n, d, pct), status))

    dset = digest_citations()
    allowset = {}
    for a in allow:
        if "fraction" not in a or "reason" not in a:
            die("not_recomputable_in_ci record needs fraction+reason: %s" % a)
        allowset[a["fraction"]] = a["reason"]
    regset = set()
    for e in entries:
        m = EXPECT.match(e["expect"])
        if m:
            regset.add((int(m.group(1)), int(m.group(2))))
    uncov = []
    for name, ln, n, d, p in doc_citations():
        if any(a == n and b == d and abs(c - p) < 0.05 for (a, b, c) in dset):
            continue
        if (n, d) in regset:
            continue
        if "%d/%d" % (n, d) in allowset:
            continue
        uncov.append("%s L%d: %d/%d = %.1f %% is quoted but neither a digest row, "
                     "a registry entry, nor an exclusion with a reason"
                     % (name, ln, n, d, p))
    findings += uncov

    print("\ndigest citations=%d  doc citations=%d  uncovered=%d"
          % (len(dset), len(doc_citations()), len(uncov)))
    if findings:
        print("FINDINGS %d" % len(findings))
        for f in findings:
            print("  - " + f)
        return 1
    print("DERIVED PERCENTS: %d recomputed from shipped bytes, 0 findings" % len(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
