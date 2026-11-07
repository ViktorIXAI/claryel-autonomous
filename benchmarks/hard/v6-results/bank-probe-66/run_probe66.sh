#!/bin/bash
# bank v6.6 probe (rule frozen in REVIEW-INBOX 2026-11-07 18:22 CET, BEFORE any v6.6 row):
# contour no-new-loss legs p66r28/29/30 (bank v6.6, stamp 0.0.2.50 behavior 2.48,
# SUBSET=H-ex6-01, matched seeds; control rows = published p65r28-30) then raw fairness
# arms basalt/codex/grok reps 28,29,30 on the v6.6 subset ws. Serial, idle endpoint.
set -u
export PATH="$HOME/.local/bin:$PATH"
{ command -v codex >/dev/null && command -v hermes >/dev/null; } || { echo "codex/hermes missing" >> ~/parb-probe66-queue.log; exit 1; }
API="http://<LAN_IP>:8080/v1/chat/completions"
QLOG=~/parb-probe66-queue.log
for rep in 28 29 30; do
  WS=~/parb-b66-contour
  cd "$WS" || { echo "ws missing" >> $QLOG; exit 1; }
  python3 ~/sah-main/scripts/plan_reps.py bank.json $rep > plan-rep$rep.json 2>>$QLOG || exit 1
  cp -f plan-rep$rep.json plan.json
  rid="p66r${rep}"
  date +%s > "${rid}-start.epoch"
  PARB_ROOT=. PARB_API="$API" \
    PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
    PARB_GATE_VERSION=0.0.2.50 PARB_SUBSET=H-ex6-01 \
    PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
    PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
    PARB_RUN_NOTES="bank v6.6 probe: bank v6.6 (published 5c86252b2ef2f422) CANDIDATE, claims-field spec; control = published p65r${rep} (bank v6.5, ws copy 919517b75a614d52); contour 0.0.2.50 behavior 2.48 on H-ex6-01 only, matched seed rep $rep; rule REVIEW-INBOX 18:22 CET" \
    python3 -u gate_run.py > "${rid}.log" 2>&1
  echo "$rid: exit=$? rows=$(wc -l < results-${rid}.jsonl 2>/dev/null)" >> $QLOG
  date +%s > "${rid}-end.epoch"
done
RAW=~/parb-b66-raw-fair
cd $RAW || exit 1
export PARB_RAW_WS=$RAW PARB_BASALT_CHAT_URL="$API"
date +%s > fair-start.epoch
python3 ~/sah-main/scripts/raw_v6.py basalt 28,29,30 > fair-basalt.log 2>&1; rcb=$?
python3 ~/sah-main/scripts/raw_v6.py codex 28,29,30 > fair-codex.log 2>&1; rcc=$?
python3 ~/sah-main/scripts/raw_v6.py grok 28,29,30 > fair-grok.log 2>&1; rcg=$?
date +%s > fair-end.epoch
echo "fair: basalt rc=$rcb rows=$(wc -l < answers-basalt.jsonl 2>/dev/null); codex rc=$rcc rows=$(wc -l < answers-codex.jsonl 2>/dev/null); grok rc=$rcg rows=$(wc -l < answers-grok.jsonl 2>/dev/null)" >> $QLOG
echo "probe66 done" >> $QLOG
