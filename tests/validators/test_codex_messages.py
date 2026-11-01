from __future__ import annotations

import pytest

from dev10x.core.domain.rules.validation_rule import Compensation
from dev10x.core.hooks.hook_transport import emit
from dev10x.core.validators.codex_messages import (
    ISSUE_REPO,
    OVERRIDE_HINT,
    UPSTREAM_ISSUE_REPO,
    adapt_message_for_codex,
    codex_tool_for_skill,
    codex_tool_name,
    format_codex_skill_block,
    template_pattern,
)
from dev10x.core.validators.prefix_friction import (
    SEMICOLON_CHAIN_MSG,
    PrefixFrictionValidator,
)
from dev10x.core.validators.skill_redirect import MCP_UNAVAILABLE_HINT as UPSTREAM_MCP_HINT
from dev10x.core.validators.skill_redirect import OVERRIDE_HINT as UPSTREAM_OVERRIDE_HINT
from dev10x.core.validators.skill_redirect import (
    UNRATIONALIZED_SKIP_MSG as UPSTREAM_UNRATIONALIZED_SKIP_MSG,
)
from dev10x.core.validators.skill_redirect import SkillRedirectValidator
from tests.fakers import BashHookInputFaker
from tests.validators.loop_shapes import BARE_POLL_LOOP


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


def _emitted_block(
    command: str,
    capsys: pytest.CaptureFixture[str],
    validator: SkillRedirectValidator | PrefixFrictionValidator | None = None,
) -> str:
    result = (validator or SkillRedirectValidator()).validate(inp=_make_input(command=command))
    assert result is not None
    with pytest.raises(SystemExit) as exc_info:
        emit(result)
    assert exc_info.value.code == 2
    return capsys.readouterr().err.rstrip("\n")


@pytest.fixture
def codex_harness(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEV10X_HARNESS", "codex")


def _assert_no_claude_vocabulary(message: str) -> None:
    assert "Skill(" not in message
    assert "mcp__plugin_Dev10x" not in message
    assert "mcp__plugin_dev10x" not in message
    assert UPSTREAM_ISSUE_REPO not in message
    assert "/Dev10x:" not in message
    assert "/dev10x:" not in message


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

    @pytest.mark.parametrize("skill", ["Dev10x:git", "dev10x:git"])
    def test_skill_with_mcp_equivalent_maps_to_cli_tool(self, skill: str) -> None:
        assert codex_tool_for_skill(skill) == "mcp__cli__push_safe"

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
        adapted = adapt_message_for_codex(f"file an issue at {UPSTREAM_ISSUE_REPO} — thanks")
        assert ISSUE_REPO in adapted
        assert UPSTREAM_ISSUE_REPO not in adapted

    @pytest.mark.parametrize("prefix", ["Dev10x", "dev10x"])
    def test_skill_call_with_codex_skill_names_the_skill(self, prefix: str) -> None:
        adapted = adapt_message_for_codex(f"Invoke `Skill({prefix}:gh-pr-monitor)`.")
        assert adapted == "Use the `$Dev10x:gh-pr-monitor` skill."

    def test_rewrites_upstream_lowercase_tool_names(self) -> None:
        adapted = adapt_message_for_codex("Use `mcp__plugin_dev10x_cli__pr_get` now.")
        assert adapted == "Use `mcp__cli__pr_get` now."

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
        adapted = adapt_message_for_codex(f"head{UPSTREAM_MCP_HINT}{UPSTREAM_OVERRIDE_HINT}")
        assert adapted.startswith("head")
        assert adapted.endswith(OVERRIDE_HINT)
        assert "invoke the skill" not in adapted
        assert "DEV10X_SKIP_CMD_VALIDATION" in adapted
        assert "gh api repos/<owner>/<repo>/pulls/<n>" in adapted

    def test_unrationalized_skip_message_keeps_rationale_form(self) -> None:
        adapted = adapt_message_for_codex(UPSTREAM_UNRATIONALIZED_SKIP_MSG)
        assert "Invoke the skill" not in adapted
        assert 'DEV10X_SKIP_CMD_VALIDATION="<reason' in adapted
        assert "mcp__cli__mktmp" in adapted

    def test_is_idempotent(self) -> None:
        once = adapt_message_for_codex(
            f"Invoke `Skill(Dev10x:git)`.{UPSTREAM_MCP_HINT}{UPSTREAM_OVERRIDE_HINT}"
            f" {UPSTREAM_ISSUE_REPO}"
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
        assert ISSUE_REPO in message
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
        assert ISSUE_REPO in message
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


class TestTemplatePattern:
    def test_captures_each_field_of_a_formatted_template(self) -> None:
        match = template_pattern("run `{cmd}` then {tail}.").fullmatch("run `git log` then ls.")
        assert match is not None
        assert match.groupdict() == {"cmd": "git log", "tail": "ls"}

    def test_repeated_field_must_carry_the_same_value(self) -> None:
        pattern = template_pattern("{head} or {head}")
        assert pattern.fullmatch("git or git") is not None
        assert pattern.fullmatch("git or gh") is None

    def test_literal_regex_characters_are_escaped(self) -> None:
        assert template_pattern("`Bash({cmd}:*)` (x)").fullmatch("`Bash(git:*)` (x)") is not None


@pytest.mark.usefixtures("codex_harness")
class TestPrefixFrictionUnderCodex:
    @pytest.mark.parametrize(
        ("command", "shape"),
        [
            ("git status; git fetch", "`;` chain"),
            ("git fetch || git pull", "`||` chain"),
            ("git status\ngit fetch", "Bare-newline chain"),
        ],
    )
    def test_chain_block_names_codex_and_keeps_both_commands(
        self, command: str, shape: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        message = _emitted_block(command, capsys, PrefixFrictionValidator())
        assert message.startswith(f"⚠️  {shape} blocked")
        assert "hides `git` behind `git`" in message
        assert "Split into separate shell calls instead." in message
        assert "Claude Code" not in message
        assert "Bash(" not in message

    def test_redirect_block_keeps_the_rewritten_command(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        message = _emitted_block(
            'find /home/user/notes 2>/dev/null -name "*.md"', capsys, PrefixFrictionValidator()
        )
        assert "Move the redirect to the end of the command:" in message
        assert "2>/dev/null" in message
        assert "Claude Code" not in message

    @pytest.mark.parametrize(
        ("command", "wrapper"),
        [
            ("for n in 1 2; do gh api repos/x/y/issues/$n; done", "for"),
            ("echo a b | xargs -I{} gh api {}", "xargs"),
        ],
    )
    def test_loop_wrap_block_steers_to_shell_calls(
        self, command: str, wrapper: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        message = _emitted_block(command, capsys, PrefixFrictionValidator())
        assert f"Shell {wrapper} wraps an allowed command (`gh`)" in message
        assert "one shell call per iteration" in message
        assert "Claude Code" not in message
        assert "Bash tool calls" not in message

    def test_rewrite_is_idempotent(self) -> None:
        claude = SEMICOLON_CHAIN_MSG.format(head_cmd="git", tail_cmd="ls")
        once = adapt_message_for_codex(claude)
        assert once != claude
        assert adapt_message_for_codex(once) == once
