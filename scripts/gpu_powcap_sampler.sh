#!/bin/bash
# 1 s GPU power/clock sampler: sampler.sh <hwmon_dir> <card_device_dir> <out_csv>
HW=$1; CARD=$2; OUT=$3
echo $$ > "$HOME/llama-vulkan/powcap_sampler.pid"
echo "epoch,power_W,gpu_clk" > "$OUT"
while [ -e "$HOME/llama-vulkan/powcap_running" ]; do
  p=$(cat "$HW/power1_input" 2>/dev/null || echo 0)
  c=$(cat "$HW/gpu_clock" 2>/dev/null)
  [ -z "$c" ] && c=$(awk '/\*/ {gsub(/[^0-9]/, "", $3); print $3; exit}' "$CARD/pp_dpm_sclk" 2>/dev/null)
  case "$c" in (''|*[!0-9]*) c=0;; esac
  echo "$(date +%s),$(( p / 1000000 )),$c" >> "$OUT"
  sleep 1
done
