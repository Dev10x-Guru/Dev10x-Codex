#!/usr/bin/env bash
# Calculate the next available worktree path.
#
# Default: ../.worktrees/<project-basename>-NN
# Finds the highest existing number and increments.
#
# Usage: next-worktree-name.sh [base-dir]
#   base-dir: override the worktrees parent (default: ../.worktrees)

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"
BASE_DIR="${1:-$(dirname "$PROJECT_ROOT")/.worktrees}"

mkdir -p "$BASE_DIR"

# Find highest existing number for this project
max=0
for dir in "$BASE_DIR"/"$PROJECT_NAME"-*; do
    [ -d "$dir" ] || continue
    num="${dir##*-}"
    if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -gt "$max" ]; then
        max=$num
    fi
done

next=$((max + 1))
echo "$BASE_DIR/$PROJECT_NAME-$next"
