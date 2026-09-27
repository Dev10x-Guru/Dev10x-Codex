"""Tests for the hooks transport adapter (GH-511).

emit()/read_hook_input() own the Claude Code wire envelope and stdin
read that used to live on the domain value objects. HookRetry's
envelope is covered in test_permission_denied.py; the cwd-resolution
path is covered in test_cwd_discipline_sweep.py.
"""

from __future__ import annotations

import io
import json

import pytest

from dev10x.domain.events.hook_input import HookAllow, HookAsk, HookResult, HookRetry
from dev10x.hooks.hook_transport import emit, read_hook_input


class TestEmitHookResult:
    def test_exits_with_code_2(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            emit(HookResult(message="blocked"))
        assert exc_info.value.code == 2

    def test_writes_deny_envelope(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            emit(HookResult(message="blocked"))
        output = json.loads(capsys.readouterr().err)
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert output["systemMessage"] == "blocked"


class TestEmitHookAllow:
    def test_exits_with_code_0(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            emit(HookAllow())
        assert exc_info.value.code == 0

    def test_writes_allow_envelope(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            emit(HookAllow(message="auto-approved"))
        output = json.loads(capsys.readouterr().err)
        assert output["hookSpecificOutput"]["permissionDecision"] == "allow"
        assert output["systemMessage"] == "auto-approved"

    def test_omits_system_message_when_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            emit(HookAllow())
        output = json.loads(capsys.readouterr().err)
        assert "systemMessage" not in output


class TestEmitHookAsk:
    def test_exits_with_code_0(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            emit(HookAsk(message="sensitive", reason="why"))
        assert exc_info.value.code == 0

    def test_writes_ask_envelope(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            emit(HookAsk(message="sensitive probe", reason="DX014 INFRA target"))
        output = json.loads(capsys.readouterr().err)
        hook_output = output["hookSpecificOutput"]
        assert hook_output["hookEventName"] == "PreToolUse"
        assert hook_output["permissionDecision"] == "ask"
        assert hook_output["permissionDecisionReason"] == "DX014 INFRA target"
        assert output["systemMessage"] == "sensitive probe"

    def test_reason_falls_back_to_message(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            emit(HookAsk(message="only a message"))
        output = json.loads(capsys.readouterr().err)
        assert output["hookSpecificOutput"]["permissionDecisionReason"] == "only a message"

    def test_omits_system_message_when_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            emit(HookAsk(reason="reason only"))
        output = json.loads(capsys.readouterr().err)
        assert "systemMessage" not in output


CODEX_TOP_LEVEL_KEYS = {
    "continue",
    "decision",
    "hookSpecificOutput",
    "reason",
    "stopReason",
    "suppressOutput",
    "systemMessage",
}
CODEX_HOOK_SPECIFIC_KEYS = {
    "additionalContext",
    "hookEventName",
    "permissionDecision",
    "permissionDecisionReason",
    "updatedInput",
}


@pytest.fixture
def codex_harness(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEV10X_HARNESS", "codex")


@pytest.mark.usefixtures("codex_harness")
class TestEmitUnderCodex:
    def test_deny_exits_2_with_plain_reason_on_stderr(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            emit(HookResult(message="blocked by DX005"))
        captured = capsys.readouterr()
        assert exc_info.value.code == 2
        assert captured.err.strip() == "blocked by DX005"
        assert captured.out == ""

    def test_allow_writes_stdout_envelope_with_event_name(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            emit(HookAllow(message="auto-approved"))
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert exc_info.value.code == 0
        assert output["hookSpecificOutput"] == {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
        }
        assert output["systemMessage"] == "auto-approved"
        assert captured.err == ""

    def test_ask_writes_stdout_envelope_with_reason(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as exc_info:
            emit(HookAsk(message="sensitive probe", reason="DX014 INFRA target"))
        output = json.loads(capsys.readouterr().out)
        assert exc_info.value.code == 0
        assert output["hookSpecificOutput"] == {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": "DX014 INFRA target",
        }

    @pytest.mark.parametrize(
        "result",
        [
            HookAllow(),
            HookAllow(message="m"),
            HookAsk(message="m", reason="r"),
            HookAsk(reason="r"),
        ],
    )
    def test_envelope_stays_within_codex_output_schema(
        self, result: HookAllow | HookAsk, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit):
            emit(result)
        output = json.loads(capsys.readouterr().out)
        assert set(output) <= CODEX_TOP_LEVEL_KEYS
        assert set(output["hookSpecificOutput"]) <= CODEX_HOOK_SPECIFIC_KEYS

    def test_retry_is_a_silent_no_op(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            emit(HookRetry(message="retry"))
        captured = capsys.readouterr()
        assert exc_info.value.code == 0
        assert captured.out == ""
        assert captured.err == ""


CLAUDE_WORDED_DENY = (
    "Use `mcp__plugin_Dev10x_cli__pr_get` or `Skill(Dev10x:git)`; "
    "file an issue at https://github.com/Dev10x-Guru/dev10x-claude"
)


class TestCodexEmitAdaptsClaudeWording:
    @pytest.mark.usefixtures("codex_harness")
    def test_deny_reason_is_rendered_for_codex(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            emit(HookResult(message=CLAUDE_WORDED_DENY))
        err = capsys.readouterr().err
        assert "`mcp__cli__pr_get`" in err
        assert "`mcp__cli__push_safe`" in err
        assert "https://github.com/Dev10x-Guru/Dev10x-Codex" in err
        assert "Skill(" not in err

    @pytest.mark.usefixtures("codex_harness")
    def test_ask_reason_is_rendered_for_codex(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            emit(HookAsk(message="m", reason="see mcp__plugin_Dev10x_db__query"))
        output = json.loads(capsys.readouterr().out)
        assert output["hookSpecificOutput"]["permissionDecisionReason"] == "see mcp__db__query"

    def test_claude_deny_message_is_emitted_verbatim(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.delenv("DEV10X_HARNESS", raising=False)
        with pytest.raises(SystemExit):
            emit(HookResult(message=CLAUDE_WORDED_DENY))
        payload = json.loads(capsys.readouterr().err)
        assert payload["systemMessage"] == CLAUDE_WORDED_DENY


class TestReadHookInput:
    def test_parses_tool_name_and_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"}})
        monkeypatch.setattr("sys.stdin", io.StringIO(payload))
        inp = read_hook_input()
        assert inp.tool_name == "Bash"
        assert inp.command == "git status"

    def test_empty_stdin_yields_blank_fields(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.stdin", io.StringIO(""))
        inp = read_hook_input()
        assert inp.tool_name == ""
        assert inp.command == ""
