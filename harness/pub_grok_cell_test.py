#!/usr/bin/env python3
"""Contract test for `scripts/pub_grok_cell_check.py` (added 2026-11-10, tick 11).

Why it exists: the owner rule says a Grok cell for an incomplete set must read
"suspended by owner quota, resumes 2026-11-12" — never a blank that reads as zero, never a
transport failure. The tick-11 audit found three result tables violating it 24 h after the legs
were stopped (GPQA-Diamond "in flight (12/198 at publish time)", HumanEval "not started yet",
MMLU-Pro "not started"), while prose elsewhere in the same documents carried the correct status.

Every invariant below is paired with a tamper control, so the checker cannot be vacuous: an
edited stale cell, a deleted grok row and a percent-less suspension cell each have to redden it.

Run with no arguments; exits non-zero on the first failed invariant.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

PASSED = 0
FAILED = []


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ok(cond, label):
    global PASSED
    if cond:
        PASSED += 1
    else:
        FAILED.append(label)
        print("FAIL:", label)


def main() -> int:
    chk = load("pub_grok_cell_check", "scripts/pub_grok_cell_check.py")

    # 0. the sentence is READ, not remembered: the checker's vocabulary is the owner-window
    #    record's, and every superseded window's sentence is a finding (tick 73, 2026-11-12:
    #    the owner cancelled Grok on the day the resume window opened and four table cells still
    #    promised a resume "2026-11-12").
    in_force, superseded = chk.load_window()
    ok(bool(in_force), "the in-force sentence comes from the owner-window record (%r)" % in_force)
    ok(len(superseded) >= 1, "the record names at least one superseded sentence (%d)" % len(superseded))
    ok(in_force not in superseded, "the in-force sentence is not also listed as superseded")

    # 1. the tracked tree is clean under the rule, and the scope is real
    docs = list(chk.DEFAULT_DOCS)
    ok(len(docs) >= 9, "checker scans every result document (%d found)" % len(docs))
    ok(all(p.exists() for p in docs), "every scanned document exists")
    findings = [f for p in docs for f in chk.check_doc(p)]
    ok(findings == [], "tracked result tables satisfy the grok cell rule: %r" % findings[:3])

    # 2. every scanned document actually carries a grok row (a silently dropped fourth arm is
    #    the same failure class as a stale cell)
    for p in docs:
        ok(len(list(chk.grok_rows(p.read_text(encoding="utf-8")))) >= 1,
           "%s has a grok arm row" % p.name)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)

        # 3. TAMPER: the exact stale cell the audit found must be a finding
        stale = (
            "| arm | model / transport | tasks | strict | wall time | call parameters |\n"
            "|---|---|---|---|---|---|\n"
            "| brain-basalt | x | 198/198 | **127/198 = 64.1 %** | 1 s | temp 0.7 |\n"
            "| grok | `grok-4.7`, hermes one-shot, toolsets off "
            "| in flight (12/198 at publish time) | pending — no percent for a partial arm "
            "| — | — |\n"
        )
        f_stale = td / "STALE-RESULT.md"
        f_stale.write_text(stale, encoding="utf-8")
        got = chk.check_doc(f_stale)
        ok(len(got) >= 2, "stale 'in flight' cell is a finding (%d)" % len(got))
        ok(any("suspension sentence" in g for g in got),
           "the missing-suspension-sentence finding fires")
        ok(any("'in flight'" in g for g in got), "the stale-marker finding fires")

        # 4. TAMPER: the corrected wording must pass, and it must be the wording the rule names
        fixed = stale.replace(
            "| in flight (12/198 at publish time) | pending — no percent for a partial arm | — | — |",
            "| **%s** (leg stopped at 139/198 stored rows, resumable by id) "
            "| no percent for a partial arm | — | — |" % chk.SUSPENSION)
        f_fixed = td / "FIXED-RESULT.md"
        f_fixed.write_text(fixed, encoding="utf-8")
        ok(chk.check_doc(f_fixed) == [], "suspension wording passes: %r" % chk.check_doc(f_fixed))

        # 5. a completed grok arm publishes a percent and passes even at full width
        done = (
            "| arm | model | tasks | strict |\n|---|---|---|---|\n"
            "| grok | `grok-4.7` | 300/300 | **288/300 = 96.0 %** |\n")
        f_done = td / "DONE-RESULT.md"
        f_done.write_text(done, encoding="utf-8")
        ok(chk.check_doc(f_done) == [], "completed grok row with a percent passes")

        # 6. TAMPER: deleting the grok row is a finding, not a silent pass
        gone = (
            "| arm | model | tasks | strict |\n|---|---|---|---|\n"
            "| brain-basalt | x | 541/541 | **467/541 = 86.3 %** |\n")
        f_gone = td / "GONE-RESULT.md"
        f_gone.write_text(gone, encoding="utf-8")
        ok(any("no grok arm row" in g for g in chk.check_doc(f_gone)),
           "a document with no grok row is a finding")

        # 7. TAMPER: an empty cell that reads as a zero must not pass
        blank = (
            "| arm | model | tasks | strict |\n|---|---|---|---|\n"
            "| grok-4.7 | 541 | — | — |\n")
        f_blank = td / "BLANK-RESULT.md"
        f_blank.write_text(blank, encoding="utf-8")
        ok(len(chk.check_doc(f_blank)) >= 1, "a blank grok cell is a finding")

        # 7b. TAMPER (tick 73, 2026-11-12): a cell that still carries the SUPERSEDED window's
        #     sentence must redden — after the owner cancelled Grok, "resumes 2026-11-12" is a
        #     false availability claim, the exact class this checker exists for.
        stale_window = stale.replace(
            "| in flight (12/198 at publish time) | pending — no percent for a partial arm | — | — |",
            "| %s | no percent for a partial arm | — | — |" % superseded[0])
        f_old = td / "OLDWINDOW-RESULT.md"
        f_old.write_text(stale_window, encoding="utf-8")
        got_old = chk.check_doc(f_old)
        ok(any("SUPERSEDED" in g for g in got_old),
           "a percent-less cell carrying the superseded sentence is a finding: %r" % got_old[:2])

        # 7c. the corrected wording for the cancelled window passes
        new_window = stale_window.replace(superseded[0], in_force)
        f_new = td / "NEWWINDOW-RESULT.md"
        f_new.write_text(new_window, encoding="utf-8")
        ok(chk.check_doc(f_new) == [], "in-force cancelled-window wording passes: %r"
           % chk.check_doc(f_new))

        # 7d. INPUT GAP: a checker with no vocabulary must refuse, never fall back to a
        #     remembered sentence (that is how a stale window survives a decision change).
        rc_gap = chk.main(["pub_grok_cell_check.py", "--pin", str(td / "no-such-pin.json")])
        ok(rc_gap == 2, "a missing owner-window record is an INPUT GAP exit 2 (got %r)" % rc_gap)

    # 8. the CLI contract: 0 on the clean tree, 3 on a tampered tree
    rc_clean = chk.main(["pub_grok_cell_check.py"])
    ok(rc_clean == 0, "CLI exits 0 on the tracked tree (got %r)" % rc_clean)
    with tempfile.TemporaryDirectory() as td2:
        p = Path(td2) / "X-RESULT.md"
        p.write_text(stale, encoding="utf-8")
        rc_bad = chk.main(["pub_grok_cell_check.py", str(p)])
        ok(rc_bad == 3, "CLI exits 3 on a stale table (got %r)" % rc_bad)

    print("pub_grok_cell_test: %d checks passed, %d failed" % (PASSED, len(FAILED)))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
