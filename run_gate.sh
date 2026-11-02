#!/usr/bin/env bash
# Launch one resumable contour series (Mode 1). Assumes config.sh sourced.
set -euo pipefail
cd "$(dirname "$0")"

if [ -n "${PARB_TELEM:-}" ] && [ -z "${PARB_TELEM_CHILD:-}" ]; then
  exec env PARB_TELEM_CHILD=1 "$PWD/scripts/telemetry/run_with_collector.sh" bash "$PWD/run_gate.sh"
fi

: "${PARB_ROOT:=$HOME/parb}"
mkdir -p "$PARB_ROOT"
[ -f "$PARB_ROOT/plan.json" ] || python3 harness/make_plan.py
cd harness
exec python3 gate_run.py
