"""Edit/Write tool validator — blocks sensitive file writes.

Loads rules from command-skill-map.yaml where matcher="Edit|Write",
iterates registered rules, first block wins.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

from dev10x.domain.validation_rule import Compensation, Rule

_YAML_PATH = Path(__file__).parent.parent / "validators" / "command-skill-map.yaml"

EditRule = Rule


def load_rules(*, yaml_path: Path = _YAML_PATH) -> list[Rule]:
    data: dict[str, Any] = yaml.safe_load(yaml_path.read_text())
    rules: list[Rule] = []
    for entry in data.get("rules", []):
        if entry.get("matcher") != "Edit|Write":
            continue
        if not entry.get("hook_block", False):
            continue
        compensations = [
            Compensation(**{k: v for k, v in c.items() if k in Compensation.__dataclass_fields__})
            for c in entry.get("compensations", [])
        ]
        rules.append(
            Rule(
                name=entry.get("name", ""),
                matcher="Edit|Write",
                hook_block=True,
                file_pattern=entry.get("file_pattern", ""),
                file_names=entry.get("file_names", []),
                file_prefixes=entry.get("file_prefixes", []),
                file_substrings=entry.get("file_substrings", []),
                content_pattern=entry.get("content_pattern", ""),
                message=(entry.get("message") or entry.get("reason") or "BLOCKED").strip(),
                compensations=compensations,
            )
        )
    return rules


def block(*, message: str) -> None:
    result = {
        "hookSpecificOutput": {"permissionDecision": "deny"},
        "systemMessage": message,
    }
    print(json.dumps(result), file=sys.stderr)
    sys.exit(2)


def _load_edit_rules(*, yaml_path: Path) -> list[EditRule]:
    from dev10x.config.loader import load_config

    config = load_config(yaml_path=yaml_path)
    return [r for r in config.rules if r.matcher == "Edit|Write" and r.hook_block]


def validate_edit_write(
    *,
    data: dict[str, Any],
    yaml_path: Path | None = None,
    debug: bool = False,
) -> None:
    tool = data.get("tool_name", "")
    if tool not in ("Edit", "Write"):
        sys.exit(0)

    inp = data.get("tool_input", {})
    file_path = inp.get("file_path", "")
    content = inp.get("new_string") or inp.get("content", "")

    resolved_path = yaml_path or _YAML_PATH
    rules = _load_edit_rules(yaml_path=resolved_path)

    if debug:
        print(f"[DEBUG] Loaded {len(rules)} Edit|Write rules", file=sys.stderr)

    for rule in rules:
        if not rule.matches_file(file_path=file_path):
            continue
        if not rule.matches_content(content=content):
            continue
        if debug:
            print(f"[DEBUG] Rule '{rule.name}' matched: {file_path}", file=sys.stderr)
        block(message=rule.format_message(file_path=file_path))

    sys.exit(0)
