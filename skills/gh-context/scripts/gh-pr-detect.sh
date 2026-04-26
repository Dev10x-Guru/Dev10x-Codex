#!/usr/bin/env bash
# gh-pr-detect.sh — Detect PR context from a URL/number arg or current branch.
#
# Usage:
#   gh-pr-detect.sh [PR_URL_OR_NUMBER]
#
# Output: Prints shell-sourceable exports:
#   PR_NUMBER=123
#   REPO=your-org/your-repo
#   PR_URL=https://github.com/your-org/your-repo/pull/123
#   BRANCH=user/TICKET-123/feature-description
#
# CRITICAL: BRANCH is always fetched from GitHub via `gh pr view --json headRefName`.
# Never use `git branch --show-current` — it returns the CURRENT WORKTREE's branch,
# which belongs to a DIFFERENT PR when working in a multi-worktree setup.
#
# Exits non-zero and prints an error to stderr if PR cannot be detected.

set -euo pipefail

ARG="${1:-}"

if [[ "$ARG" =~ ^https://github\.com/ ]]; then
    # Parse from full URL: https://github.com/org/repo/pull/123
    PR_NUMBER=$(echo "$ARG" | grep -oE '[0-9]+$')
    REPO=$(echo "$ARG" | sed 's|https://github.com/||;s|/pull/.*||')
elif [[ "$ARG" =~ ^[0-9]+$ ]]; then
    # Bare PR number — detect repo from cwd
    PR_NUMBER="$ARG"
    REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner')
elif [[ -z "$ARG" ]]; then
    # No arg — detect from current branch
    PR_NUMBER=$(gh pr view --json number -q '.number' 2>/dev/null || true)
    if [[ -z "$PR_NUMBER" ]]; then
        echo "Error: No PR found for the current branch. Provide a PR URL or number." >&2
        exit 1
    fi
    REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner')
else
    echo "Error: Unrecognised argument '$ARG'. Pass a GitHub PR URL, PR number, or nothing." >&2
    exit 1
fi

# Always fetch URL and BRANCH from GitHub — never derive BRANCH from local git state.
PR_URL=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json url -q '.url')
BRANCH=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json headRefName -q '.headRefName')

printf 'PR_NUMBER=%s\nREPO=%s\nPR_URL=%s\nBRANCH=%s\n' \
    "$PR_NUMBER" "$REPO" "$PR_URL" "$BRANCH"
