#!/usr/bin/env python3
"""Dry-run 4 arms against ONE v6 scorer import — no models, no inference.

Reports path + sha256 of the scorer module once, then per-arm per-category
coverage over the 11 categories plus D plain / D loop split.
Exit 0 when every arm resolves the identical check() / check_D_loop_v6 symbols
and the bank loads 77 tasks.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness"))

ARMS = ("contour", "basalt_raw", "codex_raw", "grok_raw")
CATS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def main() -> int:
    scorer_path = (ROOT / "harness" / "parb_check_v6.py").resolve()
    bank_path = (ROOT / "benchmarks" / "hard" / "bank-hard-v6.json").resolve()
    sandbox_path = (ROOT / "harness" / "e_sandbox.py").resolve()

    print("SCORER_PATH", scorer_path)
    print("SCORER_SHA256", sha256(scorer_path))
    print("BANK_PATH", bank_path)
    print("BANK_SHA256", sha256(bank_path))
    print("SANDBOX_PATH", sandbox_path)
    print("SANDBOX_SHA256", sha256(sandbox_path))

    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    assert len(bank) == 77, len(bank)
    by_cat = Counter(t["cat"] for t in bank)
    d_plain = sum(1 for t in bank if t["cat"] == "D" and t.get("mode") != "loop")
    d_loop = sum(1 for t in bank if t["cat"] == "D" and t.get("mode") == "loop")

    # Import ONE scorer module; all arms share it.
    v6 = importlib.import_module("parb_check_v6")
    check_id = id(v6.check)
    loop_id = id(v6.check_D_loop_v6)
    bat_id = id(v6.run_battery)

    print("IMPORT parb_check_v6 OK")
    print("SYMBOL check id=%s file=%s" % (check_id, getattr(v6.check, "__code__", None) and v6.check.__code__.co_filename))
    print("SYMBOL check_D_loop_v6 id=%s" % loop_id)
    print("SYMBOL run_battery id=%s" % bat_id)

    # Prove run_battery default path references run_docker (fail-closed), not run_sandboxed.
    import inspect
    src = inspect.getsource(v6.run_battery)
    if "run_sandboxed" in src and "run_docker" not in src:
        print("FAIL run_battery still defaults to run_sandboxed")
        return 1
    if "run_docker" not in src:
        print("FAIL run_battery missing run_docker")
        return 1
    if "sandbox_fail_closed" not in inspect.getsource(v6):
        print("FAIL missing fail-closed marker")
        return 1
    print("DEFAULT_PATH run_docker+fail_closed OK")

    rc = 0
    for arm in ARMS:
        print("ARM", arm)
        # same module object — re-import returns cached
        v6b = importlib.import_module("parb_check_v6")
        if id(v6b.check) != check_id or id(v6b.check_D_loop_v6) != loop_id:
            print("  FAIL scorer identity drift")
            rc = 1
            continue
        print("  scorer_path", scorer_path)
        print("  scorer_sha256", sha256(scorer_path))
        for cat in CATS:
            n = by_cat.get(cat, 0)
            print("  cat", cat, "tasks", n)
        print("  cat D_plain tasks", d_plain)
        print("  cat D_loop tasks", d_loop)
        # smoke: score one gold-shaped A via shared check
        a = next(t for t in bank if t["cat"] == "A")
        ans = json.dumps(a["ref"], ensure_ascii=False)
        c, f, notes = v6b.check(a, ans)
        print("  smoke_A content=%.2f format=%s notes=%s" % (c, f, notes))

    print("DRY_RUN_SAME_SCORER", "PASS" if rc == 0 else "FAIL")
    return rc


if __name__ == "__main__":
    sys.exit(main())
