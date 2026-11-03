#!/usr/bin/env python3
"""Print a compact Strata fleet audit.

This script is read-only. It deliberately avoids printing config contents,
API keys, command-line arguments containing secrets, or model payload data.
"""
from __future__ import annotations

import glob
import json
import os
import platform
import re
import socket
import subprocess
import sys
from pathlib import Path


def sh(cmd: str, timeout: int = 10) -> str:
    try:
        p = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()
        if out:
            return out
        if p.returncode:
            return f"rc={p.returncode} {err[:200]}"
        return ""
    except Exception as exc:
        return f"error {exc}"


def first(patterns: list[str]) -> list[str]:
    paths: list[str] = []
    home = Path.home()
    for pat in patterns:
        pat = pat.replace("~", str(home))
        paths.extend(glob.glob(pat))
    return paths


def json_get(text: str, key: str) -> str:
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return str(data.get(key, "-"))
    except Exception:
        pass
    m = re.search(rf'"{re.escape(key)}"\s*:\s*"([^"]+)"', text)
    if m:
        return m.group(1)
    m = re.search(rf'"{re.escape(key)}"\s*:\s*(true|false|null|[0-9.]+)', text)
    if m:
        return m.group(1)
    return "-"


def health() -> dict:
    try:
        p = subprocess.run(
            ["curl", "-s", "--max-time", "5", "http://127.0.0.1:8080/health"],
            capture_output=True, text=True, timeout=8,
        )
        return {"rc": p.returncode, "out": p.stdout.strip()[:400]}
    except Exception as exc:
        return {"rc": -1, "out": str(exc)}


def main() -> int:
    home = str(Path.home())
    print("HOST", socket.gethostname())
    print("OS", platform.system(), platform.release(), platform.machine())
    print("HOME", home)
    print("WHOAMI", os.environ.get("USER", "-"))

    tag = sh("cd ~/Strata 2>/dev/null && git describe --tags 2>/dev/null", 5)
    print("REPO_TAG", tag or "-")

    print("STRATA_CLI", sh("command -v strata 2>/dev/null || true", 5) or "-")
    print("STRATA_CLI_VERSION", sh("strata --version 2>/dev/null || true", 10) or "-")

    engine_globs = [
        "~/Strata/build-metal/BUILD.json",
        "~/Strata/engine-*/BUILD.json",
        "~/Strata/engine/BUILD.json",
        "~/Strata/engine/*/BUILD.json",
        "~/Strata/build-*/BUILD.json",
        "~/Strata/strata-engine-*/BUILD.json",
        "/Applications/Strata.app/Contents/Resources/engine-bundle/*/BUILD.json",
    ]
    for p in first(engine_globs):
        ver = sh(f"grep -o '\"version\":\"[^\"]*\"' {p} 2>/dev/null | head -1", 3)
        print("ENGINE_BUILD", p, ver or "-")

    h = health()
    out = h["out"]
    print("HEALTH_8080", "rc=" + str(h["rc"]),
          json_get(out, "status"),
          json_get(out, "model"),
          json_get(out, "engine_version"),
          json_get(out, "loaded"))

    if platform.system() == "Darwin":
        procs = sh("pgrep -lf 'serve/server.py|strata serve' 2>/dev/null | head -5 || true", 5)
    else:
        procs = sh("pgrep -af 'serve/server.py|strata serve' 2>/dev/null | head -5 || true", 5)
    print("SERVE_PROCESSES", procs.replace("\n", " | ") or "-")

    if platform.system() == "Darwin":
        agents = sh("ls ~/Library/LaunchAgents 2>/dev/null | grep -i strata | head -5 || true", 5)
        print("LAUNCH_AGENTS", agents.replace("\n", " | ") or "-")
        print("LAUNCHD_STATUS", sh("launchctl list 2>/dev/null | grep -i strata | head -5 || true", 5) or "-")
    else:
        print("CRON_KEEPUP", sh("crontab -l 2>/dev/null | grep -E 'keep-up|strata|serve' | head -5 || true", 5) or "-")

    print("DISK_DATA", sh(f"df -h {home} 2>/dev/null | tail -1 || true", 5) or "-")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
