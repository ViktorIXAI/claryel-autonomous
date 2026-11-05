#!/usr/bin/env python3
"""Write benchmarks/hard/MANIFEST.sha256 for bank + checkers + expected refs."""
from __future__ import annotations
import hashlib, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "benchmarks" / "hard" / "MANIFEST.sha256"
FILES = [
    "benchmarks/hard/bank-hard.json",
    "benchmarks/hard/bank-hard-v5.json",
    "benchmarks/hard/c_position_dist_v6.json",
    "benchmarks/hard/PROTOCOL.md",
    "benchmarks/hard/SCOREBOARD.md",
    "harness/parb_check.py",
    "harness/parb_loop.py",
    "harness/gate_run.py",
    "scripts/dedup_hard_bank.py",
    "scripts/build_hard_v6.py",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    lines = []
    lines.append("# hard bank v6 draft manifest — refs/checkers/hashes BEFORE any arm run")
    lines.append("# format: sha256  relative/path")
    for rel in FILES:
        p = ROOT / rel
        if not p.exists():
            lines.append(f"# MISSING  {rel}")
            continue
        lines.append(f"{sha256(p)}  {rel}")
    # also embed bank id list + ref digests for audit
    bank = json.loads((ROOT / "benchmarks/hard/bank-hard.json").read_text(encoding="utf-8"))
    ref_blob = json.dumps([{ "id": t["id"], "ref": t.get("ref"), "text_ref": t.get("text_ref"), "kind": t.get("kind"), "n_cand": t.get("n_cand") } for t in bank], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    rh = hashlib.sha256(ref_blob.encode("utf-8")).hexdigest()
    lines.append(f"{rh}  benchmarks/hard/EXPECTED_REFS.sha256payload")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", OUT)
    for ln in lines:
        if not ln.startswith("#"):
            print(ln[:80])


if __name__ == "__main__":
    main()
