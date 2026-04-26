"""Tests for the --ensure-base feature of update-paths.py."""

import importlib.util
import json
from pathlib import Path

import pytest

_repo_root = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT_PATH = _repo_root / "skills" / "permission-maintenance" / "scripts" / "update-paths.py"
spec = importlib.util.spec_from_file_location("update_paths", SCRIPT_PATH)
update_paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update_paths)


class TestEnsureBasePermissions:
    BASE_PERMISSIONS = [
        "Bash(/tmp/claude/bin/mktmp.sh:*)",
        "Bash(gh pr view:*)",
        "Write(/tmp/claude/git/**)",
    ]

    @pytest.fixture()
    def settings_file(self, tmp_path: Path) -> Path:
        return tmp_path / "settings.local.json"

    @pytest.fixture()
    def empty_settings(self, settings_file: Path) -> Path:
        settings_file.write_text(json.dumps({"permissions": {"allow": []}}) + "\n")
        return settings_file

    @pytest.fixture()
    def partial_settings(self, settings_file: Path) -> Path:
        settings_file.write_text(
            json.dumps(
                {
                    "permissions": {
                        "allow": [
                            "Bash(/tmp/claude/bin/mktmp.sh:*)",
                            "Bash(git log:*)",
                        ]
                    }
                }
            )
            + "\n"
        )
        return settings_file

    @pytest.fixture()
    def full_settings(self, settings_file: Path) -> Path:
        settings_file.write_text(
            json.dumps({"permissions": {"allow": list(self.BASE_PERMISSIONS)}}) + "\n"
        )
        return settings_file

    @pytest.fixture()
    def no_permissions_settings(self, settings_file: Path) -> Path:
        settings_file.write_text(json.dumps({"hooks": {}}) + "\n")
        return settings_file

    def test_adds_all_missing_to_empty(self, empty_settings: Path) -> None:
        count, messages = update_paths.ensure_base_permissions(
            empty_settings,
            self.BASE_PERMISSIONS,
        )

        assert count == 3
        data = json.loads(empty_settings.read_text())
        assert set(data["permissions"]["allow"]) == set(self.BASE_PERMISSIONS)

    def test_adds_only_missing_to_partial(self, partial_settings: Path) -> None:
        count, messages = update_paths.ensure_base_permissions(
            partial_settings,
            self.BASE_PERMISSIONS,
        )

        assert count == 2
        data = json.loads(partial_settings.read_text())
        allow = data["permissions"]["allow"]
        assert "Bash(gh pr view:*)" in allow
        assert "Write(/tmp/claude/git/**)" in allow
        assert "Bash(git log:*)" in allow  # pre-existing preserved

    def test_no_changes_when_complete(self, full_settings: Path) -> None:
        count, messages = update_paths.ensure_base_permissions(
            full_settings,
            self.BASE_PERMISSIONS,
        )

        assert count == 0
        assert messages == []

    def test_dry_run_does_not_write(self, empty_settings: Path) -> None:
        original = empty_settings.read_text()

        count, messages = update_paths.ensure_base_permissions(
            empty_settings,
            self.BASE_PERMISSIONS,
            dry_run=True,
        )

        assert count == 3
        assert len(messages) == 3
        assert empty_settings.read_text() == original

    def test_creates_permissions_key_if_absent(self, no_permissions_settings: Path) -> None:
        count, _ = update_paths.ensure_base_permissions(
            no_permissions_settings,
            self.BASE_PERMISSIONS,
        )

        assert count == 3
        data = json.loads(no_permissions_settings.read_text())
        assert "permissions" in data
        assert set(data["permissions"]["allow"]) == set(self.BASE_PERMISSIONS)

    def test_skips_invalid_json(self, settings_file: Path) -> None:
        settings_file.write_text("{invalid json}")

        count, messages = update_paths.ensure_base_permissions(
            settings_file,
            self.BASE_PERMISSIONS,
        )

        assert count == 0
        assert any("SKIP" in m for m in messages)

    def test_messages_show_added_rules(self, empty_settings: Path) -> None:
        _, messages = update_paths.ensure_base_permissions(
            empty_settings,
            self.BASE_PERMISSIONS,
        )

        assert len(messages) == 3
        assert all(m.startswith("  + ") for m in messages)

    def test_preserves_other_settings_keys(self, settings_file: Path) -> None:
        settings_file.write_text(
            json.dumps(
                {
                    "permissions": {"allow": [], "deny": ["something"]},
                    "hooks": {"PreToolUse": []},
                }
            )
            + "\n"
        )

        update_paths.ensure_base_permissions(
            settings_file,
            self.BASE_PERMISSIONS,
        )

        data = json.loads(settings_file.read_text())
        assert data["permissions"]["deny"] == ["something"]
        assert data["hooks"] == {"PreToolUse": []}
