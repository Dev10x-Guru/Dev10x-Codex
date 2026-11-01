from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest

from dev10x.mcp import server_cli as cli_server
from dev10x.tasks.mcp.plan_tools import CODEX_SKIP_REASON

SKIPPED = {"skipped": True, "reason": CODEX_SKIP_REASON}


@pytest.fixture
def codex_harness(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEV10X_HARNESS", "codex")


@pytest.fixture
def repo(tmp_path: Path) -> Iterator[Path]:
    with (
        patch("dev10x.plan.service.get_toplevel", return_value=str(tmp_path)),
        patch("dev10x.domain.documents.plan._get_branch", return_value="feature/x"),
    ):
        yield tmp_path


def _session_dir(repo: Path) -> Path:
    return repo / ".claude" / "session"


class TestPlanSyncUnderCodex:
    @pytest.mark.asyncio
    @pytest.mark.usefixtures("codex_harness")
    async def test_set_context_writes_nothing_and_reports_skipped(self, repo: Path) -> None:
        result = await cli_server.plan_sync_set_context(
            args=["work_type=feature"],
            cwd=str(repo),
        )

        assert result == SKIPPED
        assert not (repo / ".claude").exists()

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("codex_harness")
    async def test_archive_writes_nothing_and_reports_skipped(self, repo: Path) -> None:
        result = await cli_server.plan_sync_archive(cwd=str(repo))

        assert result == SKIPPED
        assert not (repo / ".claude").exists()

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("codex_harness")
    async def test_skip_reason_points_at_codex_plan_sync_issue(self, repo: Path) -> None:
        result = await cli_server.plan_sync_set_context(args=["k=v"], cwd=str(repo))

        assert "Codex" in result["reason"]
        assert "#13" in result["reason"]

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("codex_harness")
    async def test_archive_leaves_an_existing_plan_untouched(self, repo: Path) -> None:
        _session_dir(repo).mkdir(parents=True)
        (_session_dir(repo) / "plan.yaml").write_text("metadata:\n  branch: feature/x\n")
        before = sorted(p.relative_to(repo) for p in _session_dir(repo).rglob("*"))

        result = await cli_server.plan_sync_archive(cwd=str(repo))

        assert result == SKIPPED
        assert (_session_dir(repo) / "plan.yaml").exists()
        assert sorted(p.relative_to(repo) for p in _session_dir(repo).rglob("*")) == before

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("codex_harness")
    async def test_json_summary_stays_read_only_and_creates_no_files(self, repo: Path) -> None:
        result = await cli_server.plan_sync_json_summary(cwd=str(repo))

        assert result == {}
        assert not (repo / ".claude").exists()


class TestPlanSyncByDefault:
    @pytest.mark.asyncio
    async def test_set_context_is_skipped_without_the_harness_variable(
        self, repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("DEV10X_HARNESS", raising=False)

        result = await cli_server.plan_sync_set_context(args=["k=v"], cwd=str(repo))

        assert result == SKIPPED
        assert not (repo / ".claude").exists()
