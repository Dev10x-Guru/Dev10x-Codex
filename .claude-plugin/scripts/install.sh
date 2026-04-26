#!/usr/bin/env bash
# Guided installation — sets permissions and runs verification.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Dev10x Plugin Installation ==="
echo ""

echo "Checking prerequisites..."
for cmd in python3 jq git bash; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: Required tool '$cmd' not found. Please install it first."
        exit 1
    fi
done

echo "Setting script permissions..."
find "$REPO_ROOT/hooks/scripts" -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} \;
find "$REPO_ROOT/bin" -type f -name "*.sh" -exec chmod +x {} \;
find "$REPO_ROOT/servers" -type f -name "*.py" -exec chmod +x {} \;
echo "Done."

echo ""
echo "Running verification..."
echo ""
bash "$SCRIPT_DIR/verify.sh"
