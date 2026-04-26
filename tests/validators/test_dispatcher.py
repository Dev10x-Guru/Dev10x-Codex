"""Tests for the unified dispatcher entry point."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DISPATCHER = (
    Path(__file__).resolve().parent.parent.parent
    / "hooks"
    / "scripts"
    / "validate-bash-command.py"
)


def _run_hook(*, tool_name: str, command: str) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({"tool_name": tool_name, "tool_input": {"command": command}})
    return subprocess.run(
        [sys.executable, str(DISPATCHER)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=str(DISPATCHER.parent),
    )


class TestDispatcherPassThrough:
    def test_allows_simple_git_command(self) -> None:
        result = _run_hook(tool_name="Bash", command="git status")
        assert result.returncode == 0

    def test_ignores_non_bash_tools(self) -> None:
        result = _run_hook(tool_name="Read", command="anything")
        assert result.returncode == 0

    def test_allows_empty_command(self) -> None:
        result = _run_hook(tool_name="Bash", command="")
        assert result.returncode == 0


class TestDispatcherBlocking:
    def test_blocks_env_prefix_git(self) -> None:
        result = _run_hook(
            tool_name="Bash",
            command="GIT_SEQUENCE_EDITOR=true git rebase -i HEAD~3",
        )
        assert result.returncode == 2

    def test_blocks_shell_write(self) -> None:
        result = _run_hook(
            tool_name="Bash",
            command="cat > /tmp/file.txt",
        )
        assert result.returncode == 2

    def test_blocks_python3_inline(self) -> None:
        result = _run_hook(
            tool_name="Bash",
            command='python3 -c "print(1)"',
        )
        assert result.returncode == 2

    def test_blocks_implementation_verb_commit(self) -> None:
        result = _run_hook(
            tool_name="Bash",
            command='git commit -m "Add new feature"',
        )
        assert result.returncode == 2

    def test_blocks_jtbd_verb_commit_with_m_flag(self) -> None:
        result = _run_hook(
            tool_name="Bash",
            command='git commit -m "Enable new feature"',
        )
        assert result.returncode == 2
        assert "Dev10x:git-commit" in result.stderr

    def test_allows_commit_with_skill_temp_f_flag(self) -> None:
        result = _run_hook(
            tool_name="Bash",
            command="git commit -F /tmp/claude/git/commit-msg.W9DryMXsQ5Aw.txt",
        )
        assert result.returncode == 0

    def test_allows_commit_with_any_file_under_git_namespace(self) -> None:
        result = _run_hook(
            tool_name="Bash",
            command="git commit -F /tmp/claude/git/msg.txt",
        )
        assert result.returncode == 0
