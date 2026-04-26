#!/usr/bin/env bash
# Convert QA evidence files for Linear upload.
#
# Usage:
#   convert-evidence.sh screenshots /tmp/claude/self-qa/test1.png /tmp/claude/self-qa/test2.png
#   convert-evidence.sh video /tmp/claude/self-qa/qa-video-dir/recording.webm
#
# Commands:
#   screenshots  Convert PNGs to JPGs (quality 70, max 1200px wide)
#   video        Convert webm to mp4 (h264, crf 28, faststart)
#
# Output:
#   Prints converted file paths to stdout, one per line.
#   Originals are NOT deleted.

set -euo pipefail

cmd_screenshots() {
    if [[ $# -eq 0 ]]; then
        echo "Usage: convert-evidence.sh screenshots <file1.png> [file2.png ...]" >&2
        exit 1
    fi

    for src in "$@"; do
        if [[ ! -f "$src" ]]; then
            echo "SKIP: $src not found" >&2
            continue
        fi
        dst="${src%.png}.jpg"
        convert "$src" -quality 70 -resize 1200x "$dst"
        echo "$dst"
        echo "  Converted: $(basename "$src") → $(basename "$dst") ($(du -h "$dst" | cut -f1))" >&2
    done
}

cmd_video() {
    if [[ $# -eq 0 ]]; then
        echo "Usage: convert-evidence.sh video <recording.webm>" >&2
        exit 1
    fi

    local src="$1"
    if [[ ! -f "$src" ]]; then
        echo "ERROR: $src not found" >&2
        exit 1
    fi

    local dst="${src%.webm}.mp4"
    if [[ "$src" == "$dst" ]]; then
        # Source is already mp4 or has no .webm extension
        dst="${src}.mp4"
    fi

    ffmpeg -i "$src" -c:v libx264 -preset fast -crf 28 -movflags +faststart "$dst" -y \
        </dev/null

    echo "$dst"
    echo "  Converted: $(basename "$src") → $(basename "$dst") ($(du -h "$dst" | cut -f1))" >&2
}

case "${1:-}" in
    screenshots) shift; cmd_screenshots "$@" ;;
    video)       shift; cmd_video "$@" ;;
    *)
        echo "Usage: convert-evidence.sh {screenshots|video} <files...>" >&2
        exit 1
        ;;
esac
