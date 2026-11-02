#!/usr/bin/env bash
# Run a command with a 1 Hz resource collector around it.
#
# Required:
#   PARB_TELEM=/absolute/or/relative/path/to/samples.jsonl
# Optional:
#   PARB_TELEM_INTERVAL=1.0
#   PARB_MACHINE=BOX
#   PARB_GPU_INDEX=0
#
# Example:
#   PARB_TELEM=parb/telemetry/samp.jsonl \
#   scripts/telemetry/run_with_collector.sh \
#     python3 harness/gate_run.py run
set -euo pipefail

if [ -z "${PARB_TELEM:-}" ]; then
  echo "PARB_TELEM is required" >&2
  exit 2
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${PARB_REPO:-$(cd "$HERE/../.." && pwd)}"
INTERVAL="${PARB_TELEM_INTERVAL:-1.0}"
mkdir -p "$(dirname "$PARB_TELEM")"

python3 "$REPO/telemetry/collector2.py" "$PARB_TELEM" \
  --interval "$INTERVAL" \
  --run-id "${PARB_TELEM_RUN_ID:-$(basename "${PARB_TELEM%.*}")}" \
  &
COLLECTOR_PID=$!

cleanup() {
  kill "$COLLECTOR_PID" 2>/dev/null || true
  wait "$COLLECTOR_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

"$@"
