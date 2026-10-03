from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType

import pytest

from dev10x.hooks import session as session_module
from dev10x.hooks.session_codex import (
    CODEX_ALIAS_SETUP_HINT,
    CODEX_SUPPRESSED_FEATURES,
    build_codex_guidance_context,
    session_git_aliases_codex,
)
from dev10x.hooks.session_place import ALIAS_SETUP_HINT

SCRIPTS = Path(__file__).resolve().parents[2] / "hooks" / "scripts"
SESSION_START = SCRIPTS / "session-start.py"

CLAUDE_FEATURE_NAMES = [
    "session-load-marker",
    "session-git-aliases",
    "session-tmpdir",
    "session-guidance",
    "session-skills-index",
    "session-autonomy",
    "session-auto-plan",
    "session-mode-guard",
    "session-friction-setup",
    "session-install-check",
    "session-hook-version-drift",
    "session-migrate-permissions",
    "session-reload",
]

CODEX_FEATURE_NAMES = [
    "session-load-marker",
    "session-git-aliases",
    "session-tmpdir",
    "session-guidance",
]


def _load_session_start() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_session_start_codex_test", SESSION_START)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def session_start() -> ModuleType:
    return _load_session_start()


class TestFeatureSelection:
    def test_claude_feature_list_is_unchanged(
        self, session_start: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("DEV10X_HARNESS", raising=False)
        features = session_start.select_harness_features(
            features=session_start.build_features(session_module)
        )
        assert [feature.name for feature in features] == CLAUDE_FEATURE_NAMES
        guidance = next(f for f in features if f.name == "session-guidance")
        assert guidance.fn is session_module.build_guidance_context

    def test_codex_keeps_only_harness_neutral_features(
        self, session_start: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEV10X_HARNESS", "codex")
        features = session_start.select_harness_features(
            features=session_start.build_features(session_module)
        )
        assert [feature.name for feature in features] == CODEX_FEATURE_NAMES

    def test_codex_replaces_guidance_and_alias_hint(
        self, session_start: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEV10X_HARNESS", "codex")
        features = {
            feature.name: feature
            for feature in session_start.select_harness_features(
                features=session_start.build_features(session_module)
            )
        }
        assert features["session-guidance"].fn is build_codex_guidance_context
        assert features["session-git-aliases"].fn is session_git_aliases_codex

    def test_every_suppressed_name_is_a_real_feature(self) -> None:
        assert CODEX_SUPPRESSED_FEATURES <= set(CLAUDE_FEATURE_NAMES)


class TestCodexGuidance:
    def test_prefers_dev10x_mcp_tools(self) -> None:
        guidance = build_codex_guidance_context()
        for tool in (
            "mcp__cli__push_safe",
            "mcp__cli__create_pr",
            "mcp__cli__ci_check_status",
            "mcp__cli__rebase_groom",
            "mcp__cli__pr_get",
            "mcp__cli__issue_get",
        ):
            assert tool in guidance

    def test_names_the_guardrail_hooks(self) -> None:
        assert "PreToolUse" in build_codex_guidance_context()

    def test_points_at_the_codex_skills(self) -> None:
        guidance = build_codex_guidance_context()
        for skill in ("$Dev10x:git-commit", "$Dev10x:gh-pr-create", "$Dev10x:gh-pr-merge"):
            assert skill in guidance

    def test_carries_no_claude_only_vocabulary(self) -> None:
        guidance = build_codex_guidance_context()
        for claude_only in (
            "/Dev10x:",
            "Skill(",
            "TaskCreate",
            "AskUserQuestion",
            "mcp__plugin_Dev10x",
            "~/.claude",
        ):
            assert claude_only not in guidance

    def test_missing_guidance_file_yields_empty_context(self, tmp_path: Path) -> None:
        assert build_codex_guidance_context(plugin_root=tmp_path) == ""


class TestAliasHint:
    def test_codex_hint_names_the_setup_aliases_tool(self) -> None:
        assert "mcp__cli__setup_aliases" in CODEX_ALIAS_SETUP_HINT

    def test_claude_hint_is_unchanged(self) -> None:
        assert ALIAS_SETUP_HINT == (
            "Run the git-alias-setup skill (/Dev10x:git-alias-setup) to configure them."
        )

    def test_codex_alias_check_prints_codex_hint_when_aliases_missing(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr("dev10x.hooks.session_place._run_git", lambda *args: "")
        session_git_aliases_codex()
        out = capsys.readouterr().out
        assert CODEX_ALIAS_SETUP_HINT in out
        assert "/Dev10x:" not in out


def test_codex_session_start_emits_codex_briefing() -> None:
    home = tempfile.mkdtemp(prefix="dev10x-codex-session-home-")
    completed = subprocess.run(
        [sys.executable, str(SESSION_START)],
        input=json.dumps({"session_id": "codex-test", "hook_event_name": "SessionStart"}),
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(SCRIPTS.parent.parent),
        env={
            "DEV10X_HOOK_AUDIT": "0",
            "DEV10X_HARNESS": "codex",
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": home,
        },
    )
    assert completed.returncode == 0, completed.stderr
    context = json.loads(completed.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "mcp__cli__push_safe" in context
    assert "/Dev10x:" not in context
    assert not (Path(home) / ".config" / "Dev10x" / "friction.yaml").exists()
