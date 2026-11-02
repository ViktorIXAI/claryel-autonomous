#!/usr/bin/env python3
"""Four-part version scheme for contour/harness releases.

Canonical form: ``A.B.C.D``

* ``A.B``   — operator-controlled release line. The operator may change these
  first two digits without changing contour behaviour.
* ``C``     — contour track. ``1`` is the v1 contour family; ``2`` is the
  v2 contour family.
* ``D``     — contour revision inside that track. It changes whenever an
  audited contour/tooling release must be distinguishable in paired results:
  contour logic, measurement methodology, or gate reporting output.

Legacy names are accepted: ``v2.2`` and ``2.2`` become the current release
line plus contour tuple ``2.2``.
"""
from __future__ import annotations

import os
import re

DEFAULT_RELEASE_LINE = (0, 0)
CURRENT_CONTOUR = (2, 3)


def _digits(value: str) -> list[int]:
    return [int(x) for x in re.findall(r"\d+", value)]


def parse_release_line(value: str | None = None) -> tuple[int, int]:
    raw = os.environ.get("PARB_VERSION_PREFIX") if value is None else value
    parts = _digits(raw or "")
    if len(parts) >= 2:
        return (parts[0], parts[1])
    return DEFAULT_RELEASE_LINE


def parse_version(value: str | None = None) -> tuple[int, int, int, int]:
    raw = os.environ.get("PARB_GATE_VERSION") if value is None else value
    s = str(raw or "").strip().lower()
    if not s:
        return parse_release_line() + CURRENT_CONTOUR
    s = s.replace("contour", "").replace("v", "", 1).strip()
    parts = _digits(s)

    if len(parts) == 2:
        return parse_release_line() + (parts[0], parts[1])
    if len(parts) == 4:
        return (parts[0], parts[1], parts[2], parts[3])

    raise ValueError(f"unsupported contour version: {raw!r}")


def contour_tuple(value: str | None = None) -> tuple[int, int]:
    return parse_version(value)[2:]


def format_version(value: str | None = None) -> str:
    return ".".join(str(x) for x in parse_version(value))


def at_least(track: int, revision: int, value: str | None = None) -> bool:
    return contour_tuple(value) >= (track, revision)


def summary(value: str | None = None) -> dict[str, str]:
    version = parse_version(value)
    return {
        "canonical_version": ".".join(str(x) for x in version),
        "release_line": ".".join(str(x) for x in version[:2]),
        "contour_version": ".".join(str(x) for x in version[2:]),
    }
