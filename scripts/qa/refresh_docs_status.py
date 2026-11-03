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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
PATTERN = re.compile(r"Status checked:\s*\d{4}-\d{2}-\d{2}")


def run(*args: str, check: bool = True) -> int:
    print("+", " ".join(args))
    return subprocess.run(args, cwd=ROOT, check=check).returncode


def main() -> int:
    if PATTERN.search(README.read_text(encoding="utf-8")) is None:
        print("README has no `Status checked: YYYY-MM-DD` marker")
        return 1

    run(sys.executable, "scripts/qa/docs_policy.py", "--daily")
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
        run("git", "push", "origin", "HEAD:main")
        print(f"README status date refreshed to {today}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
