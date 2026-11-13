#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for the engine-build stamping in `scripts/pub_bench_run.py` (2026-11-13).

Why this exists: the 2026-11-08..11 local PUB arms carry no serving-engine stamp, and the
endpoint box moved to a new engine build and knob set on 2026-11-13 (ops records only). The
runner now hashes the endpoint's /health body next to every row and writes a leg run-record
before the first call. This test drives the REAL main() with a stubbed transport (zero
network, zero model calls) and pins:

  1. every row carries engine_sha256_16, and the value is the SHA-256/16 of the exact bytes
     the seam returned at that moment (non-vacuity: computed directly in this test);
  2. a mid-leg /health change moves the row stamp while the leg's run-record keeps naming
     the engine the leg STARTED on;
  3. a /health failure on one row never fails that row (answer and finish stay ok) but
     records engine_health_error and a null stamp;
  4. the run-record names model, api_host (the netloc of PARB_API, never the chat path),
     temp, max_tokens, the SHA-256/16 of the pinned task file, harness_git_sha, and the
     verbatim PARB_ENGINE_NOTE plus its hash;
  5. a resume does not re-stamp the leg: started_at survives, a resumes list grows, and a
     leg whose start /health differs from the stored one prints a loud WARNING and sets
     resumed_health_changed;
  6. the pre-existing row schema (id/bench/arm/model/temp/max_tokens/answer/finish/
     api_finish/ptok/ctok/seconds/task_sha16) is untouched — the stamp is an additive field.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RUNNER = os.path.join(ROOT, "scripts", "pub_bench_run.py")

CHECKS = 0
FAILED = []


