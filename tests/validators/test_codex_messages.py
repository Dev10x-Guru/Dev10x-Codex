from __future__ import annotations

import pytest

from dev10x.domain.rules.validation_rule import Compensation
from dev10x.hooks.hook_transport import emit
from dev10x.validators.codex_messages import (
    CODEX_ISSUE_REPO,
    CODEX_OVERRIDE_HINT,
    adapt_message_for_codex,
    codex_tool_for_skill,
    codex_tool_name,
    format_codex_skill_block,
)
from dev10x.validators.skill_redirect import (
    MCP_UNAVAILABLE_HINT,
    OVERRIDE_HINT,
    UNRATIONALIZED_SKIP_MSG,
    SkillRedirectValidator,
)
from tests.fakers import BashHookInputFaker
from tests.validators.loop_shapes import BARE_POLL_LOOP

CLAUDE_ISSUE_REPO = "https://github.com/Dev10x-Guru/dev10x-claude"


def _make_input(*, command: str) -> BashHookInputFaker:
    return BashHookInputFaker.build(
        tool_name="Bash",
        command=command,
        raw={"tool_name": "Bash", "tool_input": {"command": command}},
    )


def _block(command: str) -> str:
    result = SkillRedirectValidator().validate(inp=_make_input(command=command))
    assert result is not None
    return result.message


def _emitted_block(command: str, capsys: pytest.CaptureFixture[str]) -> str:
    result = SkillRedirectValidator().validate(inp=_make_input(command=command))
    assert result is not None
    with pytest.raises(SystemExit) as exc_info:
        emit(result)
    assert exc_info.value.code == 2
    return capsys.readouterr().err.rstrip("\n")


