#!/usr/bin/env python3
"""Canonical OS record used by gates, telemetry and fleet audits.

Every benchmark result and hardware snapshot records the exact OS version,
Ubuntu codename and whether the installed image is a desktop or a server.
This prevents results from two differently installed Ubuntu releases from
being compared as if they were the same operating-system environment.
"""
from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess


DESKTOP_PACKAGES = {
    "ubuntu-desktop",
    "gnome-shell",
    "plasma-workspace",
    "cinnamon-desktop",
    "xubuntu-desktop",
    "xfce4-session",
    "mate-desktop",
}


def parse_os_release(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if value and value[0] in "\"'" and value[-1:] == value[0]:
            value = value[1:-1]
        out[key.strip()] = value
    return out


def package_status(packages: dict[str, str]) -> dict[str, str]:
    return {name: status[:2] for name, status in packages.items()}


def classify_flavor(
    release: dict[str, str],
    packages: dict[str, str],
    active_display: bool = False,
    active_display_manager: bool = False,
) -> tuple[str, str]:
    """Return `(flavor, evidence)` using Ubuntu image evidence, not hostname."""
    if release.get("VARIANT_ID") == "desktop":
        return "desktop", "VARIANT_ID=desktop"
    if release.get("VARIANT_ID") == "server":
        return "server", "VARIANT_ID=server"

    if packages.get("ubuntu-desktop") == "ii":
        return "desktop", "ubuntu-desktop metapackage"
    if any(packages.get(p) == "ii" for p in DESKTOP_PACKAGES) and (
        active_display or active_display_manager
    ):
        return "desktop", "desktop session or display manager"
    if packages.get("ubuntu-server") == "ii":
        return "server", "ubuntu-server metapackage"
    if active_display or active_display_manager:
        return "desktop", "active graphical session"
    return "server", "headless default"


def _shell_out(cmd: list[str], timeout: int = 3) -> str:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (p.stdout or "").strip()
    except Exception:
        return ""


def _dpkg_abbrev(package: str) -> str:
    p = subprocess.run(
        ["dpkg-query", "-W", "-f=${db:Status-Abbrev}", package],
        capture_output=True,
        text=True,
        timeout=3,
    )
    return (p.stdout or "").strip()[:2] if p.returncode == 0 else "ab"


def detect() -> dict[str, str]:
    system = platform.system()
    if system == "Darwin":
        pretty = _shell_out(["sw_vers", "-productName"]) + " " + _shell_out(["sw_vers", "-productVersion"])
        version = _shell_out(["sw_vers", "-productVersion"])
        build = _shell_out(["sw_vers", "-buildVersion"])
        active_display = bool(_shell_out(["loginctl", "list-sessions", "--no-legend"]))
        flavor, evidence = ("desktop", "macOS desktop session") if active_display else ("desktop", "macOS desktop system")
        return {
            "id": "macos",
            "pretty": pretty.strip(),
            "version": version,
            "codename": build,
            "flavor": flavor,
            "flavor_evidence": evidence,
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "hostname": socket_hostname(),
        }

    osr_path = "/etc/os-release"
    release: dict[str, str] = {}
    if os.path.exists(osr_path):
        release = parse_os_release(open(osr_path, encoding="utf-8", errors="ignore").read())

    packages: dict[str, str] = {}
    if platform.system() == "Linux" and shutil.which("dpkg-query"):
        for pkg in ["ubuntu-desktop", "ubuntu-server", "gnome-shell"]:
            packages[pkg] = _dpkg_abbrev(pkg)

    active_display = bool(_shell_out(["loginctl", "list-sessions", "--no-legend"]))
    active_dm = (_shell_out(["systemctl", "show", "-p", "ActiveState", "display-manager.service", "--value"]) == "active")
    flavor, evidence = classify_flavor(release, packages, active_display, active_dm)
    return {
        "id": release.get("ID", platform.system().lower()),
        "pretty": release.get("PRETTY_NAME", platform.system()),
        "version": release.get("VERSION_ID", ""),
        "codename": release.get("VERSION_CODENAME", ""),
        "flavor": flavor,
        "flavor_evidence": evidence,
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "hostname": socket_hostname(),
    }


def socket_hostname() -> str:
    return socket.gethostname()


def compact(record: dict[str, str]) -> str:
    return (
        f"{record.get('id', '-')} {record.get('pretty', '-')} "
        f"({record.get('codename', '-')}), {record.get('flavor', '-')}, "
        f"kernel {record.get('kernel', '-')}"
    ).strip()


def safe_for_log(record: dict[str, str]) -> dict[str, str]:
    allowed = (
        "id", "pretty", "version", "codename", "flavor",
        "flavor_evidence", "kernel", "architecture", "hostname",
    )
    return {k: record.get(k, "") for k in allowed if k in record}
