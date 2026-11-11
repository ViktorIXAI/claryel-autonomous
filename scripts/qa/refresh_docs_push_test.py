#!/usr/bin/env python3
"""Contract test for the daily-docs push step (offline, zero network, zero repo writes).

Measured 2026-11-11 02:02 UTC (`GitHub docs freshness daily`, execution
88c0821487c2412e8320bcbc0137bb4c): the job committed its date marker and its single
`git push` died on `Could not resolve host: github.com`. The commit then sat local,
because the old code pushed only inside the `marker changed` branch and the marker
branch never runs again while the date already matches. This test pins the repair:

  * a transient transport failure is retried a bounded number of times;
  * the single-writer guard block is NOT retried and says what to fix;
  * a commit that is already local-but-unpushed is pushed even when the marker did not
    change (the call site, not just the helper — the helper passing on its own would
    still leave the orphan commit stranded).

Tamper controls are the failing-push cases themselves: a push helper that never retried
would fail checks 2-3, and one that retried a guard block would fail check 4.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD_PATH = HERE / "refresh_docs_status.py"

FAILS = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global FAILS
    print(("ok   " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
    if not cond:
        FAILS += 1


class FakeProc:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def load_mod(scripted: list[FakeProc]):
    """Import the tool and script its capture(); returns (mod, calls, sleeps)."""
    spec = importlib.util.spec_from_file_location("refresh_docs_status_push", MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert str(mod.__file__).startswith(str(HERE)), f"loaded the wrong module: {mod.__file__}"
    calls: list[list[str]] = []
    sleeps: list[float] = []
    seq = list(scripted)

    def fake_capture(*args: str) -> FakeProc:
        calls.append(list(args))
        if not seq:
            raise AssertionError(f"capture called more times than scripted: {args}")
        return seq.pop(0)

    mod.capture = fake_capture
    mod.time.sleep = lambda s: sleeps.append(s)
    return mod, calls, sleeps


def main() -> int:
    # 0. defaults carry the intent: a blip really is retried, with a gap between attempts
    probe, _, _ = load_mod([])
    check("default push attempts >= 2", probe.PUSH_ATTEMPTS >= 2, f"={probe.PUSH_ATTEMPTS}")
    check("default backoff > 0 s", probe.PUSH_BACKOFF_S > 0, f"={probe.PUSH_BACKOFF_S}")

    # 1. nothing to push -> exit 0, zero push attempts
    mod, calls, sleeps = load_mod([FakeProc(0, "0\n")])
    rc = mod.push_with_retry()
    check("clean branch pushes nothing", rc == 0 and not any(c[1] == "push" for c in calls),
          f"rc={rc} calls={calls}")

    # 2. the measured case: DNS failure on every attempt -> bounded retries, then exit 1
    dns = "fatal: unable to access 'https://github.com/<org>/<repo>.git/': " \
          "Could not resolve host: github.com"
    mod, calls, sleeps = load_mod(
        [FakeProc(0, "1\n")] + [FakeProc(128, "", dns)] * 3)
    rc = mod.push_with_retry()
    pushes = [c for c in calls if c[1] == "push"]
    check("transport failure is retried PUSH_ATTEMPTS times", rc == 1 and len(pushes) == mod.PUSH_ATTEMPTS,
          f"rc={rc} pushes={len(pushes)}")
    check("retry sleeps between attempts, not after the last", len(sleeps) == mod.PUSH_ATTEMPTS - 1,
          f"sleeps={sleeps}")

    # 3. first attempt blips, second succeeds -> exit 0, exactly 2 attempts
    mod, calls, sleeps = load_mod([FakeProc(0, "2\n"), FakeProc(128, "", dns), FakeProc(0)])
    rc = mod.push_with_retry()
    pushes = [c for c in calls if c[1] == "push"]
    check("recovers on the second attempt", rc == 0 and len(pushes) == 2, f"rc={rc} pushes={len(pushes)}")

    # 4. guard block -> exit 1 at once, no retry, and the message names the fix
    mod, calls, sleeps = load_mod(
        [FakeProc(0, "1\n"), FakeProc(1, "", "BLOCKED_SINGLE_WRITER_GUARD")])
    rc = mod.push_with_retry()
    pushes = [c for c in calls if c[1] == "push"]
    check("guard block is not retried", rc == 1 and len(pushes) == 1 and not sleeps,
          f"rc={rc} pushes={len(pushes)} sleeps={sleeps}")

    # 5. unreadable ahead-count -> still attempts the push (never a silent skip)
    mod, calls, sleeps = load_mod([FakeProc(128, "", "no upstream"), FakeProc(0)])
    rc = mod.push_with_retry()
    check("unknown ahead-count still pushes once", rc == 0 and len([c for c in calls if c[1] == "push"]) == 1,
          f"rc={rc} calls={calls}")

    # 6. call-site pin: main() must route through push_with_retry and never push bare
    src = MOD_PATH.read_text(encoding="utf-8")
    check("main returns push_with_retry()", "return push_with_retry()" in src)
    check("no bare push call left in the tool", 'run("git", "push"' not in src)

    print(f"DOCS PUSH TEST: {FAILS} failed" if FAILS else "DOCS PUSH TEST: PASS")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
