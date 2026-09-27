#!/usr/bin/env bash
# Generate a unique temp path under /tmp/Dev10x/<namespace>/.
#
# Files: returns a path WITHOUT creating the file (use --create to
# pre-create). This avoids the Write-tool overwrite gate firing on
# every call (GH-39). Callers using the Write tool will create the
# file fresh.
# Directories: always created (the directory is the resource).
#
# Usage:
#   mktmp.sh <namespace> <prefix> [.ext]            # path only, no file
#   mktmp.sh --create <namespace> <prefix> [.ext]   # pre-create empty file
#   mktmp.sh -d <namespace> <prefix>                # create a directory
#
# Examples:
#   mktmp.sh git commit-msg .txt         → /tmp/Dev10x/git/commit-msg.XXXXXXXXXXXX.txt
#   mktmp.sh git pr-review .json         → /tmp/Dev10x/git/pr-review.XXXXXXXXXXXX.json
#   mktmp.sh -d git groom                → /tmp/Dev10x/git/groom.XXXXXXXXXXXX/

set -euo pipefail

DIR_MODE=false
CREATE_FILE=false
while [[ "${1:-}" == -* ]]; do
    case "$1" in
        -d) DIR_MODE=true ;;
        --create) CREATE_FILE=true ;;
        *) echo "mktmp.sh: unknown flag: $1" >&2; exit 2 ;;
    esac
    shift
done

NAMESPACE="${1:?Usage: mktmp.sh [-d|--create] <namespace> <prefix> [.ext]}"
PREFIX="${2:?Usage: mktmp.sh [-d|--create] <namespace> <prefix> [.ext]}"
EXT="${3:-}"

BASEDIR="/tmp/Dev10x/$NAMESPACE"
mkdir -p "$BASEDIR"

TEMPLATE="${PREFIX}.XXXXXXXXXXXX${EXT}"

if $DIR_MODE; then
    mktemp -d --tmpdir="$BASEDIR" "$TEMPLATE"
elif $CREATE_FILE; then
    mktemp --tmpdir="$BASEDIR" "$TEMPLATE"
else
    mktemp --dry-run --tmpdir="$BASEDIR" "$TEMPLATE"
fi
