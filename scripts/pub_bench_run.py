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
       PARB_ENGINE_NOTE  optional one-line string the launcher captures from the endpoint box
            at leg start (engine binary + args + config hash, read live over ssh, never typed
            from memory); stored verbatim in the leg's run-record and hashed into every row

Engine-build stamping (tooling release 2026-11-13, no contour feature, no published byte):
the 2026-11-08..11 local arms carry no serving-engine stamp at all — the endpoint box moved to
a new engine build and knob set on 2026-11-13 and the build those arms ran on is attributable
only from dated ops records (PUB-PLAN.md, 2026-11-13 comparability note). Every row now carries
`engine_sha256_16`: the SHA-256/16 of the `/health` body read from the SAME endpoint moments
before that row's call, so an engine swap mid-leg is visible per row, not only per leg. The
body carries service/model-alias/max_context/loaded — not the binary version or the RAM/VRAM
knobs (no /version endpoint exists), which is why the launcher note (PARB_ENGINE_NOTE) ships
beside it; hashed names use the SHA-256/16 label explicitly (this repo runs two hash
conventions). A leg also writes `run-record-<arm>.json` into its out dir BEFORE its first call.
"""
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request

TEMP = 0.7
# The pinned call budget is 1200 for the classic answer-graded sets. Long-form sets (IFEval) need
# a larger ceiling: measured on the endpoint 2026-11-09, a 1200-token budget returns
# finish_reason=length on 300-word tasks because the serve's default thinking state bills the chain
# of thought against the same budget, so a 1200-row IFEval arm would grade truncation as an
# instruction-following failure. PARB_MAX_TOKENS pins the budget per leg and the value is written
# into every row, so a row can never wear another leg's call label.
MAX_TOKENS = int(os.environ.get("PARB_MAX_TOKENS", "1200"))
AUTH_PREFIX = "Bearer"


def health_get(url):
    """One GET, raw bytes back. Separate seam so a contract test can drive swaps/failures."""
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.read()


def sha256_16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def split_api_url(url):
    """http://host:port/v1/chat/completions -> (scheme, host:port). The /health endpoint is a
    sibling of the chat path, never the chat path itself."""
    scheme, _, rest = url.partition("://")
    return scheme, rest.split("/", 1)[0]


def harness_git_sha():
    """Repo HEAD at leg start (pub-line twin of the hard bank's HARNESS_GIT_SHA attribution).
    Empty string is legal: a runner copy outside a git checkout must not die over metadata."""
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        p = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"],
                           capture_output=True, text=True, timeout=5)
        return p.stdout.strip() if p.returncode == 0 else ""
    except Exception:                                    # noqa: BLE001 - metadata, never fatal
        return ""


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

    # Engine identity for this leg, captured mechanically — never typed from memory
    # (the same reason the parb line pins endpoint URLs from the box's own profile).
    scheme, host_port = split_api_url(url)
    health_url = "%s://%s/health" % (scheme, host_port)
    note = os.environ.get("PARB_ENGINE_NOTE") or ""
    tasks_bytes = open(tasks, "rb").read()
    try:
        hb0 = health_get(health_url)
        h_err = None
    except Exception as exc:                             # noqa: BLE001 - record, do not hide
        hb0, h_err = None, "%s: %s" % (type(exc).__name__, str(exc)[:160])

    dst = os.path.join(out, "pub-%s.jsonl" % arm)
    os.makedirs(out, exist_ok=True)
    rr_path = os.path.join(out, "run-record-%s.json" % arm)
    if os.path.exists(rr_path):
        # A resume must not silently re-stamp the leg: the first record names the engine the
        # first attempt saw; a mid-arm engine swap stays visible per row (engine_sha256_16).
        rr = json.load(open(rr_path, encoding="utf-8"))
        rr.setdefault("resumes", []).append(time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        if hb0 is not None and rr.get("health_sha256_16") not in (None, sha256_16(hb0)):
            rr["resumed_health_changed"] = True
            print("WARNING: /health body differs from the original leg record "
                  "(%s -> %s); the engine changed mid-arm — row-level stamps attribute it"
                  % (rr.get("health_sha256_16"), sha256_16(hb0)), flush=True)
    else:
        rr = {"kind": "pub-bench-leg", "arm": arm, "model": model,
              "api_host": host_port, "health_url": health_url,
              "temp": TEMP, "max_tokens": MAX_TOKENS,
              "tasks_file": os.path.basename(tasks),
              "tasks_sha256_16": sha256_16(tasks_bytes),
              "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
              "harness_git_sha": harness_git_sha(),
              "engine_note_present": bool(note)}
        if hb0 is not None:
            rr["health_body"] = hb0.decode("utf-8", "replace")
            rr["health_sha256_16"] = sha256_16(hb0)
        else:
            rr["health_error"] = h_err
    if note:
        rr["engine_note"] = note
        rr["engine_note_sha256_16"] = sha256_16(note.encode("utf-8"))
    with open(rr_path, "w", encoding="utf-8") as rf:
        json.dump(rr, rf, ensure_ascii=False, sort_keys=True)
        rf.write("\n")
    print("leg record: %s engine_health_sha256_16=%s note=%s"
          % (rr_path, rr.get("health_sha256_16", "n/a"),
           rr.get("engine_note_sha256_16", "none")), flush=True)

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
            # Engine identity moments before this row's call: a mid-leg engine swap (measured
            # 2026-11-13 on this endpoint: ops config edit 11:21, keep-up restart 11:24:01)
            # must be attributable per row, not only per leg. A failed health read never fails
            # the row — the answer verdict stays, the stamp reports the gap.
            try:
                rec["engine_sha256_16"] = sha256_16(health_get(health_url))
            except Exception as hexc:                    # noqa: BLE001 - stamp, never decide
                rec["engine_sha256_16"] = None
                rec["engine_health_error"] = "%s: %s" % (type(hexc).__name__, str(hexc)[:120])
            st = time.time()
            try:
                r = api_call(url, key, model, t["prompt"])
                ch = (r.get("choices") or [{}])[0]
                rec["answer"] = (ch.get("message") or {}).get("content") or ""
                rec["finish"] = "ok" if rec["answer"].strip() else "empty"
                # The engine's own stop reason: `length` means the answer was cut at the pinned
                # budget, which is a request-shape cost that must be counted, not folded into a
                # model verdict. Older rows lack this field; a report must say so.
                rec["api_finish"] = ch.get("finish_reason")
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
