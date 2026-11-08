#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run one arm of a public benchmark against an OpenAI-compatible endpoint.

Same discipline as the hard-bank arms: the model call is pinned (temperature, max_tokens),
answers are stored as bytes (so a scorer fix never forces a paid re-run), the run is resumable
by task id, and the record names the endpoint model + task-file sha16 so percent rows are
attributable.

Usage: pub_bench_run.py <tasks.jsonl> <arm> [--limit N] [--offset N] [--out DIR]
Env:   PARB_API  http://<host>:<port>/v1/chat/completions
       PARB_KEY_FILE  json file holding {"api_key": ...}
       PARB_MODEL     served model alias (required or the endpoint 404s)
"""
import json
import os
import sys
import time
import urllib.request

TEMP = 0.7
MAX_TOKENS = 1200
AUTH_PREFIX = "Bearer"


def api_call(url, key, model, prompt):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": TEMP, "max_tokens": MAX_TOKENS}).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": AUTH_PREFIX + " " + key})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    tasks, arm = sys.argv[1], sys.argv[2]
    limit, offset, out = None, 0, os.environ.get("PUB_OUT", os.path.dirname(os.path.abspath(tasks)))
    args = sys.argv[3:]
    for i, a in enumerate(args):
        if a == "--limit":
            limit = int(args[i + 1])
        elif a == "--offset":
            offset = int(args[i + 1])
        elif a == "--out":
            out = args[i + 1]
    url = os.environ.get("PARB_API")
    key_file = os.environ.get("PARB_KEY_FILE")
    model = os.environ.get("PARB_MODEL")
    if not (url and key_file and model):
        raise SystemExit("PARB_API, PARB_KEY_FILE and PARB_MODEL are required "
                         "(no default endpoint on purpose)")
    key = json.load(open(key_file, encoding="utf-8"))["api_key"]

    dst = os.path.join(out, "pub-%s.jsonl" % arm)
    done = set()
    if os.path.exists(dst):
        for line in open(dst, encoding="utf-8"):
            d = json.loads(line)
            if d.get("finish") == "ok":
                done.add(d["id"])
    rows = [json.loads(l) for l in open(tasks, encoding="utf-8") if l.strip()][offset:]
    if limit:
        rows = rows[:limit]

    t0 = time.time()
    n_ok = n_bad = 0
    with open(dst, "a", encoding="utf-8") as fh:
        for i, t in enumerate(rows):
            if t["id"] in done:
                continue
            rec = {"id": t["id"], "bench": t["bench"], "arm": arm, "model": model,
                   "temp": TEMP, "max_tokens": MAX_TOKENS}
            st = time.time()
            try:
                r = api_call(url, key, model, t["prompt"])
                ch = (r.get("choices") or [{}])[0]
                rec["answer"] = (ch.get("message") or {}).get("content") or ""
                rec["finish"] = "ok" if rec["answer"].strip() else "empty"
                u = r.get("usage") or {}
                rec["ptok"], rec["ctok"] = u.get("prompt_tokens"), u.get("completion_tokens")
            except Exception as exc:                      # noqa: BLE001 - store, do not hide
                rec["answer"], rec["finish"] = "", "error"
                rec["engine_error"] = "%s: %s" % (type(exc).__name__, str(exc)[:160])
            rec["seconds"] = round(time.time() - st, 2)
            rec["task_sha16"] = t.get("id")
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if rec["finish"] == "ok":
                n_ok += 1
            else:
                n_bad += 1
            if (i + 1) % 25 == 0:
                rate = (i + 1) / (time.time() - t0)
                eta = (len(rows) - i - 1) / max(rate, 0.01)
                print("%s %d/%d ok=%d bad=%d %.2f task/s eta %.0f s"
                      % (arm, i + 1, len(rows), n_ok, n_bad, rate, eta), flush=True)
    print("%s done: ok=%d bad=%d wall %.0f s -> %s" % (arm, n_ok, n_bad, time.time() - t0, dst))
    if n_bad and not n_ok:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
