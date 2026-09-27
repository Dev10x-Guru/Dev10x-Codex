from __future__ import annotations

from pathlib import Path

from dev10x.hooks.session_place import session_git_aliases

CODEX_GUIDANCE_FILE = "session-guidance-codex.md"

CODEX_ALIAS_SETUP_HINT = "Call the `mcp__cli__setup_aliases` MCP tool to configure them."

CODEX_SUPPRESSED_FEATURES = frozenset(
    {
        "session-skills-index",
        "session-autonomy",
        "session-auto-plan",
        "session-mode-guard",
        "session-friction-setup",
        "session-install-check",
        "session-hook-version-drift",
        "session-migrate-permissions",
        "session-reload",
    }
)


def _default_plugin_root() -> Path:
    return Path(__file__).parents[3]


def build_codex_guidance_context(*, plugin_root: Path | None = None) -> str:
    root = plugin_root or _default_plugin_root()
    guidance_file = root / "hooks" / "scripts" / CODEX_GUIDANCE_FILE
    return guidance_file.read_text() if guidance_file.exists() else ""


def session_git_aliases_codex() -> None:
    session_git_aliases(setup_hint=CODEX_ALIAS_SETUP_HINT)


__all__ = [
    "CODEX_ALIAS_SETUP_HINT",
    "CODEX_GUIDANCE_FILE",
    "CODEX_SUPPRESSED_FEATURES",
    "build_codex_guidance_context",
    "session_git_aliases_codex",
]
