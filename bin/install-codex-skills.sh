#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$ROOT_DIR/codex-skills"
DEST_BASE="${CODEX_HOME:-$HOME/.codex}"
DEST_DIR="$DEST_BASE/skills"

if [ ! -d "$SRC_DIR" ]; then
  echo "Missing source directory: $SRC_DIR" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"

installed=0
for skill_dir in "$SRC_DIR"/*; do
  [ -d "$skill_dir" ] || continue
  skill_name="$(basename "$skill_dir")"
  rm -rf "$DEST_DIR/$skill_name"
  cp -R "$skill_dir" "$DEST_DIR/$skill_name"
  installed=$((installed + 1))
done

echo "Installed $installed skills to $DEST_DIR"
echo "Restart Codex to pick up new skills."
