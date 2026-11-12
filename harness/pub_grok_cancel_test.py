#!/usr/bin/env python3
"""Contract test for the owner-cancel guard in `scripts/pub_bench_cloud.py` (2026-11-12, tick 73).

Owner decision 2026-11-12 06:40 CET: Grok arms are cancelled (owner-side quota too small). The
guard was added in three layers — the seven go-scripts, the chain launcher, and the transport
runner itself — because a launcher guard alone can be bypassed by a direct call or a systemd unit.
This test pins the innermost layer, where every path must converge:

  1. with the marker present, `main()` refuses a grok arm with exit 3 and reaches NO transport;
  2. non-vacuity: with the marker removed the SAME call does reach the transport (so the refusal
     is the guard's doing, not an accident of the fixture);
  3. a non-grok arm is unaffected by the marker (a codex leg must stay runnable);
  4. no answer file is written by a refused run (a refusal that still creates the arm file would
     poison the resume census);
  5. the marker path is read from `$HOME` at call time, so the test stays hermetic, and the
     assertion is "left exactly as found", never "the marker exists": this test also runs on CI,
     where no operator marker exists at all (measured 2026-11-12 - the first version asserted the
     marker is present and reddened static-qa on the runner while passing on the operator box).

The transport is replaced by a recording stub, so this test spends ZERO cloud calls.

Run with no arguments; exits non-zero on the first failed invariant.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPT = str(ROOT / "scripts" / "pub_bench_cloud.py")

CHECKS = 0
FAILED = []


def ck(cond, label):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)
        print("FAIL:", label)


def load():
    spec = importlib.util.spec_from_file_location("pub_bench_cloud", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture_tasks(path: Path):
    rows = [{"id": "x-0", "bench": "xbench", "prompt": "p0", "gold": "1", "checker": "number"},
            {"id": "x-1", "bench": "xbench", "prompt": "p1", "gold": "2", "checker": "number"}]
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def main() -> int:
    mod = load()
    real_marker = os.path.expanduser("~/pub-bench/GROK-CANCELLED")   # read BEFORE HOME is moved
    real_marker_existed = Path(real_marker).exists()
    mod.cli_version = lambda prog: "fixture-cli"                     # no subprocess in a test
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        home = td / "home"
        (home / "pub-bench").mkdir(parents=True)
        tasks = td / "x.tasks.jsonl"
        fixture_tasks(tasks)
        out = td / "out"

        calls = []
        mod.ask = lambda arm, prompt, cwd: (calls.append(arm) or ("42", "ok", ""))

        os.environ["HOME"] = str(home)          # the marker path expands from HOME at call time

        def run(arm):
            old = sys.argv
            sys.argv = [SCRIPT, str(tasks), arm, "--out", str(out)]
            buf = io.StringIO()
            try:
                with redirect_stdout(buf):
                    rc = mod.main()
            finally:
                sys.argv = old
            return rc, buf.getvalue()

        # 1. marker present -> refuse a grok arm, exit 3, zero transport calls, no arm file
        (home / "pub-bench" / "GROK-CANCELLED").write_text(
            "fixture: grok arms cancelled by owner decision\n", encoding="utf-8")
        calls.clear()
        rc, out_txt = run("grok")
        ck(rc == 3 and "REFUSED" in out_txt, "a marker-present grok run must exit 3 with REFUSED: %r %r" % (rc, out_txt[:120]))
        ck(calls == [], "a refused grok run must reach no transport (calls=%r)" % calls)
        ck(not (out / "pub-grok.jsonl").exists(),
           "a refused grok run must not create the arm file (the resume census would read it as progress)")

        # 2. non-vacuity: marker removed -> the same call reaches the transport
        (home / "pub-bench" / "GROK-CANCELLED").unlink()
        calls.clear()
        rc, out_txt = run("grok")
        ck(calls == ["grok", "grok"],
           "without the marker the transport must be reached (guard is what stops it): %r" % calls)
        ck("REFUSED" not in out_txt, "no refusal without the marker: %r" % out_txt[:120])
        rows = [json.loads(l) for l in (out / "pub-grok.jsonl").read_text(encoding="utf-8").splitlines()]
        ck(len(rows) == 2 and all(r.get("finish") == "ok" for r in rows),
           "the unguarded fixture leg stored 2 ok rows: %d" % len(rows))
        (out / "pub-grok.jsonl").unlink()

        # 3. a non-grok arm stays runnable with the marker present
        (home / "pub-bench" / "GROK-CANCELLED").write_text("fixture\n", encoding="utf-8")
        calls.clear()
        rc, out_txt = run("codex")
        ck(calls == ["codex", "codex"] and "REFUSED" not in out_txt,
           "the cancel marker must not block a codex arm: %r %r" % (calls, out_txt[:120]))

        # 4. the fixture never creates or deletes a marker in the real HOME
        ck(os.environ["HOME"] == str(home), "the test pinned HOME to its fixture")
        ck(Path(real_marker).exists() == real_marker_existed,
           "the test must leave the operator marker exactly as it found it (existed before: %s) at %s"
           % (real_marker_existed, real_marker))

    print("pub_grok_cancel contract: %d checks, %d failure(s)" % (CHECKS, len(FAILED)))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
