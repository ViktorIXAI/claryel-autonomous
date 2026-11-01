#!/bin/sh
# Clean-environment reproduction: ONLY public network endpoints are used
# (codeload.github.com, github.com releases, raw.githubusercontent).
set -e
cd /work
echo "== fetch public repo tarball (main) =="
python3 - <<'EOF'
import urllib.request, tarfile, io
u="https://codeload.github.com/ViktorIXAI/strata-autonomous-harness/tar.gz/refs/heads/main"
data=urllib.request.urlopen(u, timeout=120).read()
tarfile.open(fileobj=io.BytesIO(data)).extractall("/work")
import os
d=[x for x in os.listdir("/work") if x.startswith("strata-autonomous-harness")][0]
os.rename("/work/"+d, "/work/repo")
print("repo files:", sum(len(fs) for _,_,fs in os.walk("/work/repo")))
EOF
cd /work/repo
echo "== self-tests (fresh interpreter, no venv needed: stdlib only) =="
python3 harness/gate_fixers_test.py | tail -1
python3 harness/gate_v19_d_test.py | tail -1
python3 scripts/sanity_data.py
python3 benchmarks/privacy-boundary/test_gateway.py | tail -1
echo "== download pinned artifacts asset (public, no auth) =="
python3 - <<'EOF'
import urllib.request
u="https://github.com/ViktorIXAI/strata-autonomous-harness/releases/download/contour-v1.9/artifacts-release-2026-11-01-v2.tar.zst"
open("/work/art.tar.zst","wb").write(urllib.request.urlopen(u, timeout=300).read())
import os; print("asset bytes:", os.path.getsize("/work/art.tar.zst"))
EOF
echo "== unpack (zstd) + verify every file against logs/INDEX.md sha256 =="
apt-get update -qq >/dev/null 2>&1; apt-get install -y -qq zstd >/dev/null 2>&1
mkdir -p /work/artifacts && tar --zstd -xf /work/art.tar.zst -C /work/artifacts --strip-components=1
python3 scripts/verify_release_hashes.py /work/artifacts
echo "== recompute aggregates from raw rows, diff vs published summary =="
PARB_ARTIFACTS=/work/artifacts python3 analytics/aggregate.py > /work/recomputed.json
python3 scripts/diff_summary.py /work/recomputed.json results/summary.json
echo "== dashboard data integrity: published JSON loads =="
python3 - <<'EOF'
import json
for p in ("results/summary.json","results/summary-full.json","results/second-opinion-v18-v19-b2003.json","results/second-opinion-holdout-mini.json","results/dedup-sensitivity.json","telemetry/runs/smoke-tel-4.join.json","benchmarks/holdout/bank-holdout.json"):
    json.load(open(p)); print("ok:", p)
EOF
echo "REPRO-FINISH"
