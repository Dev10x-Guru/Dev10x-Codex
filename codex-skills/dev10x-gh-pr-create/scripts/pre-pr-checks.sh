#!/usr/bin/env bash
# Run pre-PR quality checks. Exits on first failure.
# Skip if diff contains only non-Python files.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_BRANCH="${1:-}"

if [ -z "$BASE_BRANCH" ]; then
    # shellcheck source=detect-base-branch.sh
    source "$SCRIPT_DIR/detect-base-branch.sh"
fi

# Check if any Python files changed
PYTHON_FILES=$(git diff "origin/$BASE_BRANCH..HEAD" --name-only | grep '\.py$' || true)
if [ -z "$PYTHON_FILES" ]; then
    echo "⏭️  No Python files changed — skipping pre-PR checks."
    exit 0
fi

echo "🔍 Running pre-PR checks..."

echo "  [1/4] ruff check..."
ruff check . || { echo "❌ Ruff check failed. Fix linting issues."; exit 1; }

echo "  [2/4] ruff format check..."
ruff format --check . || { echo "❌ Formatting check failed. Run: ruff format ."; exit 1; }

echo "  [3/4] MyPy type check..."
mypy . || { echo "❌ MyPy check failed. Fix type errors."; exit 1; }

echo "  [4/4] Running tests..."
pytest || { echo "❌ Tests failed. Fix failing tests."; exit 1; }

echo "✅ All pre-PR checks passed!"
