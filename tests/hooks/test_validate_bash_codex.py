from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATE_BASH = REPO_ROOT / "hooks" / "scripts" / "validate-bash-command.py"
CODEX_HOOKS = REPO_ROOT / "hooks" / "codex-hooks.json"


def codex_bash_payload(command: str) -> dict[str, object]:
    return {
        "session_id": "codex-validate-bash-test",
        "transcript_path": None,
        "cwd": str(REPO_ROOT),
        "hook_event_name": "PreToolUse",
        "model": "gpt-5.5",
        "permission_mode": "default",
        "tool_name": "Bash",
        "tool_use_id": "call_test",
        "tool_input": {"command": command},
    }


def run_hook(command: str) -> subprocess.CompletedProcess[str]:
    home = tempfile.mkdtemp(prefix="dev10x-codex-bash-home-")
    return subprocess.run(
        [sys.executable, str(VALIDATE_BASH)],
        input=json.dumps(codex_bash_payload(command)),
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(REPO_ROOT),
        env={
            "DEV10X_HOOK_AUDIT": "0",
            "DEV10X_HARNESS": "codex",
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": home,
        },
    )


class TestCodexBashHookEndToEnd:
    def test_registered_command_is_the_script_under_test(self) -> None:
        hooks = json.loads(CODEX_HOOKS.read_text())["hooks"]["PreToolUse"]
        bash = next(entry for entry in hooks if entry["matcher"] == "Bash")
        command = bash["hooks"][0]["command"]
        assert command.startswith("DEV10X_HARNESS=codex ")
        assert command.endswith(f"/hooks/scripts/{VALIDATE_BASH.name}")

    def test_raw_commit_is_denied_with_a_codex_skill_steer(self) -> None:
        completed = run_hook('git commit -m "wip"')
        assert completed.returncode == 2, completed.stdout + completed.stderr
        assert "$Dev10x:git-commit" in completed.stderr
        assert "/Dev10x:" not in completed.stderr
        assert completed.stdout.strip() == ""

    @pytest.mark.parametrize("command", ["git status", "ls"])
    def test_routine_command_passes(self, command: str) -> None:
        completed = run_hook(command)
        assert completed.returncode == 0, completed.stderr
