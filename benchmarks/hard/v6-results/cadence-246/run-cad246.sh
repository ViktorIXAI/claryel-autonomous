#!/bin/bash
# cadence-246: four-arm cadence on bank v6.2 (due since contour 2.40; stamps measured since:
# 2.41, 2.42, 2.43, 2.44, 2.45). Pre-registered in benchmarks/hard/REVIEW-INBOX.md at
# 2026-11-07 06:20 CET, BEFORE any row of this script was written.
# Stage 1: contour at 0.0.2.45 = the ADOPTED 0.0.2.43 feature matrix + contract v6.2 identity
#          (0.0.2.45 registers no contour feature; gate_v49 pins that equality).
# Stage 2: bare basalt single-shot on the SAME reps (raw seed 1000+rep), appended to
#          answers-basalt.jsonl in parb-v62-raw-reps.
# Grok + ChatGPT-codex legs on the same reps follow in the next cycle; publication happens
# when all four legs exist. Liveness = row COUNT + unit state, never GPU utilization.
set -u
export PATH="$HOME/.local/bin:$PATH"
command -v python3 >/dev/null || { echo "python3 missing"; exit 1; }
cd ~/parb-v62-contour || exit 1
LOG=band246.log
API=$(python3 -c "import json;d=json.load(open('p2005-profile.json'));h=d.get('host');h='<LAN_IP>' if h in ('0.0.0.0','','None',None) else h;print('http://%s:%s/v1/chat/completions'%(h,d['port']))")
for rep in 16 17 18; do
  python3 ~/sah-main/scripts/plan_reps.py bank.json $rep > plan-rep$rep.json 2>>$LOG || exit 1
  cp -f plan-rep$rep.json plan.json
  rid="q45r$rep"
  date +%s > "${rid}-start.epoch"
  PARB_ROOT=. PARB_API="$API" \
    PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
    PARB_GATE_VERSION=0.0.2.45 PARB_BANK_VERSION="v6.2" \
    PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
    PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
    PARB_RUN_NOTES="cadence-246 stage 1: contour 0.0.2.45 (adopted 2.43 line + scorer contract v6.2) on bank v6.2, matched seed rep $rep" \
    python3 -u gate_run.py > "${rid}.log" 2>&1
  rc=$?
  date +%s > "${rid}-end.epoch"
  echo "$rid: exit=$rc rows=$(wc -l < results-${rid}.jsonl 2>/dev/null)" >> $LOG
done
mkdir -p ~/parb-v62-raw-reps
cp -f bank.json ~/parb-v62-raw-reps/bank.json
cp -f p2005-profile.json ~/parb-v62-raw-reps/p2005-profile.json
cd ~/parb-v62-raw-reps || exit 1
date +%s > basalt-r161718-start.epoch
PARB_RAW_WS=~/parb-v62-raw-reps PARB_BASALT_CHAT_URL="$API" \
  python3 ~/sah-main/scripts/raw_v6.py basalt 16,17,18 >> band-basalt.log 2>&1
rc=$?
date +%s > basalt-r161718-end.epoch
echo "basalt 16,17,18: rc=$rc rows=$(grep -c '\"rep\": 1[678]' answers-basalt.jsonl 2>/dev/null)" >> ~/parb-v62-contour/band246.log
echo "cad246 stage1+2 done" >> ~/parb-v62-contour/band246.log
