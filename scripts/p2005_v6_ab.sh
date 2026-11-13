#!/usr/bin/env bash
# Maximum-out pass: host RAM allowed up to ~61 GiB (box has 60.5 GiB physical), VRAM still fenced at 16 GiB.
# Ladder 42 (control) -> 50 -> 55 -> 61, watching for swap thrash: pswpin/pswpout deltas and maj_flt.
cd ~/basalt
MODEL=qwen3.8-flash-next-iq3_s-basalt
cat > /tmp/v6_base.json <<'JSON'
{
  "server": {"model": "model/Qwen3.8-FN-IQ3_S.basalt", "alias": "qwen3.8-flash-next-iq3_s-basalt",
             "gpu": "0", "host": "0.0.0.0", "port": 8080},
  "engine": {"max-context": 262144, "kv": "int8", "resident-experts": true, "expert-cache": "auto",
             "prefill": "auto", "vram-reserve-mib": 8079, "resident-budget-gib": 42,
             "resident-cpu-experts": true, "conversation-cache-mib": 6144,
             "conversation-cache-slots": 6, "conversation-cache-disk-mib": 20480}
}
JSON
apply() { cp /tmp/v6_base.json basalt-config.json; python3 - "$@" <<'PY'
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
  for i in $(seq 1 12); do curl -s -m 8 http://127.0.0.1:8080/health | grep -q '"loaded": true' && { ok=1; break; }; sleep 8; done
  echo "=== arm $name (loaded=$ok)"
  [ $ok -eq 0 ] && { tail -3 basalt-serve.log | cut -c1-150; return; }
  mark=$(wc -l < basalt-serve.log)
  : > /tmp/v6_pow.txt; : > /tmp/v6_rapl.txt; : > /tmp/v6_mem.txt; : > /tmp/v6_swap.txt
  ( end=$((SECONDS+170)); while [ $SECONDS -lt $end ]; do
      printf "%s %s\n" "$(date +%s.%N)" "$(nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits)" >> /tmp/v6_pow.txt
      awk '{printf "%s %s\n", systime()+0, $1}' /sys/class/powercap/intel-rapl:0/energy_uj >> /tmp/v6_rapl.txt
      free -b | awk '/^Mem:/{printf "%s %s %s\n", systime(), $2, $3}' >> /tmp/v6_mem.txt
      awk '/^pswp(in|out)/{printf "%s %s %s\n", systime(), $1, $2}' /proc/vmstat >> /tmp/v6_swap.txt
      sleep 1; done ) &
  spid=$!
  for r in 1 2 3 4 5 6 7; do BRAIN_KEY=$(cat basalt.key) python3 brainbench.py http://127.0.0.1:8080/v1 1 $MODEL 600 1024 > /dev/null 2>&1; done
  BRAIN_KEY=$(cat basalt.key) python3 brainbench.py http://127.0.0.1:8080/v1 1 $MODEL 20000 512 >/dev/null 2>&1
  kill $spid 2>/dev/null
  nvidia-smi --query-gpu=memory.used --format=csv,noheader | sed 's/^/gpu MiB /'
  awk '{if($3>m)m=$3} END{printf "host RAM peak used %.1f GiB\n", m/1073741824}' /tmp/v6_mem.txt
  python3 - <<'PY'
sw={}
for l in open("/tmp/v6_swap.txt"):
    t,n,v=l.split(); sw.setdefault(int(t),{})[n]=int(v)
ts=sorted(sw); si=so=0
for a,b in zip(ts,ts[1:]):
    d1=sw[b].get("pswpin",0)-sw[a].get("pswpin",0); d2=sw[b].get("pswpout",0)-sw[a].get("pswpout",0)
    if d1>0: si=max(si,d1)
    if d2>0: so=max(so,d2)
print("swap max per-second: in %d pages (%.1f MiB) out %d pages (%.1f MiB)" % (si, si*4/1024, so, so*4/1024))
PY
  tail -n +$((mark+1)) basalt-serve.log | grep -aE "s[0-9] done" | grep -avc "pp=878" | sed 's/^/foreign_in_window /'
  tail -n +$((mark+1)) basalt-serve.log | grep -aE "s[0-9] done" | grep -a "pp=878" | cut -c1-150
  tail -n +$((mark+1)) basalt-serve.log | grep -a "pp=20000" | tail -1 | cut -c1-150
  tail -n +$((mark+1)) basalt-serve.log | grep -aE "ram  +floor|resident tiering" | tail -2 | cut -c1-170
  python3 - <<PY
gpu=[float(l.split()[1]) for l in open("/tmp/v6_pow.txt")]
raw=[(float(l.split()[0]), int(l.split()[1])) for l in open("/tmp/v6_rapl.txt")]
mx=int(open("/sys/class/powercap/intel-rapl:0/max_energy_range_uj").read().strip())
cpu=[]
for (t1,e1),(t2,e2) in zip(raw,raw[1:]):
    d=e2-e1
    if d<0: d+=mx
    if t2-t1>0: cpu.append(d/1e6/(t2-t1))
if gpu: print("gpu_W avg %.1f p90 %.1f max %.1f n=%d" % (sum(gpu)/len(gpu), sorted(gpu)[int(len(gpu)*.9)], max(gpu), len(gpu)))
if cpu: print("cpu_W avg %.1f p90 %.1f max %.1f n=%d" % (sum(cpu)/len(cpu), sorted(cpu)[int(len(cpu)*.9)], max(cpu), len(cpu)))
PY
}
arm b42 resident-budget-gib=42
arm b50 resident-budget-gib=50
arm b55 resident-budget-gib=55
arm b61 resident-budget-gib=61
echo ALL_V6_DONE
