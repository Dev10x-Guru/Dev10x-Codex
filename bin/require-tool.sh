#!/usr/bin/env bash
# Shared tool detection with installation guide URLs.
#
# Usage (source in your script):
#   source "$(dirname "${BASH_SOURCE[0]}")/../../bin/require-tool.sh"
#   require_tool jq
#   require_tool yq

set -euo pipefail

# ── Installation URLs (case statement for bash 3.2 compat) ────
_get_install_url() {
    case "$1" in
        jq) echo "https://jqlang.github.io/jq/download/" ;;
        yq) echo "https://github.com/mikefarah/yq#install" ;;
        gh) echo "https://cli.github.com/manual/installation" ;;
    esac
}

# require_tool <name>
#   Checks tool is available on PATH.
#   Exits with an actionable error + install URL if missing.
require_tool() {
    local name="$1"

    if command -v "$name" &>/dev/null; then
        return 0
    fi

    local url
    url=$(_get_install_url "$name")
    echo >&2 "ERROR: '$name' not found on PATH."
    if [[ -n "$url" ]]; then
        echo >&2 "Install: $url"
    fi
    exit 1
}
