#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Resolve the latest Codex JSONL session for a project directory."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def session_cwd(path: Path) -> str | None:
    try:
        with path.open() as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "session_meta":
                    payload = event.get("payload", {})
                    cwd = payload.get("cwd")
                    return cwd if isinstance(cwd, str) else None
    except OSError:
        return None
    return None


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else "latest"

    if arg.endswith(".jsonl"):
        path = Path(arg).expanduser()
        if not path.exists():
            print(f"Session file not found: {path}", file=sys.stderr)
            raise SystemExit(1)
        print(path)
        return

    target_cwd = Path.cwd() if arg == "latest" else Path(arg).expanduser()
    target_cwd = target_cwd.resolve()
    sessions_dir = Path.home() / ".codex" / "sessions"

    if not sessions_dir.exists():
        print(f"Codex sessions directory not found: {sessions_dir}", file=sys.stderr)
        raise SystemExit(1)

    matches: list[Path] = []
    for path in sessions_dir.rglob("*.jsonl"):
        cwd = session_cwd(path)
        if cwd and Path(cwd).expanduser().resolve() == target_cwd:
            matches.append(path)

    if not matches:
        print(f"No Codex session found for cwd: {target_cwd}", file=sys.stderr)
        raise SystemExit(1)

    newest = max(matches, key=lambda item: item.stat().st_mtime)
    print(newest)


if __name__ == "__main__":
    main()
