#!/bin/bash
# Four-arm cadence re-run on the ADOPTED line 0.0.2.40 (owner rule: every 5 stamps re-test the
# external arms). Overdue by 12 stamps (2.30..2.41 measured since the morning four-arm run).
# FRESH matched seeds: reps 6,7,8 for BOTH contour and bare basalt, gseeds re-derived by
# scripts/plan_reps.py from (task, rep), so contour seed k and basalt seed k are cell-matched.
# Stage 1: contour 0.0.2.40 on the contour workspace (loop-D tasks included, /77).
# Stage 2: bare basalt single-shot (loop-D not applicable to raw arms), appended to
#          ~/parb-v61-raw-reps/answers-basalt.jsonl for the published raw-reps ledger.
# Grok/ChatGPT arms on the same seeds follow in the next cycle (subscription transports).
set -u
cd ~/parb-v61-contour || exit 1
for rep in 6 7 8; do
  python3 ~/sah-main/scripts/plan_reps.py bank.json $rep > plan-rep0$rep.json 2>>band.log || exit 1
  cp -f plan-rep0$rep.json plan.json
  rid="q40r$rep"
  date +%s > "${rid}-start.epoch"
  PARB_ROOT=. PARB_API=http://<LAN_IP>:8080/v1/chat/completions \
    PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
    PARB_GATE_VERSION=0.0.2.40 PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
    PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
    PARB_RUN_NOTES="band re-run contour 0.0.2.40 seed $rep (matched fresh gseed) on bank v6.1; four-arm cadence after 12 stamps " \
    python3 -u gate_run.py > "${rid}.log" 2>&1
  rc=$?
  date +%s > "${rid}-end.epoch"
  echo "$rid: exit=$rc rows=$(wc -l < "results-${rid}.jsonl" 2>/dev/null)" >> band.log
done
cd ~/parb-v61-raw-reps || exit 1
URL=$(python3 -c "import json;d=json.load(open('p2005-profile.json'));print('http://%s:%s/v1/chat/completions'%(d['host'],d['port']))")
PARB_RAW_WS=~/parb-v61-raw-reps PARB_BASALT_CHAT_URL="$URL" \
  python3 ~/sah-main/scripts/raw_v6.py basalt 6,7,8 >> band-basalt.log 2>&1
echo "basalt 6,7,8: rc=$? rows=$(grep -c '\"rep\": *[678]' answers-basalt.jsonl)" >> ~/parb-v61-contour/band.log
cp -f plan-full.json plan.json
echo "band240 done" >> ~/parb-v61-contour/band.log
