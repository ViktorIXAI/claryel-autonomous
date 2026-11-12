#!/usr/bin/env bash
# 16 GiB VRAM / <=32 GiB RAM throughput+profit matrix on the brain box.
# Baseline engine block is rewritten every arm (no key leaks between arms).
# Each arm: apply keys, restart, bounded health wait, warm bench with GPU+RAPL sampling,
# record engine lines, RAM/VRAM, and count foreign (agent) requests inside the window.
cd ~/basalt
MODEL=qwen3.8-flash-next-iq3_s-basalt
cat > /tmp/v3_base.json <<'JSON'
{
  "server": {"model": "model/Qwen3.8-FN-IQ3_S.basalt", "alias": "qwen3.8-flash-next-iq3_s-basalt",
             "gpu": "0", "host": "0.0.0.0", "port": 8080},
  "engine": {"max-context": 262144, "kv": "int8", "resident-experts": true, "expert-cache": "auto",
             "prefill": "auto", "vram-reserve-mib": 8079, "resident-budget-gib": 22,
             "conversation-cache-mib": 6144, "conversation-cache-slots": 6,
             "conversation-cache-disk-mib": 20480}
}
JSON
apply() { cp /tmp/v3_base.json basalt-config.json; python3 - "$@" <<'PY'
import json,sys
p="basalt-config.json"; d=json.load(open(p))
for a in sys.argv[1:]:
    k,v=a.split("=",1)
    d["engine"][k]=int(v) if v.isdigit() else (True if v=="true" else (False if v=="false" else v))
json.dump(d,open(p,"w"),indent=2)
PY
}
arm() {
  name=$1; shift
  apply "$@"
  pkill -f "[b]in/basalt"; sleep 3; bash run-serve.sh
  ok=0
  for i in $(seq 1 10); do curl -s -m 8 http://127.0.0.1:8080/health | grep -q '"loaded": true' && { ok=1; break; }; sleep 8; done
  echo "=== arm $name (loaded=$ok after $((i*8))s)"
  [ $ok -eq 0 ] && { tail -4 basalt-serve.log | cut -c1-150; return; }
  mark=$(wc -l < basalt-serve.log)
  rapl0=$(awk '{print $1}' /sys/class/powercap/intel-rapl:0/energy_uj)
  : > /tmp/v3_pow.txt
  ( end=$((SECONDS+80)); while [ $SECONDS -lt $end ]; do printf "%s %s\n" "$(date +%s.%N)" "$(nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits)" >> /tmp/v3_pow.txt; sleep 1; done ) &
  spid=$!
  b0=$(date +%s.%N)
  for r in 1 2 3; do BRAIN_KEY=$(cat basalt.key) python3 brainbench.py http://127.0.0.1:8080/v1 1 $MODEL 600 1024 > /dev/null 2>&1; done
  b1=$(date +%s.%N)
  kill $spid 2>/dev/null
  free -h | sed -n '2p'
  nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
  tail -n +$((mark+1)) basalt-serve.log | grep -aE "s[0-9] done" | grep -av "pp=878" | wc -l | sed 's/^/foreign_in_window /'
  tail -n +$((mark+1)) basalt-serve.log | grep -aE "s[0-9] done" | grep -a "pp=878" | cut -c1-150
  tail -n +$((mark+1)) basalt-serve.log | grep -aE "ram  +floor" | tail -1 | cut -c1-150
  awk -v a="$b0" -v b="$b1" '$1>=a && $1<=b {s+=$2; n++; if($2>m)m=$2} END{if(n)printf "gpu_W %.1f (max %.1f n=%d)\n", s/n, m, n}' /tmp/v3_pow.txt
  awk -v e0="$rapl0" -v e1="$rapl1" -v t0="$b0" -v t1="$b1" 'BEGIN{printf "cpu_W %.1f window %.0fs\n", (e1-e0)/1e6/(t1-t0), t1-t0}'
}
arm base
arm spec4            spec=4
arm spec7            spec=7
arm spec4-suffix     spec=4 suffix-draft=true
arm spec4-kvres2048  spec=4 kv-resident=2048
arm spec4-kvres-b28  spec=4 kv-resident=2048 resident-budget-gib=28
arm spec4-ctx65k     spec=4 max-context=65536
arm spec4-elastic    spec=4 vram-elastic=true
echo ALL_V3_DONE
