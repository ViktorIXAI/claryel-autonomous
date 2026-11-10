#!/usr/bin/env python3
"""Publication-completeness gate for the percent rows of `PUB-DIGEST.md` itself.

Why this exists (2026-11-10 line audit). The standing rules of this line say a
percent row must name **bench, model, tasks, tasks pin, call parameters and checker
contract**, must not be a duplicate of another row under the same identity, and must
never publish a percent over an unscored denominator. Ticks 7-13 built checks for the
artifacts, the pins, the citations, the Grok cells and the superseded cells; nothing
checked the digest table as a table. Measured on the tracked bytes with this script's
own rules: 46 rows, 0 arithmetic findings, 0 task-pin findings — and **23 of 46 rows
name no checker contract at all** (they lean on the table head's single global
"contract in force" sentence), which is the same failure class as a stale cell one
column over: the per-row cell is what gets quoted.

A second defect was live in the writer rather than in a published byte:
`scripts/pub_bench_score.py`'s own digest call (the classic-set scorer) re-hashed the
task file with SHA-256/16 and never named the contract. Routing that cell through
`manifest_tasks_cell` (tick 10's guard) was applied to the IFEval scorer only, so the
generic scorer would still have minted `e09a5cab3782ed5b` for IFEval beside the
published `2c672531577dcc33` rows — two identities for one pinned file, which is
exactly what that guard exists to prevent. The same call site would also have written
`0/0 = **0.0%**` for an arm with no scored task (an execution-checked set scored
through the generic scorer), a fabricated zero.

Rules pinned here (no published row is edited; the fix rides on the writer):

  1. table shape: exactly one header row and one delimiter row, 6 cells per row;
  2. bench is a pinned set in `MANIFEST.json` with a non-zero task count, and the row's
     tasks count is a pre-registered prefix (0 < tasks <= pinned count);
  3. the tasks cell reproduces `MANIFEST.json`'s labelled pin for that bench through
     `pub_bench_score.manifest_tasks_cell` — never a locally re-hashed value;
  4. the strict cell parses `N/M = **P%**` with N <= M, M equal to the tasks column,
     and P equal to 100*N/M within the one-decimal rounding (0.06 pp);
  5. every row names at least one known checker contract in its call cell, unless it is
     one of the 23 pre-rule rows recorded in `LEGACY_NO_CONTRACT` by exact identity. A
     legacy entry that no longer matches a row is itself a finding (the exception list
     cannot rot), and a new contract-less row is a finding;
  6. no two rows share the identity (bench, model, tasks, contract set, request shape).
     Two rows for one bench+model+tasks are legitimate only when the request shape or
     the contract differs — the escalation-shape and matched-shape contour pairs are the
     published example, and the superseded-cell checker owns their labelling;
  7. every contract id in force per `MANIFEST.json` / the scorer modules is in this
     script's vocabulary, so the vocabulary cannot silently go stale when a corrected
     contract ships.

Exit: 0 clean, 3 findings, 2 fail closed on a missing artifact.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "benchmarks", "public")
DIGEST = os.path.join(PUB, "PUB-DIGEST.md")
MANIFEST = os.path.join(PUB, "MANIFEST.json")

FRAC = re.compile(r"(\d+)/(\d+)\s*=\s*\*\*([\d.]+)%\*\*")
PIN = re.compile(r"[0-9a-f]{16}")

# Contract ids this line has scored with. Rule 7 fails if one of the in-force ids in
# MANIFEST / the scorer modules is missing from this set, so a corrected contract that
# ships without a vocabulary update reddens the gate instead of slipping past it.
KNOWN_CONTRACTS = {
    "pub-checkers-v2",   # answer matchers: number / letter / exact
    "pytest-v1", "pytest-v2",
    "pub-ifeval-v1", "pub-ifeval-v2",
    "lcb-exec-v1", "lcb-exec-v2", "lcb-public-v1",
    "bfcl-ast-v1",
}

# The 23 rows published before the per-row contract rule (2026-11-10 audit). Identity is
# bench|model|tasks|N/M, i.e. the row itself, so an entry cannot cover a different row.
# Every one of them was scored by the contract the table head declares in force
# (`pub-checkers-v2`); the rule now bites on NEW rows, and their published bytes stay.
LEGACY_NO_CONTRACT = {
    "arc-challenge|gpt-6.1-sol|300|290/300",
    "arc-challenge|grok-4.7|300|288/300",
    "arc-challenge|qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56|300|283/300",
    "arc-challenge|qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56|300|291/300",
    "arc-challenge|qwen3.8-flash-next-iq3_s-basalt|1172|1129/1172",
    "arc-easy|gpt-6.1-sol|300|290/300",
    "arc-easy|grok-4.7|300|289/300",
    "arc-easy|qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56|300|289/300",
    "arc-easy|qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56|300|290/300",
    "arc-easy|qwen3.8-flash-next-iq3_s-basalt|2376|2261/2376",
    "gsm8k|gpt-6.1-sol|300|293/300",
    "gsm8k|grok-4.7|300|288/300",
    "gsm8k|qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56|300|290/300",
    "gsm8k|qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56|300|294/300",
    "gsm8k|qwen3.8-flash-next-iq3_s-basalt|1319|1284/1319",
    "gsm8k|qwen3.8-flash-next-iq3_s-basalt|25|24/25",
    "gpqa-diamond|gpt-6.1-sol|198|192/198",
    "gpqa-diamond|qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56|198|139/198",
    "gpqa-diamond|qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56|198|91/198",
    "gpqa-diamond|qwen3.8-flash-next-iq3_s-basalt|198|127/198",
    "mmlu-pro|gpt-6.1-sol|500|462/500",
    "mmlu-pro|qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56|500|429/500",
    "mmlu-pro|qwen3.8-flash-next-iq3_s-basalt|500|432/500",
}

# Request-shape classes used only to decide whether two same-identity rows are actually
# different measurements (rule 6). Tokens come from the digest's own vocabulary.
SHAPE_TOKENS = (
    "ladder rungs 512,1200, enable_thinking off",   # escalation shape (superseded parity)
    "first rung 1200", "first rung 2400",           # matched shape
    "sampling params not exposed", "CLI",           # cloud CLI transport
    "keep-best", "retry-only",                     # repair adoption rule
    "temp 0.7", "max_tokens 1200", "max_tokens 2400",
    "retry max_tokens 1200", "retry max_tokens 2400",
)


def load_scorer():
    spec = importlib.util.spec_from_file_location(
        "pbs", os.path.join(ROOT, "scripts", "pub_bench_score.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def shape_of(call: str) -> str:
    return "|".join(t for t in SHAPE_TOKENS if t in call)


def main() -> int:
    for p in (DIGEST, MANIFEST):
        if not os.path.exists(p):
            sys.stderr.write("MISSING ARTIFACT: %s\n" % p)
            return 2
    pbs = load_scorer()
    man = json.load(open(MANIFEST, encoding="utf-8"))
    benches = man.get("benches") or {}

    # rule 7: the vocabulary must cover every contract in force today
    in_force = set()
    for b, ent in benches.items():
        if isinstance(ent, dict) and isinstance(ent.get("checker"), str):
            in_force.add(ent["checker"])
    in_force.add(pbs.CHECKER_CONTRACT)
    exec_mod_path = os.path.join(ROOT, "scripts", "pub_bench_exec.py")
    if os.path.exists(exec_mod_path):
        espec = importlib.util.spec_from_file_location("pbe", exec_mod_path)
        emod = importlib.util.module_from_spec(espec)
        espec.loader.exec_module(emod)
        for name in dir(emod):
            if name.endswith("CHECKER") and isinstance(getattr(emod, name), str):
                in_force.add(getattr(emod, name))
    findings = []
    for cid in sorted(in_force - KNOWN_CONTRACTS):
        findings.append("contract %r is in force but not in this gate's vocabulary" % cid)

    lines = open(DIGEST, encoding="utf-8").read().splitlines()
    hdr = sum(1 for l in lines if l.startswith("| bench |"))
    sep = sum(1 for l in lines if l.strip().startswith("|---"))
    if hdr != 1:
        findings.append("header row appears %d times (expected 1)" % hdr)
    if sep != 1:
        findings.append("delimiter row appears %d times (expected 1)" % sep)

    pin_cache = {}
    rows, seen = [], {}
    for i, line in enumerate(lines, 1):
        if not line.startswith("| ") or line.startswith("| bench |"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 6:
            findings.append("line %d: %d cells (expected 6)" % (i, len(cells)))
            continue
        bench, model, tasks, pin, call, strict = cells
        rows.append((i, bench, model, tasks, pin, call, strict))

        ent = benches.get(bench)
        if not isinstance(ent, dict) or not ent.get("tasks"):
            findings.append("line %d: bench %r has no pinned non-zero task count in MANIFEST"
                            % (i, bench))
        else:
            try:
                n = int(tasks)
            except ValueError:
                findings.append("line %d: tasks column %r is not an integer" % (i, tasks))
                continue
            if not (0 < n <= int(ent["tasks"])):
                findings.append("line %d: tasks %s outside 1..%d pinned for %s"
                                % (i, tasks, int(ent["tasks"]), bench))

        if not PIN.fullmatch(pin):
            findings.append("line %d: tasks pin %r is not a 16-hex digest" % (i, pin))
        else:
            tf = os.path.join(PUB, "%s.tasks.jsonl" % bench)
            if not os.path.exists(tf):
                findings.append("line %d: no pinned task file for bench %r" % (i, bench))
            else:
                if bench not in pin_cache:
                    try:
                        pin_cache[bench] = pbs.manifest_tasks_cell(bench, tf)
                    except SystemExit:
                        pin_cache[bench] = None
                want = pin_cache[bench]
                if want is None:
                    findings.append("line %d: %s does not reproduce its MANIFEST pin "
                                    "(task file moved or pin unlabelled)" % (i, bench))
                elif pin != want:
                    findings.append("line %d: tasks pin %s != MANIFEST-labelled pin %s for %s"
                                    % (i, pin, want, bench))

        m = FRAC.search(strict)
        frac = None
        if not m:
            findings.append("line %d: strict cell %r has no `N/M = **P%%**`" % (i, strict[:60]))
        else:
            n_ok, den, pct = int(m.group(1)), int(m.group(2)), float(m.group(3))
            frac = "%d/%d" % (n_ok, den)
            if n_ok > den:
                findings.append("line %d: %s has more passes than the denominator" % (i, frac))
            if tasks.isdigit() and int(tasks) != den:
                findings.append("line %d: tasks %s != denominator %d" % (i, tasks, den))
            if den and abs(100.0 * n_ok / den - pct) > 0.06:
                findings.append("line %d: %s prints %.1f%%, arithmetic says %.3f%%"
                                % (i, frac, pct, 100.0 * n_ok / den))
            if den == 0:
                findings.append("line %d: percent over denominator 0" % i)

        named = frozenset(c for c in KNOWN_CONTRACTS if c in call)
        if not named:
            ident = "%s|%s|%s|%s" % (bench, model, tasks, frac or "?")
            if ident not in LEGACY_NO_CONTRACT:
                findings.append("line %d: row %s names no checker contract and is not a "
                                "recorded pre-rule row" % (i, ident))
        key = (bench, model, tasks, tuple(sorted(named)), shape_of(call))
        if key in seen:
            findings.append("line %d: duplicate of line %d under identity %s"
                            % (i, seen[key], " + ".join(map(str, key))))
        else:
            seen[key] = i

    used = set()
    for (i, bench, model, tasks, pin, call, strict) in rows:
        m = FRAC.search(strict)
        if m:
            used.add("%s|%s|%s|%d/%d" % (bench, model, tasks, int(m.group(1)), int(m.group(2))))
    for stale in sorted(LEGACY_NO_CONTRACT - used):
        findings.append("LEGACY exception %s matches no row (exception list is stale)" % stale)

    print("digest rows=%d  contracts named=%d  pre-rule exceptions used=%d/%d"
          % (len(rows), sum(1 for r in rows if any(c in r[5] for c in KNOWN_CONTRACTS)),
             len(used & LEGACY_NO_CONTRACT), len(LEGACY_NO_CONTRACT)))
    if findings:
        for f in findings:
            print("FINDING: " + f)
        print("DIGEST ROW RULE: %d finding(s)" % len(findings))
        return 3
    print("DIGEST ROW RULE: %d rows, 0 findings" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
