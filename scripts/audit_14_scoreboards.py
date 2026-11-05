"""Issue #14 deliverables: three scoreboards from frozen published answers + 77-row audit JSONL.

Frozen inputs (hash-pinned, same pins as audit_hard_v5): bank-hard.json v5,
parb_check.py/parb_loop.py v5 scorer, answers-contour.jsonl, artifacts
results-v5fix.jsonl (D traces), answers-{basalt,grok,codex}.jsonl (q5-experiment).
No model re-runs. Modes:
  strict      = contour official loop accounting; raw arms strict_plain (PROTOCOL)
  content_only= content==1.0, format ignored
  clusters    = mean over byte-identical-prompt groups (group value = pass rate inside)
                + equal-category weighting
Outputs: SCOREBOARDS-14.md, audit-77-rows-v14.jsonl, per-pair discordant ids.
"""
import collections
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "harness"))
import parb_check as CK  # noqa: E402
import parb_loop as PL  # noqa: E402

BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard.json")
CONTOUR = os.path.join(ROOT, "benchmarks", "hard", "audit-20261105", "answers-contour.jsonl")
ART = os.path.join(ROOT, "benchmarks", "hard", "audit-20261105", "artifacts", "results-v5fix.jsonl")
RAW = os.path.join(ROOT, "benchmarks", "hard", "q5-experiment", "answers-%s.jsonl")
PINS = {"bank-hard.json": "32953591ba2a6c51", "parb_check.py": "1c032ef022607d7b",
        "parb_loop.py": "f5f5b78ab46a0f0c", "results-v5fix.jsonl": "91ccc27a3248b9b5"}
