#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cadence scorer for the v6.2 measurement stack (bank v6.2 + scorer contract v6.2).

`raw_rep_score_v6.py`/`arm_bands_v61.py` are frozen v6.1 artifacts (v6.1 bank, v6.1
scorer bytes hardcoded). Cadence-246 and later cadences run on `bank-hard-v6.2.json`
with the contract registry, so scoring must go through `gate_scorer_contract.load_contract`
and name both identities next to every number (owner directive 2026-11-07: every table
carries bank sha16 + scorer contract version).

Pre-registered cadence rule (c) is implemented here: the contour legs' stored ledger
scores are re-derived from the result answer bytes with the same contract; any
per-cell disagreement is printed cell by cell (scorer-routing bug), never averaged.

Common set: single-shot non-E cells (bank minus mode==loop minus cat E), identical
denominators for every arm. E needs the docker battery and cadence seeds do not
re-execute it for raw arms (every published seed scores 10/10 on E), so E is excluded
symmetrically and stated. Loop-D is N/A for single-shot brains by protocol.

Usage:
  python3 scripts/cadence_score_v62.py --ws ~/parb-v62-contour --raw-ws ~/parb-v62-raw-reps \
      --reps 16,17,18 --prefix q45 --arms basalt codex grok \
      --gpu-csv ~/parb-v62-contour/gpu-power-246.csv --out v6-results/cadence-246
