#!/bin/bash
# Bank-identity probe (NOT a contour pair): does bank v6.3's single prompt correction make
# B-ex6-04 passible by an honest reader? Both arms run the SAME adopted contour line 0.0.2.48
# (harness 3ae462167529 stamped into both workspaces, HARNESS_GIT_SHA), the SAME sp1 seeds
# (reps 22/23/24, gseed sha256(task|rep): 861061/593370/188460), the SAME idle P2005 endpoint,
# serially, PARB_SUBSET=B-ex6-04. The only difference is the bank bytes:
#   ~/parb-v62-probe  bank copy d1e8d11df5840dcc (published v6.2 3c866ea7daae611c)
#   ~/parb-v63-probe  bank copy 42bf2ecf69558dc2 (published v6.3 73f7a04d57473545, one field:
#                     B-ex6-04.prompt now states the year the gold already used)
# PRE-REGISTERED RULE (REVIEW-INBOX 2026-11-07 12:16 CET - the verdict is decided ONLY by that text):
#   v6.3 becomes the WORKING hard bank iff (i) >=2/3 v6.3 rows strict-pass (content==1.0 and
#   format_ok), (ii) <=1/3 v6.2 rows strict-pass in this same session, and (iii) verify_bank_v63
#   PASS with a derivability-audit delta of exactly B-ex6-04. Otherwise v6.3 stays PROVISIONAL and
#   the cell returns to the defect queue with these rows as evidence. No contour stamp is involved;
#   contour work on this cell is closed either way.
# Energy is not sampled for a 6-row probe; cost comes from ledger ptok/ctok/seconds.
set -u
run() {  # $1=ws-dir $2=bank-tag(62|63) $3=rep
  local ws=$1 tag=$2 rep=$3
  local rid="p${tag}r${rep}"
  cd "$ws" || exit 1
  cp -f "plan-rep${rep}.json" plan.json
  date +%s > "${rid}-start.epoch"
  PARB_ROOT=. PARB_API=http://<LAN_IP>:8080/v1/chat/completions \
    PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=<KEYFILE> \
    PARB_GATE_VERSION=0.0.2.48 PARB_SUBSET=B-ex6-04 \
    PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
    PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
    PARB_RUN_NOTES="bank-identity probe bank v6.${tag#6} (ws copy sha in run record) contour 0.0.2.48 seed ${rep} on B-ex6-04 only; v6.3 = v6.2 + stated year, gold bytes identical; paired with the other bank tag at identical sp1 seeds" \
    python3 -u gate_run.py > "${rid}.log" 2>&1
  local rc=$?
  date +%s > "${rid}-end.epoch"
  echo "$rid: exit=$rc rows=$(wc -l < "results-${rid}.jsonl" 2>/dev/null)" >> queue.log
}
for rep in 22 23 24; do run /<LOCAL_PATH> 62 $rep; done
for rep in 22 23 24; do run /<LOCAL_PATH> 63 $rep; done
echo "bank63probe done" >> /<LOCAL_PATH>
