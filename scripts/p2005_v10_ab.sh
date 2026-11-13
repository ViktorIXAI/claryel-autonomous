#!/usr/bin/env bash
# True concurrency: 4 simultaneous chat requests, aggregate tokens/s from the engine's own done lines.
cd ~/basalt
BIN=$HOME/basalt-033/bin/basalt
PYBIN=$HOME/basalt/.venv/bin/python
LOG=$HOME/basalt-033/serve-100.log
CFG=/tmp/v10_cfg.json
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
p="/tmp/v10_cfg.json"; d=json.load(open(p))
for a in sys.argv[1:]:
    k,v=a.split("=",1)
    v=int(v) if v.lstrip("-").isdigit() else (True if v=="true" else (False if v=="false" else v))
    d["engine"][k]=v
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
  # warm the model and the prompt so all four streams hit the same path
  BRAIN_KEY=$(cat basalt.key) python3 brainbench.py http://127.0.0.1:8080/v1 1 $MODEL 600 128 >/dev/null 2>&1
  mark=$(wc -l < $LOG); t0=$(date +%s.%N)
  pids=""
  for i in 1 2 3 4; do
    BRAIN_KEY=$(cat basalt.key) python3 brainbench.py http://127.0.0.1:8080/v1 1 $MODEL 600 1024 > /tmp/v10_run$i.json 2>&1 &
    pids="$pids $!"
  done
  wait $pids
  t1=$(date +%s.%N)
  tail -n +$((mark+1)) $LOG | grep -aE "s[0-9]+ done" | cut -c1-150
  tail -n +$((mark+1)) $LOG | grep -aE "s[0-9]+ done" | sed -E 's/.*tg=([0-9]+).*/\1/' | awk -v w="$(python3 -c "print($t1-$t0)")" '{n+=$1} END{printf "parallel: %d streams, %d tokens in %.1fs = %.1f tok/s aggregate\n", NR, n, w, n/w}'
  python3 - <<'PY'
import json
for i in (1,2,3,4):
    try:
        d=json.load(open(f"/tmp/v10_run{i}.json"))
        r=d["runs"][0] if isinstance(d,dict) and "runs" in d else d
        print("stream%d ttft %.2fs  chars %d  wall %.1fs  %.0f chars/s" % (i, r.get("ttft_s") or -1, r.get("chars") or 0, r.get("wall_s") or 0, (r.get("chars") or 0)/max(r.get("wall_s") or 1,1e-9)))
    except Exception as e:
        print("stream%d parse fail %s" % (i, e))
PY
  free -h | sed -n 2p | sed 's/^/mem /'
  nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader | sed 's/^/gpu MiB /'
}
arm v10_batch1
arm v10_batch4 batch=4
arm v10_batch4_cpu batch=4 prefill-cpu-share=0.3
echo ALL_V10_DONE
