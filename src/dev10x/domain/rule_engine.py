"""RuleEngine — single entry point for all rule evaluation.

Replaces the procedural loops in edit_validator.validate_edit_write()
and SkillRedirectValidator.validate() with a unified collection class
that supports lazy iteration (stops at first blocking match).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from dev10x.domain.validation_rule import Compensation, Rule

EditRule = Rule


@dataclass(frozen=True)
class CommandRule:
    name: str
    patterns: list[re.Pattern[str]]
    except_: list[str]
    compensations: list[dict[str, Any]]


@dataclass(frozen=True)
class RuleMatch:
    rule_name: str
    message: str


@dataclass
class RuleEngine:
    edit_rules: list[EditRule] = field(default_factory=list)
    command_rules: list[CommandRule] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, *, path: Path) -> RuleEngine:
        data: dict[str, Any] = yaml.safe_load(path.read_text())
        edit_rules: list[EditRule] = []
        command_rules: list[CommandRule] = []

        for entry in data.get("rules", []):
            matcher = entry.get("matcher", "Bash")
            if not entry.get("hook_block", False):
                continue

            if matcher == "Edit|Write":
                fp = entry.get("file_pattern")
                cp = entry.get("content_pattern")
                compensations = [
                    Compensation(
                        **{k: v for k, v in c.items() if k in Compensation.__dataclass_fields__}
                    )
                    for c in entry.get("compensations", [])
                ]
                edit_rules.append(
                    EditRule(
                        name=entry.get("name", ""),
                        file_pattern=fp or "",
                        file_names=list(entry.get("file_names", [])),
                        file_prefixes=list(entry.get("file_prefixes", [])),
                        file_substrings=list(entry.get("file_substrings", [])),
                        content_pattern=cp or "",
                        message=(entry.get("message") or entry.get("reason") or "BLOCKED").strip(),
                        compensations=compensations,
                    )
                )
            elif matcher == "Bash":
                command_rules.append(
                    CommandRule(
                        name=entry.get("name", ""),
                        patterns=[re.compile(p) for p in entry.get("patterns", [])],
                        except_=entry.get("except", []),
                        compensations=entry.get("compensations", []),
                    )
                )

        return cls(edit_rules=edit_rules, command_rules=command_rules)

    def evaluate(
        self,
        *,
        file_path: str,
        content: str,
    ) -> RuleMatch | None:
        for rule in self.edit_rules:
            if not rule.matches_file(file_path=file_path):
                continue
            if not rule.matches_content(content=content):
                continue
            return RuleMatch(
                rule_name=rule.name,
                message=rule.format_message(file_path=file_path),
            )
        return None

    def evaluate_file(self, *, file_path: str) -> RuleMatch | None:
        for rule in self.edit_rules:
            if not rule.matches_file(file_path=file_path):
                continue
            return RuleMatch(
                rule_name=rule.name,
                message=rule.format_message(file_path=file_path),
            )
        return None

    def evaluate_command(self, *, command: str) -> CommandRule | None:
        for rule in self.command_rules:
            if not any(p.search(command) for p in rule.patterns):
                continue
            if any(exc in command for exc in rule.except_):
                continue
            return rule
        return None
