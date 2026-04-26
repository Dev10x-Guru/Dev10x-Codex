"""Tests for session-start-reload.py hook."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
START_HOOK = _REPO_ROOT / "hooks" / "scripts" / "session-start-reload.py"


def _git_toplevel() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _run_reload(
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    import os

    run_env = {**os.environ, **(env or {})}
    return subprocess.run(
        [str(START_HOOK)],
        input="{}",
        capture_output=True,
        text=True,
        timeout=10,
        env=run_env,
    )


def _create_state_file(*, home: Path, session_id: str) -> None:
    toplevel = _git_toplevel()
    project_hash = hashlib.md5(toplevel.encode()).hexdigest()
    state_dir = home / ".claude" / "projects" / "_session_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "session_id": session_id,
        "branch": "develop",
        "worktree": "",
        "working_directory": toplevel,
        "timestamp": "2026-01-01T00:00:00Z",
        "modified_files": [],
        "staged_files": [],
        "recent_commits": ["abc1234 Test commit"],
        "has_plan": False,
    }
    (state_dir / f"{project_hash}.json").write_text(json.dumps(state))


class TestSessionStartReload:
    def test_exits_successfully_without_state(self) -> None:
        result = _run_reload()
        assert result.returncode == 0

    def test_outputs_nothing_without_state(self, tmp_path: Path) -> None:
        result = _run_reload(env={"HOME": str(tmp_path)})
        assert result.stdout == ""

    def test_outputs_context_with_state(self, tmp_path: Path) -> None:
        _create_state_file(home=tmp_path, session_id="reload-test-session")
        result = _run_reload(env={"HOME": str(tmp_path)})
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "Prior session state detected" in context
        assert "reload-test-session" in context

    def test_cleans_up_state_after_reload(self, tmp_path: Path) -> None:
        _create_state_file(home=tmp_path, session_id="cleanup-test")
        state_dir = tmp_path / ".claude" / "projects" / "_session_state"
        assert len(list(state_dir.glob("*.json"))) == 1
        _run_reload(env={"HOME": str(tmp_path)})
        assert len(list(state_dir.glob("*.json"))) == 0
