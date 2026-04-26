#!/usr/bin/env bash
# Create a draft PR with two-pass body generation.
# Usage: create-pr.sh <title> <job_story> <issue_id> [<fixes_url>] [<base_branch>]
# Outputs the PR number on success.
set -euo pipefail

TITLE="$1"
JOB_STORY="$2"
ISSUE="$3"
FIXES_URL="${4:-}"
BASE_BRANCH="${5:-}"

FIXES_LINE=""
if [ -n "$FIXES_URL" ]; then
    FIXES_LINE=$(printf '\nFixes: %s\n' "$FIXES_URL")
fi

BRANCH_NAME=$(git symbolic-ref --short HEAD)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Detect base branch if not provided
if [ -z "$BASE_BRANCH" ]; then
    # shellcheck source=detect-base-branch.sh
    source "$SCRIPT_DIR/detect-base-branch.sh"
fi

# Load checklist template (substitute issue ID placeholder)
CHECKLIST=""
if [ -f .github/checklist.md ]; then
    CHECKLIST=$(sed "s/ISSUE-NO/$ISSUE/" .github/checklist.md)
fi

# Push branch
git push --set-upstream origin "$BRANCH_NAME"

# First pass: create PR with plain commit list + checklist
COMMITS=$(git log "origin/$BASE_BRANCH..HEAD" --reverse --format="- %s")
BODY=$(printf '%s\n\n---\n\n%s%s\n\n---\n\n%s' \
    "$JOB_STORY" "$COMMITS" "$FIXES_LINE" "$CHECKLIST")
gh pr create --draft --base "$BASE_BRANCH" --title "$TITLE" --body "$BODY"

# Get PR number
PR_NUMBER=$(gh pr view --json number -q .number)

# Second pass: update body with linked commits
LINKED_COMMITS=$("$SCRIPT_DIR/generate-commit-list.sh" "$PR_NUMBER" "$BASE_BRANCH")
FINAL_BODY=$(printf '%s\n\n---\n\n%s%s\n\n---\n\n%s' \
    "$JOB_STORY" "$LINKED_COMMITS" "$FIXES_LINE" "$CHECKLIST")
gh pr edit "$PR_NUMBER" --body "$FINAL_BODY"

echo "$PR_NUMBER"
