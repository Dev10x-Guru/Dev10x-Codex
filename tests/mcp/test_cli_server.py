"""Tests for servers/cli_server.py core infrastructure and tools.

This file covers the helper functions and a representative sample
of MCP tools. Full 100% coverage of all 21 tools is tracked in
GH-493 and will be completed incrementally.
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

# Import the server module — needs mcp available
cli_server = pytest.importorskip("dev10x.mcp.server_cli", reason="mcp not installed")

# GitHub tools extracted to dev10x.mcp.github
gh = pytest.importorskip("dev10x.mcp.github", reason="dev10x not installed")


class TestDetectRepo:
    @patch("dev10x.mcp.github.subprocess.run")
    def test_returns_repo_on_success(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Dev10x-Guru/dev10x-claude\n",
            stderr="",
        )

        result = gh._detect_repo()

        assert result == "Dev10x-Guru/dev10x-claude"

    @patch("dev10x.mcp.github.subprocess.run")
    def test_returns_none_on_failure(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="not a git repo",
        )

        result = gh._detect_repo()

        assert result is None


class TestGhApi:
    @patch("dev10x.mcp.github.subprocess.run")
    def test_builds_get_command(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="{}",
            stderr="",
        )

        gh._gh_api(endpoint="/repos/owner/repo")

        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "gh"
        assert cmd[1] == "api"
        assert "/repos/owner/repo" in cmd
        assert "-X" not in cmd

    @patch("dev10x.mcp.github.subprocess.run")
    def test_adds_method_for_non_get(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="{}",
            stderr="",
        )

        gh._gh_api(
            endpoint="/repos/owner/repo/pulls",
            method="POST",
        )

        cmd = mock_run.call_args[0][0]
        assert "-X" in cmd
        post_idx = cmd.index("-X")
        assert cmd[post_idx + 1] == "POST"

    @patch("dev10x.mcp.github.subprocess.run")
    def test_adds_jq_filter(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="value",
            stderr="",
        )

        gh._gh_api(
            endpoint="/repos/owner/repo",
            jq=".name",
        )

        cmd = mock_run.call_args[0][0]
        assert "--jq" in cmd
        jq_idx = cmd.index("--jq")
        assert cmd[jq_idx + 1] == ".name"

    @patch("dev10x.mcp.github.subprocess.run")
    def test_handles_string_fields(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="{}",
            stderr="",
        )

        gh._gh_api(
            endpoint="/repos/owner/repo",
            method="POST",
            fields={"title": "My PR"},
        )

        cmd = mock_run.call_args[0][0]
        assert "-f" in cmd
        f_idx = cmd.index("-f")
        assert cmd[f_idx + 1] == "title=My PR"

    @patch("dev10x.mcp.github.subprocess.run")
    def test_handles_int_fields(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="{}",
            stderr="",
        )

        gh._gh_api(
            endpoint="/repos/owner/repo",
            method="POST",
            fields={"count": 42},
        )

        cmd = mock_run.call_args[0][0]
        assert "-F" in cmd
        f_idx = cmd.index("-F")
        assert cmd[f_idx + 1] == "count=42"

    @patch("dev10x.mcp.github.subprocess.run")
    def test_handles_list_fields(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="{}",
            stderr="",
        )

        gh._gh_api(
            endpoint="/repos/owner/repo",
            method="POST",
            fields={"reviewers": ["alice", "bob"]},
        )

        cmd = mock_run.call_args[0][0]
        assert "-f" in cmd
        f_indices = [i for i, c in enumerate(cmd) if c == "-f"]
        assert len(f_indices) == 2
        assert cmd[f_indices[0] + 1] == "reviewers[]=alice"
        assert cmd[f_indices[1] + 1] == "reviewers[]=bob"


class TestResolveRepo:
    def test_returns_provided_repo(self) -> None:
        result, error = gh._resolve_repo(repo="owner/repo")

        assert result == "owner/repo"
        assert error is None

    @patch("dev10x.mcp.github._detect_repo", return_value="detected/repo")
    def test_detects_repo_when_none_provided(
        self,
        _mock: MagicMock,
    ) -> None:
        result, error = gh._resolve_repo(repo=None)

        assert result == "detected/repo"
        assert error is None

    @patch("dev10x.mcp.github._detect_repo", return_value=None)
    def test_returns_error_when_detection_fails(
        self,
        _mock: MagicMock,
    ) -> None:
        result, error = gh._resolve_repo(repo=None)

        assert result is None
        assert error is not None
        assert "error" in error


class TestDetectTracker:
    @pytest.mark.asyncio
    @patch("dev10x.mcp.github.run_script")
    async def test_returns_parsed_output_on_success(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="TRACKER=github\nTICKET_ID=GH-15\nTICKET_NUMBER=15\nFIXES_URL=https://github.com/org/repo/issues/15",
            stderr="",
        )

        result = await cli_server.detect_tracker(ticket_id="GH-15")

        assert result["TRACKER"] == "github"
        assert result["TICKET_NUMBER"] == "15"

    @pytest.mark.asyncio
    @patch("dev10x.mcp.github.run_script")
    async def test_returns_error_on_failure(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Unknown tracker",
        )

        result = await cli_server.detect_tracker(ticket_id="UNKNOWN-1")

        assert "error" in result


class TestMktmp:
    @pytest.mark.asyncio
    @patch("dev10x.mcp.utilities.run_script")
    async def test_creates_temp_file(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="/tmp/claude/git/commit-msg.abc123.txt",
            stderr="",
        )

        result = await cli_server.mktmp(
            namespace="git",
            prefix="commit-msg",
            ext=".txt",
        )

        assert result["path"] == "/tmp/claude/git/commit-msg.abc123.txt"
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0]
        assert call_args[0] == "bin/mktmp.sh"
        assert "git" in call_args
        assert "commit-msg" in call_args

    @pytest.mark.asyncio
    @patch("dev10x.mcp.utilities.run_script")
    async def test_creates_temp_directory(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="/tmp/claude/audit/session.abc123",
            stderr="",
        )

        result = await cli_server.mktmp(
            namespace="audit",
            prefix="session",
            directory=True,
        )

        assert result["path"] == "/tmp/claude/audit/session.abc123"
        call_args = mock_run.call_args[0]
        assert "-d" in call_args

    @pytest.mark.asyncio
    @patch("dev10x.mcp.utilities.run_script")
    async def test_returns_error_on_failure(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Permission denied",
        )

        result = await cli_server.mktmp(
            namespace="git",
            prefix="msg",
        )

        assert "error" in result


class TestIssueCreate:
    @pytest.mark.asyncio
    @patch("dev10x.mcp.github.run_script")
    async def test_creates_issue_with_title_only(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"number":123,"title":"Fix bug","url":"https://github.com/org/repo/issues/123"}',
            stderr="",
        )

        result = await cli_server.issue_create(title="Fix bug")

        assert result["number"] == 123
        assert result["title"] == "Fix bug"
        call_args = mock_run.call_args[0]
        assert call_args[0] == "skills/gh-context/scripts/gh-issue-create.sh"
        assert "Fix bug" in call_args

    @pytest.mark.asyncio
    @patch("dev10x.mcp.github.run_script")
    async def test_creates_issue_with_body_and_labels(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"number":456,"title":"New feature","url":"https://github.com/org/repo/issues/456"}',
            stderr="",
        )

        result = await cli_server.issue_create(
            title="New feature",
            body="Details here",
            labels=["enhancement", "priority"],
            repo="org/repo",
        )

        assert result["number"] == 456
        call_args = mock_run.call_args[0]
        assert "--body" in call_args
        assert "Details here" in call_args
        assert "--label" in call_args
        assert "--repo" in call_args

    @pytest.mark.asyncio
    @patch("dev10x.mcp.github.run_script")
    async def test_returns_error_on_failure(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Permission denied",
        )

        result = await cli_server.issue_create(title="Test")

        assert "error" in result

    @pytest.mark.asyncio
    @patch("dev10x.mcp.github.run_script")
    async def test_falls_back_to_key_value_on_bad_json(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="NUMBER=789\nTITLE=Test",
            stderr="",
        )

        result = await cli_server.issue_create(title="Test")

        assert result["NUMBER"] == "789"


class TestPrDetect:
    @pytest.mark.asyncio
    @patch("dev10x.mcp.github.run_script")
    async def test_detects_pr_from_number(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="PR_NUMBER=123\nREPO=owner/repo\nBRANCH=feature/xyz\nSTATE=open\nHEAD_REF=feature/xyz",
            stderr="",
        )

        result = await cli_server.pr_detect(arg="#123")

        assert "PR_NUMBER" in result
        mock_run.assert_called_once()

    @pytest.mark.asyncio
    @patch("dev10x.mcp.github.run_script")
    async def test_handles_detection_error(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Invalid PR reference",
        )

        result = await cli_server.pr_detect(arg="invalid")

        assert "error" in result


class TestNextWorktreeName:
    @pytest.mark.asyncio
    @patch("dev10x.mcp.git.run_script")
    async def test_calculates_next_worktree_number(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="../.worktrees/project-05",
            stderr="",
        )

        result = await cli_server.next_worktree_name()

        assert "path" in result
        mock_run.assert_called_once()

    @pytest.mark.asyncio
    @patch("dev10x.mcp.git.run_script")
    async def test_handles_error_in_calculation(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Failed to calculate",
        )

        result = await cli_server.next_worktree_name()

        assert "error" in result


class TestSetupAliases:
    @pytest.mark.asyncio
    @patch("dev10x.mcp.git.run_script")
    async def test_sets_up_git_aliases(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Aliases configured",
            stderr="",
        )

        result = await cli_server.setup_aliases()

        assert isinstance(result, dict)
        assert result.get("success") is True
        mock_run.assert_called_once()

    @pytest.mark.asyncio
    @patch("dev10x.mcp.git.run_script")
    async def test_handles_alias_setup_error(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Failed to configure",
        )

        result = await cli_server.setup_aliases()

        assert "error" in result


class TestVerifyPrState:
    @pytest.mark.asyncio
    @patch("dev10x.mcp.github.run_script")
    async def test_verifies_pr_state_before_creation(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="BRANCH_NAME=feature/test\nISSUE=GH-123\nBASE_BRANCH=develop",
            stderr="",
        )

        result = await cli_server.verify_pr_state()

        assert isinstance(result, dict)
        mock_run.assert_called_once()

    @pytest.mark.asyncio
    @patch("dev10x.mcp.github.run_script")
    async def test_blocks_pr_on_protected_branch(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Cannot create PR from main branch",
        )

        result = await cli_server.verify_pr_state()

        assert "error" in result


class TestPrePrChecks:
    @pytest.mark.asyncio
    @patch("dev10x.mcp.github.run_script")
    async def test_runs_quality_checks_successfully(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="All checks passed",
            stderr="",
        )

        result = await cli_server.pre_pr_checks()

        assert result["success"] is True
        assert result["output"] == "All checks passed"
        mock_run.assert_called_once()

    @pytest.mark.asyncio
    @patch("dev10x.mcp.github.run_script")
    async def test_reports_check_failures(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Linting failed",
        )

        result = await cli_server.pre_pr_checks(base_branch="develop")

        assert result["success"] is False
        assert "error" in result
        assert result["error"] == "Linting failed"


class TestRebaseGroom:
    @pytest.mark.asyncio
    @patch("dev10x.mcp.git.run_script")
    async def test_rebases_and_grooms_commits(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="SUCCESS=true\nCOMMITS_REWRITTEN=5",
            stderr="",
        )

        result = await cli_server.rebase_groom(
            seq_path="/tmp/seq",
            base_ref="develop",
        )

        assert isinstance(result, dict)
        mock_run.assert_called_once()


class TestCreateWorktree:
    @pytest.mark.asyncio
    @patch("dev10x.mcp.git.run_script")
    async def test_creates_worktree(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="WORKTREE_PATH=../.worktrees/feature-01\nBRANCH=feature-branch\nCREATED=true",
            stderr="",
        )

        result = await cli_server.create_worktree(branch="feature-branch")

        assert "WORKTREE_PATH" in result
        mock_run.assert_called_once()

    @pytest.mark.asyncio
    @patch("dev10x.mcp.git.run_script")
    async def test_handles_worktree_creation_error(
        self,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Branch already exists",
        )

        result = await cli_server.create_worktree(branch="existing-branch")

        assert "error" in result
