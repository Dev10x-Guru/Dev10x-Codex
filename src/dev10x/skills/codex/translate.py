from __future__ import annotations

import os
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

import yaml

from dev10x.skills.codex.catalog import VERIFIED_SKILLS

UPSTREAM_SKILLS_RELPATH = PurePosixPath("skills")
CODEX_SKILLS_RELPATH = PurePosixPath("codex") / "skills"
TOOL_EQUIVALENTS_RELPATH = PurePosixPath("codex") / "references" / "claude-tool-equivalents.md"

COPIED_SUFFIXES: frozenset[str] = frozenset({".md", ".yaml", ".yml"})
UPSTREAM_ONLY_DIRS: frozenset[str] = frozenset({"evals", "scripts", "templates"})
SKILL_FILE = "SKILL.md"
OPENAI_YAML_RELPATH = PurePosixPath("agents") / "openai.yaml"

NAME_MAX_LENGTH = 64
DESCRIPTION_MAX_LENGTH = 1024
PLUGIN_ROOT_PLACEHOLDER = "<plugin-root>"

SKILL_ALIASES: dict[str, str] = {"test": "py-test"}

DISPLAY_ACRONYMS: dict[str, str] = {
    "adr": "ADR",
    "afk": "AFK",
    "acc": "AC",
    "db": "DB",
    "ddd": "DDD",
    "dod": "DoD",
    "gh": "GH",
    "ide": "IDE",
    "jtbd": "JTBD",
    "k8s": "K8s",
    "pr": "PR",
    "py": "Python",
    "qa": "QA",
    "tts": "TTS",
    "uv": "uv",
    "yt": "YouTube",
}

_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)
_MCP_PREFIX_RE = re.compile(r"mcp__plugin_Dev10x_(cli|db)__")
_PLUGIN_ROOT_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}|\$CLAUDE_PLUGIN_ROOT\b")
_SKILL_CALL_RE = re.compile(
    r"Skill\(\s*(?:skill\s*=\s*)?[\"']?(Dev10x:[a-z0-9-]+\b|test\b)[\"']?"
    r"(?:\s*,\s*(?:args\s*=\s*)?|\s+)?([^)]*?)\s*\)"
)
_SLASH_SKILL_RE = re.compile(r"(^|[\s`(\[\"'])/(Dev10x:[a-z0-9-]+)", re.MULTILINE)
_SKILL_MENTION_RE = re.compile(r"(?<![\w/-])Dev10x:([a-z0-9]+(?:-[a-z0-9]+)*)")
_MARKDOWN_LINK_RE = re.compile(r"(\[[^\]\n]*\]\()([^)\s]+)((?:\s+\"[^\"\n]*\")?\))")
_EXTERNAL_TARGET_RE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|#|/|~|<|\$)", re.IGNORECASE)


class InvalidSkillName(ValueError):
    pass


class InvalidSkillFile(ValueError):
    pass


@dataclass(frozen=True)
class CodexSkillTree:
    files: dict[PurePosixPath, str]
    warnings: list[str] = field(default_factory=list)


def codex_skill_name(directory: str) -> str:
    if len(directory) > NAME_MAX_LENGTH or not _NAME_RE.match(directory):
        raise InvalidSkillName(
            f"{directory!r} is not a valid Codex skill name: lowercase letters, digits and "
            f"single hyphens, at most {NAME_MAX_LENGTH} characters"
        )
    return directory


def display_name(directory: str) -> str:
    return " ".join(DISPLAY_ACRONYMS.get(word, word.capitalize()) for word in directory.split("-"))


def split_front_matter(text: str) -> tuple[dict, str]:
    match = _FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text
    data = yaml.safe_load(match.group(1)) or {}
    if not isinstance(data, dict):
        return {}, text
    return data, text[match.end() :]


def codex_skill_reference(name: str) -> str:
    skill = SKILL_ALIASES.get(name, name.removeprefix("Dev10x:"))
    return f"$Dev10x:{skill}"


