#!/usr/bin/env bash
# gh-issue-create.sh — Create a GitHub issue and return JSON.
#
# Usage:
#   gh-issue-create.sh TITLE [--body BODY] [--label LABEL]... [--repo REPO]
#
# If REPO is omitted, detects from current directory.
#
# Output: JSON with number, title, url

set -euo pipefail

TITLE="${1:?Usage: gh-issue-create.sh TITLE [--body BODY] [--label LABEL]... [--repo REPO]}"
shift

BODY=""
REPO=""
MILESTONE=""
LABELS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --body)
            BODY="$2"
            shift 2
            ;;
        --label)
            LABELS+=("$2")
            shift 2
            ;;
        --milestone)
            MILESTONE="$2"
            shift 2
            ;;
        --repo)
            REPO="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

if [[ -z "$REPO" ]]; then
    REPO="$(gh repo view --json nameWithOwner -q '.nameWithOwner')"
fi

ARGS=(gh issue create --repo "$REPO" --title "$TITLE")

if [[ -n "$BODY" ]]; then
    ARGS+=(--body "$BODY")
fi

for label in "${LABELS[@]}"; do
    ARGS+=(--label "$label")
done

if [[ -n "$MILESTONE" ]]; then
    ARGS+=(--milestone "$MILESTONE")
fi

URL=$("${ARGS[@]}")
NUMBER=$(echo "$URL" | grep -oP '/issues/\K[0-9]+$')

gh issue view "$NUMBER" --repo "$REPO" --json number,title,url
