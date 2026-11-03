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
LATEST = SNAP_DIR / "latest.json"


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


def snapshot_summary(snap: dict) -> list[dict]:
    out = []
    for m in snap["machines"]:
        row = {"label": m.get("label", ""), "reachable": bool(m.get("reachable"))}
        if row["reachable"]:
            row["os"] = m.get("os", {})
        else:
            row["error"] = m.get("error", "")
        out.append(row)
    return out


def previous_snapshot() -> dict | None:
    try:
        return json.loads(LATEST.read_text(encoding="utf-8"))
    except Exception:
        return None


def changed_rows(previous: list[dict], current: list[dict]) -> list[dict]:
    old = {r["label"]: r for r in previous}
    changed = []
    for row in current:
        if old.get(row["label"]) != row:
            changed.append(row)
    for label, row in old.items():
        if label not in {r["label"] for r in current}:
            changed.append(row)
    return changed


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
    previous = previous_snapshot()
    previous_rows = snapshot_summary(previous) if previous else None
    current_rows = snapshot_summary(snap)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    LATEST.write_text(json.dumps(snap, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"wrote {path}", file=sys.stderr)
    if "--print-all" in sys.argv:
        for m in snap["machines"]:
            if m.get("reachable"):
                print("%-12s %s" % (m["label"], os_record.compact(m["os"])), file=sys.stderr)
            else:
                print("%-12s unreachable: %s" % (m["label"], m.get("error", "")), file=sys.stderr)

    # A scheduled audit is silent when the fleet OS baseline has not changed.
    # It alerts only on a new OS/kernel/flavor value, an unreachable machine
    # becoming reachable, or a reachable machine disappearing from the fleet.
    if previous_rows is None:
        print("Fleet OS baseline recorded: %d machines. "
              "Canonical OS records are now written into gates, ledgers and telemetry headers." % len(current_rows))
    else:
        changes = changed_rows(previous_rows, current_rows)
        if changes:
            lines = []
            for row in changes:
                if not row.get("reachable"):
                    lines.append("%s: unreachable (%s)" % (row["label"], row.get("error", "")))
                else:
                    lines.append("%s: %s" % (row["label"], os_record.compact(row.get("os", {}))))
            print("Fleet OS change detected:\n" + "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
