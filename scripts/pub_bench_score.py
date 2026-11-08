#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score a public-benchmark arm deterministically and print/append its percent row.

Checkers are the point of this file: a public benchmark is only comparable across arms if the
scorer is fixed and public. `number`, `letter` and `exact` are implemented here; `pytest`
(HumanEval) and `ifeval` (instruction-following) are counted separately as UNSCORED until their
checkers ship, and the percent is then labelled "over the scored subset" instead of silently
dividing by the full task count. A missing answer counts as a loss, but an arm with >5% missing
answers is refused outright (partial arm, no percent).
"""
import hashlib
import json
import os
import re
import sys
import tempfile

NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
LET = re.compile(r"\b([A-J])\b")
FRAC = re.compile(r"^\s*(-?\d[\d,]*(?:\.\d+)?)\s*/\s*(-?\d[\d,]*(?:\.\d+)?)\s*$")
PLAIN_GOLD = re.compile(r"^-?\d[\d,]*(?:\.\d+)?$")

# Checker contract id. Bumped 08.11: `number` used to read a non-plain gold ("3/4", "72%")
# through the same last-number regex as an answer, so a fraction gold silently became its
# denominator and a false verdict was published. Now a gold this contract cannot parse
# returns None (UNSCORED, excluded from the denominator) instead of guessing, and an answer
# written as a fraction ("ANSWER: 3/4") is evaluated. On the pinned gsm8k set (1319/1319
# plain-integer golds, 0 answers with '/', '%' or '$' in the ANSWER line) both changes are
# verdict-neutral - proven by an old-vs-new rescore of every saved answer, not asserted.
CHECKER_CONTRACT = "pub-checkers-v2"


def norm_number(s):
    m = NUM.findall(str(s or ""))
    if not m:
        return None
    try:
        return float(m[-1].replace(",", ""))
    except ValueError:
        return None


def gold_number(g):
    s = str(g if g is not None else "").strip()
    if not PLAIN_GOLD.match(s):
        return None
    return float(s.replace(",", ""))


def answer_number(ans):
    # prefer an explicit ANSWER: line, else the last number in the text
    m = re.search(r"ANSWER:\s*([^\n]+)", ans or "", re.I)
    seg = m.group(1) if m else (ans or "")
    fm = FRAC.match(seg.split(" ")[0] if m else "")
    if fm:
        try:
            return float(fm.group(1).replace(",", "")) / float(fm.group(2).replace(",", ""))
        except ZeroDivisionError:
            return None
    return norm_number(seg)


def answer_letter(ans):
    m = re.search(r"ANSWER:\s*([A-J])\b", ans or "", re.I)
    if m:
        return m.group(1).upper()
    m = LET.search(ans or "")
    return m.group(1).upper() if m else None


def call_label(rows, temp):
    """Name the call parameters that were ACTUALLY used, never an assumed one.

    The local endpoint arm pins temperature/max_tokens and stores them; the cloud CLI arms do
    not expose sampling parameters at all, so printing `temp None` there would be a fabricated
    pin. Label the transport instead and say the parameters are not exposed. An arm whose
    transport genuinely differs from the plain single-call shape (the frozen contour runtime
    streams, pins a seed and walks a token ladder) carries `transport_note`, which is printed
    verbatim: a harness row must never wear the bare row's call label.
    """
    note = next((str(r.get("transport_note")) for r in rows if r.get("transport_note")), "")
    if note:
        return note
    if temp is not None:
        return "temp %s, max_tokens 1200" % temp
    tr = next((str(r.get("transport")) for r in rows if r.get("transport")), "")
    if tr:
        return "%s CLI (sampling params not exposed by the transport)" % tr
    return "parameters not recorded"


def digest_head():
    """The digest header is regenerated on every write so the contract in force is never stale."""
    return ("# Public benchmark percent digest\n\n"
            "One row per scored arm, newest first, written by `scripts/pub_bench_score.py`. "
            "Rows are only comparable when the task-file sha16 and the call parameters match. "
            "Deterministic checkers live here; the HumanEval `pytest-v1` execution checker "
            "lives in `scripts/pub_bench_exec.py` and names itself in the call column; an "
            "unshipped checker keeps its tasks out of the denominator and says so. "
            "Checker contract in force: `%s` - the scorer refuses to publish while its own "
            "self-test fails, and a gold the contract cannot parse is scored as UNSCORED, never "
            "guessed. A row re-scored under another contract id is a new row, not an edit.\n\n"
            % CHECKER_CONTRACT)


def digest_row(bench, model, n_tasks, tasks_sha16, call, ok, scored):
    return "| %s | %s | %d | %s | %s | %d/%d = **%.1f%%** |" % (
        bench, model, n_tasks, tasks_sha16, call, ok, scored, 100.0 * ok / max(scored, 1))


def write_digest(row, dst=None):
    """Prepend one percent row, newest first. One writer, one format: an execution-checked arm
    (`pub_bench_exec.py`) must land in the same table, not a side table nobody compares."""
    if dst is None:
        dst = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "..", "benchmarks", "public", "PUB-DIGEST.md"))
    hdr = ("| bench | model | tasks | tasks sha16 | call | strict |\n"
           "|---|---|---|---|---|---|")
    old = open(dst, encoding="utf-8").read() if os.path.exists(dst) else ""
    body = [l for l in old.splitlines() if l.startswith("| ") and "bench |" not in l
            and not set(l) <= set("|- ")]
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(digest_head() + hdr + "\n" + "\n".join([row] + body) + "\n")
    return dst


def check(checker, gold, ans):
    if checker == "number":
        g, a = gold_number(gold), answer_number(ans)
        if g is None:
            return None                           # gold outside this contract: unscored, not guessed
        return a is not None and abs(a - g) < 1e-6
    if checker == "letter":
        return answer_letter(ans) == str(gold).strip().upper()
    if checker == "exact":
        return (ans or "").strip().lower() == str(gold).strip().lower()
    return None


def selftest():
    """Checkers are only worth a percent if they separate right from wrong on known examples.

    Mirrors pub_bench_exec.py: the scorer refuses to publish anything while its own examples
    fail, so a regex edit cannot silently turn a benchmark into a scoring artifact.
    """
    cases = [
        # checker, gold, answer, expected (True win / False loss / None unscored)
        ("number", "72", "work...\nANSWER: 72", True),
        ("number", "72", "ANSWER: 73", False),
        ("number", "1200", "ANSWER: 1,200", True),
        ("number", "72", "I cannot solve this", False),
        ("number", "6,250", "ANSWER: 6250", True),
        ("number", "0.75", "ANSWER: 3/4", True),
        ("number", "3/4", "ANSWER: 0.75", None),
        ("number", "72%", "ANSWER: 72", None),
        ("letter", "C", "ANSWER: C", True),
        ("letter", "C", "the answer is (B)", False),
        ("letter", "C", "no letter here", False),
        ("exact", "hello", "  HELLO\n", True),
        ("exact", "hello", "hello world", False),
        ("pytest", "x", "def f(): pass", None),
        ("ifeval", "x", "anything", None),
    ]
    bad = [(ck, gold, exp, check(ck, gold, ans)) for ck, gold, ans, exp in cases
           if check(ck, gold, ans) is not exp]
    labels = [
        ([{"transport": "x"}], 0.7, lambda s: "temp 0.7" in s and "None" not in s),
        ([{"transport": "codex-cli 0.166.0"}], None,
         lambda s: "codex-cli" in s and "not exposed" in s and "None" not in s),
        ([], None, lambda s: "not recorded" in s and "None" not in s),
    ]
    bad += [("call_label", repr((rows, temp)), None, call_label(rows, temp))
            for rows, temp, ok in labels if not ok(call_label(rows, temp))]
    # the digest writer is a published artifact: prepend order and header must be stable,
    # and an execution-checked arm lands in the SAME table (tested on a temp path only).
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "PUB-DIGEST.md")
        r1 = digest_row("bench-a", "m1", 10, "abc123", "temp 0.7, max_tokens 1200", 8, 10)
        write_digest(r1, p)
        r2 = digest_row("bench-b", "m2", 5, "def456", "temp 0.7; checker pytest-v1", 4, 5)
        write_digest(r2, p)
        txt = open(p, encoding="utf-8").read()
        rows_out = [l for l in txt.splitlines()
                    if l.startswith("| ") and "bench |" not in l and not set(l) <= set("|- ")]
        if rows_out != [r2, r1] or CHECKER_CONTRACT not in txt or txt.count("# Public") != 1:
            bad.append(("digest_writer", repr(rows_out), "newest-first, one header", txt[:160]))
    print("selftest cases=%d failures=%d" % (len(cases) + len(labels) + 1, len(bad)))
    for b in bad:
        print("  FAIL %s gold=%r expected=%r got=%r" % b)
    if bad:
        return 1
    print("scorer self-test OK")
    return 0


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "selftest":
        return selftest()
    if selftest() != 0:
        print("refusing to score: scorer self-test failed")
        return 1
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    tasks_f, res_f = sys.argv[1], sys.argv[2]
    limit, offset = None, 0
    rest = sys.argv[3:]
    for i, a in enumerate(rest):
        if a == "--limit":
            limit = int(rest[i + 1])
        elif a == "--offset":
            offset = int(rest[i + 1])
    all_tasks = [json.loads(l) for l in open(tasks_f, encoding="utf-8") if l.strip()]
    window = all_tasks[offset:offset + limit] if limit else all_tasks[offset:]
    tasks = {t["id"]: t for t in window}
    ans, model, temp = {}, "unknown", None
    for line in open(res_f, encoding="utf-8"):
        d = json.loads(line)
        if d["id"] not in ans:
            ans[d["id"]] = d
            model = d.get("model", model)
            temp = d.get("temp", temp)
    missing = [t for t in tasks if t not in ans or not (ans[t].get("answer") or "").strip()]
    if len(missing) > 0.05 * len(tasks):
        raise SystemExit("arm is partial: %d/%d answers present - no percent printed"
                         % (len(tasks) - len(missing), len(tasks)))
    by = {}
    for tid, t in tasks.items():
        b, ck = t["bench"], t["checker"]
        ok = check(ck, t["gold"], ans.get(tid, {}).get("answer", ""))
        r = by.setdefault(b, {"scored": 0, "ok": 0, "unscored": 0})
        if ok is None:
            r["unscored"] += 1
        else:
            r["scored"] += 1
            r["ok"] += int(ok)
    print("checker contract: %s" % CHECKER_CONTRACT)
    for b, r in sorted(by.items()):
        pct = (100.0 * r["ok"] / r["scored"]) if r["scored"] else 0.0
        note = "" if not r["unscored"] else ("  [%d unscored, checker pending]" % r["unscored"])
        print("%-14s %4d/%4d = %5.1f%%  (answers %d/%d)%s"
              % (b, r["ok"], r["scored"], pct, len(tasks) - len(missing), len(tasks), note))
    row = digest_row(
        os.path.basename(tasks_f).replace(".tasks.jsonl", ""), model, len(tasks),
        hashlib.sha256(open(tasks_f, "rb").read()).hexdigest()[:16],
        call_label(list(ans.values()), temp),
        sum(r["ok"] for r in by.values()), sum(r["scored"] for r in by.values()))
    dst = write_digest(row)
    print("-> %s" % os.path.basename(dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