def _replace_skill_call(match: re.Match[str]) -> str:
    reference = codex_skill_reference(match.group(1))
    arguments = (match.group(2) or "").strip()
    return f"{reference} (args: {arguments})" if arguments else reference


def rewrite_text(text: str) -> str:
    text = _MCP_PREFIX_RE.sub(r"mcp__\1__", text)
    text = _PLUGIN_ROOT_RE.sub(PLUGIN_ROOT_PLACEHOLDER, text)
    text = _SKILL_CALL_RE.sub(_replace_skill_call, text)
    return _SLASH_SKILL_RE.sub(lambda m: f"{m.group(1)}{codex_skill_reference(m.group(2))}", text)


def unknown_skill_mentions(text: str, known: Iterable[str]) -> list[str]:
    known_names = set(known)
    return sorted({name for name in _SKILL_MENTION_RE.findall(text) if name not in known_names})


def codex_path_for(upstream: PurePosixPath) -> PurePosixPath:
    return CODEX_SKILLS_RELPATH / upstream.relative_to(UPSTREAM_SKILLS_RELPATH)


def _normalize(path: PurePosixPath) -> PurePosixPath | None:
    normalized = PurePosixPath(os.path.normpath(path.as_posix()))
    if normalized.parts and normalized.parts[0] == "..":
        return None
    return normalized


def rewrite_links(
    text: str,
    *,
    source: PurePosixPath,
    target: PurePosixPath,
    copied: frozenset[PurePosixPath],
    exists: Callable[[PurePosixPath], bool],
) -> str:
    def replace(match: re.Match[str]) -> str:
        link = match.group(2)
        if _EXTERNAL_TARGET_RE.match(link):
            return match.group(0)
        path_part, hash_sign, anchor = link.partition("#")
        resolved = _normalize(source.parent / path_part) if path_part else None
        if resolved is None or not exists(resolved):
            return match.group(0)
        mapped = codex_path_for(resolved) if resolved in copied else resolved
        relative = os.path.relpath(mapped.as_posix(), target.parent.as_posix())
        return f"{match.group(1)}{relative}{hash_sign}{anchor}{match.group(3)}"

    return _MARKDOWN_LINK_RE.sub(replace, text)


def codex_description(description: object) -> str:
    folded = " ".join(rewrite_text(str(description or "")).split())
    folded = folded.replace("<", "‹").replace(">", "›")
    if len(folded) <= DESCRIPTION_MAX_LENGTH:
        return folded
    cut = folded[: DESCRIPTION_MAX_LENGTH - 1].rsplit(" ", 1)[0]
    return f"{cut}…"


def render_front_matter(*, name: str, description: str, upstream: PurePosixPath) -> str:
    document = {
        "name": name,
        "description": description,
        "metadata": {"upstream": upstream.as_posix()},
    }
    dumped = yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=10_000)
    return f"---\n{dumped}---\n"


def render_preamble(*, directory: str, target: PurePosixPath, verified: bool) -> str:
    equivalents = os.path.relpath(TOOL_EQUIVALENTS_RELPATH.as_posix(), target.parent.as_posix())
    upstream_dir = (UPSTREAM_SKILLS_RELPATH / directory).as_posix()
    lines = [
        f"> **Running in Codex.** Generated from `{upstream_dir}/` by "
        "`dev10x skill codex-skills` — edit the upstream skill, not this file.",
        "> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, "
        f"`Agent`, `Monitor`, …), use the Codex equivalent in [{equivalents}]({equivalents}).",
        f"> `{PLUGIN_ROOT_PLACEHOLDER}` is the Dev10x plugin folder (the one holding "
        f"`.codex-plugin/`); this skill's `scripts/` and `templates/` stay in "
        f"`{PLUGIN_ROOT_PLACEHOLDER}/{upstream_dir}/`.",
    ]
    if not verified:
        lines.append(
            "> Not yet verified in Codex (tracked in Dev10x-Codex#24): expect gaps and "
            "confirm before any step that writes to GitHub or rewrites history."
        )
    return "\n".join(lines) + "\n"


