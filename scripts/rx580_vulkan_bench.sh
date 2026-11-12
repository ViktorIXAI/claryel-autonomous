#!/bin/bash
# P3001: (1) full error for our-model GPU offload, (2) 8-10 min sustained Vulkan GPU stress for thermal read,
# (3) our model with small layer offload.
D=$HOME/llama-vulkan
BIN=$D/llama-b12318/llama-bench
OUR=$HOME/Strata-data/models/IQ3_S/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf
SML=$D/models/Qwen2.5-3B-Instruct-Q4_K_M.gguf
R=$D/report4.txt
: > $R
say(){ echo "$(date +%H:%M:%S) $*" | tee -a $R; }
export GGML_VK_VISIBLE_DEVICES=0

say "1) our model -ngl 99 full stderr"
timeout 300 $BIN -m $OUR -ngl 99 -ncmoe 99 -pg "8,8" -r 1 --no-warmup 2>&1 | grep -vE "^ggml_vulkan: [0-9]|load_backend" | tail -25 | tee -a $R

say "2) GPU stress (3B on RX580, sustained prefill) for thermals"
nohup bash -c 'while true; do echo "$(date +%H:%M:%S) $(( $(cat /sys/class/drm/card1/device/hwmon/hwmon3/power1_input)/1000 ))W $(( $(cat /sys/class/drm/card1/device/hwmon/hwmon3/temp1_input)/1000 ))C busy=$(cat /sys/class/drm/card1/device/gpu_busy_percent) clock=$(cat /sys/class/drm/card1/device/hwmon/hwmon3/freq1_input)" >> ~/llama-vulkan/stress_pow.log; sleep 10; done' > /dev/null 2>&1 &
MON=$!
timeout 900 $BIN -m $SML -ngl 99 -fa off -pg "2048,256" -r 4 2>&1 | grep -E "Qwen|pp2048|tg256|error|Error" | tail -12 | tee -a $R
kill $MON 2>/dev/null
say "   stress power/temp trace:"
tail -20 $D/stress_pow.log | tee -a $R

say "3) our model with partial offload"
for ngl in 4 12 24; do
  say "3.$ngl our-model ngl=$ngl ncmoe=99"
  timeout 900 $BIN -m $OUR -ngl $ngl -ncmoe 99 -ctk q8_0 -ctv q8_0 -fa off -pg "512,128" -r 2 2>&1 | grep -E "qwen4exp|offloaded|error|Error|out of memory|not enough|pp512|tg128" | tail -10 | tee -a $R
done
say "ALL_DONE4"
