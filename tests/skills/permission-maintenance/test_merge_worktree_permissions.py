"""Tests for the merge-worktree-permissions.py script."""

import importlib.util
from pathlib import Path

import pytest

_repo_root = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT_PATH = (
    _repo_root / "skills" / "permission-maintenance" / "scripts" / "merge-worktree-permissions.py"
)
spec = importlib.util.spec_from_file_location("merge_worktree_permissions", SCRIPT_PATH)
merge_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge_mod)


class TestIsNoise:
    @pytest.mark.parametrize(
        "entry",
        [
            "Bash(find /work/example -name '*.py')",
            "Bash(find . -type f -name foo)",
            "Read(/tmp/claude/session/abc.A1b2C3d4.txt)",
            "Bash(if [ -f foo ])",
            "Bash(then echo hello)",
            "Bash(else exit 1)",
            "Bash(fi)",
            "Bash(GROOM_SEQ_FILE=/tmp/foo git rebase)",
            'Bash("PAY-123" something)',
            "Bash(bash -c 'echo hello')",
            "Bash(git-push-safe.sh -u origin janusz/PAY-123/fix)",
        ],
    )
    def test_detects_noise(self, entry: str) -> None:
        assert merge_mod.is_noise(entry) is True

    @pytest.mark.parametrize(
        "entry",
        [
            "Bash(git log:*)",
            "Bash(docker compose up)",
            "mcp__plugin_Dev10x_cli__detect_tracker",
            "Read(/work/example/app-pos/src/file.py)",
        ],
    )
    def test_allows_stable_entries(self, entry: str) -> None:
        assert merge_mod.is_noise(entry) is False


class TestGeneralizePermission:
    @pytest.mark.parametrize(
        "entry,expected",
        [
            ("detect-tracker.sh PAY-123", "detect-tracker.sh"),
            ("gh-issue-get.sh 42", "gh-issue-get.sh"),
            ("git reset --hard origin/main", "git reset --hard"),
            ("git reset --soft abc123def", "git reset --soft"),
        ],
    )
    def test_generalizes_known_patterns(self, entry: str, expected: str) -> None:
        assert merge_mod.generalize_permission(entry) == expected

    def test_leaves_stable_entry_unchanged(self) -> None:
        assert merge_mod.generalize_permission("Bash(git log:*)") == "Bash(git log:*)"
