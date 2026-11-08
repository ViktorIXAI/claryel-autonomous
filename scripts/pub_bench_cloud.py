#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run a public-benchmark arm through the cloud CLI transports (codex, grok).

Transports are the ones proven on the hard bank (raw_v6.py): codex = subscription CLI,
reasoning xhigh, read-only sandbox, prompt through STDIN; grok = hermes one-shot with toolsets
disabled and the prompt inline, so the transport cannot reach the workspace. Same rule as
pub_bench_run.py: answers are stored as bytes, the row names model + CLI version, the run is
resumable by task id, and a leg whose transport is broken stops instead of scoring blanks.

Usage: pub_bench_cloud.py <tasks.jsonl> codex|grok [--limit N] [--offset N] [--out DIR]
"""
import json
import os
import subprocess
import sys
import time

OUT_DEFAULT = os.environ.get("PUB_OUT", os.path.expanduser("~/pub-bench"))


def cli_version(prog):
    try:
        r = subprocess.run([prog, "--version"], capture_output=True, text=True, timeout=30)
        return (r.stdout or r.stderr).strip().splitlines()[0][:60] if (r.stdout or r.stderr) else "?"
    except Exception:                                     # noqa: BLE001 - provenance is not fatal
        return "?"


def ask(arm, prompt, cwd):
    if arm == "codex":
        last = os.path.join(cwd, ".last-pub-codex.txt")
        cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "read-only",
               "-c", "model_reasoning_effort=xhigh", "-m", "gpt-6.1-sol",
               "--output-last-message", last, "-"]
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                           timeout=900, cwd=cwd)
        txt = open(last, encoding="utf-8").read() if os.path.exists(last) else ""
        return txt.strip(), ("ok" if r.returncode == 0 and txt.strip() else "rc%d" % r.returncode), \
            (r.stderr or "")[:300]
    if arm == "grok":
        r = subprocess.run(["hermes", "-z", prompt, "-m", "grok-4.7",
                            "--provider", "xai-oauth", "-t", ""],
                           capture_output=True, text=True, timeout=900, cwd=cwd)
        return r.stdout.strip(), ("ok" if r.returncode == 0 and r.stdout.strip() else "rc%d" % r.returncode), \
            (r.stderr or "")[:300]
    raise SystemExit("unknown cloud arm: " + arm)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    tasks_f, arm = sys.argv[1], sys.argv[2]
    limit, offset, out = None, 0, OUT_DEFAULT
    rest = sys.argv[3:]
    for i, a in enumerate(rest):
        if a == "--limit":
            limit = int(rest[i + 1])
        elif a == "--offset":
            offset = int(rest[i + 1])
        elif a == "--out":
            out = rest[i + 1]
    os.makedirs(out, exist_ok=True)
    prov = {"codex": {"model": "gpt-6.1-sol", "cli": "codex " + cli_version("codex")},
            "grok": {"model": "grok-4.7", "cli": "hermes " + cli_version("hermes") + " toolsets off"}}[arm]

    dst = os.path.join(out, "pub-%s.jsonl" % arm)
    done = set()
    if os.path.exists(dst):
        for line in open(dst, encoding="utf-8"):
            d = json.loads(line)
            if d.get("finish") == "ok":
                done.add(d["id"])
    all_tasks = [json.loads(l) for l in open(tasks_f, encoding="utf-8") if l.strip()]
    rows = all_tasks[offset:offset + limit] if limit else all_tasks[offset:]

    t0, n_ok, n_bad, consec_bad = time.time(), 0, 0, 0
    with open(dst, "a", encoding="utf-8") as fh:
        for i, t in enumerate(rows):
            if t["id"] in done:
                continue
            rec = {"id": t["id"], "bench": t["bench"], "arm": arm, "model": prov["model"],
                   "transport": prov["cli"]}
            st = time.time()
            try:
                ans, fin, err = ask(arm, t["prompt"], out)
            except Exception as exc:                      # noqa: BLE001 - store, do not hide
                ans, fin, err = "", "error", "%s: %s" % (type(exc).__name__, str(exc)[:200])
            rec["answer"], rec["finish"], rec["seconds"] = ans, fin, round(time.time() - st, 2)
            if fin != "ok":
                rec["engine_error"] = err
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if fin == "ok":
                n_ok += 1
                consec_bad = 0
            else:
                n_bad += 1
                consec_bad += 1
                # cadence-255 lesson: an expired oauth token produced 186 blank rows before
                # anyone noticed. Three consecutive transport failures stop the leg.
                if consec_bad >= 3:
                    print("%s: transport dead (%s) after %d ok rows - stopping leg"
                          % (arm, err[:120], n_ok), flush=True)
                    return 1
            if (i + 1) % 20 == 0:
                rate = (i + 1) / (time.time() - t0)
                print("%s %d/%d ok=%d bad=%d elapsed %.0f s (%.1f s/task) eta %.0f min"
                      % (arm, i + 1, len(rows), n_ok, n_bad, time.time() - t0,
                         (time.time() - t0) / (i + 1),
                         (len(rows) - i - 1) / rate / 60), flush=True)
    print("%s done: ok=%d bad=%d wall %.0f s -> %s" % (arm, n_ok, n_bad, time.time() - t0, dst))
    return 0 if n_ok else 1


if __name__ == "__main__":
    sys.exit(main())
