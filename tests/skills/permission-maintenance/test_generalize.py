"""Tests for the --generalize feature of update-paths.py."""

import importlib.util
import json
from pathlib import Path

import pytest

_repo_root = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT_PATH = _repo_root / "skills" / "permission-maintenance" / "scripts" / "update-paths.py"
spec = importlib.util.spec_from_file_location("update_paths", SCRIPT_PATH)
update_paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update_paths)


class TestGeneralizePermission:
    @pytest.mark.parametrize(
        "entry,expected",
        [
            ("Bash(detect-tracker.sh PAY-123:*)", "Bash(detect-tracker.sh:*)"),
            ("Bash(gh-issue-get.sh 15:*)", "Bash(gh-issue-get.sh:*)"),
            ("Bash(gh-pr-detect.sh 42:*)", "Bash(gh-pr-detect.sh:*)"),
            ("Bash(generate-commit-list.sh 42:*)", "Bash(generate-commit-list.sh:*)"),
            ("Bash(generate-commit-list.sh PLACEHOLDER:*)", "Bash(generate-commit-list.sh:*)"),
            ("Bash(extract-session.sh abc123:*)", "Bash(extract-session.sh:*)"),
        ],
    )
    def test_generalizes_script_args(self, entry: str, expected: str) -> None:
        result = update_paths.generalize_permission(entry)

        assert result == expected

    @pytest.mark.parametrize(
        "entry",
        [
            "Bash(git log:*)",
            "Bash(gh pr view:*)",
            "Bash(/tmp/claude/bin/mktmp.sh:*)",
            "mcp__plugin_Dev10x_*",
        ],
    )
    def test_leaves_stable_permissions_unchanged(self, entry: str) -> None:
        result = update_paths.generalize_permission(entry)

        assert result is None

    def test_generalizes_temp_file_hashes(self) -> None:
        entry = "Write(/tmp/claude/git/msg.AbCdEfGh.txt)"

        result = update_paths.generalize_permission(entry)

        assert result == "Write(/tmp/claude/git/*)"


class TestGeneralizePermissions:
    @pytest.fixture()
    def settings_file(self, tmp_path: Path) -> Path:
        return tmp_path / "settings.local.json"

    def test_replaces_session_specific_with_generalized(self, settings_file: Path) -> None:
        settings_file.write_text(
            json.dumps(
                {
                    "permissions": {
                        "allow": [
                            "Bash(git log:*)",
                            "Bash(detect-tracker.sh PAY-123:*)",
                            "Bash(gh-pr-detect.sh 42:*)",
                        ]
                    }
                }
            )
            + "\n"
        )

        count, messages = update_paths.generalize_permissions(settings_file)

        assert count == 2
        data = json.loads(settings_file.read_text())
        allow = data["permissions"]["allow"]
        assert "Bash(git log:*)" in allow
        assert "Bash(detect-tracker.sh:*)" in allow
        assert "Bash(gh-pr-detect.sh:*)" in allow
        assert "Bash(detect-tracker.sh PAY-123:*)" not in allow

    def test_dry_run_does_not_write(self, settings_file: Path) -> None:
        settings_file.write_text(
            json.dumps({"permissions": {"allow": ["Bash(detect-tracker.sh PAY-123:*)"]}}) + "\n"
        )
        original = settings_file.read_text()

        count, messages = update_paths.generalize_permissions(
            settings_file,
            dry_run=True,
        )

        assert count == 1
        assert settings_file.read_text() == original

    def test_no_changes_when_already_generalized(self, settings_file: Path) -> None:
        settings_file.write_text(
            json.dumps({"permissions": {"allow": ["Bash(git log:*)", "Bash(gh pr view:*)"]}})
            + "\n"
        )

        count, messages = update_paths.generalize_permissions(settings_file)

        assert count == 0
        assert messages == []

    def test_skips_invalid_json(self, settings_file: Path) -> None:
        settings_file.write_text("{invalid json}")

        count, messages = update_paths.generalize_permissions(settings_file)

        assert count == 0
        assert any("SKIP" in m for m in messages)

    def test_skips_when_generalized_already_exists(self, settings_file: Path) -> None:
        settings_file.write_text(
            json.dumps(
                {
                    "permissions": {
                        "allow": [
                            "Bash(detect-tracker.sh PAY-123:*)",
                            "Bash(detect-tracker.sh:*)",
                        ]
                    }
                }
            )
            + "\n"
        )

        count, messages = update_paths.generalize_permissions(settings_file)

        assert count == 0

    def test_preserves_other_settings_keys(self, settings_file: Path) -> None:
        settings_file.write_text(
            json.dumps(
                {
                    "permissions": {
                        "allow": ["Bash(detect-tracker.sh PAY-123:*)"],
                        "deny": ["something"],
                    },
                    "hooks": {"PreToolUse": []},
                }
            )
            + "\n"
        )

        update_paths.generalize_permissions(settings_file)

        data = json.loads(settings_file.read_text())
        assert data["permissions"]["deny"] == ["something"]
        assert data["hooks"] == {"PreToolUse": []}
