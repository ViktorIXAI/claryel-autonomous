#!/bin/bash
# GPU board-power sampler for cadence-255 arm energy windows (fresh csv per cadence, 2 Hz).
set -u
OUT=<LOCAL_PATH>/parb-b66-contour/gpu-power-c255.csv
while true; do
  v=$(ssh <SSH_AUTH_ARGS> \
      <WORKER_HOST> \
      "nvidia-smi --query-gpu=power.draw,utilization.gpu,memory.used,temperature.gpu --format=csv,noheader,nounits" 2>/dev/null)
  [ -n "$v" ] && echo "$(date +%s.%N),$v" >> "$OUT"
  sleep 2
done
