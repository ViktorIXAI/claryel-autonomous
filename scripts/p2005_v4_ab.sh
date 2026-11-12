#!/usr/bin/env bash
# Round 4: squeeze decode under a hard 16 GiB VRAM window and <=32 GiB host RAM, with per-arm
# energy (GPU nvidia-smi + CPU RAPL with wrap handling) so every arm gets W and a cost number.
cd ~/basalt
MODEL=qwen3.8-flash-next-iq3_s-basalt
cat > /tmp/v4_base.json <<'JSON'
{
  "server": {"model": "model/Qwen3.8-FN-IQ3_S.basalt", "alias": "qwen3.8-flash-next-iq3_s-basalt",
             "gpu": "0", "host": "0.0.0.0", "port": 8080},
  "engine": {"max-context": 262144, "kv": "int8", "resident-experts": true, "expert-cache": "auto",
             "prefill": "auto", "vram-reserve-mib": 8079, "resident-budget-gib": 22,
             "conversation-cache-mib": 6144, "conversation-cache-slots": 6,
             "conversation-cache-disk-mib": 20480}
}
JSON
apply() { cp /tmp/v4_base.json basalt-config.json; python3 - "$@" <<'PY'
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
  echo "=== arm $name (loaded=$ok)"
  [ $ok -eq 0 ] && { tail -3 basalt-serve.log | cut -c1-150; return; }
  mark=$(wc -l < basalt-serve.log)
  : > /tmp/v4_pow.txt; : > /tmp/v4_rapl.txt
  ( end=$((SECONDS+150)); while [ $SECONDS -lt $end ]; do printf "%s %s\n" "$(date +%s.%N)" "$(nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits)" >> /tmp/v4_pow.txt; awk '{printf "%s %s\n", systime()+0, $1}' /sys/class/powercap/intel-rapl:0/energy_uj >> /tmp/v4_rapl.txt; sleep 1; done ) &
  spid=$!
  for r in 1 2 3 4 5 6; do BRAIN_KEY=$(cat basalt.key) python3 brainbench.py http://127.0.0.1:8080/v1 1 $MODEL 600 1024 > /dev/null 2>&1; done
  kill $spid 2>/dev/null
  free -h | sed -n '2p'
  nvidia-smi --query-gpu=memory.used --format=csv,noheader
  tail -n +$((mark+1)) basalt-serve.log | grep -aE "s[0-9] done" | grep -avc "pp=878" | sed 's/^/foreign_in_window /'
  tail -n +$((mark+1)) basalt-serve.log | grep -aE "s[0-9] done" | grep -a "pp=878" | cut -c1-150
  python3 - <<PY
gpu=[float(l.split()[1]) for l in open("/tmp/v4_pow.txt")]
raw=[(float(l.split()[0]), int(l.split()[1])) for l in open("/tmp/v4_rapl.txt")]
mx=int(open("/sys/class/powercap/intel-rapl:0/max_energy_range_uj").read().strip())
cpu=[]
for (t1,e1),(t2,e2) in zip(raw,raw[1:]):
    d=e2-e1
    if d<0: d+=mx
    dt=t2-t1
    if dt>0: cpu.append(d/1e6/dt)
if gpu: print("gpu_W avg %.1f p90 %.1f max %.1f n=%d" % (sum(gpu)/len(gpu), sorted(gpu)[int(len(gpu)*.9)], max(gpu), len(gpu)))
if cpu: print("cpu_W avg %.1f p90 %.1f max %.1f n=%d" % (sum(cpu)/len(cpu), sorted(cpu)[int(len(cpu)*.9)], max(cpu), len(cpu)))
PY
}
arm base
arm spec2            spec=2
arm spec4            spec=4
arm spec7            spec=7
arm ctx65k-spec7     spec=7 max-context=65536
arm ec12000          spec=4 expert-cache=12000
arm cpux-experts     spec=4 resident-cpu-experts=true
arm mtp2             spec=4 mtp-max-t=2
echo ALL_V4_DONE
