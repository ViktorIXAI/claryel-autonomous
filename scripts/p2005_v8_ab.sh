#!/usr/bin/env bash
# Basalt 0.3.3 (new engine, separate worktree) on our live settings, then the promising knobs.
# All arms run on the new binary; the old 0.2.1 binary stays on disk untouched for rollback.
# Config is the v2 shape (models[] + engine{} + server{}). Engine lines in the log prove what was active.
cd ~/basalt
BIN=$HOME/basalt-033/bin/basalt
PYBIN=$HOME/basalt/.venv/bin/python
LOG=$HOME/basalt-033/serve-033.log
CFG=/tmp/v8_cfg.json
MODEL=qwen3.8-flash-next-iq3_s-basalt
base_cfg() {
cat > $CFG <<'JSON'
{
  "version": 2,
  "server": {"host": "0.0.0.0", "port": 8080},
  "models": [{"model": "/home/claryel/basalt/model/Qwen3.8-FN-IQ3_S.basalt", "alias": "qwen3.8-flash-next-iq3_s-basalt",
              "gpu": "0", "kv": "int8", "max-context": 262144}],
  "engine": {"resident-experts": true, "expert-cache": "auto", "prefill": "auto",
             "vram-reserve-mib": 512, "resident-budget-gib": 42, "resident-cpu-experts": true,
             "conversation-cache-mib": 6144, "conversation-cache-slots": 6,
             "conversation-cache-disk-mib": 20480}
}
JSON
}
apply() { base_cfg; python3 - "$@" <<'PY'
import json,sys
p="/tmp/v8_cfg.json"; d=json.load(open(p))
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
  : > /tmp/v8_pow.txt; : > /tmp/v8_rapl.txt; : > /tmp/v8_mem.txt; : > /tmp/v8_swap.txt
  ( end=$((SECONDS+170)); while [ $SECONDS -lt $end ]; do
      printf "%s %s\n" "$(date +%s.%N)" "$(nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits)" >> /tmp/v8_pow.txt
      awk '{printf "%s %s\n", systime()+0, $1}' /sys/class/powercap/intel-rapl:0/energy_uj >> /tmp/v8_rapl.txt
      free -b | awk '/^Mem:/{printf "%s %s %s\n", systime(), $2, $3}' >> /tmp/v8_mem.txt
      awk '/^pswp(in|out)/{printf "%s %s %s\n", systime(), $1, $2}' /proc/vmstat >> /tmp/v8_swap.txt
      sleep 1; done ) &
  spid=$!
  for r in 1 2 3 4 5 6 7; do BRAIN_KEY=$(cat basalt.key) python3 brainbench.py http://127.0.0.1:8080/v1 1 $MODEL 600 1024 > /dev/null 2>&1; done
  BRAIN_KEY=$(cat basalt.key) python3 brainbench.py http://127.0.0.1:8080/v1 1 $MODEL 20000 512 >/dev/null 2>&1
  kill $spid 2>/dev/null
  nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader | sed 's/^/gpu MiB /'
  awk '{if($3>m)m=$3} END{printf "host RAM peak used %.1f GiB (ceiling 61)\n", m/1073741824}' /tmp/v8_mem.txt
  python3 - <<'PY'
sw={}
for l in open("/tmp/v8_swap.txt"):
    t,n,v=l.split(); sw.setdefault(int(t),{})[n]=int(v)
ts=sorted(sw); si=so=0
for a,b in zip(ts,ts[1:]):
    d1=sw[b].get("pswpin",0)-sw[a].get("pswpin",0); d2=sw[b].get("pswpout",0)-sw[a].get("pswpout",0)
    if d1>0: si=max(si,d1)
    if d2>0: so=max(so,d2)
print("swap max per-second: in %d pages (%.1f MiB) out %d pages (%.1f MiB)" % (si, si*4/1024, so, so*4/1024))
PY
  tail -n +$((mark+1)) $LOG | grep -aE "s[0-9] done" | grep -avc "pp=878" | sed 's/^/foreign_in_window /'
  tail -n +$((mark+1)) $LOG | grep -aE "s[0-9] done" | grep -a "pp=878" | cut -c1-150
  tail -n +$((mark+1)) $LOG | grep -a "pp=27553" | tail -1 | cut -c1-150
  tail -n +$((mark+1)) $LOG | grep -aE "^..server. (engine|ram) |RAM copy|experts on SSD|free VRAM" | tail -3 | cut -c1-190
  python3 - <<PY
gpu=[float(l.split()[1]) for l in open("/tmp/v8_pow.txt")]
raw=[(float(l.split()[0]), int(l.split()[1])) for l in open("/tmp/v8_rapl.txt")]
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
arm n_base
arm n_ram50 ram-reserve-mib=4096 resident-budget-gib=50
arm n_k8v4 model.kv=k8v4
arm n_par2 server.parallel=2
arm n_pre32k prefill=auto:32768
arm n_cpu02 prefill-cpu-share=0.2
arm n_relax relaxed-drafting=0.5
arm n_pleram ple-io=ram
echo ALL_V8_DONE
