#!/bin/bash
# Paired contour arms on bank v6.1: 0.0.2.40 (ADOPTED control line, pair-240) vs 0.0.2.43
# (D-loop best-of-2 SELECTION on the `banned_attempted:<TOOL>` note family: one extra loop run at
# seed+8117, adopted only if strictly better; monotone - it can only fire on rows the loop scorer
# already failed). The MEASURED NEGATIVE 2.42 prevention nudge is frozen to exactly (2,42) and does
# NOT ride into 2.43 (gate_v49/v57 pin the matrix).
# Target class (published): pair-243's loop map - the whole loop-D loss family carries
# banned_attempted:<TOOL> (READ_FILE -> banned mutation attempt, scored even though mock_exec blocks
# it -> content 0.7, format dead). PRE-LAUNCH DRY-RUN: over the 24 published 0.0.2.40-line loop
# seeds (m40/n40/o40/q40, 144 loop cells) the note appears on exactly 9 rows and every one of them
# strict-fails; ZERO fires on a strict-passing loop row; loop-only path, zero single-shot fires.
# PRE-REGISTERED RULE (written before any p* row - the verdict is decided ONLY by this text):
#  (a) LIVE TARGET: MEASURED iff >=1 control (p40) loop row carries a banned-attempt note AND
#      strict-fails. Zero live target = UNMEASURED (pair-233/238/242 mode), never a pass.
#  (b) CELL ATTRIBUTION: a conversion counts only if the candidate strict-PASSES where the control
#      strict-failed, the row carries fix:v243_d_best2_banned_win (plus the fired event), and the
#      adopted trajectory shows no banned attempt. fired-but-not-better = wiring evidence only.
#  (c) GUARDS: ZERO candidate loop strict-fails where the control passed (any such cell means the
#      monotonicity claim is broken in CODE, not a model regression - close the stamp); zero v243
#      events outside loop rows; frozen-feature parity (zero 2.30-32/34/36/38/41/42-gated events in
#      either arm - the 2.42 policy tail must be absent); adopted-line parity (2.39/2.40 J fires and
#      2.35 B repair identical in both arms); the 2.11 v31_d_best2 trigger keeps its own events.
#  (d) RESOLUTION: loop pool n=18/arm published with the exact sign test; an arm-mean delta under
#      ~2 cells on the 77-cell pool is UNRESOLVABLE and never quoted as the reason; candidate not
#      >2 cells below control. ADOPT 0.0.2.43 iff (a) holds, >=1 evented conversion, all guards
#      clean. Otherwise freeze D_BEST2_BANNED to CONTOUR_REVISION == (2,43) and publish the
#      negative with the same detail as a win.
set -u
cd ~/parb-v61-contour || exit 1

for rep in 0 1 2; do
  case $rep in
    0) plan=plan-full.json ;;
    1) plan=plan-rep01.json ;;
    2) plan=plan-rep02.json ;;
  esac
  for v in 40 43; do
    rid="p${v}r${rep}"
    date +%s > "${rid}-start.epoch"
    cp -f "$plan" plan.json
    PARB_ROOT=. PARB_API=http://<LAN_IP>:<PORT>/v1/chat/completions \
      PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
      PARB_GATE_VERSION=0.0.2.$v PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
      PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
      PARB_RUN_NOTES="paired contour 0.0.2.${v} seed ${rep} on bank v6.1 (2.43 = loop best-of-2 on the banned_attempted note family, one retry at seed+8117, strict-better only; control 0.0.2.40 the adopted line; 2.30-2.34/2.36/2.38/2.41/2.42 frozen) " \
      python3 -u gate_run.py > "${rid}.log" 2>&1
    rc=$?
    date +%s > "${rid}-end.epoch"
    echo "$rid: exit=$rc rows=$(wc -l < "results-${rid}.jsonl" 2>/dev/null)" >> queue.log
  done
done
cp -f plan-full.json plan.json
echo "pair244 done" >> queue.log
