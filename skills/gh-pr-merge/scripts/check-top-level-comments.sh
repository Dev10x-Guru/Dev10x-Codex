#!/usr/bin/env bash
# Check for unaddressed automated review comments on a PR.
# Usage: check-top-level-comments.sh <owner> <repo> <pr_number>
# Outputs JSON array of unaddressed findings (empty array = pass).
set -euo pipefail

OWNER="$1"
REPO="$2"
PR_NUMBER="$3"

gh api "repos/${OWNER}/${REPO}/issues/${PR_NUMBER}/comments" \
  --jq '[.[] | select(
    (.body | test("REQUIRED|CRITICAL|BLOCKING|\\*\\*\\[BLOCKING\\]\\*\\*|\\*\\*\\[CRITICAL\\]\\*\\*"))
    and (.user.type == "Bot" or (.user.login | test("claude|github-actions")))
  ) | {id, user: .user.login, snippet: (.body | split("\n")[0][:80])}]'
