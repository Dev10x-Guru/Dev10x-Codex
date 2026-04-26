from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cached_property


@dataclass(frozen=True)
class Compensation:
    type: str
    skill: str = ""
    tool: str = ""
    alias: str = ""
    guardrails: str = ""
    fallback: str = ""
    description: str = ""


@dataclass(frozen=True)
class Rule:
    name: str
    patterns: list[str] = field(default_factory=list)
    matcher: str = "Bash"
    except_: list[str] = field(default_factory=list)
    compensations: list[Compensation] = field(default_factory=list)
    hook_block: bool = True
    reason: str = ""
    message: str = ""
    related: list[str] = field(default_factory=list)
    file_pattern: str = ""
    file_names: list[str] = field(default_factory=list)
    file_prefixes: list[str] = field(default_factory=list)
    file_substrings: list[str] = field(default_factory=list)
    content_pattern: str = ""

    @cached_property
    def compiled_patterns(self) -> list[re.Pattern[str]]:
        return [re.compile(p) for p in self.patterns]

    @cached_property
    def compiled_file_pattern(self) -> re.Pattern[str] | None:
        return re.compile(self.file_pattern) if self.file_pattern else None

    @cached_property
    def compiled_content_pattern(self) -> re.Pattern[str] | None:
        return re.compile(self.content_pattern) if self.content_pattern else None

    def matches_file(self, *, file_path: str) -> bool:
        if self.compiled_file_pattern and self.compiled_file_pattern.search(file_path):
            return True
        name = file_path.rsplit("/", 1)[-1] if "/" in file_path else file_path
        if name in self.file_names:
            return True
        if any(name.startswith(p) for p in self.file_prefixes):
            return True
        return any(s in file_path for s in self.file_substrings)

    def matches_content(self, *, content: str) -> bool:
        if self.compiled_content_pattern is None:
            return True
        return self.compiled_content_pattern.search(content) is not None

    def format_message(self, *, file_path: str) -> str:
        text = self.message or self.reason or "BLOCKED"
        msg = text.format(file_path=file_path)
        for comp in self.compensations:
            desc = comp.description
            if desc:
                msg += f"\n\n{desc.strip()}"
        return msg

    def matches_command(self, *, command: str) -> bool:
        if not any(p.search(command) for p in self.compiled_patterns):
            return False
        if any(exc in command for exc in self.except_):
            return False
        return True


@dataclass(frozen=True)
class Config:
    friction_level: str = "strict"
    plugin_repo: str = ""
    rules: list[Rule] = field(default_factory=list)
