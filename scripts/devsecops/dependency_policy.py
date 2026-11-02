#!/usr/bin/env python3
"""Dependency supply-chain policy.

This repository intentionally keeps the runtime dependency set empty.
If dependencies are ever added, they must be pinned and reviewed.
"""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    failures = []

    if any(ROOT.glob("requirements*.txt")):
        failures.append("requirements*.txt is not allowed; use explicit pinned dependencies in pyproject.toml")

    if any(ROOT.glob("poetry.lock")):
        failures.append("poetry.lock is not allowed; use a reviewed lock policy before enabling it")

    with (ROOT / "pyproject.toml").open("rb") as f:
        data = tomllib.load(f)

    deps = data.get("project", {}).get("dependencies", [])
    optional = data.get("project", {}).get("optional-dependencies", {})

    for dep in deps:
        if not any(op in dep for op in ("==", ">=", "<=", "~=")):
            failures.append(f"unpinned dependency: {dep}")

    for extra, values in optional.items():
        for dep in values:
            if not any(op in dep for op in ("==", ">=", "<=", "~=")):
                failures.append(f"unpinned optional dependency [{extra}]: {dep}")

    if failures:
        print("Dependency policy failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Dependency policy: ok (runtime deps: {len(deps)}, optional groups: {len(optional)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