"""
import argparse
import csv
import glob
import importlib.util
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "harness"))
import gate_scorer_contract as SC  # noqa: E402

BANK_PUB = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.2.json")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, "missing module: " + path
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def strict(c, f):
    return c == 1.0 and bool(f)


def _loop_rows_from_steps(steps):
    """Mirror of the GENERATED workspace adapter `parb_loop.check_D_loop` (pinned in
    WS_PINNED; cadence-249 correction 2026-11-07): loop result rows store the harness
    step list in the sibling field `agent_steps`, and the adapter turns those steps into
    the scorer row form (JSON-string parsed actions; `gate_block` -> attempted-tool dict;
    `gate_rejected` -> marked dict). An external re-scorer that only looks for
    `answer._loop_rows` wrongly reports every loop cell 'not replayable' — 18/18 replay
    clean (0 ledger mismatches) once the pinned mapping is applied."""
    rows = []
    for s in (steps or []):
        p = s.get("parsed")
        if p is None and "gate_block" in s:
            rows.append({"tool": s["gate_block"], "arg": None})
            continue
        if s.get("gate_rejected"):
            rows.append(dict(p, gate_rejected=True) if isinstance(p, dict)
                        else {"gate_rejected": True})
            continue
        rows.append(p if isinstance(p, str) else json.dumps(p, ensure_ascii=False))
    return rows


def sign_test(w, l):
    n = w + l
    if n == 0:
        return 1.0
    k = min(w, l)
    return min(1.0, sum(math.comb(n, i) for i in range(0, k + 1)) * 2 / 2 ** n)


def rows_of(path):
    out = {}
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("task"):
            out[(r["task"], int(r.get("rep", 0)))] = r  # later rows win (APPEND semantics)
    return out


def energy_wh(csv_path, start, end):
    rows = []
    for line in open(csv_path, encoding="utf-8"):
        parts = [p.strip() for p in line.strip().split(",")]
        if len(parts) < 3:
            continue
        try:
            ts, pw, util = float(parts[0]), float(parts[1]), float(parts[2])
        except ValueError:
            continue
        if ts < start or ts > end:
            continue
        rows.append((ts, pw, util))
    if len(rows) < 2:
        return None
    rows.sort()
    j = sum(((p0 + p1) / 2.0) * (t1 - t0)
            for (t0, p0, _), (t1, p1, _) in zip(rows, rows[1:]) if 0 < (t1 - t0) <= 30)
    busy = sum(1 for _, _, u in rows if u >= 90) / len(rows)
    return {"wh": j / 3600.0, "busy": busy, "samples": len(rows)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws", required=True)
    ap.add_argument("--raw-ws", required=True)
    ap.add_argument("--reps", default="16,17,18")
    ap.add_argument("--prefix", default="q45")
    ap.add_argument("--arms", nargs="*", default=["basalt", "codex", "grok"])
    ap.add_argument("--gpu-csv", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--bank-pub", default="bank-hard-v6.2.json",
                    help="published bank file under benchmarks/hard (default keeps "
                         "cadence-246 reproducible; cadence-249 passes bank-hard-v6.4.json)")
    args = ap.parse_args()
    reps = [int(x) for x in args.reps.split(",")]
    ws = os.path.expanduser(args.ws)
    raw_ws = os.path.expanduser(args.raw_ws)

    # ---- stack identity: fail closed on any drift or bank mismatch -------------
    CK = SC.load_contract("v6.2")  # registry verifies pinned bytes
    BANK_PUB = os.path.join(ROOT, "benchmarks", "hard", args.bank_pub)
    bank_pub = json.load(open(BANK_PUB, encoding="utf-8"))
    bank_ws = json.load(open(os.path.join(ws, "bank.json"), encoding="utf-8"))
    bank_pub = bank_pub if isinstance(bank_pub, list) else bank_pub["tasks"]
    bank_ws = bank_ws if isinstance(bank_ws, list) else bank_ws["tasks"]
    assert len(bank_pub) == len(bank_ws) == 77, "bank size wrong"
    tpub = {t["id"]: t for t in bank_pub}
    tws = {t["id"]: t for t in bank_ws}
    diff = sorted(t for t in tpub
                  if (tpub[t].get("prompt") != tws[t].get("prompt")
                      or json.dumps(tpub[t].get("ref")) != json.dumps(tws[t].get("ref"))
                      or tpub[t].get("cat") != tws[t].get("cat")
                      or tpub[t].get("mode") != tws[t].get("mode")))
    assert not diff, "ws bank copy differs from published %s on: %s" % (args.bank_pub, diff)
    bank_sha16 = SC._sha16(BANK_PUB)
    ws_bank_sha16 = SC._sha16(os.path.join(ws, "bank.json"))
    loop = {k for k in tpub if tpub[k].get("mode") == "loop"}
    eset = {k for k in tpub if tpub[k]["cat"] == "E"}
    common = sorted(k for k in tpub if k not in loop and k not in eset)

    print("## stack identity")
    print("bank %s published sha16 %s (ws copy %s, 77 tasks field-identical)" % (args.bank_pub, bank_sha16, ws_bank_sha16))
    print("scorer contract %s (%s), strict rule: %s, seed protocol %s"
          % (SC.SCORER_CONTRACT, SC.CONTRACT_PINS["v6.2"], SC.STRICT_RULE, SC.SEED_PROTOCOL))
    print("common set: %d single-shot non-E cells (loop-D N/A for raw arms; E excluded symmetrically)\n" % len(common))

    # ---- contour legs: ledger scores + rule (c) re-score from bytes ------------
    contour = {}   # (task,rep) -> strict
    contour_plain = {}  # non-loop only
    mismatches, not_replay = [], []
    for rep in reps:
        rid = "%sr%d" % (args.prefix, rep)
        led = rows_of(os.path.join(ws, "ledger-%s.jsonl" % rid))
        res = rows_of(os.path.join(ws, "results-%s.jsonl" % rid))
        assert len(led) == 77 and len(res) == 77, "%s incomplete: led %d res %d" % (rid, len(led), len(res))
        for key, lr in led.items():
            task = key[0]
            st = strict(lr.get("content"), lr.get("format_ok"))
            contour[key] = st
            if task not in loop:
                contour_plain[key] = st
            rr = res.get(key)
            if rr is None or not rr.get("answer"):
                mismatches.append((key, "blank_answer_bytes"))
                continue
            if task in loop:
                if "agent_steps" in rr:
                    tr = _loop_rows_from_steps(rr["agent_steps"])
                else:
                    try:
                        tr = json.loads(rr["answer"]).get("_loop_rows")
                    except (TypeError, ValueError):
                        tr = None
                if tr is None:
                    not_replay.append((key, "trajectory_not_stored"))
                    continue
                c, f, n = CK.check_D_loop_v6(tpub[task], tr)
            elif tpub[task]["cat"] == "E":
                not_replay.append((key, "needs_sandbox"))  # E = docker battery, not offline-replayable
                continue
            else:
                c, f, n = CK.CHECK[tpub[task]["cat"]](tpub[task], rr["answer"])
            if strict(c, f) != st:
                mismatches.append((key, "ledger %s vs rescore %s notes=%s"
                                   % (st, strict(c, f), n)))
    print("## rule (c) contour re-score audit (stored bytes vs stored ledger, contract v6.2)")
    print("mismatched cells: %d%s" % (len(mismatches), "" if not mismatches else " -> scorer-routing bug, fix before publishing"))
    for k, why in mismatches:
        print("  MISMATCH %s r%s: %s" % (k[0], k[1], why))
    from collections import Counter as _C
    why = _C(w for _, w in not_replay)
    print("rule (c) not-offline-replayable cells: %s (E = docker battery, not offline-replayable; loop cells replay from agent_steps via the pinned adapter mapping)" % dict(why))
    blank_ans = sum(1 for rep in reps for t, r in
                    rows_of(os.path.join(ws, "results-%sr%d.jsonl" % (args.prefix, rep))).items()
                    if not r.get("answer"))
    print("blank result answers across contour legs: %d\n" % blank_ans)

    # ---- raw arms ----------------------------------------------------------------
    raw = {}  # arm -> (task,rep) -> strict
    empties = {}
    for arm in args.arms:
        path = os.path.join(raw_ws, "answers-%s.jsonl" % arm)
        if not os.path.exists(path):
            print("## leg %s: answers file missing — leg pending\n" % arm)
            continue
        rows = rows_of(path)
        sc = {}
        emp = 0
        for (task, rep), r in rows.items():
            if rep not in reps or task in loop or task in eset:
                continue
            ans = r.get("answer") or ""
            if not ans.strip():
                emp += 1
            c, f, n = CK.CHECK[tpub[task]["cat"]](tpub[task], ans)
            sc[(task, rep)] = strict(c, f)
        raw[arm] = sc
        empties[arm] = emp
        print("## leg %s: %d scored cells, %d empty answers" % (arm, len(sc), emp))

    # ---- per-rep paired tables ---------------------------------------------------
    print("\n## paired tables (%d cells per rep)" % len(common))
    hdr = "| arm | rep | contour plain /71 | loop /6 | contour/%d vs arm/%d | W / L | exact p |" % (len(common), len(common))
    print(hdr)
    pooled = {arm: [0, 0] for arm in raw}
    for arm, sc in raw.items():
        for rep in reps:
            cs = [contour[(t, rep)] for t in common]
            rs = [sc.get((t, rep)) for t in common]
            missing = sum(1 for x in rs if x is None)
            if missing:
                print("| %s | rep%d | leg INCOMPLETE: %d/%d cells present, pair skipped |" % (arm, rep, len(common) - missing, len(common)))
                continue
            assert all(x is not None for x in rs), "%s missing cells at rep %s" % (arm, rep)
            w = sum(1 for a, b in zip(cs, rs) if a > b)
            l = sum(1 for a, b in zip(cs, rs) if a < b)
            pooled[arm][0] += w
            pooled[arm][1] += l
            plain = sum(v for (_, tr), v in contour_plain.items() if tr == rep)
            lp = sum(contour.get((t, rep), 0) for t in loop if (t, rep) in contour)
            print("| %s | rep%d | %d | %d/%d | %d vs %d | %d / %d | %.5f |"
                  % (arm, rep, plain, lp, len(loop),
                     sum(cs), sum(rs), w, l, sign_test(w, l)))
        w, l = pooled[arm]
        expected = len(common) * len(reps)
        if len(sc) != expected:
            print("| **%s pooled** | r%s | leg INCOMPLETE (%d/%d cells), pooled held until leg done |" % (arm, args.reps, len(sc), expected))
            continue
        print("| **%s pooled** | r%s |  |  | %d vs %d | **%d / %d** | **%.6f** |"
              % (arm, args.reps, sum(contour[(t, r)] for t in common for r in reps),
                 sum(raw[arm].get((t, r), 0) for t in common for r in reps), w, l, sign_test(w, l)))

    # ---- per-category pooled (strict cells over reps) ----------------------------
    print("\n## per-category pooled strict (rows = %d reps)" % len(reps))
    cats = sorted({tpub[t]["cat"] for t in common})
    print("| cat | n | contour | " + " | ".join(raw.keys()) + " |")
    for c in cats:
        ids = [t for t in common if tpub[t]["cat"] == c]
        row = [c, str(len(ids) * len(reps)), str(sum(contour.get((t, r), 0) for t in ids for r in reps))]
        for arm in raw:
            row.append(str(sum(raw[arm].get((t, r), 0) for t in ids for r in reps)))
        print("| " + " | ".join(row) + " |")

    # ---- corrected-gold fairness check --------------------------------------------
    print("\n## corrected-gold fairness check (v6.2-defect cells, strict over %d reps)" % len(reps))
    for tid in ("A-ex6-03", "C-ex6-02", "K-ex6-03"):
        if tid not in tpub:
            continue
        cs = sum(contour.get((tid, r), 0) for r in reps)
        line = ["| %s | contour %d/%d" % (tid, cs, len(reps))]
        for arm in raw:
            line.append("%s %d/%d" % (arm, sum(raw[arm].get((tid, r), 0) for r in reps), len(reps)))
        print(" | ".join(line) + " |")

    # ---- wall and energy -----------------------------------------------------------
    print("\n## wall and energy")
    if args.gpu_csv and os.path.exists(args.gpu_csv):
        tot = 0.0
        for rep in reps:
            rid = "%sr%d" % (args.prefix, rep)
            s = float(open(os.path.join(ws, rid + "-start.epoch")).read())
            e = float(open(os.path.join(ws, rid + "-end.epoch")).read())
            en = energy_wh(args.gpu_csv, s, e)
            if en is None:
                print("%s: NO GPU SAMPLES in window — energy not measurable" % rid)
                continue
            tot += en["wh"]
            print("%s: wall %ds energy %.2fWh busy %.2f" % (rid, int(e - s), en["wh"], en["busy"]))
        print("contour total: %.2fWh" % tot)
        for arm in ("basalt",):
            sp, ep = (os.path.join(raw_ws, x) for x in ("basalt-r161718-start.epoch", "basalt-r161718-end.epoch"))
            if os.path.exists(sp) and os.path.exists(ep):
                s, e = float(open(sp).read()), float(open(ep).read())
                en = energy_wh(args.gpu_csv, s, e)
                if en is None:
                    print("%s leg: NO GPU SAMPLES in window — energy not measurable" % arm)
                else:
                    print("%s leg: wall %ds energy %.2fWh busy %.2f" % (arm, int(e - s), en["wh"], en["busy"]))
    for arm in ("codex", "grok"):
        sp, ep = (os.path.join(raw_ws, x) for x in ("cloud-r161718-start.epoch", "cloud-r161718-end.epoch"))
        if arm in raw and os.path.exists(sp) and os.path.exists(ep):
            print("%s leg: wall %ds (cloud CLI, no local GPU energy)" % (arm, int(float(open(ep).read()) - float(open(sp).read()))))

    # ---- per-cell CSV ---------------------------------------------------------------
    if args.out:
        # contour arm label comes from the legs' own run records (the contour stamp
        # they ran under), never a hardcoded revision: a hardcoded "contour-2.45"
        # mislabeled the cadence-249 legs (stamp 2.49 / behavior 2.48) in the CSV.
        contour_label = "contour"
        for rep in reps:
            rp = os.path.join(ws, "run-record-%sr%d.json" % (args.prefix, rep))
            if os.path.exists(rp):
                try:
                    stamp = (json.load(open(rp)).get("stack") or {}).get("contour_stamp")
                    if stamp:
                        contour_label = "contour-%s" % stamp
                        break
                except (ValueError, OSError):
                    pass
        out_dir = os.path.join(ROOT, "benchmarks", "hard", args.out) if not os.path.isabs(args.out) else args.out
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "cadence-cells-v62.csv"), "w", newline="") as fh:
            wr = csv.writer(fh)
            wr.writerow(["arm", "rep", "task", "cat", "strict", "bank_sha16", "contract"])
            for key, st in sorted(contour.items()):
                wr.writerow([contour_label, key[1], key[0], tpub[key[0]]["cat"], st, bank_sha16, SC.SCORER_CONTRACT])
            for arm, sc in raw.items():
                for key, st in sorted(sc.items()):
                    wr.writerow([arm, key[1], key[0], tpub[key[0]]["cat"], st, bank_sha16, SC.SCORER_CONTRACT])
        print("\ncells csv written: %s/cadence-cells-v62.csv" % out_dir)

    if mismatches:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
