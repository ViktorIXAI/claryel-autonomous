#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Budget-matched simple baselines vs the v1.9 contour (external-review item).

Question from the external audits: does an evolved contour beat what any
engineer gets from a validator, one retry, or a few dozen lines of code at
the SAME budget? This script runs four simple arms on the exact (task, rep)
pairs the published v1.9 series measured, with the same request seeds,
temperature 0.7, thinking off, and the same validators for scoring:

  S0_direct      one call, max_tokens=1024, no machinery
  S1_generic     one call + one generic retry ("output only the requested
                 format") if the validator says the format failed
  S2_min_gate    one call + one retry carrying the validator's actual
                 complaint and the previous answer (the contour's minimal
                 core, ~40 lines)
  S4_best_of_2   two independent calls, keep the validator-best answer
                 (sampling instead of machinery, same call budget as S2)

The contour arm (S3) is NOT re-run: its published rows are joined by
(task, rep) so the comparison is paired on identical seeds.

Outputs: baselines-results.jsonl (one row per arm/task/rep with tokens and
seconds) and baselines-ledger.jsonl. Scoring uses the same parb_check /
parb_loop validators as every published series, so scores are comparable.

Usage:
  PARB_BANK=benchmarks/text-gates/bank.json \
  PARB_V19=/path/to/results-v19-b2003.jsonl \
  PARB_API=... PARB_MODEL=... PARB_OUT=./baselines \
  python3 experiments/baselines/simple_baselines.py [--per-cat 6] [--smoke]
"""
import json, os, re, sys, time, hashlib, urllib.request
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(ROOT, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "harness"))
import parb_check as CK          # same validators as all published series
import parb_loop as LP

API = os.environ.get("PARB_API", "http://127.0.0.1:8080/v1/chat/completions")
MODEL = os.environ.get("PARB_MODEL", "qwen3.8-flash-next-iq3_s")
TIMEOUT = 420
OUT = os.environ.get("PARB_OUT", ".")
BANK = os.environ.get("PARB_BANK", os.path.join(REPO, "benchmarks/text-gates/bank.json"))
V19 = os.environ["PARB_V19"]
CATS = os.environ.get("PARB_CATS", "ABCDEFGHIJK")

_kf = os.environ.get("PARB_KEY_FILE")
HDRS = {"Content-Type": "application/json"}
if _kf and os.path.exists(_kf):
    HDRS["Authorization"] = "Bearer " + json.load(open(_kf))["api_key"]


def log(m):
    print("%s %s" % (time.strftime("%H:%M:%S"), m), flush=True)


def call_api(msgs, mt, seed):
    body = {"model": MODEL, "messages": msgs, "temperature": 0.7, "max_tokens": mt,
            "stream": True, "seed": seed,
            "reasoning_effort": "none",
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers=HDRS)
    t0 = time.monotonic()
    txt, ptok, ctok, finish, err = "", None, None, None, None
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            for raw in resp:
                ln = raw.decode("utf-8", "ignore").strip()
                if not ln.startswith("data:"):
                    continue
                d = ln[5:].strip()
                if d == "[DONE]":
                    break
                try:
                    j = json.loads(d)
                except Exception:
                    continue
                ch = (j.get("choices") or [{}])[0]
                txt += (ch.get("delta") or {}).get("content") or ch.get("content") or ""
                if ch.get("finish_reason"):
                    finish = ch["finish_reason"]
                if j.get("usage"):
                    ptok = j["usage"].get("prompt_tokens", ptok)
                    ctok = j["usage"].get("completion_tokens", ctok)
    except Exception as e:
        err = ("%s: %s" % (type(e).__name__, e))[:200]
    return {"text": txt, "ptok": ptok, "ctok": ctok, "finish": finish,
            "err": err, "el": time.monotonic() - t0}


def msgs_for(t):
    content = (t.get("assembled_doc", "") + "\n\n" + t["prompt"]) if t.get("assembled_doc") else t["prompt"]
    return ([{"role": "system", "content": t["sys"]}] if t.get("sys") else []) + \
           [{"role": "user", "content": content}]


def score(t, ans):
    """Same validators and same dispatch as every published series."""
    try:
        if t["kind"] == "loop":
            rec = {"answer": ans, "agent_final": ans, "agent_steps": []}
            return LP.check_D_loop(t, rec)
        return CK.CHECK[t["cat"]](t, ans)
    except Exception as e:
        return None, None, ["scorer_error"]


def pick_pairs(per_cat):
    bank = {t["id"]: t for t in json.load(open(BANK, encoding="utf-8"))}
    rows = {}
    for ln in open(V19, encoding="utf-8", errors="ignore"):
        try:
            r = json.loads(ln)
        except Exception:
            continue
        k = (r.get("task"), r.get("rep"))
        if r.get("task") and k not in rows:
            rows[k] = r
    by_cat = defaultdict(list)
    for (tid, rep), r in sorted(rows.items()):
        t = bank.get(tid)
        if not t or t["cat"] not in CATS:
            continue
        if r.get("gen", {}).get("request_seed") is None:
            continue
        by_cat[t["cat"]].append((tid, rep, r))
    pairs = []
    for c in sorted(by_cat):
        pairs += by_cat[c][:per_cat]
    return bank, pairs


def run_arm(arm, t, rep, gseed, msgs, out):
    calls = []
    answers = []

    def one(m, seed):
        r = call_api(m, 1024, seed)
        calls.append(r)
        answers.append(r["text"])
        return r

    one(msgs, gseed)
    c0, f0, n0 = score(t, answers[0])
    if arm == "S1_generic" and f0 == 0:
        m2 = msgs + [{"role": "assistant", "content": answers[0][:6000]},
                     {"role": "user", "content": "Repeat the task. Output ONLY the requested "
                      "format, no explanations."}]
        one(m2, gseed + 1)
    elif arm == "S2_min_gate" and f0 == 0:
        m2 = msgs + [{"role": "assistant", "content": answers[0][:6000]},
                     {"role": "user", "content": "FORMAT CHECK FAILED: %s. Fix the previous "
                      "answer and output only the requested format, no explanations." %
                      (";".join(n0) or "invalid format")}]
        one(m2, gseed + 1)
    elif arm == "S4_best_of_2":
        one(msgs, gseed + 1)
    best = None
    for a in answers:
        c, f, n = score(t, a)
        if c is None:
            continue
        if best is None or (c, f) > (best[0], best[1]):
            best = (c, f, n, a)
    if best is None:
        best = (None, None, ["scorer_error"], "")
    ptok = sum(x["ptok"] or 0 for x in calls)
    ctok = sum(x["ctok"] or 0 for x in calls)
    secs = sum(x["el"] for x in calls)
    row = {"arm": arm, "task": t["id"], "rep": rep, "cat": t["cat"], "kind": t["kind"],
           "calls": len(calls), "ptok": ptok, "ctok": ctok, "total_s": round(secs, 2),
           "content": best[0], "format_ok": best[1], "notes": best[2],
           "answer_sha256": hashlib.sha256(best[3].encode()).hexdigest()[:16],
           "answer": best[3][:4000],
           "engine_error": next((x["err"] for x in calls if x["err"]), None)}
    out.write(json.dumps(row, ensure_ascii=False) + "\n")
    out.flush()
    return row


def main():
    per_cat = 6
    if "--per-cat" in sys.argv:
        per_cat = int(sys.argv[sys.argv.index("--per-cat") + 1])
    smoke = "--smoke" in sys.argv
    bank, pairs = pick_pairs(per_cat)
    if smoke:
        pairs = pairs[:3]
    log("pairs selected: %d (categories %s)" % (len(pairs), CATS))
    os.makedirs(OUT, exist_ok=True)
    res = open(os.path.join(OUT, "baselines-results.jsonl"), "a", encoding="utf-8")
    done = set()
    pth = os.path.join(OUT, "baselines-results.jsonl")
    for ln in open(pth, encoding="utf-8", errors="ignore"):
        try:
            r = json.loads(ln)
            done.add((r["arm"], r["task"], r["rep"]))
        except Exception:
            pass
    t0 = time.time()
    n = 0
    for arm in ("S0_direct", "S1_generic", "S2_min_gate", "S4_best_of_2"):
        for tid, rep, v19row in pairs:
            if (arm, tid, rep) in done:
                continue
            t = bank[tid]
            gseed = v19row["gen"]["request_seed"]
            run_arm(arm, t, rep, gseed, msgs_for(t), res)
            n += 1
            if n % 10 == 0:
                log("%d/%d arms done, %.0f s" % (n, len(pairs) * 4, time.time() - t0))
    log("baselines finished: %d rows, %.0f s" % (n, time.time() - t0))


if __name__ == "__main__":
    main()
