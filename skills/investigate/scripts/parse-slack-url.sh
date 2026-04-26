#!/usr/bin/env bash
# Usage: parse-slack-url.sh <slack-url>
# Outputs: <channel_id> <thread_ts>
#
# Example:
#   https://example.slack.com/archives/CGV0GRW6S/p1771847635513919
#   → CGV0GRW6S 1771847635.513919

set -euo pipefail

url="${1:?Usage: parse-slack-url.sh <slack-url>}"

channel_id=$(echo "$url" | sed 's|.*/archives/\([^/]*\)/.*|\1|')
raw_ts=$(echo "$url" | sed 's|.*p\([0-9]*\)$|\1|')
thread_ts="${raw_ts:0:-6}.${raw_ts: -6}"

echo "$channel_id $thread_ts"
