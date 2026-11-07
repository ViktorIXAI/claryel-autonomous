#!/usr/bin/env python3
"""Regenerate benchmarks/hard/MANIFEST.v6.sha256 with full P0 pin set."""
from __future__ import annotations
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "benchmarks" / "hard" / "MANIFEST.v6.sha256"
FILES = [
    "benchmarks/hard/bank-hard-v6.json",
    "benchmarks/hard/BANK-VERSIONS.json",
    "benchmarks/hard/gold-answers-v6.jsonl",
    "benchmarks/hard/c_position_dist_v6.json",
    "benchmarks/hard/PROTOCOL.md",
    "harness/parb_check_v6.py",
    "harness/parb_loop.py",
    "harness/parb_check_v6_2.py",
    "harness/gate_scorer_contract.py",
    "harness/gate_bank_versions.py",
    "harness/parb_bank_v6.py",
    "harness/e_sandbox.py",
    "harness/verify_manifest.py",
    "scripts/gold_selftest_v6.py",
    "scripts/semantic_suite_v6.py",
    "scripts/dry_run_same_scorer_v6.py",
    "scripts/build_hard_v6_ws.py",
    "scripts/dedup_hard_bank.py",
    "scripts/leakage_scan_v6.py",
    "benchmarks/hard/WS-GENERATED.v6.sha256",
    "benchmarks/hard/WS-GENERATED.v62.sha256",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> None:
    lines = [
        "# hard bank official v6 freeze line (issue #15 P0)",
        "# format: sha256  relative/path",
        "# Pins bank + semantic checkers + builder + shim workspace script + gold + suites + sandbox.",
        "# v5 pins live in MANIFEST.v5.sha256 and must stay immutable.",
    ]
    for rel in FILES:
        p = ROOT / rel
        if not p.is_file():
            raise SystemExit("missing pin target: %s" % rel)
        lines.append("%s  %s" % (sha256(p), rel))
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", OUT)
    for ln in lines:
        if not ln.startswith("#"):
            print(ln)


if __name__ == "__main__":
    main()
