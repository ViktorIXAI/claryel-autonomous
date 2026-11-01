#!/usr/bin/env bash
# Automated DevSecOps pre-push gate for this repository.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

REPORT_DIR="${SAH_SECURITY_REPORT_DIR:-$HOME/.hermes/bench/parb/security}"
mkdir -p "$REPORT_DIR"

echo "DevSecOps pre-push: JSON/schema QA"
python3 scripts/qa/validate_json.py

echo "DevSecOps pre-push: dependency policy"
python3 scripts/devsecops/dependency_policy.py

echo "DevSecOps pre-push: static tests"
python3 scripts/qa/static_checks.py

echo "DevSecOps pre-push: secret scan"
python3 scripts/security/secret_scan.py --dir . --strict \
  --report "$REPORT_DIR/prepush-devsecops.json"

echo "DevSecOps pre-push: git hygiene"
git diff --check
git diff --cached --check || true

echo "DevSecOps pre-push passed."
