#!/usr/bin/env bash
# gh-issue-get.sh — Fetch GitHub issue details as JSON.
#
# Usage:
#   gh-issue-get.sh NUMBER [REPO]
#
# If REPO is omitted, detects from current directory.
#
# Output: JSON with title, body, state, labels, assignees, comments

set -euo pipefail

NUMBER="${1:?Usage: gh-issue-get.sh NUMBER [REPO]}"
REPO="${2:-$(gh repo view --json nameWithOwner -q '.nameWithOwner')}"

gh issue view "$NUMBER" --repo "$REPO" \
    --json number,title,body,state,labels,assignees,comments
