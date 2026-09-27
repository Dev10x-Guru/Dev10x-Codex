from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest
import yaml

from dev10x.hooks.edit_validator import reset_engine_cache, validate_edit_write


def _patch(*body: str) -> str:
    return "\n".join(["*** Begin Patch", *body, "*** End Patch"])


def _apply_patch_payload(patch: str, *, cwd: str = "/work/repo") -> dict[str, Any]:
    return {
        "tool_name": "apply_patch",
        "tool_input": {"command": patch},
        "cwd": cwd,
        "hook_event_name": "PreToolUse",
    }


@pytest.fixture(autouse=True)
def _isolated_engine(monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.delenv("DEV10X_HOOK_EXPERIMENTAL", raising=False)
    reset_engine_cache()
    yield
    reset_engine_cache()


@pytest.fixture()
def rules_yaml(tmp_path: Path) -> Path:
    path = tmp_path / "rules.yaml"
    path.write_text(
        yaml.dump(
            {
                "rules": [
                    {
                        "name": "sensitive-files",
                        "matcher": "Edit|Write",
                        "hook_block": True,
                        "file_names": [".env"],
                        "message": "BLOCKED: Editing sensitive file: {file_path}",
                    },
                    {
                        "name": "eval-in-skills",
                        "matcher": "Edit|Write",
                        "hook_block": True,
                        "file_pattern": r"/\.claude/skills/.*\.md$",
                        "content_pattern": r"\beval\s+[\"$]",
                        "message": "eval is not allowed in skill files",
                    },
                ]
            }
        )
    )
    return path


@pytest.fixture()
def codex(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEV10X_HARNESS", "codex")


def _run(data: dict[str, Any], rules_yaml: Path) -> int:
    with pytest.raises(SystemExit) as exc_info:
        validate_edit_write(data=data, yaml_path=rules_yaml)
    code = exc_info.value.code
    return code if isinstance(code, int) else 0


@pytest.mark.usefixtures("codex")
class TestApplyPatchUnderCodex:
    def test_patch_touching_blocked_file_is_denied_naming_the_file(
        self, rules_yaml: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        data = _apply_patch_payload(
            _patch("*** Add File: README.md", "+hi", "*** Update File: .env", "@@", "+KEY=1")
        )

        code = _run(data, rules_yaml)

        captured = capsys.readouterr()
        assert code == 2
        assert captured.out == ""
        assert "/work/repo/.env" in captured.err
        assert "BLOCKED: Editing sensitive file" in captured.err

    def test_content_rule_applies_to_added_lines_only(
        self, rules_yaml: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        data = _apply_patch_payload(
            _patch("*** Update File: .claude/skills/x/SKILL.md", "@@", '+eval "$cmd"')
        )

        code = _run(data, rules_yaml)

        assert code == 2
        assert "/work/repo/.claude/skills/x/SKILL.md" in capsys.readouterr().err

    def test_removed_lines_do_not_trigger_content_rules(self, rules_yaml: Path) -> None:
        data = _apply_patch_payload(
            _patch("*** Update File: .claude/skills/x/SKILL.md", "@@", '-eval "$cmd"', "+ok")
        )

        assert _run(data, rules_yaml) == 0

    def test_deleting_a_blocked_file_is_denied(self, rules_yaml: Path) -> None:
        assert _run(_apply_patch_payload(_patch("*** Delete File: .env")), rules_yaml) == 2

    def test_moving_onto_a_blocked_path_is_denied(self, rules_yaml: Path) -> None:
        data = _apply_patch_payload(
            _patch("*** Update File: env.example", "*** Move to: .env", "@@", "+A=1")
        )

        assert _run(data, rules_yaml) == 2

    def test_harmless_patch_passes_silently(
        self, rules_yaml: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        data = _apply_patch_payload(
            _patch("*** Add File: src/new.py", "+x = 1", "*** Update File: a.py", "@@", "+y")
        )

        code = _run(data, rules_yaml)

        captured = capsys.readouterr()
        assert code == 0
        assert captured.out == ""

    def test_patch_text_is_not_validated_as_a_shell_command(self, rules_yaml: Path) -> None:
        data = _apply_patch_payload(
            _patch("*** Add File: notes.md", "+git commit -m wip", "+rm -rf /")
        )

        assert _run(data, rules_yaml) == 0

    def test_malformed_patch_falls_through_to_allow_with_a_warning(
        self, rules_yaml: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.WARNING, logger="dev10x.hooks.edit_validator")

        code = _run(_apply_patch_payload("*** Begin Patch\n*** Add File: .env\n+X"), rules_yaml)

        assert code == 0
        assert any("apply_patch" in record.getMessage() for record in caplog.records)


class TestCodexHookRegistration:
    def test_apply_patch_matcher_routes_to_edit_write_validator(self) -> None:
        config_path = Path(__file__).resolve().parents[2] / "hooks" / "codex-hooks.json"
        entries = json.loads(config_path.read_text())["hooks"]["PreToolUse"]

        commands = [
            hook["command"]
            for entry in entries
            if entry["matcher"] == "apply_patch"
            for hook in entry["hooks"]
        ]

        assert commands == [
            "DEV10X_HARNESS=codex $PLUGIN_ROOT/hooks/scripts/audit-wrap validate-edit-write "
            "$PLUGIN_ROOT/hooks/scripts/validate-edit-write.py"
        ]


class TestClaudeEditPathUnchanged:
    def test_edit_on_blocked_file_is_denied_with_claude_envelope(
        self,
        rules_yaml: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("DEV10X_HARNESS", raising=False)
        data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "/work/repo/.env", "new_string": "KEY=1"},
        }

        code = _run(data, rules_yaml)

        payload = json.loads(capsys.readouterr().err)
        assert code == 2
        assert payload == {
            "hookSpecificOutput": {"permissionDecision": "deny"},
            "systemMessage": "BLOCKED: Editing sensitive file: /work/repo/.env",
        }

    def test_edit_on_harmless_file_exits_zero_without_output(
        self,
        rules_yaml: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("DEV10X_HARNESS", raising=False)
        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "/work/repo/main.py", "content": "x = 1"},
        }

        code = _run(data, rules_yaml)

        captured = capsys.readouterr()
        assert code == 0
        assert captured.out == ""
        assert captured.err == ""

    def test_other_tools_are_ignored(self, rules_yaml: Path) -> None:
        assert _run({"tool_name": "Read", "tool_input": {}}, rules_yaml) == 0
