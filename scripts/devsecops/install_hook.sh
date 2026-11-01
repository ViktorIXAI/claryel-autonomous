#!/usr/bin/env bash
# Install the local Git pre-push DevSecOps gate.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

cat > .git/hooks/pre-push <<'HOOK'
#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
exec ./scripts/devsecops/prepush.sh
HOOK

chmod +x .git/hooks/pre-push
echo "Installed Git pre-push hook."
