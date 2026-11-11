#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for `scripts/pub_grok_resume_check.py` (added 2026-11-11).

Runs hermetic fixtures in a temp dir with `PUB_MANIFEST_OVERRIDE` pointing at a fixture
`MANIFEST.json`, so it never reads the real partial answer files and makes no network call.

What it pins:

  1. a healthy partial returns READY (exit 0) and prints the resume set;
  2. the gate is not vacuous — each tamper class returns NO-GO (exit 3) on its own:
     a stored-answer byte change (file SHA drift), a duplicate id parked in the arm file,
     a non-`ok` row parked in the arm file, an `ok` row with an empty answer, a resume set
     that no longer matches the pin, a pin whose tasks cell is wrong, and a pin whose
     pinned task count is wrong;
  3. progress is legal: a legitimate new stored row with the pin regenerated to match
     returns READY, while the same row with the pin left stale returns NO-GO (the gate
     tracks the resume point, it does not freeze one moment forever);
  4. a completed set (every pinned id stored, remaining 0) returns READY;
  5. input gaps exit 1, never READY: an expected answer file missing, a queue entry with
     no arm record, a missing pin file, a malformed `--as-of` (compact `20261113` or a
     calendar-invalid `2026-02-30` — the window mode is a string compare, and a compact
     date always compares greater than the ISO `suspended_until`, which would silently
     report a closed window as OPEN), and a pin whose `suspended_until` is not ISO —
     while a well-formed ISO `--as-of` still decides both window states correctly;
  6. the MANIFEST pin guard is wired: a task file whose bytes moved is refused with exit 2
     and the published guard text (no second hash identity for one pinned file).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "scripts", "pub_grok_resume_check.py")

CHECKS = 0
FAILED = []


