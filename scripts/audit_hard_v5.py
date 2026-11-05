#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproducible audit of hard-bank v5 (77 tasks) at commit 5941690.

Usage (repo root):  python3 scripts/audit_hard_v5.py [> results.csv]

Scores four arms against benchmarks/hard/bank-hard.json with the frozen
scorers in harness/:
  raw arms (single chat call, published answers):
    basalt  = qwen3.8-flash-next-iq3_s-basalt, one call, temp 0.7, no contour
    codex   = gpt-6.1-sol, reasoning effort xhigh (Codex CLI 0.166.0)
    grok    = grok-4.7 (hermes CLI)
  contour arm:
    contour 0.0.2.12 over the same basalt; per-task content/format recorded
    at run time and published (its D answers come from the agent-loop, so
    the loop scorer applied them, unlike single-shot text).

Modes printed:
  strict_loop  : format required; D judged by the contour loop scorer
                 (structured steps required) -> single-shot raw arms cannot pass D
  strict_plain : OFFICIAL for raw arms; format required; D judged by plain
                 plan scorer on the final text (only D mode fair to one-shot)
  content_only : auditor variant; ignores format_ok (what an outside recount
                 using simple scorers reproduces)

Completeness (77 unique task ids per arm, no empty answers) is asserted;
any violation fails the audit loudly.
"""
import hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "harness"))
import parb_check as CK  # noqa: E402

BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard.json")
RAW = os.path.join(ROOT, "benchmarks", "hard", "q5-experiment", "answers-%s.jsonl")
CONTOUR = os.path.join(ROOT, "benchmarks", "hard", "audit-20261105", "answers-contour.jsonl")
ARMS = ("basalt", "grok", "codex")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def load(p):
    return [json.loads(l) for l in open(p) if l.strip()]


def load_bank(p):
    return json.load(open(p))


def main():
    bank = {t["id"]: t for t in load_bank(BANK)}
    print("# bank=%s sha=%s" % ("hard-v5", sha(BANK)))
    print("# scorer=parb_check.py sha=%s" % sha(os.path.join(ROOT, "harness", "parb_check.py")))
    ids = sorted(bank)
    answers = {}
    for a in ARMS:
        rows = load(RAW % a)
        got = [r["task"] for r in rows]
        assert len(rows) == 77, (a, len(rows))
        assert len(set(got)) == 77, "duplicate task ids in %s" % a
        assert set(got) == set(ids), "task id mismatch in %s" % a
        assert all(r.get("answer") for r in rows), "empty answer in %s" % a
        answers[a] = {r["task"]: r["answer"] for r in rows}
    contour = {r["task"]: r for r in load(CONTOUR)}
    assert set(contour) == set(ids), "contour answer set mismatch"

    def raw_pass(arm, tid, mode):
        t = bank[tid]
        ans = answers[arm][tid]
        try:
            if t["cat"] == "D":
                if mode == "strict_loop":
                    import parb_loop
                    c, f, _n = parb_loop.check_D_loop(t, {"agent_steps": [], "agent_final": ans})
                else:
                    c, f = CK.check_D(t, ans)[:2]
            else:
                c, f = getattr(CK, "check_" + t["cat"])(t, ans)[:2]
        except Exception:
            return False
        return c == 1.0 and (True if mode == "content_only" else f == 1)

    hdr = ["task", "cat", "contour(c,f)",
           "basalt:loop", "basalt:plain", "basalt:co",
           "grok:loop", "grok:plain", "grok:co",
           "codex:loop", "codex:plain", "codex:co",
           "contour_rescored"]
    print(",".join(hdr))
    tot = {m: {a: 0 for a in ARMS} for m in ("strict_loop", "strict_plain", "content_only")}
    ctot = 0
    cres = {"agree": 0, "mismatch": 0, "not_rescorable": 0}
    cres_pass = {"agree": 0, "mismatch": 0, "not_rescorable": 0}
    mismatches = []
    for tid in ids:
        c = contour[tid]
        cp = "1,1" if (c.get("content") == 1.0 and c.get("format_ok") == 1) else \
             "%s,%s" % (c.get("content"), c.get("format_ok"))
        cp_pass = c.get("content") == 1.0 and c.get("format_ok") == 1
        ctot += cp_pass
        # independent re-score of the contour arm from archived answer text.
        # Category D needs the recorded agent-step trace; contour per-task
        # archives store only the final text, so D cells are explicitly
        # NOT independently re-scorable (issue #6 rule), not silently trusted.
        if bank[tid]["cat"] == "D":
            tag = "NR"
            cres["not_rescorable"] += 1
            cres_pass["not_rescorable"] += cp_pass
        else:
            x = None
            try:
                x = getattr(CK, "check_" + bank[tid]["cat"])(bank[tid], c.get("answer") or "")
                rp = x[0] == 1.0 and x[1] == 1
            except Exception:
                rp = False
            if rp == cp_pass:
                tag = "agree"
                cres["agree"] += 1
                cres_pass["agree"] += rp
            else:
                tag = "MISMATCH"
                cres["mismatch"] += 1
                mismatches.append((tid, "stored=%s,%s" % (c.get("content"), c.get("format_ok")),
                                   "rescored=%s,%s" % ((x[0], x[1]) if x else "scorer_error")))
        row = [tid, bank[tid]["cat"], cp]
        for a in ARMS:
            for m in ("strict_loop", "strict_plain", "content_only"):
                p = raw_pass(a, tid, m)
                tot[m][a] += p
                row.append("PASS" if p else "")
        row.append(tag)
        print(",".join(row))
    print("# CONTOUR 0.0.2.12 recorded %d/77" % ctot)
    print("# CONTOUR rescored: agree %d, mismatch %d, not-rescorable(D) %d"
          % (cres["agree"], cres["mismatch"], cres["not_rescorable"]))
    print("# CONTOUR pass among agreed-rescored %d, among D-recorded %d"
          % (cres_pass["agree"], cres_pass["not_rescorable"]))
    for m in mismatches:
        print("# MISMATCH", *m)
    for m in ("strict_loop", "strict_plain", "content_only"):
        print("# %-13s %s" % (m, " ".join("%s %d/77" % (a, tot[m][a]) for a in ARMS)))


main()
