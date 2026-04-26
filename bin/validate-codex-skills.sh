#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACK_DIR="$ROOT_DIR/codex-skills"

if [ ! -d "$PACK_DIR" ]; then
  echo "Missing codex-skills directory: $PACK_DIR" >&2
  exit 1
fi

status=0
count=0

for skill_dir in "$PACK_DIR"/*; do
  [ -d "$skill_dir" ] || continue
  count=$((count + 1))
  skill_md="$skill_dir/SKILL.md"
  skill_name="$(basename "$skill_dir")"

  if [ ! -f "$skill_md" ]; then
    echo "ERROR [$skill_name]: missing SKILL.md"
    status=1
    continue
  fi

  if ! sed -n '1p' "$skill_md" | rg -q '^---$'; then
    echo "ERROR [$skill_name]: first line must be ---"
    status=1
    continue
  fi

  fm="$(awk 'NR==1{next} /^---$/{exit} {print}' "$skill_md")"
  fm_keys="$(echo "$fm" | rg -o '^[a-zA-Z0-9_-]+:' | sed 's/:$//' || true)"
  fm_key_count="$(echo "$fm_keys" | sed '/^$/d' | wc -l | tr -d ' ')"

  if [ "$fm_key_count" -ne 2 ]; then
    echo "ERROR [$skill_name]: frontmatter must contain exactly 2 keys (name, description)"
    status=1
  fi

  if ! echo "$fm" | rg -q '^name: [a-z0-9-]+$'; then
    echo "ERROR [$skill_name]: missing/invalid name in frontmatter"
    status=1
  fi

  if ! echo "$fm" | rg -q '^description: .+'; then
    echo "ERROR [$skill_name]: missing/invalid description in frontmatter"
    status=1
  fi

  if echo "$fm" | rg -q '^(user-invocable|invocation-name|allowed-tools|metadata):'; then
    echo "ERROR [$skill_name]: Claude-only keys found in frontmatter"
    status=1
  fi
done

echo "Validated $count skills in $PACK_DIR"
exit "$status"
