#!/usr/bin/env bash
# Verify branch state before creating a PR.
# Exits with code 1 on validation failure, printing the error message.
# On success, prints: BRANCH_NAME=<name> ISSUE=<ticket-id> BASE_BRANCH=<base>
#
# Options:
#   --force    Allow targeting a non-development base even when a
#              development branch (develop/development) exists
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

FORCE=false
for arg in "$@"; do
    [ "$arg" = "--force" ] && FORCE=true
done

# shellcheck source=detect-base-branch.sh
source "$SCRIPT_DIR/detect-base-branch.sh" ${FORCE:+--force}

BRANCH_NAME=$(git symbolic-ref --short HEAD)

# Cannot create PR from protected branches
if [[ "$BRANCH_NAME" =~ ^(develop|development|main|master|trunk)$ ]]; then
    echo "❌ Cannot create PR from $BRANCH_NAME. Checkout a feature branch first." >&2
    exit 1
fi

# Check for uncommitted changes (ignore untracked files — they don't affect the PR)
if [ -n "$(git status --porcelain | grep -v '^??')" ]; then
    echo "⚠️  You have uncommitted changes. Commit them first before creating a PR." >&2
    exit 1
fi

# Check if branch has commits ahead of base
COMMITS_AHEAD=$(git log "origin/$BASE_BRANCH..HEAD" --oneline)
if [ -z "$COMMITS_AHEAD" ]; then
    echo "⚠️  No commits to create PR from. Make some changes first." >&2
    exit 1
fi

# Check if branch contains commits from a release branch not on the base.
# Only relevant when the base is a development branch and a separate
# release branch (main/master) exists.
if [ -n "$DEV_BRANCH" ]; then
    MASTER_REF=""
    if git rev-parse --verify origin/master &>/dev/null; then
        MASTER_REF="origin/master"
    elif git rev-parse --verify origin/main &>/dev/null; then
        MASTER_REF="origin/main"
    fi

    if [ -n "$MASTER_REF" ]; then
        TOTAL_AHEAD=$(git log "origin/$BASE_BRANCH..HEAD" --oneline | wc -l)
        WITHOUT_MASTER=$(git log "origin/$BASE_BRANCH..HEAD" --oneline --not "$MASTER_REF" | wc -l)
        if [ "$WITHOUT_MASTER" -lt "$TOTAL_AHEAD" ]; then
            echo "⚠️  This branch includes commits from $MASTER_REF not on $BASE_BRANCH." >&2
            echo "The PR would target $MASTER_REF instead of $BASE_BRANCH." >&2
            echo "Rebase first: git rebase --onto origin/$BASE_BRANCH $MASTER_REF" >&2
            exit 1
        fi
    fi
fi

# Extract ticket ID from branch name (username/TICKET-ID/[worktree/]description)
ISSUE=$(echo "$BRANCH_NAME" | cut -d'/' -f2)

echo "BRANCH_NAME=$BRANCH_NAME"
echo "ISSUE=$ISSUE"
echo "BASE_BRANCH=$BASE_BRANCH"
