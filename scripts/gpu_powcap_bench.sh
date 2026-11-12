#!/bin/bash
# P3001 / RX 580: decode+prefill speed vs GPU power cap, on the models that are fast and useful here.
# Caps: 120 W (VBIOS ceiling / default), 100, 70, 50, 30 W. OD off, level=high for a clean A/B.
export GGML_VK_VISIBLE_DEVICES=0
R=$HOME/llama-vulkan/powcap_report.txt; : > $R
say(){ echo "$(date +%H:%M:%S) $*" | tee -a $R; }
LKB=$(find $HOME/llama-vulkan -name llama-bench -type f | head -1)
N4=$HOME/nemotron/Nano-4B-Q4_K_M.gguf
BO=$HOME/nemotron/Bolt-E4B-Q4_K_XL.gguf
TH=$(find $HOME -name "Qwen2.5-3B-Instruct-Q4_K_M.gguf" -type f 2>/dev/null | head -1)
OUR=$HOME/Strata-data/models/IQ3_S/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf
CARD=$(for c in /sys/class/drm/card*/device; do d=$(readlink -f $c/driver); [ "$(basename $d)" = "amdgpu" ] && echo $c; done | head -1)
HW=$(ls -d $CARD/hwmon/hwmon* | head -1)
WIN=$HOME/llama-vulkan/powcap_windows.txt
SAMP=$HOME/llama-vulkan/powcap_power.csv
RUN=$HOME/llama-vulkan/powcap_running

say "== preflight"
for f in "$N4" "$BO" "$TH" "$OUR"; do [ -f "$f" ] && say "   ok $(basename $f)" || say "   MISSING $f"; done
say "   card=$CARD hwmon=$HW cap=$(($(cat $HW/power1_cap)/1000000))W min=$(($(cat $HW/power1_cap_min 2>/dev/null || echo 0)/1000000))W max=$(($(cat $HW/power1_cap_max)/1000000))W"
say "   waiting for the bonsai chain to release the GPU"
while pgrep -x llama-bench >/dev/null 2>&1 || ! grep -q DONE_BONSAI9 $HOME/llama-vulkan/bonsai9_report.txt 2>/dev/null; do sleep 20; done
say "== start"
touch $RUN
setsid nohup bash $HOME/p3001_powcap_sampler.sh "$HW" "$CARD" "$SAMP" >/dev/null 2>&1 &
sleep 2; say "   sampler pid=$(cat $HOME/llama-vulkan/powcap_sampler.pid 2>/dev/null)"

setcap(){ echo $(( $1 * 1000000 )) | sudo tee $HW/power1_cap >/dev/null 2>&1
  echo 0 | sudo tee $CARD/pp_sclk_od >/dev/null 2>&1; echo 0 | sudo tee $CARD/pp_mclk_od >/dev/null 2>&1
  echo high | sudo tee $CARD/power_dpm_force_performance_level >/dev/null 2>&1
  say "   cap=$(($(cat $HW/power1_cap)/1000000))W level=$(cat $CARD/power_dpm_force_performance_level) od=$(cat $CARD/pp_sclk_od)/$(cat $CARD/pp_mclk_od)"; }

bench(){ local tag="$1"; shift; echo "$tag $(date +%s)" >> $WIN
  local out=$(timeout 900 $LKB "$@" -pg "512,128" -r ${PC_REPS:-2} 2>&1)
  echo "$tag $(( $(date +%s) )) " >> $WIN; sed -i "\$s/\$/$(( $(date +%s) ))/" $WIN
  echo "$out" | grep -E "\| *(pp512|tg128) " | awk -F'|' -v t="$tag" '{v=$NF; gsub(/ ±.*/,"",v); gsub(/ /,"",v); printf "   %-26s %s = %s\n", t, $(NF-1), v}' | tee -a $R
  echo "$out" | grep -iE "error|failed|out of memory|cannot" | head -2 | sed 's/^/   ! /' | tee -a $R
  sleep 12; }

: > $WIN
for CAP in 120 100 70 50 30; do
  say "== cap ${CAP} W"
  setcap $CAP
  bench "cap${CAP}_3B"      -m "$TH"  -ngl 99 -fa off
  bench "cap${CAP}_Nano4B"  -m "$N4"  -ngl 99 -fa off
  bench "cap${CAP}_BoltE4B" -m "$BO"  -ngl 99 -fa off
  PC_REPS=1 bench "cap${CAP}_ourIQ3S" -m "$OUR" -ngl 99 -ncmoe 99 -ctk q8_0 -ctv q8_0 -fa off
done

kill $(cat $HOME/llama-vulkan/powcap_sampler.pid) 2>/dev/null; rm -f $RUN
say "== restore"
cat $HW/power1_cap_default | sudo tee $HW/power1_cap >/dev/null 2>&1
echo auto | sudo tee $CARD/power_dpm_force_performance_level >/dev/null 2>&1
say "   cap=$(($(cat $HW/power1_cap)/1000000))W level=$(cat $CARD/power_dpm_force_performance_level)"
python3 - <<'PY' | tee -a $R
import csv,os
D=os.path.expanduser('~/llama-vulkan')
W=[l.split() for l in open(D+'/powcap_windows.txt') if l.strip()]
S=[r for r in csv.DictReader(open(D+'/powcap_power.csv'))]
print("   window                      avg_W   max_W  clk_avg  n")
for w in W:
    tag,s = w[0], int(w[1]); e = int(w[2]) if len(w)>2 else s
    rows=[r for r in S if s<=int(r['epoch'])<=e]
    pw=[float(r['power_W']) for r in rows if float(r['power_W'])>5]
    ck=[float(r['gpu_clk']) for r in rows if float(r['gpu_clk'])>0]
    if pw: print(f"   {tag:26s} {sum(pw)/len(pw):6.1f} {max(pw):6.0f} {sum(ck)/len(ck) if ck else 0:8.0f} {len(pw):4d}")
PY
say DONE_POWCAP
