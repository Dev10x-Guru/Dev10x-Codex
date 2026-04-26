"""Tests for bin/require-tool.sh bash 3.2 compatibility."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = _REPO_ROOT / "bin" / "require-tool.sh"


def _run_bash(
    *,
    code: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    run_env = {**os.environ, **(env or {})}
    return subprocess.run(
        ["bash", "-c", code],
        capture_output=True,
        text=True,
        timeout=10,
        env=run_env,
    )


class TestRequireTool:
    def test_sourcing_does_not_error(self) -> None:
        result = _run_bash(code=f'source "{SCRIPT}"')
        assert result.returncode == 0, result.stderr

    def test_require_tool_succeeds_for_present_tool(self) -> None:
        result = _run_bash(
            code=f'source "{SCRIPT}" && require_tool bash',
        )
        assert result.returncode == 0, result.stderr

    def test_require_tool_fails_for_missing_tool(self) -> None:
        result = _run_bash(
            code=f'source "{SCRIPT}" && require_tool nonexistent_tool_xyz',
        )
        assert result.returncode == 1
        assert "nonexistent_tool_xyz" in result.stderr

    def test_install_url_shown_for_known_tool(self) -> None:
        result = _run_bash(
            code=f'source "{SCRIPT}" && _get_install_url jq',
        )
        assert result.returncode == 0
        assert "jqlang.github.io" in result.stdout

    def test_no_install_url_for_unknown_tool(self) -> None:
        result = _run_bash(
            code=f'source "{SCRIPT}" && require_tool nonexistent_tool_xyz',
        )
        assert result.returncode == 1
        assert "Install:" not in result.stderr


class TestGetInstallUrl:
    @pytest.mark.parametrize(
        ("tool", "expected_url"),
        [
            ("jq", "jqlang.github.io"),
            ("yq", "github.com/mikefarah/yq"),
            ("gh", "cli.github.com"),
        ],
    )
    def test_returns_url_for_known_tools(
        self,
        tool: str,
        expected_url: str,
    ) -> None:
        result = _run_bash(
            code=f'source "{SCRIPT}" && _get_install_url "{tool}"',
        )
        assert result.returncode == 0
        assert expected_url in result.stdout

    def test_returns_empty_for_unknown_tool(self) -> None:
        result = _run_bash(
            code=f'source "{SCRIPT}" && _get_install_url unknown_tool',
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""


class TestBash32Compatibility:
    def test_no_associative_array_declarations(self) -> None:
        content = SCRIPT.read_text()
        assert "declare -A" not in content, (
            "declare -A requires bash 4.0+ and breaks on macOS bash 3.2"
        )
