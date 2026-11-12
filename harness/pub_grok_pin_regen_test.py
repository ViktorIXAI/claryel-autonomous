#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for `scripts/pub_grok_resume_check.py --write-pin` (added 2026-11-12).

Hermetic fixtures in a temp dir with `PUB_MANIFEST_OVERRIDE` at a fixture `MANIFEST.json`:
zero model calls, zero cloud calls, no network, no real answer file touched.

Why this test exists: the resume gate prints "regenerate the pin at window end" and every
pin so far was hand-written JSON. A hand-typed pin over a several-hundred-id `pinned_ok_ids`
list is the same defect family the line has already been bitten by twice (19 hand readings of
the same partial at ticks 21-39; a gate BLIND to a leg the pin predates at tick 68). So the
writer needs the same treatment as the gate: pinned behaviour plus mechanical non-vacuity.

What it pins:

  1. round trip: the writer mints a pin that the GATE accepts (exit 0, READY) and prints the
     same resume set for;
  2. every written field is READ from bytes: the record equals the fixture's own census
     (rows / unique / ok / empty / answer-file SHA-256-16 / remaining count and range /
     pinned ok ids), and the tasks cell equals the MANIFEST pin (no second hash convention);
  3. in-flight guard: a partial leg is REFUSED (exit 3) unless `--allow-in-flight`, and a
     refusal leaves the existing pin file BYTE-IDENTICAL;
  4. corruption guards: duplicate id, parked non-`ok` row, empty `ok` answer each refuse the
     write and leave the pin byte-identical (a pin must never launder corrupt bytes);
  5. a completed set writes without the flag and the gate then prints `resume set 0 ids`;
  6. preservation: `owner_window`, `queue_order`, `resume_rule` and the per-arm `quarantine`
     evidence are carried over verbatim;
  7. a never-legged set (no answer file at all) is written as a zero record with
     `answer_file: null`, and the gate reads it as READY;
  8. non-vacuity, mechanically: `PUB_RESUME_SCRIPT` points at a copy of the tool with the
     writer dispatch removed - the same fixture then writes NOTHING (pin bytes unchanged, no
     "PIN WRITTEN" line), and after a real write, deleting one stored row makes the gate
     NO-GO ("GONE from the arm file"), so `pinned_ok_ids` really pins the work.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.environ.get("PUB_RESUME_SCRIPT") or os.path.join(
    ROOT, "scripts", "pub_grok_resume_check.py")

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
    """One bench of `n` pinned tasks with `stored` answer rows in an untracked ws tree."""

    def __init__(self, tmp: str, n: int = 3, stored: int = 2, bench: str = "demo-bench"):
        self.tmp = tmp
        self.bench = bench
        self.repo = os.path.join(tmp, "repo")
        self.pub = os.path.join(self.repo, "benchmarks", "public")
        self.ws = os.path.join(tmp, "ws")
        os.makedirs(self.pub, exist_ok=True)
        os.makedirs(os.path.join(self.ws, bench), exist_ok=True)
        tasks = b"".join((json.dumps({"id": "t-%03d" % i, "q": i}) + "\n").encode()
                         for i in range(n))
        self.tasks_path = os.path.join(self.pub, "%s.tasks.jsonl" % bench)
        with open(self.tasks_path, "wb") as fh:
            fh.write(tasks)
        self.cell = sha16(tasks)
        manifest = {"benches": {bench: {"tasks_sha16": self.cell,
                                        "tasks_sha256_16": self.cell}}}
        self.manifest = os.path.join(self.pub, "MANIFEST.json")
        with open(self.manifest, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh)
        self.arm = os.path.join(self.ws, bench, "pub-grok.jsonl")
        self.rel = "%s/pub-grok.jsonl" % bench
        self.rows = [row(i) for i in range(stored)]
        self.n = n
        self.write_arm()

    def write_arm(self) -> None:
        with open(self.arm, "w", encoding="utf-8") as fh:
            for r in self.rows:
                fh.write(json.dumps(r) + "\n")

    def derived(self) -> dict:
        """Independent census, written here without calling the tool under test."""
        rows = [json.loads(l) for l in open(self.arm, encoding="utf-8") if l.strip()]
        ok = [r for r in rows if r.get("finish") == "ok"]
        order = ["t-%03d" % i for i in range(self.n)]
        remaining = [i for i in order if i not in {r["id"] for r in ok}]
        return {
            "expected_tasks_cell": self.cell,
            "expected_pinned_tasks": self.n,
            "answer_file": self.rel,
            "expected_rows": len(rows),
            "expected_unique": len({r["id"] for r in rows}),
            "expected_ok": len(ok),
            "expected_empty": sum(1 for r in ok if not (r.get("answer") or "").strip()),
            "answer_file_sha256_16": sha16(open(self.arm, "rb").read()),
            "pinned_ok_ids": [i for i in order if i in {r["id"] for r in ok}],
            "expected_remaining": len(remaining),
            "expected_first_remaining": remaining[0] if remaining else None,
            "expected_last_remaining": remaining[-1] if remaining else None,
        }

    def seed_pin(self, name: str = "seed-pin.json", quarantine=None) -> str:
        """The pin the writer preserves its vocabulary from (schema/owner_window/queue)."""
        d = {"expected_tasks_cell": self.cell, "expected_pinned_tasks": self.n,
             "answer_file": self.rel, "status": "fixture seed",
             "expected_rows": 0, "expected_unique": 0, "expected_ok": 0,
             "expected_empty": 0, "answer_file_sha256_16": "-", "pinned_ok_ids": [],
             "expected_remaining": self.n, "expected_first_remaining": "t-000",
             "expected_last_remaining": "t-%03d" % (self.n - 1)}
        if quarantine:
            d["quarantine"] = quarantine
        pin = {"schema": "grok-resume-pin-v1", "as_of": "seed",
               "owner_window": {"suspended_until": "2026-11-12", "reason": "fixture window"},
               "queue_order": [self.bench],
               "resume_rule": "fixture resume rule",
               "arms": {self.bench: d}}
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(pin, fh, indent=2)
        return path

    def _env(self, script: str | None = None) -> dict:
        return dict(os.environ, PUB_MANIFEST_OVERRIDE=self.manifest)

    def write(self, pin: str, allow_in_flight: bool = False,
              script: str | None = None) -> tuple[int, str]:
        cmd = [sys.executable, script or SCRIPT, "--write-pin", "--pin", pin,
               "--ws", self.ws, "--repo", self.repo]
        if allow_in_flight:
            cmd.append("--allow-in-flight")
        p = subprocess.run(cmd, capture_output=True, text=True, env=self._env(), timeout=120)
        return p.returncode, p.stdout + p.stderr

    def gate(self, pin: str, asof: str = "2026-11-13") -> tuple[int, str]:
        cmd = [sys.executable, SCRIPT, "--pin", pin, "--ws", self.ws, "--repo", self.repo,
               "--as-of", asof]
        p = subprocess.run(cmd, capture_output=True, text=True, env=self._env(), timeout=120)
        return p.returncode, p.stdout + p.stderr


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="grok-pin-regen-")

    # 1+2. round trip and byte-read fields: writer output == independent census, and the
    #      gate accepts what the writer minted.
    f = Fixture(os.path.join(tmp, "a"), n=4, stored=3)
    pin = f.seed_pin()
    before = open(pin, "rb").read()
    rc, out = f.write(pin, allow_in_flight=True)
    ck(rc == 0 and "PIN WRITTEN" in out, "writer must accept an explicit in-flight pin: %s"
       % out[-300:])
    got = json.load(open(pin, encoding="utf-8"))["arms"][f.bench]
    want = f.derived()
    for k, v in want.items():
        ck(got.get(k) == v, "written %s is %r, the stored bytes say %r" % (k, got.get(k), v))
    ck(got.get("expected_tasks_cell") == f.cell,
       "the written tasks cell must be the MANIFEST pin, not a re-hash")
    ck("rows    3 ok    3 sha256-16" in out and "resume    1 ids t-003..t-003" in out,
       "the writer must print the identity it wrote: %s" % out[-400:])
    rc, out = f.gate(pin)
    ck(rc == 0 and "RESUME GATE: READY" in out and "resume set    1 ids t-003..t-003" in out,
       "the gate must accept the regenerated pin: %s" % out[-400:])
    # 6. vocabulary preserved
    seed = json.loads(before.decode())
    now = json.load(open(pin, encoding="utf-8"))
    ck(now.get("owner_window") == seed["owner_window"]
       and now.get("queue_order") == seed["queue_order"]
       and now.get("resume_rule") == seed["resume_rule"],
       "owner_window / queue_order / resume_rule must survive regeneration verbatim")

    # 3. in-flight guard: REFUSED without the flag, pin byte-identical
    g = Fixture(os.path.join(tmp, "b"), n=4, stored=3)
    pin2 = g.seed_pin()
    keep = open(pin2, "rb").read()
    rc, out = g.write(pin2)
    ck(rc == 3 and "REFUSED" in out and "in flight" in out,
       "a growing leg must be refused without --allow-in-flight: %s" % out[-300:])
    ck(open(pin2, "rb").read() == keep, "a refused write must leave the pin byte-identical")

    # 4. corruption guards: refuse, and the pin stays byte-identical
    for tag, mut, needle in (
            ("dup", lambda x: x.rows.append(row(0, answer="7")), "duplicate ids"),
            ("nonok", lambda x: x.rows.append(row(3, answer="", finish="timeout")),
             "non-ok rows parked"),
            ("empty", lambda x: x.rows.__setitem__(1, row(1, answer="   ")),
             "empty finish=ok")):
        h = Fixture(os.path.join(tmp, "c-" + tag), n=4, stored=3)
        pin3 = h.seed_pin()
        keep3 = open(pin3, "rb").read()
        mut(h)
        h.write_arm()
        rc, out = h.write(pin3, allow_in_flight=True)
        ck(rc == 3 and needle in out and "PIN WRITER: NO-GO" in out,
           "%s bytes must refuse the pin write: %s" % (tag, out[-400:]))
        ck(open(pin3, "rb").read() == keep3,
           "%s refusal must leave the existing pin byte-identical" % tag)
        # and the same bytes are still a gate finding, so nothing was laundered
        rc, out = h.gate(h.seed_pin("late-%s.json" % tag))
        ck(rc == 3, "the corruption class must still be NO-GO at the gate after %s: %s"
           % (tag, out[-200:]))

    # 5. a completed set writes with no flag, and the gate then has no resume set
    k = Fixture(os.path.join(tmp, "d"), n=3, stored=3)
    pin4 = k.seed_pin()
    rc, out = k.write(pin4)
    ck(rc == 0 and "PIN WRITTEN" in out, "a completed set must write without any flag: %s"
       % out[-300:])
    rc, out = k.gate(pin4)
    ck(rc == 0 and "resume set    0 ids" in out,
       "the regenerated completed pin must leave no resume set: %s" % out[-300:])
    ck(json.load(open(pin4, encoding="utf-8"))["arms"][k.bench]["status"]
       .startswith("complete: 3/3"), "a completed arm must say so in its status line")

    # 7. never-legged set: no answer file anywhere -> zero record, gate READY
    m = Fixture(os.path.join(tmp, "e"), n=3, stored=0)
    os.remove(m.arm)
    pin5 = m.seed_pin(quarantine=[{"file": "%s/pub-grok.jsonl.dead1.bak" % m.bench,
                                   "note": "fixture quarantine"}])
    rc, out = m.write(pin5)
    ck(rc == 0, "a never-legged set must write a zero record: %s" % out[-300:])
    rec5 = json.load(open(pin5, encoding="utf-8"))["arms"][m.bench]
    ck(rec5["expected_rows"] == 0 and rec5["expected_remaining"] == 3
       and rec5["expected_last_remaining"] == "t-002",
       "the zero record must carry the full resume set: %s" % json.dumps(rec5)[:300])
    ck(rec5.get("quarantine") == [{"file": "%s/pub-grok.jsonl.dead1.bak" % m.bench,
                                   "note": "fixture quarantine"}],
       "quarantine evidence must be carried over verbatim, never rewritten from bytes")
    rc, out = m.gate(pin5)
    ck(rc == 0 and "resume set    3 ids" in out,
       "the gate must read the regenerated zero record as READY: %s" % out[-300:])

    # 8a. non-vacuity of the CLI wiring: with the writer dispatch stripped from a copy,
    #     the SAME fixture writes nothing at all.
    src = open(SCRIPT, encoding="utf-8").read()
    stripped = re.sub(r"\n *if args\.write_pin:\n *return write_pin\(args\)\n", "\n", src)
    ck(stripped != src, "the dispatch-line control assumes this exact call site exists")
    dead = os.path.join(tmp, "gate-without-writer.py")
    with open(dead, "w", encoding="utf-8") as fh:
        fh.write(stripped)
    n1 = Fixture(os.path.join(tmp, "f"), n=4, stored=3)
    pin6 = n1.seed_pin()
    keep6 = open(pin6, "rb").read()
    rc, out = n1.write(pin6, allow_in_flight=True, script=dead)
    ck("PIN WRITTEN" not in out and open(pin6, "rb").read() == keep6,
       "without the writer dispatch the tool must leave the pin untouched (the test drives "
       "the real code path): rc=%d %s" % (rc, out[-200:]))

    # 8b. non-vacuity of `pinned_ok_ids`: after a real write, one vanished stored row is a
    #     NO-GO, so the written id list really pins the work.
    p2 = Fixture(os.path.join(tmp, "g"), n=4, stored=3)
    pin7 = p2.seed_pin()
    rc, out = p2.write(pin7, allow_in_flight=True)
    ck(rc == 0, "setup write for the id-list control must succeed: %s" % out[-200:])
    p2.rows = p2.rows[:2]
    p2.write_arm()
    rc, out = p2.gate(pin7)
    ck(rc == 3 and "GONE from the arm file" in out,
       "a pinned ok row that vanished after regeneration must be NO-GO: %s" % out[-300:])

    print("pub_grok_resume_check --write-pin contract: %d checks, %d failure(s)"
          % (CHECKS, len(FAILED)))
    for m_ in FAILED:
        print("FAIL: %s" % m_)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
