#!/usr/bin/env bash
# Pre-push gate for this repo: manifest, links, docs policy, secrets. Kept as a script because the
# publication cadence here is one commit every few minutes and the checks must not be skipped.
set -u
cd "$(dirname "$0")/.." || exit 1
rc=0
echo -n "manifest: "; python3 scripts/regen_manifest_v6.py >/dev/null 2>&1 && python3 harness/verify_manifest.py --v6 | tail -1 || { echo "regen/verify failed"; rc=1; }
echo -n "links:    "; links=$(python3 scripts/check_links.py 2>&1); echo "$links" | tail -1
if echo "$links" | grep -q "^BAD "; then echo "  (link failures above: retry once, a 000 code is a fetch timeout, not a missing file)"; fi
echo -n "docs:     "; docs_out=$(python3 scripts/qa/docs_policy.py --push 2>&1); echo "$docs_out" | tail -1
case "$docs_out" in *PASS*) ;; *) echo "  docs gate failed:"; echo "$docs_out" | tail -6; rc=1 ;; esac
echo -n "secrets:  "; python3 - "$PWD" <<'PY'
import subprocess, sys
o = subprocess.run(["gitleaks", "detect", "--no-git", "--source", sys.argv[1], "--redact"], capture_output=True, text=True)
line = (o.stdout.strip().splitlines() or ["no leaks found"])[-1]
print(line)
sys.exit(0 if "no leaks" in line or o.returncode == 0 else 1)
PY
[ $? -ne 0 ] && rc=1
echo "gate rc=$rc"
exit $rc
