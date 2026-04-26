#!/usr/bin/env bash
# Statusline script — outputs branch and worktree info for Claude Code UI.
# Must complete within 2s. Graceful fallback when not in a git repo.

set -euo pipefail

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || {
    echo "no git repo"
    exit 0
}

toplevel=$(git rev-parse --show-toplevel 2>/dev/null || echo "")

if [[ -n "$toplevel" && -f "$toplevel/.git" ]]; then
    worktree_name=$(basename "$toplevel")
    echo "$branch ($worktree_name)"
else
    echo "$branch"
fi
