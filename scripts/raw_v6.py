#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Raw (bare-model) arm runner for HARD v6 bank. One shot per task, no contour,
no fixers, one transport retry. Loop-protocol D tasks are NOT applicable to
single-shot arms: skipped and scored N/A (documented in run-record).
Arms: basalt (direct HTTP, temp 0.7, seeded), codex (subscription CLI, xhigh),
grok (xai-oauth via hermes -z). Scorers applied afterwards by score_v6.py.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.expanduser(os.environ.get("PARB_RAW_WS", "~/parb-v61-raw"))
bank = json.load(open(os.path.join(ROOT, "bank.json")))
brain = sys.argv[1]
REPS = [int(x) for x in (sys.argv[2].split(",") if len(sys.argv) > 2 else ["0"])]
out = os.path.join(ROOT, "answers-%s.jsonl" % brain)
done = set()
if os.path.exists(out):
    for l in open(out):
        r = json.loads(l)
        done.add((r["task"], r.get("rep", 0)))

def one(task, rep):
    p = task["prompt"]
    if brain == "basalt":
        key = json.load(open(os.path.join(ROOT, "p2005-profile.json")))["api_key"]
        body = {"model": "qwen3.8-flash-next-iq3_s-basalt",
                "messages": [{"role": "user", "content": p}],
                "temperature": 0.7, "max_tokens": 4096, "seed": 1000 + rep}
        url = os.environ.get("PARB_BASALT_CHAT_URL")
        if not url:
            raise SystemExit(
                "PARB_BASALT_CHAT_URL is unset; set it to the basalt OpenAI-compatible "
                "chat completions endpoint URL (scheme://host:port/v1/chat/completions)")
        req = urllib.request.Request(url,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer" + " " + key})
        d = json.loads(urllib.request.urlopen(req, timeout=600).read().decode())
        ch = d["choices"][0]
        u = d.get("usage", {})
        return ch["message"].get("content") or "", ch.get("finish_reason", "?"), u.get("completion_tokens", 0), ""
    if brain == "codex":
        f = os.path.join(ROOT, ".last-%s.txt" % brain)
        cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "read-only",
               "-c", "model_reasoning_effort=xhigh", "-m", "gpt-6.1-sol",
               "--output-last-message", f, "-"]
        r = subprocess.run(cmd, input=p, capture_output=True, text=True, timeout=900, cwd=ROOT)
        txt = open(f).read() if os.path.exists(f) else ""
        return txt.strip(), ("ok" if r.returncode == 0 and txt else "rc%d" % r.returncode), 0, (r.stderr or "")[:300]
    if brain == "grok":
        # finding S3 from the v6 series: the @file transport left the model able to reach
        # file tools. Raw arms run with toolsets disabled and the prompt inline, so the
        # transport cannot touch the workspace at all.
        r = subprocess.run(["hermes", "-z", p, "-m", "grok-4.7",
                            "--provider", "xai-oauth", "-t", ""],
                           capture_output=True, text=True, timeout=900, cwd=ROOT)
        return r.stdout.strip(), ("ok" if r.returncode == 0 else "rc%d" % r.returncode), 0, (r.stderr or "")[:300]
    raise SystemExit("unknown brain")

# Provenance gap found on the v6.1 four-arm: raw answer rows carried no model identity, so a
# score change between bank versions could not be attributed to the bank or to a model update.
# Every row now records the model id (and CLI version where the transport exposes it).
def _cli_version(prog: str) -> str:
    """Transport version for provenance. Must never be fatal: a bare `import raw_v6` (or a
    basalt-only run on a host where the codex CLI is not on PATH) used to die here."""
    path = shutil.which(prog)
    if not path:
        return "not installed"
    try:
        out = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=30)
        return (out.stdout or out.stderr or "").strip().splitlines()[0] if (out.stdout or out.stderr) else "unknown"
    except Exception as exc:
        return "unknown (%s)" % type(exc).__name__


PROV = {"basalt": {"model": "qwen3.8-flash-next-iq3_s-basalt", "cli": "direct HTTP temp 0.7"},
        "codex": {"model": "gpt-6.1-sol", "cli": "codex " + _cli_version("codex")},
        "grok": {"model": "grok-4.7", "cli": "hermes " + _cli_version("hermes") + " toolsets off"}}


BANK_SHA = hashlib.sha256(open(os.path.join(ROOT, "bank.json"), "rb").read()).hexdigest()[:16]


skipped = 0
# cadence-255 lesson: the grok leg lost 186/213 rows to an expired xai-oauth token that
# only healed mid-leg; every dead call still wrote a row (the done-set then skips those
# seeds forever) and stderr was thrown away. Transport failure with an empty answer
# repeated this many times in a row = abort the leg instead of burning the window.
CONSEC_TRANSPORT_FAILS = 5
for t in bank:
    if t["cat"] == "D" and t.get("mode") == "loop":
        skipped += 1
        continue
    for rep in REPS:
        if (t["id"], rep) in done:
            continue
        t0 = time.time()
        ans, fin, toks, err = "", "err", 0, ""
        for attempt in range(2):
            try:
                ans, fin, toks, err = one(t, rep)
                if ans:
                    break
            except Exception as e:
                fin = type(e).__name__
                err = (err or "")[:300]
                time.sleep(5)
        row = {"task": t["id"], "rep": rep, "cat": t["cat"], "answer": ans,
               "finish": fin, "seconds": round(time.time() - t0, 1),
               "arm": brain, "mode": "strict_plain",
               "model": PROV[brain]["model"], "cli": PROV[brain]["cli"],
               "bank_sha16": BANK_SHA}
        if err:
            row["err"] = err
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(t["id"], fin, row["seconds"], "s", flush=True)
        if ans:
            CONSEC_TRANSPORT_FAILS = 0
        else:
            CONSEC_TRANSPORT_FAILS += 1
            if CONSEC_TRANSPORT_FAILS >= 5:
                print("ABORT: 5 consecutive empty answers (transport dead); last finish=%s err=%r"
                      % (fin, err[:200]), flush=True)
                raise SystemExit(3)
print("done; loop tasks skipped:", skipped)
