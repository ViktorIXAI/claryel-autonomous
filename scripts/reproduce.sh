#!/usr/bin/env bash
# Reproduce every published number from the release archive.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d artifacts ] || { echo "unpack artifacts-release-2026-11-01.tar.zst here first (see results/independent-validation.md)"; exit 2; }
echo "[1/3] verifying raw archive against logs/INDEX.md ..."
python3 - <<'EOF'
import hashlib, re, sys, os
bad = 0
for ln in open("logs/INDEX.md", encoding="utf-8"):
    m = re.match(r"\| (\S+\.jsonl) \| .* \| (\d+) \| `([0-9a-f]{16})`", ln)
    if not m:
        continue
    rel, size, want = m.group(1), int(m.group(2)), m.group(3)
    p = os.path.join("artifacts", rel)
    if not os.path.exists(p):
        print("MISSING", rel); bad += 1; continue
    data = open(p, "rb").read()
    got = hashlib.sha256(data).hexdigest()[:16]
    if len(data) != size or got != want:
        print("MISMATCH", rel, size, len(data), want, got); bad += 1
sys.exit(1 if bad else 0)
EOF
echo "[2/3] recomputing aggregates ..."
PARB_ARTIFACTS=./artifacts python3 analytics/aggregate.py > /tmp/summary-recomputed.json
echo "[3/3] diffing against committed summary ..."
diff <(python3 -m json.tool results/summary.json) <(python3 -m json.tool /tmp/summary-recomputed.json) \
  && echo "IDENTICAL — published numbers verified" || { echo "MISMATCH — do not trust the README tables"; exit 1; }