ARMS = ["basalt", "grok", "codex"]


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def main():
    for path, pin in ((BANK, PINS["bank-hard.json"]),
                      (os.path.join(ROOT, "harness", "parb_check.py"), PINS["parb_check.py"]),
                      (os.path.join(ROOT, "harness", "parb_loop.py"), PINS["parb_loop.py"]),
                      (ART, PINS["results-v5fix.jsonl"])):
        got = sha16(path)
        assert got == pin, "PIN MISMATCH %s" % path
    bank = {t["id"]: t for t in json.load(open(BANK))}
    ids = sorted(bank)
    cont = {r["task"]: r for r in map(json.loads, open(CONTOUR))}
    art = {r["task"]: r for r in map(json.loads, open(ART))}
    raw = {}
    for a in ARMS:
        rows = list(map(json.loads, open(RAW % a)))
        assert len(rows) == 77 and all(r.get("answer") for r in rows)
        raw[a] = {r["task"]: r["answer"] for r in rows}

    def raw_res(arm, tid, mode):
        t, ans = bank[tid], raw[arm][tid]
        try:
            if t["cat"] == "D":
                if mode == "strict_loop":
                    c, f, _ = PL.check_D_loop(t, {"agent_steps": [], "agent_final": ans})
                else:
                    c, f = CK.check_D(t, ans)[:2]
            else:
                c, f = getattr(CK, "check_" + t["cat"])(t, ans)[:2]
        except Exception:
            return None
        strict = c == 1.0 and f == 1
        return {"content": c, "fmt": f, "strict": strict, "co": c == 1.0}

    def cont_res(tid):
        r = cont[tid]
        if bank[tid]["cat"] == "D":
            lc, lf, _ = PL.check_D_loop(bank[tid], art[tid])
            return {"content": lc, "fmt": lf, "strict": lc == 1.0 and lf == 1, "co": lc == 1.0}
        c, f = getattr(CK, "check_" + bank[tid]["cat"])(bank[tid], r.get("answer") or "")[:2]
        return {"content": c, "fmt": f, "strict": c == 1.0 and f == 1, "co": c == 1.0}

    res = {"contour": {tid: cont_res(tid) for tid in ids}}
    for a in ARMS:
        res[a] = {tid: raw_res(a, tid, "strict_plain") for tid in ids}
        assert all(v is not None for v in res[a].values())

    out = []
    W = out.append
    W("# Issue #14 scoreboards (frozen answers, hash-pinned inputs)")
    W("")
    W("Pins: bank %s, parb_check %s, parb_loop %s, artifacts %s. Contour re-scored from "
      "archived answers + D step traces; raw arms re-scored from published answers."
      % (sha16(BANK), sha16(os.path.join(ROOT, "harness", "parb_check.py")),
         sha16(os.path.join(ROOT, "harness", "parb_loop.py")), sha16(ART)))
    W("")
    # 1) strict
    W("## 1) Strict contract (77 rows; contour=loop accounting for D, raw arms=strict_plain)")
    W("")
    W("| arm | perfect/77 | pct |")
    W("|---|---|---|")
    strict_n = {}
    for a in ["contour"] + ARMS:
        n = sum(res[a][t]["strict"] for t in ids)
        strict_n[a] = n
        W("| %s | %d/77 | %.1f%% |" % (a, n, n / 77 * 100))
    W("")
    # raw strict_loop for completeness
    W("Raw arms under strict_loop (empty-step scorer, lower bound): " + ", ".join(
        "%s %d/77" % (a, sum((raw_res(a, t, "strict_loop") or {"strict": False})["strict"] for t in ids))
        for a in ARMS))
    W("")
    # 2) content-only
    W("## 2) Content-only (content==1.0, format ignored)")
    W("")
    W("| arm | content/77 | pct |")
    W("|---|---|---|")
    for a in ["contour"] + ARMS:
        n = sum(res[a][t]["co"] for t in ids)
        W("| %s | %d/77 | %.1f%% |" % (a, n, n / 77 * 100))
    W("")
    # format-failure inventory
    W("Format-only failures (content==1, fmt==0): " + ", ".join(
        "%s %d" % (a, sum(res[a][t]["co"] and not res[a][t]["fmt"] for t in ids))
        for a in ["contour"] + ARMS))
    W("")
    # 3) sensitivity
    groups = collections.defaultdict(list)
    for t in bank.values():
        groups[t["prompt"]].append(t["id"])
    uniq_groups = sorted(groups.values())
    W("## 3) Sensitivity (byte-identical prompt groups; %d unique groups)" % len(uniq_groups))
    W("")
    W("| arm | cluster score | equal-category score |")
    W("|---|---|---|")
    cat_ids = collections.defaultdict(list)
    for t in bank.values():
        cat_ids[t["cat"]].append(t["id"])
    for a in ["contour"] + ARMS:
        gs = [sum(res[a][i]["strict"] for i in g) / len(g) for g in uniq_groups]
        cluster = sum(gs) / len(gs)
        cs = [sum(res[a][i]["strict"] for i in cids) / len(cids) for cids in cat_ids.values()]
        eqcat = sum(cs) / len(cs)
        W("| %s | %.1f%% (%d/%d groups full-pass: %d) | %.1f%% |"
          % (a, cluster * 100, sum(1 for x in gs if x == 1.0), len(gs),
             sum(1 for x in gs if x == 1.0), eqcat * 100))
    W("")
    W("Duplicate groups: " + "; ".join(
        "%s x%d" % (bank[g[0]]["cat"], len(g)) for g in uniq_groups if len(g) > 1))
    W("")
    # discordant ids
    W("## Pairwise discordant task ids (strict; contour pass/raw fail + contour fail/raw pass)")
    for a in ARMS:
        cf = sorted(t for t in ids if res["contour"][t]["strict"] and not res[a][t]["strict"])
        rf = sorted(t for t in ids if not res["contour"][t]["strict"] and res[a][t]["strict"])
        W("- contour vs %s: contour-only %d %s | raw-only %d %s" % (a, len(cf), cf, len(rf), rf))
    W("")

    # 77-row audit JSONL (Hermes decisions)
    dup = {t["prompt"] for t in bank.values() if len(groups[t["prompt"]]) > 1}
    rows = []
    for tid in ids:
        t = bank[tid]
        ver, why, flags = "VALID", "", []
        if t["prompt"] in dup:
            ver, why = "REPEATED_TEMPLATE", "byte-identical prompt shared by %d ids" % len(groups[t["prompt"]])
        if t["cat"] == "K" and tid in ("K-ex-00-0", "K-ex-01-0", "K-ex-03-0"):
            ver, why = "AMBIGUOUS", "instruction says three lines but lists four fields"
            if tid in ("K-ex-00-0", "K-ex-03-0"):
                flags.append("tax_field_not_stated_in_text")
        if t["cat"] == "C":
            letters = t["ref"]["letters"]
            pref = [chr(65 + i) for i in range(len(letters))]
            if letters == pref:
                flags.append("position_leak_leading_letters")
        if t["cat"] == "G":
            flags.append("raw_arm_input_parity_unproven_assembled_doc_not_archived")
        rows.append({"id": tid, "cat": t["cat"], "verdict": ver, "rationale": why, "flags": flags})
    vcount = collections.Counter(r["verdict"] for r in rows)
    with open(os.path.join(ROOT, "benchmarks", "hard", "audit-20261105", "audit-77-rows-v14.jsonl"),
              "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    out.append("## 77-row audit verdicts (Hermes): " + ", ".join("%s=%d" % kv for kv in sorted(vcount.items())))
    out.append("Machine-readable: audit-77-rows-v14.jsonl (this directory).")
    txt = "\n".join(out) + "\n"
    open(os.path.join(ROOT, "benchmarks", "hard", "audit-20261105", "SCOREBOARDS-14.md"), "w",
         encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
