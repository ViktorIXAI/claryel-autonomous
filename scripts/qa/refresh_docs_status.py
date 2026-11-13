#!/usr/bin/env python3
"""Refresh the public README status date after a mechanical daily check.

The script does not pretend to know deep content changes. It only verifies
that the deterministic documentation policy is clean, then updates the date
marker so the scheduled public check has a fresh reviewed-at value. Content
claims still need human or agent review before they are changed; this script
is deliberately narrow and commits only the date marker.
"""
from __future__ import annotations

import datetime as dt
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
PATTERN = re.compile(r"Status checked:\s*\d{4}-\d{2}-\d{2}")

# Why these exist (measured 2026-11-11 02:02 UTC, job `GitHub docs freshness daily`,
# execution 88c0821487c2412e8320bcbc0137bb4c): the run committed its date marker and the
# single `git push` attempt died on `Could not resolve host: github.com` (exit 128). The
# marker commit then sat local until an unrelated push carried it, because the old code
# pushed only inside the `marker changed` branch — and the next day the marker already
# matches its own date, so that branch never runs again and nothing pushes the orphan.
# A transient DNS/network blip is retried; the single-writer guard block is not.
PUSH_ATTEMPTS = int(os.environ.get("SAH_DOCS_PUSH_ATTEMPTS", "3"))
PUSH_BACKOFF_S = float(os.environ.get("SAH_DOCS_PUSH_BACKOFF_S", "30"))


def run(*args: str, check: bool = True) -> int:
    print("+", " ".join(args))
    return subprocess.run(args, cwd=ROOT, check=check).returncode


def capture(*args: str) -> subprocess.CompletedProcess:
    print("+", " ".join(args))
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


def unpushed_count() -> int | None:
    """Commits on this branch that the upstream does not have; None if unknowable."""
    res = capture("git", "rev-list", "--count", "@{u}..HEAD")
    if res.returncode != 0:
        return None
    try:
        return int((res.stdout or "").strip())
    except ValueError:
        return None


def push_with_retry() -> int:
    """Push unpushed commits, retrying a transient transport failure.

    Returns 0 when there is nothing to push or a push attempt succeeded, 1 when every
    attempt failed or the single-writer guard blocked the push (a configuration error,
    never retried).
    """
    ahead = unpushed_count()
    if ahead is None:
        print("cannot read the unpushed-commit count; attempting the push anyway")
    elif ahead == 0:
        print("nothing to push (HEAD == upstream)")
        return 0
    else:
        print(f"{ahead} unpushed commit(s) on this branch")

    for attempt in range(1, max(1, PUSH_ATTEMPTS) + 1):
        res = capture("git", "push", "origin", "HEAD:main")
        blob = ((res.stdout or "") + "\n" + (res.stderr or "")).strip()
        if res.returncode == 0:
            print(f"push ok on attempt {attempt}")
            return 0
        if "BLOCKED_SINGLE_WRITER_GUARD" in blob:
            print("push blocked by the single-writer guard: the job wrapper must export "
                  "ALLOW_HARD_V6_PUSH=1 for this push — not retrying")
            return 1
        last = blob.splitlines()[-1] if blob else "no output"
        print(f"push attempt {attempt}/{PUSH_ATTEMPTS} failed: {last}")
        if attempt < max(1, PUSH_ATTEMPTS):
            time.sleep(PUSH_BACKOFF_S)
    print(f"push failed after {PUSH_ATTEMPTS} attempt(s); the commit stays local and the "
          "next run retries the push even though the marker date no longer changes")
    return 1


def main() -> int:
    if PATTERN.search(README.read_text(encoding="utf-8")) is None:
        print("README has no `Status checked: YYYY-MM-DD` marker")
        return 1

    # The precondition is the PUSH-mode policy, not --daily. The date-staleness
    # finding is exactly what this job exists to repair, so gating the repair on
    # it self-locks after any red streak: measured 2026-11-13 03:00 CET (job
    # `GitHub docs freshness daily`, capture 2026-11-13_03-00-18) the run died at
    # this call with "README status date is stale: 2026-11-11 is 2 days old",
    # because the 11-11/12 runs died later (row_count_census pin, removed by
    # 5be2855) and never refreshed the marker — after which no future run can
    # ever reach the marker write again. Structure, links and forbidden-phrase
    # checks stay fail-closed; the "at least once per day" policy is enforced by
    # this job writing the marker daily, not by refusing to run once it is late.
    run(sys.executable, "scripts/qa/docs_policy.py", "--push")
    env = os.environ.copy()
    env["SAH_LINK_MODE"] = "offline"
    subprocess.run([sys.executable, "scripts/qa/static_checks.py"], cwd=ROOT, check=True, env=env)

    if run("git", "status", "--porcelain", check=False) != 0:
        print("git status failed")
        return 1

    today = dt.date.today().isoformat()
    text = README.read_text(encoding="utf-8")
    updated = PATTERN.sub(f"Status checked: {today}", text, count=1)
    if updated != text:
        README.write_text(updated, encoding="utf-8")
        run("git", "add", "README.md")
        run("git", "diff", "--cached", "--check")
        run("git", "commit", "-m", f"Daily docs freshness check: {today}")
        print(f"README status date refreshed to {today}")
    # The push step is outside the marker branch on purpose: a commit an earlier run made
    # but could not push has no other path back to origin, because the marker branch never
    # runs again while the date already matches.
    return push_with_retry()


if __name__ == "__main__":
    raise SystemExit(main())
