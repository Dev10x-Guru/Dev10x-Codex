from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from dev10x.mcp.git import mass_rewrite, rebase_groom


def _completed(
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=[],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


CONFLICT_STDOUT = (
    "CONFLICT_DETECTED\n"
    "conflicted_files=src/service.py,src/models.py,\n"
    "rebase_head=abc1234\n"
    "hint=Resolve conflicts, git add, then git rebase --continue"
)


class TestRebaseGroomConflictDetection:
    @pytest.fixture()
    def conflict_result(self) -> subprocess.CompletedProcess[str]:
        return _completed(returncode=1, stdout=CONFLICT_STDOUT)

    @pytest.fixture()
    def non_conflict_failure(self) -> subprocess.CompletedProcess[str]:
        return _completed(returncode=1, stderr="fatal: invalid upstream")

    @pytest.fixture()
    def success_result(self) -> subprocess.CompletedProcess[str]:
        return _completed(stdout="commits_rewritten=3")

    @patch("dev10x.mcp.git.run_script")
    def test_returns_conflict_info_on_conflict(
        self,
        mock_run_script,
        conflict_result,
    ) -> None:
        mock_run_script.return_value = conflict_result

        result = rebase_groom(seq_path="/tmp/seq.txt", base_ref="develop")

        assert result["success"] is False
        assert result["conflict"] is True
        assert result["conflicted_files"] == ["src/service.py", "src/models.py"]
        assert result["rebase_head"] == "abc1234"

    @patch("dev10x.mcp.git.run_script")
    def test_returns_error_on_non_conflict_failure(
        self,
        mock_run_script,
        non_conflict_failure,
    ) -> None:
        mock_run_script.return_value = non_conflict_failure

        result = rebase_groom(seq_path="/tmp/seq.txt", base_ref="develop")

        assert result["success"] is False
        assert "conflict" not in result
        assert result["error"] == "fatal: invalid upstream"

    @patch("dev10x.mcp.git.run_script")
    def test_returns_parsed_output_on_success(
        self,
        mock_run_script,
        success_result,
    ) -> None:
        mock_run_script.return_value = success_result

        result = rebase_groom(seq_path="/tmp/seq.txt", base_ref="develop")

        assert result["commits_rewritten"] == "3"


class TestMassRewriteConflictDetection:
    @pytest.fixture()
    def conflict_result(self) -> subprocess.CompletedProcess[str]:
        return _completed(
            returncode=1,
            stdout=(
                "Base: develop  |  Commits to rewrite: 2\n"
                "Running rebase…\n"
                "CONFLICT_DETECTED\n"
                "conflicted_files=src/handler.py,\n"
                "rebase_head=def5678\n"
                "hint=Resolve conflicts, git add, then git rebase --continue"
            ),
        )

    @pytest.fixture()
    def non_conflict_failure(self) -> subprocess.CompletedProcess[str]:
        return _completed(
            returncode=1,
            stdout="Base: develop",
            stderr="Rebase failed.",
        )

    @pytest.fixture()
    def success_result(self) -> subprocess.CompletedProcess[str]:
        return _completed(stdout="Done. New log:\nabc1234 Enable feature")

    @patch("dev10x.mcp.git.run_script")
    def test_returns_conflict_info_on_conflict(
        self,
        mock_run_script,
        conflict_result,
    ) -> None:
        mock_run_script.return_value = conflict_result

        result = mass_rewrite(config_path="/tmp/config.json")

        assert result["success"] is False
        assert result["conflict"] is True
        assert result["conflicted_files"] == ["src/handler.py"]
        assert result["rebase_head"] == "def5678"

    @patch("dev10x.mcp.git.run_script")
    def test_returns_error_on_non_conflict_failure(
        self,
        mock_run_script,
        non_conflict_failure,
    ) -> None:
        mock_run_script.return_value = non_conflict_failure

        result = mass_rewrite(config_path="/tmp/config.json")

        assert result["success"] is False
        assert "conflict" not in result
        assert result["error"] == "Rebase failed."

    @patch("dev10x.mcp.git.run_script")
    def test_returns_output_on_success(
        self,
        mock_run_script,
        success_result,
    ) -> None:
        mock_run_script.return_value = success_result

        result = mass_rewrite(config_path="/tmp/config.json")

        assert result["success"] is True
        assert "Enable feature" in result["output"]
