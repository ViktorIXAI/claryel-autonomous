#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sanitize and gate run-record JSON before publish.

Replaces RFC1918 addresses in api_host (and elsewhere) and absolute local
home paths with placeholders. Call sanitize_run_record_dict / write_run_record
from publication scripts; call check_tree from CI.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

HOST_PLACEHOLDER = "<redacted-lan-host>"
PATH_PLACEHOLDER = "<redacted-local-path>"

PRIVATE_IP = re.compile(
    r"\b(?:10(?:\.[0-9]{1,3}){3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|"
    r"172\.(?:1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3})\b"
)
HOME_PATH = re.compile(
    r"(?:/home/[A-Za-z0-9_.-]+|/Users/[A-Za-z0-9_.-]+|C:\\\\Users\\\\[A-Za-z0-9_.-]+)"
)
API_HOST_URL = re.compile(r"^(https?://)([^/:]+)(:\d+)?(/.*)?$")


def _sanitize_string(value: str, *, is_api_host: bool = False) -> str:
    if is_api_host and PRIVATE_IP.search(value):
        m = API_HOST_URL.match(value)
        if m:
            return f"{m.group(1)}{HOST_PLACEHOLDER}{m.group(3) or ''}{m.group(4) or ''}"
        return HOST_PLACEHOLDER
    value = PRIVATE_IP.sub(HOST_PLACEHOLDER, value)
    value = HOME_PATH.sub(PATH_PLACEHOLDER, value)
    return value


def sanitize_run_record_dict(data: Any) -> Any:
    if isinstance(data, dict):
        out = {}
        for key, val in data.items():
            if key == "api_host" and isinstance(val, str):
                out[key] = _sanitize_string(val, is_api_host=True)
            else:
                out[key] = sanitize_run_record_dict(val)
        return out
    if isinstance(data, list):
        return [sanitize_run_record_dict(x) for x in data]
    if isinstance(data, str):
        return _sanitize_string(data)
    return data


def findings_in_text(text: str) -> list[str]:
    hits: list[str] = []
    if PRIVATE_IP.search(text):
        hits.append("private_ip")
    if HOME_PATH.search(text):
        hits.append("home_path")
    return hits


def assert_sanitized_text(text: str, *, path: str = "<memory>") -> None:
    hits = findings_in_text(text)
    if hits:
        raise ValueError(f"unsanitized run-record {path}: {', '.join(hits)}")


def write_run_record(path: Path | str, data: dict) -> None:
    """Pre-publish gate: sanitize, re-validate JSON, refuse to write leaks."""
    path = Path(path)
    clean = sanitize_run_record_dict(data)
    dumped = json.dumps(clean, indent=2, ensure_ascii=False) + "\n"
    assert_sanitized_text(dumped, path=str(path))
    # Round-trip JSON so publication cannot emit corrupted rows.
    json.loads(dumped)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumped, encoding="utf-8")


def check_tree(root: Path | str) -> list[str]:
    root = Path(root)
    bad: list[str] = []
    for path in sorted(root.rglob("run-record*.json")):
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = findings_in_text(text)
        if hits:
            bad.append(f"{path.relative_to(root)}:{','.join(hits)}")
    return bad


def selftest() -> None:
    # Build synthetic values from parts so this source file never contains a
    # literal RFC1918 address or home path that would trip secret-scan.
    lan_a = ".".join(["10", "0", "0", "1"])
    lan_b = ".".join(["172", "16", "1", "2"])
    home = "/" + "/".join(["home", "example", "work"])
    dirty = {
        "api_host": f"http://{lan_a}:8080",
        "notes": f"path {home} and peer {lan_b}",
    }
    clean = sanitize_run_record_dict(dirty)
    assert clean["api_host"] == f"http://{HOST_PLACEHOLDER}:8080", clean
    assert HOST_PLACEHOLDER in clean["notes"] and PATH_PLACEHOLDER in clean["notes"], clean
    assert_sanitized_text(json.dumps(clean))
    try:
        assert_sanitized_text(json.dumps(dirty))
    except ValueError:
        pass
    else:
        raise AssertionError("expected dirty record to fail gate")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check-tree", metavar="ROOT", help="fail if any run-record*.json leaks")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        selftest()
        print("sanitize_run_record selftest ok")
        return 0
    if args.check_tree:
        bad = check_tree(args.check_tree)
        if bad:
            print("unsanitized run-record files:")
            for row in bad:
                print(" ", row)
            return 1
        print("all run-record*.json sanitized")
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
