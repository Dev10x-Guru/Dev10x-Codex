"""Tests for bin/statusline.sh."""

from __future__ import annotations

import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = _REPO_ROOT / "bin" / "statusline.sh"


def _run_statusline(*, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=3,
        cwd=cwd,
    )


class TestStatusline:
    def test_exits_successfully(self) -> None:
        result = _run_statusline()
        assert result.returncode == 0

    def test_outputs_branch_name(self) -> None:
        result = _run_statusline()
        assert len(result.stdout.strip()) > 0

    def test_outputs_single_line(self) -> None:
        result = _run_statusline()
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 1

    def test_completes_within_timeout(self) -> None:
        result = _run_statusline()
        assert result.returncode == 0

    def test_graceful_outside_git_repo(self, tmp_path: Path) -> None:
        result = _run_statusline(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "no git repo" in result.stdout
