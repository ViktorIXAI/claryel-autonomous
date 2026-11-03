#!/usr/bin/env python3
"""Collect a canonical OS record from every reachable fleet host.

The local OS is detected through `harness/os_record.py`. Remote hosts use the
same module shipped through SSH stdin, so Desktop/Server classification is not
invented from hostnames or kernel versions.

The fleet list is local-only by default:
  ~/.hermes/fleet-os.json  or  PARB_FLEET_OS_CONFIG

Example local config (do not commit real host values):
  [{"label":"P1005","user":"claryel","host":"192.0.2.10",
    "key":"~/.ssh/strata_key"}]
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness"))
import os_record  # noqa: E402

CONFIG = pathlib.Path(os.environ.get(
    "PARB_FLEET_OS_CONFIG", str(pathlib.Path.home() / ".hermes" / "fleet-os.json")))
MODULE = (ROOT / "harness" / "os_record.py").read_text(encoding="utf-8")
SNAP_DIR = ROOT / "hardware" / "os-snapshots"


def local_record() -> dict:
    return {
        "label": "localhost",
        "reachable": True,
        "os": os_record.safe_for_log(os_record.detect()),
    }


def remote_record(entry: dict) -> dict:
    label = entry.get("label") or entry.get("host") or "unknown"
    user = entry["user"]
    host = entry["host"]
    key = os.path.expanduser(str(entry.get("key", ""))) if entry.get("key") else None
    code = MODULE + "\n\nimport json\nprint(json.dumps(safe_for_log(detect()), ensure_ascii=False))\n"
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "-o", "ServerAliveInterval=10"]
    if key:
        cmd += ["-i", key]
    cmd += [f"{user}@{host}", "python3 -"]
    try:
        p = subprocess.run(cmd, input=code, capture_output=True, text=True, timeout=25)
        if p.returncode == 0 and p.stdout.strip():
            return {"label": label, "reachable": True, "os": json.loads(p.stdout.strip())}
        return {"label": label, "reachable": False, "error": "ssh_unreachable", "ssh_rc": p.returncode}
    except Exception:
        return {"label": label, "reachable": False, "error": "ssh_or_parser_error"}


def main() -> int:
    snap = {
        "kind": "fleet-os-snapshot",
        "checked_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "policy": "Every benchmark, telemetry and hardware record must carry os.id, os.pretty, os.codename, os.flavor and os.kernel.",
        "machines": [local_record()],
    }
    if CONFIG.exists():
        try:
            entries = json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"fleet config unreadable: {exc}", file=sys.stderr)
            entries = []
        for entry in entries:
            try:
                snap["machines"].append(remote_record(entry))
            except KeyError as exc:
                snap["machines"].append({"label": entry.get("label", "unknown"), "reachable": False, "error": f"missing config key {exc}"})
    else:
        snap["note"] = f"local fleet config not found at {CONFIG}; only localhost was collected"

    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAP_DIR / (dt.date.today().isoformat() + ".json")
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"wrote {path}")
    for m in snap["machines"]:
        if m.get("reachable"):
            print("%-12s %s" % (m["label"], os_record.compact(m["os"])))
        else:
            print("%-12s unreachable: %s" % (m["label"], m.get("error", "")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
