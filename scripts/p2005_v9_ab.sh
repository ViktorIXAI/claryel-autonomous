#!/usr/bin/env bash
# Basalt 0.3.3 batch slots: single-stream cost of batch 4/8, plus real 4-stream throughput.
cd ~/basalt
BIN=$HOME/basalt-033/bin/basalt
PYBIN=$HOME/basalt/.venv/bin/python
LOG=$HOME/basalt-033/serve-099.log
CFG=/tmp/v9_cfg.json
# Privacy fix (pub-line tick 109, 2026-11-13): see p2005_v8_ab.sh — $HOME resolves to
# the same directory, so the written config bytes are unchanged.
MODEL_ABS=$HOME/basalt/model/Qwen3.8-FN-IQ3_S.basalt
MODEL=qwen3.8-flash-next-iq3_s-basalt
base_cfg() {
cat > $CFG <<JSON
{
  "version": 2,
  "server": {"host": "0.0.0.0", "port": 8080},
  "models": [{"model": "$MODEL_ABS", "alias": "qwen3.8-flash-next-iq3_s-basalt",
              "gpu": "0", "kv": "int8", "max-context": 262144}],
  "engine": {"resident-experts": true, "expert-cache": "auto", "prefill": "auto",
             "vram-reserve-mib": 512, "resident-budget-gib": 42, "resident-cpu-experts": true,
             "conversation-cache-mib": 6144, "conversation-cache-slots": 6,
             "conversation-cache-disk-mib": 20480}
}
JSON
}
apply() {
  base_cfg; python3 - "$@" <<'PY'
import json,sys
p="/tmp/v9_cfg.json"; d=json.load(open(p))
for a in sys.argv[1:]:
    k,v=a.split("=",1)
    v=int(v) if v.lstrip("-").isdigit() else (True if v=="true" else (False if v=="false" else v))
    if k.startswith("server."): d["server"][k.split(".",1)[1]]=v
    elif k.startswith("model."): d["models"][0][k.split(".",1)[1]]=v
    else: d["engine"][k]=v
json.dump(d,open(p,"w"),indent=2)
PY
}
arm() {
  name=$1; shift
  apply "$@"
  pkill -f "[s]erve.server"; pkill -x basalt; sleep 5
  K=$(cat ~/basalt/basalt.key)
  setsid nohup $BIN serve --config $CFG --python $PYBIN --api-key "$K" >> $LOG 2>&1 &
  ok=0
  for i in $(seq 1 12); do curl -s -m 8 http://127.0.0.1:8080/health | grep -q '"loaded": true' && { ok=1; break; }; sleep 8; done
  echo "=== arm $name (loaded=$ok)"
  [ $ok -eq 0 ] && { tail -4 $LOG | cut -c1-160; return; }
  mark=$(wc -l < $LOG)
  : > /tmp/v9_pow.txt; : > /tmp/v9_rapl.txt; : > /tmp/v9_mem.txt
  ( end=$((SECONDS+230)); while [ $SECONDS -lt $end ]; do
      printf "%s %s\n" "$(date +%s.%N)" "$(nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits)" >> /tmp/v9_pow.txt
      awk '{printf "%s %s\n", systime()+0, $1}' /sys/class/powercap/intel-rapl:0/energy_uj >> /tmp/v9_rapl.txt
      free -b | awk '/^Mem:/{printf "%s %s %s\n", systime(), $2, $3}' >> /tmp/v9_mem.txt
      sleep 1; done ) &
  spid=$!
  for r in 1 2 3 4 5; do BRAIN_KEY=$(cat basalt.key) python3 brainbench.py http://127.0.0.1:8080/v1 1 $MODEL 600 1024 > /dev/null 2>&1; done
  BRAIN_KEY=$(cat basalt.key) python3 brainbench.py http://127.0.0.1:8080/v1 1 $MODEL 20000 512 >/dev/null 2>&1
  echo "--- 4 streams x 600 in / 1024 out:"
  BRAIN_KEY=$(cat basalt.key) timeout 220 python3 brainbench.py http://127.0.0.1:8080/v1 4 $MODEL 600 1024 2>&1 | tail -9 | sed 's/^/c4 /'
  kill $spid 2>/dev/null
  nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader | sed 's/^/gpu MiB /'
  awk '{if($3>m)m=$3} END{printf "host RAM peak used %.1f GiB (ceiling 61)\n", m/1073741824}' /tmp/v9_mem.txt
  tail -n +$((mark+1)) $LOG | grep -aE "s[0-9] done" | grep -avc "pp=878" | sed 's/^/foreign_in_window /'
  tail -n +$((mark+1)) $LOG | grep -aE "s[1-8] done" | grep -a "pp=878" | cut -c1-150
  tail -n +$((mark+1)) $LOG | grep -a "pp=27553" | tail -2 | cut -c1-150
  python3 - <<PY
gpu=[float(l.split()[1]) for l in open("/tmp/v9_pow.txt")]
raw=[(float(l.split()[0]), int(l.split()[1])) for l in open("/tmp/v9_rapl.txt")]
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
arm v9_base
arm v9_batch4 batch=4
arm v9_batch8 batch=8
echo ALL_V9_DONE
