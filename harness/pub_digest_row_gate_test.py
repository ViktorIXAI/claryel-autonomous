#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for the PUB digest percent-row gate (`scripts/pub_digest_row_check.py`).

Why this exists (2026-11-10 line audit). `PUB-DIGEST.md` is the table every verdict on
this line quotes, and no gate looked at it as a table. The owner's fail-closed rule says
a percent row names bench, model, tasks, tasks pin, call parameters AND checker
contract, is unique per identity, and never publishes a percent over an unscored
denominator. Census on the tracked bytes: 46 rows, 0 arithmetic or task-pin findings, but
**23 rows name no contract at all**. The writer still producing such rows was found
broken in two ways: `pub_bench_score.main()` re-hashed the task file with SHA-256/16
instead of routing through `manifest_tasks_cell` (an IFEval run through the generic
scorer would have minted the unlabelled second identity `e09a5cab3782ed5b` beside the
published `2c672531577dcc33` rows), and it would have written `0/0 = **0.0%**` for an arm
with no scored task.

Every rule below is proven with a tamper control, so the gate cannot be vacuous. The
tracked digest and every published arm byte stay untouched: the mutations happen on
copies inside a temp dir.
"""
import importlib.util
import json
import os
import sys
import tempfile
from io import StringIO

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PUB = os.path.join(REPO, "benchmarks", "public")
GATE = os.path.join(REPO, "scripts", "pub_digest_row_check.py")
sys.path.insert(0, os.path.join(REPO, "scripts"))

fails = []
checks = [0]


def chk(cond, name):
    checks[0] += 1
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pbs = load(os.path.join(REPO, "scripts", "pub_bench_score.py"), "pbs_gate")
pbs.MANIFEST_PATH = os.path.join(PUB, "MANIFEST.json")
digest_text = open(os.path.join(PUB, "PUB-DIGEST.md"), encoding="utf-8").read()


def run_gate_on(text):
    """Run the gate over a mutated copy of the digest; the tracked file is never touched."""
    with tempfile.TemporaryDirectory() as td:
        dst = os.path.join(td, "PUB-DIGEST.md")
        open(dst, "w", encoding="utf-8").write(text)
        g2 = load(GATE, "gate_copy")
        g2.DIGEST = dst
        g2.MANIFEST = os.path.join(PUB, "MANIFEST.json")
        g2.load_scorer = lambda: pbs
        buf, err = StringIO(), StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf, err
        try:
            code = g2.main()
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return code, buf.getvalue() + err.getvalue()


def replace_row(text, needle, new):
    lines = text.splitlines()
    hits = [i for i, l in enumerate(lines)
            if needle in l and l.startswith("| ") and not l.startswith("| bench |")]
    assert len(hits) == 1, "needle %r hits %d rows" % (needle, len(hits))
    lines[hits[0]] = new
    return "\n".join(lines) + "\n"


def table_row_lines(text):
    """The gate's own row filter (6-cell `| ... |` lines, header excluded).

    The census and the exception-set pins used to name 46 and 23 literally, which is a
    mutable enumeration: every published arm row moves the first number (2026-11-12:
    49 rows, the check went red on a clean publication). Both pins are derived here from
    the bytes and from the gate's own registry; the numbers they assert are unchanged in
    meaning, just no longer hand-copied.
    """
    out = []
    for line in text.splitlines():
        if not line.startswith("| ") or line.startswith("| bench |"):
            continue
        if len([c.strip() for c in line.strip().strip("|").split("|")]) == 6:
            out.append(line)
    return out


# 1. the tracked table passes, and the pre-rule exception set matches it exactly
code, out = run_gate_on(digest_text)
chk(code == 0, "tracked_digest_passes_gate")
_n_rows = len(table_row_lines(digest_text))
chk(_n_rows > 0 and ("digest rows=%d " % _n_rows) in out, "row_count_census")
# non-vacuity: the census tracks the table, so deleting one row moves the printed count
_dropped = digest_text.replace(table_row_lines(digest_text)[0] + "\n", "", 1)
_code2, out2 = run_gate_on(_dropped)
chk(("digest rows=%d " % (_n_rows - 1)) in out2, "row_count_census_tracks_the_table")
_n_legacy = len(load(GATE, "gate_ref").LEGACY_NO_CONTRACT)
chk(_n_legacy > 0 and ("pre-rule exceptions used=%d/%d" % (_n_legacy, _n_legacy)) in out,
    "legacy_exception_set_exact")
chk("duplicate" not in out, "matched_and_escalation_pair_is_not_a_duplicate")

gsm_row = next(l for l in digest_text.splitlines()
               if l.startswith("| gsm8k | qwen3.8-flash-next-iq3_s-basalt | 1319"))

# 2. a printed percent that disagrees with its own fraction
bad = gsm_row.replace("1284/1319 = **97.3%**", "1284/1319 = **99.0%**")
chk(bad != gsm_row, "percent_edit_changed_the_row")
code, out = run_gate_on(replace_row(digest_text,
                                    "| gsm8k | qwen3.8-flash-next-iq3_s-basalt | 1319", bad))
chk(code == 3 and "prints 99.0%" in out, "tamper_percent_disagrees_with_fraction")

# 3. a tasks cell that is a locally re-hashed value, not the MANIFEST-labelled pin
ife_row = next(l for l in digest_text.splitlines()
               if l.startswith("| ifeval | qwen3.8-flash-next-iq3_s-basalt | 541"))
code, out = run_gate_on(replace_row(
    digest_text, "| ifeval | qwen3.8-flash-next-iq3_s-basalt | 541",
    ife_row.replace("2c672531577dcc33", "e09a5cab3782ed5b")))
chk(code == 3 and "!= MANIFEST-labelled pin" in out, "tamper_unlabelled_sha256_tasks_cell")

# 4. a verbatim duplicate row is a finding
code, out = run_gate_on(digest_text + gsm_row + "\n")
chk(code == 3 and "duplicate of line" in out, "tamper_duplicate_row")

# 5. a NEW row that names no checker contract
new_row = ("| gsm8k | qwen3.8-flash-next-iq3_s-basalt | 1319 | 7dd0080ff23b8bc3 "
           "| temp 0.9, one call | 100/1319 = **7.6%** |")
code, out = run_gate_on(digest_text + new_row + "\n")
chk(code == 3 and "names no checker contract" in out, "tamper_new_row_without_contract")

# 6. a percent over an empty denominator
zero_row = ("| gsm8k | qwen3.8-flash-next-iq3_s-basalt | 0 | 7dd0080ff23b8bc3 "
            "| temp 0.9, checker pub-checkers-v2 | 0/0 = **0.0%** |")
code, out = run_gate_on(digest_text + zero_row + "\n")
chk(code == 3 and ("denominator 0" in out or "outside 1.." in out), "tamper_zero_denominator")

# 7. deleting a pre-rule row turns its exception record stale
kept = [l for l in digest_text.splitlines()
        if not l.startswith("| gsm8k | grok-4.7 | 300")]
chk(len(kept) == len(digest_text.splitlines()) - 1, "legacy_row_removed_once")
code, out = run_gate_on("\n".join(kept) + "\n")
chk(code == 3 and "exception list is stale" in out, "tamper_stale_legacy_exception")

# 8. an unknown contract id in force reddens the vocabulary rule
gate_src = load(GATE, "gate_vocab_probe")
shrunk = set(gate_src.KNOWN_CONTRACTS) - {"pub-checkers-v2"}
gate_src.KNOWN_CONTRACTS = shrunk
with tempfile.TemporaryDirectory() as td:
    dst = os.path.join(td, "PUB-DIGEST.md")
    open(dst, "w", encoding="utf-8").write(digest_text)
    gate_src.DIGEST = dst
    gate_src.MANIFEST = os.path.join(PUB, "MANIFEST.json")
    gate_src.load_scorer = lambda: pbs
    buf = StringIO()
    old_out = sys.stdout
    sys.stdout = buf
    try:
        code_v = gate_src.main()
    finally:
        sys.stdout = old_out
chk(code_v == 3 and "not in this gate's vocabulary" in buf.getvalue(),
    "tamper_stale_contract_vocabulary")

# 9. writer guard: an unscored set through the generic scorer exits 2 and writes NO row
captured = []
_real_write = pbs.write_digest


def _spy(row, dst=None):
    # Record only the writes that would hit the REAL table (dst=None means the default
    # published path); self-test's own round-trip passes an explicit temp path and must not
    # pollute the census. The real writer still runs, on a temp path, so nothing here ever
    # touches the tracked PUB-DIGEST.md.
    if dst is None:
        captured.append((row, dst))
        dst = os.path.join(_spy.td, "PUB-DIGEST.md")
    return _real_write(row, dst)


_spy.td = tempfile.mkdtemp(prefix="pub-digest-test-")
pbs.write_digest = _spy
with tempfile.TemporaryDirectory() as td:
    ifev_tasks = [json.loads(l) for l in
                  open(os.path.join(PUB, "ifeval.tasks.jsonl"), encoding="utf-8")
                  .readlines()[:4]]
    ans = os.path.join(td, "answers.jsonl")
    with open(ans, "w", encoding="utf-8") as fh:
        for t in ifev_tasks:
            fh.write(json.dumps({"id": t["id"], "answer": "42 words in this answer.",
                                 "model": "m", "temp": 0.7, "max_tokens": 1200}) + "\n")
    argv = sys.argv
    captured.clear()          # self-test rows land here too; watch only this run's write
    sys.argv = ["pub_bench_score.py", os.path.join(PUB, "ifeval.tasks.jsonl"), ans,
                "--limit", "4"]
    try:
        rc_ifeval = pbs.main()
    finally:
        sys.argv = argv
chk(rc_ifeval == 2, "writer_refuses_unscored_ifeval_arm")
chk(not captured, "writer_wrote_no_row_for_unscored_arm")
# 10. writer guard: a classic-set row names its contract and the MANIFEST pin
with tempfile.TemporaryDirectory() as td:
    tk = json.loads(open(os.path.join(PUB, "gsm8k.tasks.jsonl"), encoding="utf-8")
                    .readline())
    ans = os.path.join(td, "answers.jsonl")
    with open(ans, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"id": tk["id"], "answer": "ANSWER: %s" % tk["gold"],
                             "model": "m-test", "temp": 0.7, "max_tokens": 1200}) + "\n")
    argv = sys.argv
    captured.clear()
    sys.argv = ["pub_bench_score.py", os.path.join(PUB, "gsm8k.tasks.jsonl"), ans,
                "--limit", "1"]
    try:
        rc_ok = pbs.main()
    finally:
        sys.argv = argv
row_ok = captured[-1][0] if captured else ""
chk(rc_ok == 0 and row_ok.startswith("| gsm8k |"), "writer_builds_classic_row")
chk("checker pub-checkers-v2" in row_ok, "writer_row_names_checker_contract")
chk("7dd0080ff23b8bc3" in row_ok, "writer_row_uses_manifest_pin")
chk(row_ok.endswith("| 1/1 = **100.0%** |"), "writer_row_denominator_is_scored_count")
chk(len(captured) == 1, "writer_wrote_exactly_one_row")

# 11. that writer-shaped row satisfies the gate's row rules (control for rule 5)
ok_row = ("| gsm8k | m-test | 1 | 7dd0080ff23b8bc3 "
          "| temp 0.7, max_tokens 1200; checker pub-checkers-v2 | 1/1 = **100.0%** |")
code, out = run_gate_on(digest_text + ok_row + "\n")
chk(code == 0, "gate_accepts_writer_shaped_row_with_contract")

print("\n%d checks, %d failed" % (checks[0], len(fails)))
if fails:
    print("FAILED: " + ", ".join(fails))
sys.exit(1 if fails else 0)
