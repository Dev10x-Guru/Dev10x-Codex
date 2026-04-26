#!/usr/bin/env bash
# Safe git push wrapper — blocks force push to protected branches.
#
# Usage: git-push-safe.sh [git push arguments...]
#
# Default protected branches: main master
# Override: GIT_PROTECTED_BRANCHES="main master staging" git-push-safe.sh ...

set -euo pipefail

if [[ -n "${GIT_PROTECTED_BRANCHES:-}" ]]; then
    read -r -a PROTECTED_BRANCHES <<< "$GIT_PROTECTED_BRANCHES"
else
    PROTECTED_BRANCHES=(main master)
fi

is_protected() {
    local branch="$1"
    for protected in "${PROTECTED_BRANCHES[@]}"; do
        if [[ "$branch" == "$protected" ]]; then
            return 0
        fi
    done
    return 1
}

# Detect force-push flags (--force-with-lease is intentionally allowed)
force=0
for arg in "$@"; do
    if [[ "$arg" == "--force" || "$arg" == "-f" ]]; then
        force=1
    fi
done

if [[ $force -eq 1 ]]; then
    target_branch=""
    for arg in "$@"; do
        if [[ "$arg" != -* ]]; then
            target_branch="${arg##*:}"
        fi
    done

    if [[ -z "$target_branch" ]]; then
        target_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
    fi

    if is_protected "$target_branch"; then
        echo "BLOCKED: --force push to protected branch '$target_branch' is not allowed." >&2
        echo "Use --force-with-lease on a feature branch instead." >&2
        exit 2
    fi
fi

exec git push "$@"