@pytest.fixture
def codex_harness(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEV10X_HARNESS", "codex")


@pytest.fixture
def claude_harness(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEV10X_HARNESS", raising=False)


def _assert_no_claude_vocabulary(message: str) -> None:
    assert "Skill(" not in message
    assert "mcp__plugin_Dev10x" not in message
    assert CLAUDE_ISSUE_REPO not in message
    assert "/Dev10x:" not in message


class TestCodexToolName:
    @pytest.mark.parametrize(
        ("claude_name", "codex_name"),
        [
            ("mcp__plugin_Dev10x_cli__push_safe", "mcp__cli__push_safe"),
            ("mcp__plugin_Dev10x_db__query", "mcp__db__query"),
            ("Grep", "Grep"),
        ],
    )
    def test_claude_plugin_prefix_becomes_codex_server_prefix(
        self, claude_name: str, codex_name: str
    ) -> None:
        assert codex_tool_name(claude_name) == codex_name

    def test_skill_with_mcp_equivalent_maps_to_cli_tool(self) -> None:
        assert codex_tool_for_skill("Dev10x:git") == "mcp__cli__push_safe"

    def test_skill_without_mcp_equivalent_has_no_tool(self) -> None:
        assert codex_tool_for_skill("Dev10x:git-commit") is None


class TestAdaptMessageForCodex:
    def test_rewrites_claude_tool_names(self) -> None:
        adapted = adapt_message_for_codex("Use `mcp__plugin_Dev10x_cli__pr_get` now.")
        assert adapted == "Use `mcp__cli__pr_get` now."

    def test_sensitive_file_block_does_not_name_claude(self) -> None:
        adapted = adapt_message_for_codex(
            "BLOCKED: Editing sensitive file: .env\n\n"
            "Sensitive files must not be edited by Claude. Ask the user"
        )
        assert "Claude" not in adapted
        assert "must not be edited by the agent." in adapted

    def test_points_issues_at_the_codex_repo(self) -> None:
        adapted = adapt_message_for_codex(f"file an issue at {CLAUDE_ISSUE_REPO} — thanks")
        assert CODEX_ISSUE_REPO in adapted
        assert CLAUDE_ISSUE_REPO not in adapted

    def test_skill_call_with_codex_skill_names_the_skill(self) -> None:
        adapted = adapt_message_for_codex("Invoke `Skill(Dev10x:gh-pr-monitor)`.")
        assert adapted == "Use the `$Dev10x:gh-pr-monitor` skill."

    def test_skill_call_with_only_a_tool_equivalent_names_the_tool(self) -> None:
        adapted = adapt_message_for_codex("Invoke `Skill(Dev10x:git-alias-setup)`.")
        assert adapted == "Call the MCP tool `mcp__cli__setup_aliases`."

    def test_skill_call_without_equivalent_says_not_available(self) -> None:
        adapted = adapt_message_for_codex("Invoke `Skill(Dev10x:k8s)`.")
        assert "not yet available in Codex" in adapted
        assert "Skill(" not in adapted

    def test_if_skill_fails_prefix_names_the_codex_skill(self) -> None:
        adapted = adapt_message_for_codex(
            "If Skill(Dev10x:git-commit) fails, apply guardrails manually: (1) gitmoji"
        )
        assert adapted == "If `$Dev10x:git-commit` fails, apply guardrails manually: (1) gitmoji"

    def test_if_skill_fails_prefix_is_dropped_when_no_equivalent(self) -> None:
        adapted = adapt_message_for_codex(
            "If Skill(Dev10x:k8s) fails, apply guardrails manually: (1) context"
        )
        assert adapted == "Apply guardrails manually: (1) context"

    def test_if_skill_fails_prefix_names_the_tool_when_only_a_tool_exists(self) -> None:
        adapted = adapt_message_for_codex(
            "If Skill(Dev10x:git-alias-setup) fails, add the aliases manually"
        )
        assert adapted == "If `mcp__cli__setup_aliases` fails, add the aliases manually"

    def test_bare_skill_call_names_the_codex_skill(self) -> None:
        assert (
            adapt_message_for_codex("then Skill(Dev10x:git-groom)") == "then `$Dev10x:git-groom`"
        )

    def test_slash_skill_with_codex_skill_names_the_skill(self) -> None:
        adapted = adapt_message_for_codex("Run: /Dev10x:git-groom")
        assert adapted == "Run: the `$Dev10x:git-groom` skill"

    def test_slash_skill_with_equivalent_names_the_tool(self) -> None:
        adapted = adapt_message_for_codex("Run: /Dev10x:git-alias-setup")
        assert adapted == "Run: the `mcp__cli__setup_aliases` MCP tool"

    def test_generic_footers_are_replaced_with_codex_wording(self) -> None:
        adapted = adapt_message_for_codex(f"head{MCP_UNAVAILABLE_HINT}{OVERRIDE_HINT}")
        assert adapted.startswith("head")
        assert adapted.endswith(CODEX_OVERRIDE_HINT)
        assert "invoke the skill" not in adapted
        assert "DEV10X_SKIP_CMD_VALIDATION" in adapted
        assert "gh api repos/<owner>/<repo>/pulls/<n>" in adapted

    def test_unrationalized_skip_message_keeps_rationale_form(self) -> None:
        adapted = adapt_message_for_codex(UNRATIONALIZED_SKIP_MSG)
        assert "Invoke the skill" not in adapted
        assert 'DEV10X_SKIP_CMD_VALIDATION="<reason' in adapted
        assert "mcp__cli__mktmp" in adapted

    def test_is_idempotent(self) -> None:
        once = adapt_message_for_codex(
            f"Invoke `Skill(Dev10x:git)`.{MCP_UNAVAILABLE_HINT}{OVERRIDE_HINT} {CLAUDE_ISSUE_REPO}"
        )
        assert adapt_message_for_codex(once) == once


class TestFormatCodexSkillBlock:
    def test_codex_skill_with_a_tool_names_both(self) -> None:
        message = format_codex_skill_block(
            label="git push",
            comp=Compensation(
                type="use-skill",
                skill="Dev10x:git",
                guardrails="protected branch checks",
                fallback="use --force-with-lease",
            ),
        )
        assert "Skill: `$Dev10x:git`" in message
        assert "Or call the MCP tool `mcp__cli__push_safe` directly." in message
        assert "use --force-with-lease" in message
        assert CODEX_ISSUE_REPO in message
        _assert_no_claude_vocabulary(message)

    def test_codex_skill_without_a_tool_steers_to_the_skill(self) -> None:
        message = format_codex_skill_block(
            label="git commit",
            comp=Compensation(
                type="use-skill",
                skill="Dev10x:git-commit",
                guardrails="gitmoji prefix",
                fallback="(1) prefix with gitmoji",
            ),
        )
        assert "Skill: `$Dev10x:git-commit`" in message
        assert "Or call the MCP tool" not in message
        assert "not yet available in Codex" not in message
        assert "(1) prefix with gitmoji" in message
        _assert_no_claude_vocabulary(message)

    def test_tool_only_skill_steers_to_the_tool(self) -> None:
        message = format_codex_skill_block(
            label="git config alias",
            comp=Compensation(
                type="use-skill",
                skill="Dev10x:git-alias-setup",
                guardrails="alias names",
                fallback="(1) add aliases",
            ),
        )
        assert "Tool: `mcp__cli__setup_aliases`" in message
        _assert_no_claude_vocabulary(message)

    def test_skill_without_equivalent_gives_manual_guardrails(self) -> None:
        message = format_codex_skill_block(
            label="release notes",
            comp=Compensation(
                type="use-skill",
                skill="Dev10x:release-notes",
                guardrails="PR attribution",
                fallback="(1) list merged PRs",
            ),
        )
        assert "not yet available in Codex" in message
        assert "(1) list merged PRs" in message
        _assert_no_claude_vocabulary(message)

    def test_skill_without_fallback_asks_the_user(self) -> None:
        message = format_codex_skill_block(
            label="kubectl",
            comp=Compensation(type="use-skill", skill="Dev10x:k8s", guardrails="context"),
        )
        assert "ask the user" in message


@pytest.mark.usefixtures("codex_harness")
class TestSkillRedirectUnderCodex:
    def test_force_push_block_is_already_codex_worded_at_the_validator(self) -> None:
        message = _block("git push --force origin main")
        assert "mcp__cli__push_safe" in message
        assert "--force-with-lease" in message
        assert CODEX_ISSUE_REPO in message
        _assert_no_claude_vocabulary(message)

    def test_commit_steers_to_the_codex_skill_and_keeps_guardrails(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        message = _emitted_block("git commit -m wip", capsys)
        assert "$Dev10x:git-commit" in message
        assert "not yet available in Codex" not in message
        assert "gitmoji" in message
        assert "mktmp" in message
        _assert_no_claude_vocabulary(message)

    def test_tool_redirect_uses_codex_tool_name(self, capsys: pytest.CaptureFixture[str]) -> None:
        message = _emitted_block("gh pr view 12", capsys)
        assert "mcp__cli__pr_get" in message
        assert "invoke the skill" not in message
        _assert_no_claude_vocabulary(message)

    def test_alternatives_block_uses_codex_tool_name(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        message = _emitted_block(BARE_POLL_LOOP, capsys)
        assert "mcp__cli__ci_check_status" in message
        _assert_no_claude_vocabulary(message)

    def test_wrong_temp_path_heal_uses_codex_tool_name(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        message = _emitted_block("git commit -F /tmp/Dev10x/commit/msg.txt", capsys)
        assert "mcp__cli__mktmp" in message
        _assert_no_claude_vocabulary(message)

    def test_boolean_skip_rejection_is_codex_worded(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        message = _emitted_block("DEV10X_SKIP_CMD_VALIDATION=true git push -f", capsys)
        assert "Un-rationalized" in message
        assert "Invoke the skill" not in message
        _assert_no_claude_vocabulary(message)


@pytest.mark.usefixtures("claude_harness")
class TestSkillRedirectUnderClaudeIsUnchanged:
    def test_push_block_keeps_claude_skill_wording(self) -> None:
        message = _block("git push --force origin main")
        assert message.startswith(
            "⛔  `git push` blocked — use the skill instead.\n\n  Skill: `Skill(Dev10x:git)`\n\n"
        )
        assert "mcp__plugin_Dev10x_cli__push_safe" in message
        assert CLAUDE_ISSUE_REPO in message
        assert message.endswith(OVERRIDE_HINT)

    def test_tool_block_keeps_claude_tool_name(self) -> None:
        message = _block("gh pr view 12")
        assert "Tool: `mcp__plugin_Dev10x_cli__pr_get`" in message
        assert MCP_UNAVAILABLE_HINT in message
