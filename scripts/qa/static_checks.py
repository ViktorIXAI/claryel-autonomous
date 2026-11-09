#!/usr/bin/env python3
"""Repository static QA gates without external dependencies."""
from __future__ import annotations

import compileall
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEST_FILES = sorted((ROOT / "harness").glob("*test.py")) + [
    ROOT / "telemetry" / "resource_quality_test.py",
]
EXTRA_SCRIPTS = [
    "scripts/sanity_data.py",
    "scripts/check_links.py",
    # the link gate's own contract: repo URL kinds (blob/tree/commit/issues)
    # must classify correctly, or documentation links go red on a green repo
    "scripts/qa/check_links_test.py",
    "scripts/qa/validate_json.py",
    # the JSONL line-splitting contract: a U+2028 inside a prompt string must not
    # turn one valid record into two phantom syntax errors
    "scripts/qa/validate_json_test.py",
    # the scanner's vendored-file exception: byte-pinned upstream data may be excepted only for
    # metadata rules, only at the manifest-pinned sha16, and never for a credential rule
    "scripts/qa/secret_scan_exception_test.py",
    # the publication scrub: masking must never edit a scored answer byte or break the JSON of the
    # line it touched, and a path token proven from the pinned task file must survive verbatim
    "scripts/qa/publish_scrub_test.py",
]
EXTRA_ARG_SCRIPTS = [
    ["scripts/qa/docs_policy.py", "--push"],
]
LINK_MODE = os.environ.get("SAH_LINK_MODE", "online")


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    ok = True

    if not compileall.compile_dir(ROOT, quiet=1, maxlevels=10, force=True):
        print("compileall failed")
        ok = False

    for test in TEST_FILES:
        try:
            run([sys.executable, str(test.relative_to(ROOT))])
        except subprocess.CalledProcessError:
            ok = False

    for script in EXTRA_SCRIPTS:
        path = ROOT / script
        if path.exists():
            cmd = [sys.executable, script]
            if script == "scripts/check_links.py" and LINK_MODE == "offline":
                cmd.append("--offline")
            try:
                run(cmd)
            except subprocess.CalledProcessError:
                ok = False

    for cmd in EXTRA_ARG_SCRIPTS:
        if (ROOT / cmd[0]).exists():
            try:
                run([sys.executable] + cmd)
            except subprocess.CalledProcessError:
                ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
