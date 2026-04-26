"""Tests for HookInput and HookResult DTOs."""

from __future__ import annotations

import pytest

from dev10x.domain import HookInput, HookResult


class TestHookInputFromDict:
    @pytest.fixture()
    def hook_input(self) -> HookInput:
        return HookInput.from_dict(
            data={
                "tool_name": "Bash",
                "tool_input": {"command": "git status"},
            }
        )

    def test_tool_name(self, hook_input: HookInput) -> None:
        assert hook_input.tool_name == "Bash"

    def test_command(self, hook_input: HookInput) -> None:
        assert hook_input.command == "git status"

    def test_raw_preserved(self, hook_input: HookInput) -> None:
        assert hook_input.raw["tool_name"] == "Bash"


class TestHookInputFromEmptyDict:
    @pytest.fixture()
    def hook_input(self) -> HookInput:
        return HookInput.from_dict(data={})

    def test_tool_name_empty(self, hook_input: HookInput) -> None:
        assert hook_input.tool_name == ""

    def test_command_empty(self, hook_input: HookInput) -> None:
        assert hook_input.command == ""


class TestHookResult:
    def test_emit_exits_with_code_2(self) -> None:
        result = HookResult(message="blocked")
        with pytest.raises(SystemExit) as exc_info:
            result.emit()
        assert exc_info.value.code == 2


class TestHookAllow:
    def test_emit_exits_with_code_0(self) -> None:
        from dev10x.domain import HookAllow

        allow = HookAllow()
        with pytest.raises(SystemExit) as exc_info:
            allow.emit()
        assert exc_info.value.code == 0

    def test_emit_with_message_exits_0(self) -> None:
        from dev10x.domain import HookAllow

        allow = HookAllow(message="auto-approved")
        with pytest.raises(SystemExit) as exc_info:
            allow.emit()
        assert exc_info.value.code == 0
