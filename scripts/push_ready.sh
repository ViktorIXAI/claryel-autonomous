#!/usr/bin/env bash
# Pre-push gate for this repo: manifest, links, docs policy, secrets. Kept as a script because the
# publication cadence here is one commit every few minutes and the checks must not be skipped.
set -u
cd "$(dirname "$0")/.." || exit 1
rc=0
# Status discipline, fixed 2026-11-16 (PUB tick 198). Every step's exit status is captured into a
# variable on the line AFTER the call and only then printed. The manifest step used to read:
#   python3 scripts/regen_manifest_v6.py >/dev/null 2>&1 \
#     && python3 harness/verify_manifest.py --v6 | tail -1 || { echo "regen/verify failed"; rc=1; }
# and the status of `cmd | tail -1` is TAIL's, so a verify_manifest that fails on pin drift printed
# its own "VERIFY FAIL" line and this script still finished `gate rc=0`: the standing pre-push gate
# was fail-open on the one step whose whole job is to refuse pin drift. The links step was
# status-blind the same way — a failing check_links.py only printed a retry hint and never moved rc,
# although CI gates on that same script's exit code. Both are the PUB tick-173 trap class
# (`echo "$(basename $f) rc=$?"` reports basename's status) one level up, in the gate that decides
# whether a bad commit even reaches CI. harness/pub_push_ready_gates_test.py reproduces the old
# shape (rc 0 on a failing verify) and the new shape (rc 1) as bash fixtures and censuses this file
# so a pipe-consumed status cannot come back.
out=$(python3 scripts/regen_manifest_v6.py 2>&1); st=$?
if [ $st -ne 0 ]; then echo "manifest regen FAILED (status $st):"; printf '%s\n' "$out" | tail -8; rc=1; fi
out=$(python3 harness/verify_manifest.py --v6 2>&1); st=$?
echo "manifest: $(printf '%s' "$out" | tail -1) (status $st)"
if [ $st -ne 0 ]; then printf '%s\n' "$out" | tail -8 | sed 's/^/  /'; rc=1; fi
links=$(python3 scripts/check_links.py 2>&1); st=$?
echo "links:    $(printf '%s' "$links" | tail -1) (status $st)"
if echo "$links" | grep -q "^BAD "; then echo "  (link failures above: retry once, a 000 code is a fetch timeout, not a missing file)"; fi
if [ $st -ne 0 ]; then rc=1; printf '%s\n' "$links" | grep '^BAD ' | sed 's/^/  /'; fi
docs_out=$(python3 scripts/qa/docs_policy.py --push 2>&1); st=$?
echo "docs:     $(printf '%s' "$docs_out" | tail -1) (status $st)"
case "$docs_out" in *PASS*) ;; *) echo "  docs gate failed:"; echo "$docs_out" | tail -6; rc=1 ;; esac
if [ $st -ne 0 ]; then rc=1; fi
echo -n "secrets:  "; python3 - "$PWD" <<'PY'
import subprocess, sys
o = subprocess.run(["gitleaks", "detect", "--no-git", "--source", sys.argv[1], "--redact"], capture_output=True, text=True)
line = (o.stdout.strip().splitlines() or ["no leaks found"])[-1]
print(line)
sys.exit(0 if "no leaks" in line or o.returncode == 0 else 1)
PY
secrets_st=$?
echo "secrets:  gitleaks status $secrets_st"
[ $secrets_st -ne 0 ] && rc=1
# The repo's own infra scanner, the one that catches `absolute_local_path` in tracked sources and
# `ssh-connection-material` in published samplers — the rule that red the CI secret-scan job twice.
# gitleaks' built-in detectors do not cover either pattern, so a green gitleaks row here used to mean
# the push could still carry a LAN address, and only CI found it afterwards.
sec_out=$(python3 scripts/security/secret_scan.py --dir . --strict 2>&1); st=$?
sec_cell=$(printf '%s\n' "$sec_out" | grep -o '"total_findings": *[0-9]*' | head -1)
echo "infra-sec: ${sec_cell:-NO total_findings CELL} (status $st)"
if [ $st -ne 0 ]; then rc=1; printf '%s\n' "$sec_out" | tail -12; fi
if [ -z "$sec_cell" ]; then echo "  the scanner printed no total_findings cell: input gap, never green"; rc=1; fi
# PUB-line gates. Ticks 7-17 ran these by hand in every tick; a standing push gate is the
# only form that cannot be forgotten between ticks. Each names its own finding count on the last
# line and exits non-zero on findings or on a missing artifact (fail closed).
# Corrected 2026-11-16 (tick 198): this list carried FIVE of the six publication gates the PUB-PLAN
# enumerates in every tick block — `scripts/pub_three_arm_parity_check.py`, the item-P0 gate that
# decides whether the ladder queue is empty at all, was never run here. The three-arm parity row is
# the number the verdict line quotes ("49 rows / 9 sets / 0 findings"), so the standing gate had
# forgotten exactly the check that makes that sentence computable. A named gate whose file is absent
# is now an explicit MISSING row and a non-zero rc, never a silent skip: measured the same morning, a
# hand loop guarded by `if [ -f ... ]` skipped two gates on a typo'd name and printed a green suite
# with four of six rows.
PUB_GATES=(
  "scripts/pub_arms_index.py --check"
  "scripts/pub_derived_percent_check.py"
  "scripts/pub_grok_cell_check.py"
  "scripts/pub_superseded_cell_check.py"
  "scripts/pub_digest_row_check.py"
  "scripts/pub_three_arm_parity_check.py"
)
echo "pub gates:"
n=0
for g in "${PUB_GATES[@]}"; do
    gate_path=${g%% *}
    n=$((n+1))
    if [ ! -f "$gate_path" ]; then
        printf '  %-46s MISSING (input gap, never green)\n' "$g"
        rc=1
        continue
    fi
    out=$(python3 $g 2>&1); st=$?
    printf '  %-46s status %d  %s\n' "$g" "$st" "$(printf '%s' "$out" | tail -1)"
    if [ $st -ne 0 ]; then rc=1; printf '%s\n' "$out" | tail -8; fi
done
echo "pub gate rows: $n"
echo "gate rc=$rc"
exit $rc
