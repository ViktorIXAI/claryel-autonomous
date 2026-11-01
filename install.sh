#!/usr/bin/env bash
# One-time setup: stdlib-only harness, isolated venv, run the self-tests.
set -euo pipefail
cd "$(dirname "$0")"

PY="$(command -v python3 || true)"
if [ -z "$PY" ] || ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
  echo "python >= 3.9 required (the harness uses only the standard library)" >&2
  exit 1
fi

if [ ! -d .venv ]; then
  "$PY" -m venv .venv
fi
PYV=".venv/bin/python3"
[ -x "$PYV" ] || PYV=".venv/Scripts/python.exe"   # windows venv layout

echo "[install] contour self-tests (mechanical fixers, v1.9 slot normalizer)..."
"$PYV" harness/gate_fixers_test.py
"$PYV" harness/gate_v19_d_test.py

cat <<'EOF'
[install] OK. Next:
  1) cp config.example.sh config.sh   # set PARB_API / PARB_MODEL for your endpoint
  2) source config.sh
  3) bash run_gate.sh                 # builds plan.json from benchmarks/text-gates/bank.json, runs v1.9
EOF
