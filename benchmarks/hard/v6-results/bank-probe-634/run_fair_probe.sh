#!/bin/bash
# bank v6.4 raw-arm fairness probe (rule frozen in REVIEW-INBOX 2026-11-07 12:56 CET).
set -u
export PATH="$HOME/.local/bin:$PATH"
LOG=~/parb-v64-raw-fair
{ command -v codex >/dev/null && command -v hermes >/dev/null; } || { echo "codex/hermes missing from PATH" >> $LOG/queue.log; exit 1; }
export PARB_RAW_WS=$LOG
export PARB_BASALT_CHAT_URL=http://<LAN_IP>:8080/v1/chat/completions
cd $LOG || exit 1
date +%s > fair-start.epoch
python3 ~/sah-main/scripts/raw_v6.py basalt 22,23,24 > fair-basalt.log 2>&1; rcb=$?
python3 ~/sah-main/scripts/raw_v6.py codex 22,23,24 > fair-codex.log 2>&1; rcc=$?
python3 ~/sah-main/scripts/raw_v6.py grok 22,23,24 > fair-grok.log 2>&1; rcg=$?
date +%s > fair-end.epoch
echo "basalt rc=$rcb rows=$(wc -l < answers-basalt.jsonl 2>/dev/null); codex rc=$rcc rows=$(wc -l < answers-codex.jsonl 2>/dev/null); grok rc=$rcg rows=$(wc -l < answers-grok.jsonl 2>/dev/null)" >> queue.log
echo "bank64fair done" >> queue.log
