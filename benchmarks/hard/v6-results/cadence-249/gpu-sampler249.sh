#!/bin/bash
# GPU board-power sampler for cadence-249 arm energy windows (fresh csv per cadence).
set -u
OUT=<LOCAL_PATH>/parb-v64-contour/gpu-power-249.csv
while true; do
  v=$(ssh <SSH_AUTH_ARGS> <WORKER_HOST> \  # key + BatchMode flags redacted (scanner: ssh-connection-material)
      "nvidia-smi --query-gpu=power.draw,utilization.gpu,memory.used,temperature.gpu --format=csv,noheader,nounits" 2>/dev/null)
  [ -n "$v" ] && echo "$(date +%s.%N),$v" >> "$OUT"
  sleep 2
done
