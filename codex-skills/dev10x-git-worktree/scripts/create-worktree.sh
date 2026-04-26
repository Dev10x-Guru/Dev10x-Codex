#!/usr/bin/env bash
# Create a git worktree, optionally from a different repo root.
#
# Usage: create-worktree.sh <worktree-path> <branch-name> [repo-root]
#   worktree-path: absolute path for the new worktree
#   branch-name:   new branch to create (e.g. user/TICKET-123/feature-description)
#   repo-root:     optional; defaults to current working directory's git root
#                  useful when running from a different directory, e.g.:
#                  create-worktree.sh /work/myproject/.worktrees/myproject-1 \
#                    user/TICKET-123/feature /work/myproject/myproject

set -euo pipefail

WORKTREE_PATH="${1:?Usage: create-worktree.sh <worktree-path> <branch-name> [repo-root]}"
BRANCH_NAME="${2:?Usage: create-worktree.sh <worktree-path> <branch-name> [repo-root]}"
REPO_ROOT="${3:-}"

if [ -n "$REPO_ROOT" ]; then
    git -C "$REPO_ROOT" worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME"
else
    git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME"
fi
