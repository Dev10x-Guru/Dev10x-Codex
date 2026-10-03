from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from dev10x.skills.codex.catalog import DEFERRED_AGENTS
from dev10x.skills.codex.translate import (
    PLUGIN_ROOT_PLACEHOLDER,
    TOOL_EQUIVALENTS_RELPATH,
    InvalidPluginRoot,
    rewrite_text,
    split_front_matter,
)
from dev10x.skills.codex.tree import GeneratedTree

UPSTREAM_AGENTS_RELPATH = PurePosixPath("agents")
CODEX_AGENTS_RELPATH = PurePosixPath("codex") / "agents"
ROLE_PREFIX = "Dev10x:"

EFFORT_BY_MODEL: dict[str, str] = {"opus": "high", "sonnet": "medium", "haiku": "low"}
DEFAULT_EFFORT = "medium"
EDITING_TOOLS: frozenset[str] = frozenset({"edit", "multiedit", "notebookedit", "write"})

_AGENT_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class InvalidAgentFile(ValueError):
    pass


def codex_role_name(stem: str) -> str:
    if not _AGENT_NAME_RE.match(stem):
        raise InvalidAgentFile(
            f"{stem!r} is not a valid agent file name: lowercase letters, digits and "
            "single hyphens"
        )
    return f"{ROLE_PREFIX}{stem}"


def agent_tools(value: object, *, source: PurePosixPath) -> frozenset[str]:
    if value is None:
        return frozenset()
    if isinstance(value, str):
        parts = value.split(",")
    elif isinstance(value, list) and all(isinstance(part, str) for part in value):
        parts = value
    else:
        raise InvalidAgentFile(
            f"{source}: tools must be a comma-separated string or a list of tool names"
        )
    return frozenset(part.strip() for part in parts if part.strip())


def is_read_only(tools: frozenset[str]) -> bool:
    return bool(tools) and not {tool.lower() for tool in tools} & EDITING_TOOLS


def reasoning_effort(model: object) -> str | None:
    if model is None or (isinstance(model, str) and not model.strip()):
        return DEFAULT_EFFORT
    if not isinstance(model, str):
        return None
    normalized = model.strip().lower()
    return next((effort for tier, effort in EFFORT_BY_MODEL.items() if tier in normalized), None)


def _escape_char(char: str, *, multiline: bool) -> str:
    if char == "\\":
        return "\\\\"
    if char == '"' and not multiline:
        return '\\"'
    if multiline and char in "\n\t":
        return char
    if char == "\t":
        return "\\t"
    if ord(char) < 0x20 or ord(char) == 0x7F:
        return f"\\u{ord(char):04x}"
    return char


def toml_string(text: str) -> str:
    return '"' + "".join(_escape_char(char, multiline=False) for char in text) + '"'


def toml_multiline_string(text: str) -> str:
    body = text if text.endswith("\n") else f"{text}\n"
    escaped = "".join(_escape_char(char, multiline=True) for char in body)
    return '"""\n' + escaped.replace('"""', '""\\"') + '"""'


def render_instructions(*, stem: str, body: str, read_only: bool) -> str:
    equivalents = f"{PLUGIN_ROOT_PLACEHOLDER}/{TOOL_EQUIVALENTS_RELPATH.as_posix()}"
    lines = [
        f"You are the Dev10x `{stem}` agent, running as a Codex subagent.",
        f"Where these instructions name a Claude Code tool, use the Codex equivalent in "
        f"`{equivalents}`, where `{PLUGIN_ROOT_PLACEHOLDER}` is the Dev10x plugin folder.",
    ]
    if read_only:
        lines.append(
            "Read-only: never create, modify or delete files and never commit. Codex cannot "
            "restrict your tools, so keeping this rule is up to you."
        )
    return "\n".join(lines) + "\n\n" + rewrite_text(body).strip() + "\n"


def render_role(*, stem: str, description: str, effort: str, instructions: str) -> str:
    upstream = (UPSTREAM_AGENTS_RELPATH / f"{stem}.md").as_posix()
    return (
        f"# Generated from {upstream} by `dev10x skill codex-agents` — edit the upstream "
        "agent, not this file.\n"
        f"name = {toml_string(codex_role_name(stem))}\n"
        f"description = {toml_string(description)}\n"
        f"model_reasoning_effort = {toml_string(effort)}\n"
        f"developer_instructions = {toml_multiline_string(instructions)}\n"
    )


def codex_role_description(description: object, *, source: PurePosixPath) -> str:
    if not isinstance(description, str) or not description.strip():
        raise InvalidAgentFile(
            f"{source}: front matter must be a YAML mapping with a non-empty description — "
            "Codex offers a role to the model by its description"
        )
    return " ".join(rewrite_text(description).split())


def _agent_files(root: Path) -> list[Path]:
    agents_root = root / UPSTREAM_AGENTS_RELPATH
    files = sorted(agents_root.glob("*.md")) if agents_root.is_dir() else []
    if not files:
        raise InvalidPluginRoot(
            f"{agents_root} holds no agent files — refusing to translate an empty plugin"
        )
    return files


def translate_agents(root: Path) -> GeneratedTree:
    files: dict[PurePosixPath, str] = {}
    warnings: list[str] = []
    for path in _agent_files(root):
        stem = path.stem
        if stem in DEFERRED_AGENTS:
            continue
        source = UPSTREAM_AGENTS_RELPATH / path.name
        front_matter, body = split_front_matter(path.read_text(encoding="utf-8"), source=source)
        if not body.strip():
            raise InvalidAgentFile(f"{source}: agent body is empty — the role would carry no task")
        declared = front_matter.get("name")
        if declared is not None and declared != stem:
            warnings.append(f"{source}: name {declared!r} differs from the file name {stem!r}")
        model = front_matter.get("model")
        effort = reasoning_effort(model)
        if effort is None:
            warnings.append(
                f"{source}: model {model!r} names no known tier; using {DEFAULT_EFFORT} effort"
            )
            effort = DEFAULT_EFFORT
        files[CODEX_AGENTS_RELPATH / f"{stem}.toml"] = render_role(
            stem=stem,
            description=codex_role_description(front_matter.get("description"), source=source),
            effort=effort,
            instructions=render_instructions(
                stem=stem,
                body=body,
                read_only=is_read_only(agent_tools(front_matter.get("tools"), source=source)),
            ),
        )
    return GeneratedTree(output=CODEX_AGENTS_RELPATH, files=files, warnings=warnings)