def ck(cond: bool, msg: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(msg)


def sha16(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def row(i: int, answer: str = "42", finish: str = "ok") -> dict:
    return {"id": "t-%03d" % i, "answer": answer, "finish": finish, "model": "fixture"}


class Fixture:
    """A tiny repo + workspace pair with one bench of `n` tasks and `stored` rows."""

    def __init__(self, tmp: str, n: int = 3, stored: int = 2, bench: str = "demo-bench"):
        self.tmp = tmp
        self.bench = bench
        self.repo = os.path.join(tmp, "repo")
        self.pub = os.path.join(self.repo, "benchmarks", "public")
        self.ws = os.path.join(tmp, "ws")
        os.makedirs(os.path.join(self.pub), exist_ok=True)
        os.makedirs(os.path.join(self.ws, bench), exist_ok=True)
        tasks = b"".join((json.dumps({"id": "t-%03d" % i, "q": i}) + "\n").encode()
                         for i in range(n))
        self.tasks_path = os.path.join(self.pub, "%s.tasks.jsonl" % bench)
        with open(self.tasks_path, "wb") as fh:
            fh.write(tasks)
        manifest = {"benches": {bench: {"tasks_sha16": sha16(tasks),
                                        "tasks_sha256_16": sha16(tasks)}}}
        self.manifest = os.path.join(self.pub, "MANIFEST.json")
        with open(self.manifest, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh)
        self.arm = os.path.join(self.ws, bench, "pub-grok.jsonl")
        self.rows = [row(i) for i in range(stored)]
        self.write_arm()
        self.n = n

    def write_arm(self) -> None:
        with open(self.arm, "w", encoding="utf-8") as fh:
            for r in self.rows:
                fh.write(json.dumps(r) + "\n")

    def derived(self) -> dict:
        rows = [json.loads(l) for l in open(self.arm, encoding="utf-8") if l.strip()]
        ok = [r for r in rows if r.get("finish") == "ok"]
        order = ["t-%03d" % i for i in range(self.n)]
        remaining = [i for i in order if i not in {r["id"] for r in ok}]
        return {
            "expected_rows": len(rows),
            "expected_unique": len({r["id"] for r in rows}),
            "expected_ok": len(ok),
            "expected_empty": sum(1 for r in ok if not (r.get("answer") or "").strip()),
            "answer_file_sha256_16": sha16(open(self.arm, "rb").read()),
            "pinned_ok_ids": sorted(r["id"] for r in rows if r.get("finish") == "ok"),
            "expected_remaining": len(remaining),
            "expected_first_remaining": remaining[0] if remaining else None,
            "expected_last_remaining": remaining[-1] if remaining else None,
        }

    def make_pin(self, **over) -> str:
        d = {"expected_tasks_cell": sha16(open(self.tasks_path, "rb").read()),
             "expected_pinned_tasks": self.n,
             "answer_file": "%s/pub-grok.jsonl" % self.bench,
             "status": "fixture"}
        d.update(self.derived())
        d.update(over)
        pin = {"schema": "grok-resume-pin-v1", "as_of": "fixture",
               "owner_window": {"suspended_until": "2026-11-12"},
               "queue_order": [self.bench], "arms": {self.bench: d}}
        path = os.path.join(self.pub, "GROK-RESUME-PIN.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(pin, fh, indent=2)
        return path

    def run(self, pin: str) -> tuple[int, str]:
        env = dict(os.environ, PUB_MANIFEST_OVERRIDE=self.manifest)
        p = subprocess.run([sys.executable, SCRIPT, "--pin", pin, "--ws", self.ws,
                            "--repo", self.repo],
                           capture_output=True, text=True, env=env, timeout=120)
        return p.returncode, p.stdout + p.stderr


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="grok-resume-test-")

    # 1. healthy: two of three ids stored, pin derived from the same bytes
    f = Fixture(tmp)
    rc, out = f.run(f.make_pin())
    ck(rc == 0, "healthy fixture must be READY, got exit %d: %s" % (rc, out[-300:]))
    ck("RESUME GATE: READY" in out, "healthy fixture must print READY: %s" % out[-300:])
    ck("resume set    1 ids t-002..t-002" in out,
       "healthy fixture must print the derived resume set: %s" % out[-500:])

    # 2. byte drift in a stored answer (the identity trap): pin from the ORIGINAL bytes
    f2 = Fixture(os.path.join(tmp, "b2"))
    pin2 = f2.make_pin()
    f2.rows[0]["answer"] = "43"
    f2.write_arm()
    rc, out = f2.run(pin2)
    ck(rc == 3 and "SHA-256/16" in out, "answer byte drift must be NO-GO (exit 3): %s" % out[-300:])

    # 3. duplicate id parked in the arm file (scorer keeps the FIRST row per id)
    f3 = Fixture(os.path.join(tmp, "b3"))
    pin3 = f3.make_pin()
    f3.rows.append(row(0, answer="7"))
    f3.write_arm()
    rc, out = f3.run(pin3)
    ck(rc == 3 and "duplicate ids" in out, "duplicate id must be NO-GO: %s" % out[-300:])

    # 4. non-ok row parked in the arm file (a parked blank is scored forever)
    f4 = Fixture(os.path.join(tmp, "b4"))
    pin4 = f4.make_pin()
    f4.rows.append(row(2, answer="", finish="timeout"))
    f4.write_arm()
    rc, out = f4.run(pin4)
    ck(rc == 3 and "non-ok rows parked" in out, "parked non-ok row must be NO-GO: %s" % out[-300:])

    # 5. ok row with an empty answer
    f5 = Fixture(os.path.join(tmp, "b5"))
    pin5 = f5.make_pin()
    f5.rows[1]["answer"] = "   "
    f5.write_arm()
    rc, out = f5.run(pin5)
    ck(rc == 3 and "empty answer" in out, "empty ok answer must be NO-GO: %s" % out[-300:])

    # 6/3. progress: inside the CLOSED window any growth is an uncredited write; once the
    # window is OPEN the same growth is legal progress over the pinned floor.
    f6 = Fixture(os.path.join(tmp, "b6"))
    stale = json.load(open(f6.make_pin(), encoding="utf-8"))
    f6.rows.append(row(2))
    f6.write_arm()
    rc, out = f6.run(_write(tmp, "stale-pin.json", stale))
    ck(rc == 3 and "INSIDE the closed owner window" in out,
       "growth inside the closed window must be NO-GO (the 2026-11-11 05:31 class): %s" % out[-400:])
    rc, out = f6.run(f6.make_pin())
    ck(rc == 0, "the same progress with the pin regenerated must be READY: %s" % out[-300:])
    # the same stale pin, judged one day later, is legal progress and must not halt a queue
    env = dict(os.environ, PUB_MANIFEST_OVERRIDE=f6.manifest)
    p = subprocess.run([sys.executable, SCRIPT, "--pin", _write(tmp, "stale-pin2.json", stale),
                        "--ws", f6.ws, "--repo", f6.repo, "--as-of", "2026-11-13"],
                       capture_output=True, text=True, env=env, timeout=120)
    ck(p.returncode == 0 and "progress:" in (p.stdout + p.stderr)
       and "window is OPEN" in (p.stdout + p.stderr),
       "growth with the window open must be READY plus a progress note: %s"
       % (p.stdout + p.stderr)[-400:])
    # and in that open state, a pinned stored row that vanished is still a finding
    f6.rows = f6.rows[:1]
    f6.write_arm()
    p = subprocess.run([sys.executable, SCRIPT, "--pin", _write(tmp, "stale-pin3.json", stale),
                        "--ws", f6.ws, "--repo", f6.repo, "--as-of", "2026-11-13"],
                       capture_output=True, text=True, env=env, timeout=120)
    ck(p.returncode == 3 and "GONE from the arm file" in (p.stdout + p.stderr),
       "a pinned ok row that vanished must be NO-GO even with the window open: %s"
       % (p.stdout + p.stderr)[-400:])

    # 4/3. completed set
    f7 = Fixture(os.path.join(tmp, "b7"), stored=3)
    rc, out = f7.run(f7.make_pin())
    ck(rc == 0 and "resume set    0 ids" in out, "a completed set must be READY: %s" % out[-300:])

    # 5. input gaps: expected answer file missing / queue entry without an arm / no pin
    f8 = Fixture(os.path.join(tmp, "b8"))
    pin8 = f8.make_pin()
    os.remove(f8.arm)
    rc, out = f8.run(pin8)
    ck(rc == 1 and "INPUT GAP" in out, "missing expected answer file must be INPUT GAP: %s" % out[-300:])

    f9 = Fixture(os.path.join(tmp, "b9"))
    p9 = json.load(open(f9.make_pin(), encoding="utf-8"))
    p9["queue_order"].append("ghost-bench")
    rc, out = f9.run(_write(tmp, "gap-pin.json", p9))
    ck(rc == 1 and "no arm record" in out, "queue entry with no arm record must be INPUT GAP: %s" % out[-300:])

    rc, out = f9.run(os.path.join(tmp, "no-such-pin.json"))
    ck(rc == 1 and "no resume pin" in out, "missing pin file must be INPUT GAP: %s" % out[-300:])

    # 5b. a malformed --as-of must be an INPUT GAP, never a silently wrong window
    #     mode (measured 2026-11-11: a compact `--as-of 20261111` string-compares
    #     as >= "2026-11-12", which read the closed suspension window as OPEN).
    def _run_asof(fix, asof):
        env = dict(os.environ, PUB_MANIFEST_OVERRIDE=fix.manifest)
        p = subprocess.run([sys.executable, SCRIPT, "--pin", fix.make_pin(),
                            "--ws", fix.ws, "--repo", fix.repo, "--as-of", asof],
                           capture_output=True, text=True, env=env, timeout=120)
        return p.returncode, p.stdout + p.stderr

    f13 = Fixture(os.path.join(tmp, "b13"))
    rc, out = _run_asof(f13, "20261113")
    ck(rc == 1 and "INPUT GAP" in out and "--as-of" in out,
       "a compact --as-of must be INPUT GAP, not a byte-wise OPEN verdict: %s" % out[-300:])
    rc, out = _run_asof(f13, "2026-02-30")
    ck(rc == 1 and "INPUT GAP" in out,
       "a calendar-invalid dashed --as-of must be INPUT GAP: %s" % out[-300:])
    rc, out = _run_asof(f13, "2026-11-11")
    ck(rc == 0 and "window is CLOSED" in out,
       "a well-formed ISO --as-of before the resume day must still be READY with CLOSED mode "
       "(the new guard must not refuse valid dates): %s" % out[-300:])

    f14 = Fixture(os.path.join(tmp, "b14"))
    p14 = json.load(open(f14.make_pin(), encoding="utf-8"))
    p14["owner_window"]["suspended_until"] = "20261112"
    rc, out = f14.run(_write(tmp, "bad-until-pin.json", p14))
    ck(rc == 1 and "suspended_until" in out,
       "a compact owner_window.suspended_until in the pin must be INPUT GAP: %s" % out[-300:])

    # 2. pin vocabulary: wrong tasks cell / wrong pinned task count
    f10 = Fixture(os.path.join(tmp, "b10"))
    rc, out = f10.run(f10.make_pin(expected_tasks_cell="0" * 16))
    ck(rc == 3 and "tasks cell is" in out, "a wrong tasks cell must be NO-GO: %s" % out[-300:])
    rc, out = f10.run(f10.make_pin(expected_pinned_tasks=99))
    ck(rc == 3 and "pin expects 99" in out, "a wrong pinned task count must be NO-GO: %s" % out[-300:])

    # 6. the MANIFEST pin guard is wired: task bytes moved => refused, exit 2
    f11 = Fixture(os.path.join(tmp, "b11"))
    pin11 = f11.make_pin()
    with open(f11.tasks_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"id": "t-003", "q": 3}) + "\n")
    rc, out = f11.run(pin11)
    ck(rc == 2 and "MANIFEST GUARD" in out,
       "a moved task file must be refused by the published pin guard (exit 2): %s" % out[-400:])

    # non-vacuity: a zero-row arm with no answer file is READY, not an input gap
    f12 = Fixture(os.path.join(tmp, "b12"), stored=0)
    p12 = json.load(open(f12.make_pin(), encoding="utf-8"))
    p12["arms"][f12.bench]["answer_file"] = None
    p12["arms"][f12.bench]["answer_file_sha256_16"] = "-"
    rc, out = f12.run(_write(tmp, "never-legged.json", p12))
    ck(rc == 0 and "resume set    3 ids" in out,
       "a never-legged set with no answer file must be READY: %s" % out[-300:])

    print("pub_grok_resume_check contract: %d checks, %d failure(s)" % (CHECKS, len(FAILED)))
    for m in FAILED:
        print("FAIL: %s" % m)
    return 1 if FAILED else 0


def _write(tmp: str, name: str, obj) -> str:
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2)
    return path


if __name__ == "__main__":
    raise SystemExit(main())
