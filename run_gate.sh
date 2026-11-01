#!/usr/bin/env bash
# Launch one resumable contour series (Mode 1). Assumes config.sh sourced.
set -euo pipefail
cd "$(dirname "$0")"
: "${PARB_ROOT:=$HOME/parb}"
mkdir -p "$PARB_ROOT"
[ -f "$PARB_ROOT/plan.json" ] || python3 harness/make_plan.py
cd harness
exec python3 gate_run.py
