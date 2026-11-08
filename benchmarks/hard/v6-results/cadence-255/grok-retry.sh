#!/usr/bin/env bash
# cadence-255 grok leg retry (transport dead in first 186 calls; token healed mid-leg)
export PATH="$HOME/.local/bin:$PATH"
command -v hermes >/dev/null || { echo "ABORT: hermes not on PATH" >&2; exit 1; }
export PARB_RAW_WS="$HOME/parb-b66-raw-reps"
date +%s > "$PARB_RAW_WS/cloud-grokretry-start.epoch"
cd "$PARB_RAW_WS"
python3 "$HOME/sah-main/scripts/raw_v6.py" grok 52,53,54 >> band-grok-retry.log 2>&1
rc=$?
date +%s > "$PARB_RAW_WS/cloud-grokretry-end.epoch"
echo "cad255 grok-retry done rc=$rc $(date -Iminutes)" >> band-grok-retry.log