def ck(cond: bool, msg: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(msg)


def sha16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def load_runner():
    spec = importlib.util.spec_from_file_location("pub_bench_run", RUNNER)
    if spec is None or spec.loader is None:
        raise SystemExit("cannot load the runner under test: " + RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.__file__ == RUNNER, "the runner under test must be the repo file"
    return mod


HEALTH_A = (b'{"status": "ok", "max_context": 262144, "model": "m-alias", '
            b'"images": true, "api_key": true, "loaded": true, "loading": false, '
            b'"service": "basalt", "percent": null, "swap": null}')
HEALTH_B = (b'{"status": "ok", "max_context": 131072, "model": "m-alias", '
            b'"images": true, "api_key": true, "loaded": true, "loading": false, '
            b'"service": "basalt", "percent": null, "swap": null}')


class HealthScript:
    """Deterministic /health seam: serves queued bodies; 'boom' raises."""

    def __init__(self, bodies):
        self.bodies = list(bodies)
        self.calls = 0

    def __call__(self, url):
        self.calls += 1
        item = self.bodies.pop(0) if self.bodies else self.bodies_default()
        if item == "boom":
            raise OSError("connection refused")
        return item

    def bodies_default(self):
        return HEALTH_A


def ok_chat(url, key, model, prompt):
    return {"choices": [{"message": {"content": "ANSWER: 42"},
                         "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3}}


def make_ws(tmp: str) -> str:
    tasks = os.path.join(tmp, "bench.tasks.jsonl")
    with open(tasks, "w", encoding="utf-8") as fh:
        for i in range(3):
            fh.write(json.dumps({"id": "t-%02d" % i, "bench": "dummybench",
                                 "prompt": "q%d" % i}) + "\n")
    kf = os.path.join(tmp, "key.json")
    with open(kf, "w", encoding="utf-8") as fh:
        json.dump({"api_key": "sekret"}, fh)
    return tasks


def run_leg(mod, tasks, out, health_script, note=None):
    env = {"PARB_API": "http://endpoint.invalid:8080/v1/chat/completions",
           "PARB_KEY_FILE": os.path.join(os.path.dirname(tasks), "key.json"),
           "PARB_MODEL": "m-alias",
           "PUB_OUT": out}
    saved = {k: os.environ.get(k) for k in list(env) + ["PARB_ENGINE_NOTE"]}
    os.environ.update(env)
    if note is not None:
        os.environ["PARB_ENGINE_NOTE"] = note
    else:
        os.environ.pop("PARB_ENGINE_NOTE", None)
    mod.health_get = health_script
    mod.api_call = ok_chat
    argv_saved = list(sys.argv)
    sys.argv = ["pub_bench_run.py", tasks, "stamp-test"]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = mod.main()
    finally:
        sys.argv = argv_saved
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return rc, buf.getvalue()


def rows_of(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def main() -> int:
    mod = load_runner()

    # 0. pure seams
    ck(mod.split_api_url("http://h:8080/v1/chat/completions") == ("http", "h:8080"),
       "split_api_url must return scheme + netloc")
    ck(mod.split_api_url("https://box.lan/v1/chat/completions") == ("https", "box.lan"),
       "split_api_url without a port must keep the host")

    with tempfile.TemporaryDirectory() as tmp:
        tasks = make_ws(tmp)
        out = os.path.join(tmp, "out")
        note = "/opt/engine/bin/engine --serve --resident-budget-gib 42 --cfg-sha abc123"

        # 1-2. healthy leg, /health changes before the LAST row
        hs = HealthScript([HEALTH_A, HEALTH_A, HEALTH_A, HEALTH_B])
        rc, out_text = run_leg(mod, tasks, out, hs, note=note)
        ck(rc == 0, "a healthy leg must exit 0, got %s (%s)" % (rc, out_text[-300:]))
        rows = rows_of(os.path.join(out, "pub-stamp-test.jsonl"))
        ck(len(rows) == 3, "three rows expected, got %d" % len(rows))
        ck(all("engine_sha256_16" in r for r in rows), "every row must carry the stamp")
        ck([r["engine_sha256_16"] for r in rows] == [sha16(HEALTH_A)] * 2 + [sha16(HEALTH_B)],
           "row stamps must be the SHA-256/16 of the exact bytes at that moment: %s"
           % [r["engine_sha256_16"] for r in rows])
        ck(hs.calls == 4, "one leg-start read + one per row expected, got %d" % hs.calls)

        rr = json.load(open(os.path.join(out, "run-record-stamp-test.json"), encoding="utf-8"))
        ck(rr["kind"] == "pub-bench-leg" and rr["arm"] == "stamp-test",
           "run-record must name kind/arm")
        ck(rr["api_host"] == "endpoint.invalid:8080",
           "api_host is the netloc, never the chat path: %s" % rr.get("api_host"))
        ck(rr["health_url"] == "http://endpoint.invalid:8080/health",
           "the health URL is a sibling of the chat path: %s" % rr.get("health_url"))
        ck(rr["health_sha256_16"] == sha16(HEALTH_A),
           "the leg record names the engine the leg STARTED on")
        ck(rr["health_body"] == HEALTH_A.decode(), "the raw /health body must ship")
        ck(rr["tasks_sha256_16"] == sha16(open(tasks, "rb").read()),
           "run-record must pin the task-file bytes with the SHA-256/16 label")
        ck(rr["temp"] == mod.TEMP and rr["max_tokens"] == mod.MAX_TOKENS,
           "call parameters must be in the record")
        ck(rr["engine_note"] == note and rr["engine_note_sha256_16"] == sha16(note.encode()),
           "PARB_ENGINE_NOTE must be stored verbatim AND hashed")
        ck(len(rr.get("harness_git_sha", "")) in (0, 40),
           "harness_git_sha is 40 hex or empty, never garbage: %r" % rr.get("harness_git_sha"))
        started_at = rr["started_at"]

        # 6. the pre-existing row schema survived
        r0 = rows[0]
        for field in ("id", "bench", "arm", "model", "temp", "max_tokens", "answer",
                      "finish", "api_finish", "ptok", "ctok", "seconds", "task_sha16"):
            ck(field in r0, "row schema lost field %r" % field)
        ck(r0["finish"] == "ok" and r0["api_finish"] == "stop",
           "answer plumbing must be untouched by the stamp")

        # 5. resume: started_at survives, resumes grows; a start-health change warns loudly
        hs2 = HealthScript([HEALTH_B, HEALTH_A, HEALTH_A, HEALTH_A])
        rc, out_text = run_leg(mod, tasks, out, hs2, note=note)
        ck(rc == 0, "a resume leg must exit 0")
        rr = json.load(open(os.path.join(out, "run-record-stamp-test.json"), encoding="utf-8"))
        ck(rr["started_at"] == started_at, "a resume must not re-stamp started_at")
        ck(rr.get("resumes") and len(rr["resumes"]) == 1, "the resume list must grow")
        ck(rr.get("resumed_health_changed") is True,
           "a resume onto a different engine must set resumed_health_changed")
        ck("WARNING" in out_text and "engine changed mid-arm" in out_text,
           "the engine swap on resume must be loud: %s" % out_text[-300:])

    with tempfile.TemporaryDirectory() as tmp:
        tasks = make_ws(tmp)
        out = os.path.join(tmp, "out2")

        # 3. a /health failure on one row: row stays ok, stamp reports the gap
        hs3 = HealthScript([HEALTH_A, HEALTH_A, "boom", HEALTH_A])
        rc, out_text = run_leg(mod, tasks, out, hs3)
        ck(rc == 0, "a health gap must not fail the leg")
        rows = rows_of(os.path.join(out, "pub-stamp-test.jsonl"))
        ck(len(rows) == 3 and all(r["finish"] == "ok" for r in rows),
           "the answer verdicts must survive a health gap")
        ck(rows[1]["engine_sha256_16"] is None
           and "connection refused" in rows[1].get("engine_health_error", ""),
           "the failed row must carry a null stamp + the error text: %s" % rows[1])
        ck("engine_health_error" not in rows[0], "a healthy row must not carry an error field")
        rr3 = json.load(open(os.path.join(out, "run-record-stamp-test.json"), encoding="utf-8"))
        ck(rr3.get("engine_note_present") is False,
           "engine_note_present must be recorded False when no note was supplied")

        # 4. a dead /health at leg start: record reports health_error, leg still runs
        out3 = os.path.join(tmp, "out3")
        hs4 = HealthScript(["boom", HEALTH_A, HEALTH_A, HEALTH_A])
        rc, out_text = run_leg(mod, tasks, out3, hs4)
        rr = json.load(open(os.path.join(out3, "run-record-stamp-test.json"), encoding="utf-8"))
        ck(rc == 0 and "health_error" in rr and "health_body" not in rr,
           "a leg started against a dead /health must record the gap, not die")
        ck(all(r["engine_sha256_16"] == sha16(HEALTH_A)
               for r in rows_of(os.path.join(out3, "pub-stamp-test.jsonl"))),
           "rows after a dead leg-start read must still be stamped")

    print("pub_bench_run engine-stamp contract: %d checks, %d failure(s)" % (CHECKS, len(FAILED)))
    for m in FAILED:
        print("FAIL: %s" % m)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
