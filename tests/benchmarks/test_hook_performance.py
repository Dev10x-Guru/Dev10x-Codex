"""Benchmark suite for CLI hook commands.

Uses pytest-benchmark to measure validate-bash and validate-edit
performance with representative inputs. Run with:
    pytest tests/benchmarks/ --benchmark-only
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK_SCRIPT = REPO_ROOT / "hooks" / "scripts" / "validate-bash-command.py"
EDIT_HOOK = REPO_ROOT / "hooks" / "scripts" / "validate-edit-write.py"


def _run_bash_hook(payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
    )


def _run_edit_hook(payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(EDIT_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
    )


@pytest.mark.benchmark(group="bash-hook")
class TestBashHookPerformance:
    def test_simple_allowed_command(self, benchmark) -> None:
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
        }
        result = benchmark(_run_bash_hook, payload=payload)
        assert result.returncode == 0

    def test_skill_redirected_command(self, benchmark) -> None:
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git push origin main"},
        }
        result = benchmark(_run_bash_hook, payload=payload)
        assert result.returncode == 2


@pytest.mark.benchmark(group="edit-hook")
class TestEditHookPerformance:
    def test_allowed_file_edit(self, benchmark) -> None:
        payload = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "/work/project/src/main.py",
                "new_string": "print('hello')",
            },
        }
        result = benchmark(_run_edit_hook, payload=payload)
        assert result.returncode == 0

    def test_blocked_env_file(self, benchmark) -> None:
        payload = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "/work/project/.env",
                "new_string": "SECRET=value",
            },
        }
        result = benchmark(_run_edit_hook, payload=payload)
        assert result.returncode == 2
