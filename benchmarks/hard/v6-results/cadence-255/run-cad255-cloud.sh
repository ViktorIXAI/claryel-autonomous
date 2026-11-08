#!/bin/bash
# cadence-255 stages 3+4: Grok + ChatGPT-codex legs on matched reps 52,53,54 (bank v6.6),
# pre-registered in REVIEW-INBOX 2026-11-08 (same entry as run-cad255.sh). Transports
# identical to cadence-246/249: codex = subscription CLI xhigh read-only, prompt via
# STDIN; grok = hermes -z toolsets off, prompt inline (finding S3). Cloud legs never
# touch the serve; done-set keyed on (task,rep). PATH must be set explicitly:
# systemd-run --user scopes do not inherit the shell PATH (dead codex legs lesson).
set -u
export PATH="$HOME/.local/bin:$PATH"
LOG=~/parb-b66-contour/band255.log
command -v codex >/dev/null && command -v hermes >/dev/null || { echo "codex/hermes missing from PATH" >> $LOG; exit 1; }
mkdir -p ~/parb-b66-raw-reps
cd ~/parb-b66-raw-reps || exit 1
[ -f bank.json ] || { echo "raw-reps bank.json not staged before cloud launch" >> $LOG; exit 1; }
[ -f p2005-profile.json ] || { echo "raw-reps p2005-profile.json not staged" >> $LOG; exit 1; }
date +%s > cloud-r525354-start.epoch
PARB_RAW_WS=~/parb-b66-raw-reps python3 ~/sah-main/scripts/raw_v6.py codex 52,53,54 >> band-codex.log 2>&1 &
pidc=$!
PARB_RAW_WS=~/parb-b66-raw-reps python3 ~/sah-main/scripts/raw_v6.py grok 52,53,54 >> band-grok.log 2>&1 &
pidg=$!
wait $pidc; rcc=$?
wait $pidg; rcg=$?
date +%s > cloud-r525354-end.epoch
echo "codex 52,53,54: rc=$rcc rows=$(grep -c '\"rep\": 5[234]' answers-codex.jsonl 2>/dev/null)" >> $LOG
echo "grok 52,53,54: rc=$rcg rows=$(grep -c '\"rep\": 5[234]' answers-grok.jsonl 2>/dev/null)" >> $LOG
echo "cad255 stage3+4 cloud done" >> $LOG
