#!/usr/bin/env bash
# Grooming rebase wrapper — uses git-seq-editor.sh as GIT_SEQUENCE_EDITOR.
#
# Usage:
#   git-rebase-groom.sh <seq-file> <base-ref>
#
# Before calling: write rebase todo to <seq-file>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEQ_EDITOR="$SCRIPT_DIR/git-seq-editor.sh"

if [[ $# -lt 2 ]]; then
    echo "Usage: git-rebase-groom.sh <seq-file> <base-ref>" >&2
    exit 1
fi

GROOM_SEQ_FILE="$1"
shift
base_ref="$1"
shift

if [[ ! -f "$GROOM_SEQ_FILE" ]]; then
    echo "ERROR: $GROOM_SEQ_FILE not found." >&2
    echo "Use the Write tool to write the rebase todo to $GROOM_SEQ_FILE first." >&2
    exit 1
fi

if [[ ! -x "$SEQ_EDITOR" ]]; then
    echo "ERROR: $SEQ_EDITOR not found or not executable." >&2
    exit 1
fi

export GROOM_SEQ_FILE
GIT_SEQUENCE_EDITOR="$SEQ_EDITOR" \
GIT_EDITOR="true" \
    exec git rebase -i "$base_ref" "$@"
