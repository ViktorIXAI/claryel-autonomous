#!/bin/bash
# Paired contour arms on bank v6.1: 0.0.2.43 (ADOPTED control line, pair-244) vs 0.0.2.44
# (D-loop best-of-2 SELECTION on the `false_completion_claim` note family: the answer CLAIMS a
# banned action was performed, the frozen scorer caps content at 0.3; one extra loop run at
# seed+12289 - third distinct offset, 2.11 uses 4096 and 2.43 uses 8117 - adopted only if
# strictly better; monotone, it can only fire on rows the loop scorer already failed).
# Trigger precedence for BOTH offset and event naming: banned > claim > 2.11 (one retry per task).
# The rejected 2.42 policy tail is frozen to exactly (2,42); the ADOPTED 2.43 banned trigger
# inherits as line behavior (gate_v49/v58 pin the matrix).
# Target class (published): UNSTABLE-CELLS-V61 03:50 addendum - the last loop note family with no
# selection trigger. PRE-LAUNCH DRY-RUN: 504 published loop rows across 13 pair dirs, the claim
# note appears 13 times, ALL 13 strict-fail at exactly 0.3, ZERO on strict-passing rows; pair-244
# proved live the 2.43 trigger never fires on it (p43r2 l3).
# PRE-REGISTERED RULE (written before any q* row - the verdict is decided ONLY by this text):
#  (a) LIVE TARGET: MEASURED iff >=1 control (q43) loop row carries a false_completion_claim note
#      AND strict-fails. Zero live target = UNMEASURED (pair-233/238/242 mode), never a pass.
#  (b) CELL ATTRIBUTION: a conversion counts only if the candidate strict-PASSES where the control
#      strict-failed, the row carries fix:v244_d_best2_claim_win (plus contour:v244_d_best2_claim_fired),
#      and the claim note is ABSENT from the adopted trajectory.
#  (c) GUARDS: ZERO candidate loop strict-fails where the control passed (monotonicity broken in
#      CODE - close the stamp); zero v244 events outside loop rows; zero frozen-band events
#      (2.30-32/34/36/38/41/42); adopted-2.43 parity (v243 events fire ONLY on banned-note rows in
#      BOTH arms); adopted-line parity (2.11 v31 events, 2.39/2.40 J fires, 2.35 B repair identical).
#  (d) RESOLUTION: loop pool n=18/arm published with the exact sign test; an arm-mean delta under
#      ~2 cells on the 77-cell pool is UNRESOLVABLE and never quoted as the reason; candidate not
#      >2 cells below control. ADOPT 0.0.2.44 iff (a) holds, >=1 evented conversion, all guards
#      clean. Otherwise freeze D_BEST2_CLAIM to CONTOUR_REVISION == (2,44) and publish the
#      negative with the same detail as a win.
set -u
cd ~/parb-v61-contour || exit 1
for rep in 0 1 2; do
  case $rep in
    0) plan=plan-full.json ;;
    1) plan=plan-rep01.json ;;
    2) plan=plan-rep02.json ;;
  esac
  for v in 43 44; do
    rid="q${v}r${rep}"
    date +%s > "${rid}-start.epoch"
    cp -f "$plan" plan.json
    PARB_ROOT=. PARB_API=http://<LAN_IP>:<PORT>/v1/chat/completions \
      PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
      PARB_GATE_VERSION=0.0.2.$v PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
      PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
      PARB_RUN_NOTES="paired contour 0.0.2.${v} seed ${rep} on bank v6.1 (2.44 = loop best-of-2 on the false_completion_claim note family, one retry at seed+12289, strict-better only; control 0.0.2.43 the adopted line; 2.30-2.34/2.36/2.38/2.41/2.42 frozen) " \
      python3 -u gate_run.py > "${rid}.log" 2>&1
    rc=$?
    date +%s > "${rid}-end.epoch"
    echo "$rid: exit=$rc rows=$(wc -l < "results-${rid}.jsonl" 2>/dev/null)" >> queue.log
  done
done
cp -f plan-full.json plan.json
echo "pair245 done" >> queue.log
