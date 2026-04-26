#!/usr/bin/env bash
# Safe git push wrapper — blocks force push to protected branches.
#
# Usage: git-push-safe.sh [flags] [remote] [refspec]
#   Do NOT include "push" — the script runs `git push` itself.
#
# Default protected branches: main master develop development staging trunk
# Override: GIT_PROTECTED_BRANCHES="main master staging" git-push-safe.sh -u origin branch
# Per-call: git-push-safe.sh --protected staging --protected release/* -u origin branch

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Parse --protected flags before sourcing shared config
CUSTOM_PROTECTED=()
PUSH_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --protected)
            CUSTOM_PROTECTED+=("$2")
            shift 2
            ;;
        *)
            PUSH_ARGS+=("$1")
            shift
            ;;
    esac
done

if [[ ${#CUSTOM_PROTECTED[@]} -gt 0 ]]; then
    GIT_PROTECTED_BRANCHES="${CUSTOM_PROTECTED[*]}"
    export GIT_PROTECTED_BRANCHES
fi

# shellcheck source=protected-branches.sh
source "$SCRIPT_DIR/protected-branches.sh"

# Detect force-push flags (--force-with-lease is intentionally allowed)
force=0
for arg in "${PUSH_ARGS[@]}"; do
    if [[ "$arg" == "--force" || "$arg" == "-f" ]]; then
        force=1
    fi
done

if [[ $force -eq 1 ]]; then
    target_branch=""
    for arg in "${PUSH_ARGS[@]}"; do
        if [[ "$arg" != -* ]]; then
            target_branch="${arg##*:}"
        fi
    done

    if [[ -z "$target_branch" ]]; then
        target_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
    fi

    if is_protected_branch "$target_branch"; then
        echo "BLOCKED: --force push to protected branch '$target_branch' is not allowed." >&2
        echo "Use --force-with-lease on a feature branch instead." >&2
        exit 2
    fi
fi

exec git push "${PUSH_ARGS[@]}"
