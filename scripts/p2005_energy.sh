#!/usr/bin/env bash
# P2005 energy under decode load: timestamped GPU (nvidia-smi) + CPU package (RAPL) samples,
# plus the engine's own tg=/pp= accounting lines for the same window.
cd ~/basalt
logmark=$(wc -l < basalt-serve.log)
rapl0=$(awk '{print $1}' /sys/class/powercap/intel-rapl:0/energy_uj); r0=$(date +%s.%N)
: > /tmp/p2005_pow.txt
end=$((SECONDS+110))
( while [ $SECONDS -lt $end ]; do printf "%s %s\n" "$(date +%s.%N)" "$(nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits)" >> /tmp/p2005_pow.txt; sleep 1; done ) &
SPID=$!
b0=$(date +%s.%N)
BRAIN_KEY=$(cat basalt.key) python3 brainbench.py http://127.0.0.1:8080/v1 2 qwen3.8-flash-next-iq3_s-basalt 600 1024 > /tmp/p2005_bench.txt 2>&1
b1=$(date +%s.%N)
kill $SPID 2>/dev/null
rapl1=$(awk '{print $1}' /sys/class/powercap/intel-rapl:0/energy_uj); r1=$(date +%s.%N)
echo "=== bench (SSE client)"
python3 - <<PY
import json
d=json.load(open("/tmp/p2005_bench.txt"))
for r in d["runs"]:
    print({k:(round(v,3) if isinstance(v,float) else v) for k,v in r.items()})
PY
echo "=== engine lines for this run"
tail -n +$((logmark+1)) basalt-serve.log | grep -aE "done|pp=|tg=" | tail -6 | cut -c1-190
echo "=== power"
awk -v a="$b0" -v b="$b1" '$1>=a && $1<=b {s+=$2; n++; if($2>m)m=$2} END{if(n)printf "gpu_W_avg_in_bench %.1f gpu_W_max %.1f samples %d\n", s/n, m, n; else print "no samples in bench window"}' /tmp/p2005_pow.txt
awk -v e0="$rapl0" -v e1="$rapl1" -v t0="$r0" -v t1="$r1" 'BEGIN{printf "cpu_package_W_window %.1f (window %.0fs incl. idle)\n", (e1-e0)/1e6/(t1-t0), t1-t0}'