def render_openai_yaml(*, directory: str, implicit: bool) -> str:
    return (
        "interface:\n"
        f'  display_name: "{display_name(directory)}"\n'
        "policy:\n"
        f"  allow_implicit_invocation: {'true' if implicit else 'false'}\n"
    )


def _copied_files(skill_dir: Path, upstream_dir: PurePosixPath) -> list[PurePosixPath]:
    files: list[PurePosixPath] = []
    for path in sorted(skill_dir.rglob("*")):
        relative = path.relative_to(skill_dir)
        if not path.is_file() or path.suffix not in COPIED_SUFFIXES:
            continue
        if relative.parts[0] in UPSTREAM_ONLY_DIRS or "__pycache__" in relative.parts:
            continue
        files.append(upstream_dir / PurePosixPath(relative.as_posix()))
    return files


def _skill_directories(root: Path) -> list[Path]:
    skills_root = root / UPSTREAM_SKILLS_RELPATH
    return sorted(
        path for path in skills_root.iterdir() if path.is_dir() and (path / SKILL_FILE).is_file()
    )


def translate_skills(root: Path) -> CodexSkillTree:
    directories = _skill_directories(root)
    known = [directory.name for directory in directories]
    sources: dict[str, list[PurePosixPath]] = {
        directory.name: _copied_files(directory, UPSTREAM_SKILLS_RELPATH / directory.name)
        for directory in directories
    }
    copied = frozenset(path for paths in sources.values() for path in paths)
    files: dict[PurePosixPath, str] = {}
    warnings: list[str] = []

    def relink(text: str, *, source: PurePosixPath, target: PurePosixPath) -> str:
        return rewrite_links(
            rewrite_text(text),
            source=source,
            target=target,
            copied=copied,
            exists=lambda path: (root / path).exists(),
        )

    for directory in directories:
        name = codex_skill_name(directory.name)
        verified = name in VERIFIED_SKILLS
        for source in sources[name]:
            target = codex_path_for(source)
            text = (root / source).read_text(encoding="utf-8")
            for unknown in unknown_skill_mentions(text, known):
                warnings.append(f"{source}: mentions Dev10x:{unknown}, which has no skill")
            if source.name == SKILL_FILE and source.parent.name == name:
                front_matter, body = split_front_matter(text)
                description = front_matter.get("description")
                if not isinstance(description, str) or not description.strip():
                    raise InvalidSkillFile(
                        f"{source}: front matter must be a YAML mapping with a non-empty "
                        "description — Codex lists a skill by its description"
                    )
                files[target] = (
                    render_front_matter(
                        name=name,
                        description=codex_description(description),
                        upstream=source,
                    )
                    + "\n"
                    + render_preamble(directory=name, target=target, verified=verified)
                    + relink(body, source=source, target=target)
                )
            elif source.suffix == ".md":
                files[target] = relink(text, source=source, target=target)
            else:
                files[target] = rewrite_text(text)
        files[CODEX_SKILLS_RELPATH / name / OPENAI_YAML_RELPATH] = render_openai_yaml(
            directory=name, implicit=verified
        )

    return CodexSkillTree(files=files, warnings=warnings)


def read_tree(root: Path) -> dict[PurePosixPath, str]:
    codex_root = root / CODEX_SKILLS_RELPATH
    if not codex_root.is_dir():
        return {}
    return {
        CODEX_SKILLS_RELPATH / PurePosixPath(path.relative_to(codex_root).as_posix()): (
            path.read_text(encoding="utf-8")
        )
        for path in sorted(codex_root.rglob("*"))
        if path.is_file()
    }


def stale_paths(root: Path, tree: CodexSkillTree) -> list[PurePosixPath]:
    current = read_tree(root)
    return sorted(
        path
        for path in current.keys() | tree.files.keys()
        if current.get(path) != tree.files.get(path)
    )
