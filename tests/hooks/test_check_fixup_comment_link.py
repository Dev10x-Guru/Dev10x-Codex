"""Tests for git/check-fixup-comment-link hook."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = _REPO_ROOT / "hooks" / "git" / "check-fixup-comment-link"


def _run_hook(*, commit_msg: str) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(commit_msg)
        f.flush()
        return subprocess.run(
            ["bash", str(HOOK), f.name],
            capture_output=True,
            text=True,
        )


class TestNonFixupCommits:
    def test_allows_regular_commit(self) -> None:
        result = _run_hook(commit_msg="Enable new feature\n\nSome description")
        assert result.returncode == 0

    def test_allows_emoji_commit(self) -> None:
        result = _run_hook(commit_msg="✨ GH-123 Enable widget rendering")
        assert result.returncode == 0


class TestFixupWithValidLink:
    def test_allows_fixup_with_discussion_link(self) -> None:
        msg = (
            "fixup! Enable new feature\n\n"
            "Addresses review comment:\n"
            "https://github.com/owner/repo/pull/42#discussion_r123456"
        )
        result = _run_hook(commit_msg=msg)
        assert result.returncode == 0

    def test_allows_fixup_with_review_link(self) -> None:
        msg = (
            "fixup! Enable new feature\n\n"
            "Addresses review:\n"
            "https://github.com/owner/repo/pull/42#pullrequestreview-789012"
        )
        result = _run_hook(commit_msg=msg)
        assert result.returncode == 0


class TestFixupWithoutLink:
    def test_blocks_fixup_with_body_but_no_link(self) -> None:
        msg = "fixup! Enable new feature\n\nFixed the thing"
        result = _run_hook(commit_msg=msg)
        assert result.returncode == 1
        assert "must reference" in result.stderr.lower()

    def test_allows_bare_fixup_no_body(self) -> None:
        result = _run_hook(commit_msg="fixup! Enable new feature")
        assert result.returncode == 0

    def test_allows_fixup_with_only_comments(self) -> None:
        msg = "fixup! Enable new feature\n\n# This is a comment line"
        result = _run_hook(commit_msg=msg)
        assert result.returncode == 0


class TestFixupWithMultipleLinks:
    def test_blocks_fixup_with_two_links(self) -> None:
        msg = (
            "fixup! Enable new feature\n\n"
            "Addresses:\n"
            "https://github.com/owner/repo/pull/42#discussion_r111111\n"
            "https://github.com/owner/repo/pull/42#discussion_r222222"
        )
        result = _run_hook(commit_msg=msg)
        assert result.returncode == 1
        assert "exactly one" in result.stderr.lower()


class TestStandaloneFixup:
    def test_allows_standalone_fixup(self) -> None:
        msg = "fixup! Enable new feature\n\nStandalone fixup\nFixed typo in variable name"
        result = _run_hook(commit_msg=msg)
        assert result.returncode == 0


class TestMissingFile:
    def test_fails_for_missing_file(self) -> None:
        result = subprocess.run(
            ["bash", str(HOOK), "/nonexistent/file.txt"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
