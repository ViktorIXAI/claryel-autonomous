#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify MANIFEST.v5.sha256 / MANIFEST.v6.sha256 before any gate run.

Usage:
  python3 harness/verify_manifest.py                 # both manifests
  python3 harness/verify_manifest.py --v5
  python3 harness/verify_manifest.py --v6
  python3 harness/verify_manifest.py path/to/MANIFEST.sha256

Exit 0 on match; non-zero on drift / missing file.
Does not print file contents — only paths and hash status.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = [
    ROOT / "benchmarks" / "hard" / "MANIFEST.v5.sha256",
    ROOT / "benchmarks" / "hard" / "MANIFEST.v6.sha256",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_manifest(path: Path) -> list[tuple[str, str]]:
    rows = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) < 2:
            raise ValueError("bad manifest line in %s: %r" % (path, ln))
        digest, rel = parts[0], parts[1]
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("bad digest in %s: %r" % (path, digest))
        rows.append((digest, rel))
    return rows


def verify_one(manifest: Path) -> int:
    if not manifest.is_file():
        print("MISSING_MANIFEST", manifest)
        return 1
    bad = 0
    rows = parse_manifest(manifest)
    print("manifest", manifest.relative_to(ROOT) if manifest.is_relative_to(ROOT) else manifest, "entries", len(rows))
    for want, rel in rows:
        p = ROOT / rel
        if not p.is_file():
            print("MISSING", rel)
            bad += 1
            continue
        got = sha256_file(p)
        if got != want:
            print("DRIFT", rel)
            print("  want", want)
            print("  got ", got)
            bad += 1
        else:
            print("OK", got[:16], rel)
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifests", nargs="*", type=Path)
    ap.add_argument("--v5", action="store_true")
    ap.add_argument("--v6", action="store_true")
    args = ap.parse_args(argv)

    targets: list[Path] = []
    if args.manifests:
        targets.extend(args.manifests)
    if args.v5:
        targets.append(ROOT / "benchmarks" / "hard" / "MANIFEST.v5.sha256")
    if args.v6:
        targets.append(ROOT / "benchmarks" / "hard" / "MANIFEST.v6.sha256")
    if not targets:
        targets = list(DEFAULTS)

    # de-dupe preserving order
    seen = set()
    uniq = []
    for t in targets:
        t = t.resolve() if t.is_absolute() else (ROOT / t).resolve() if not str(t).startswith("/") else t
        if not t.is_absolute():
            t = (Path.cwd() / t).resolve()
        if t in seen:
            continue
        seen.add(t)
        uniq.append(t)

    rc = 0
    for m in uniq:
        rc |= verify_one(m)
    if rc:
        print("VERIFY FAIL")
    else:
        print("VERIFY PASS")
    return rc


if __name__ == "__main__":
    sys.exit(main())
