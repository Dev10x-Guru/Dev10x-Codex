from __future__ import annotations

import functools
import re

from dev10x.domain.rules.validation_rule import Compensation
from dev10x.skills.codex.catalog import codex_skill_for, to_codex_casing

CODEX_ISSUE_REPO = "https://github.com/Dev10x-Guru/Dev10x-Codex"
CLAUDE_ISSUE_REPO = "https://github.com/Dev10x-Guru/dev10x-claude"
NOT_AVAILABLE_IN_CODEX = "not yet available in Codex"

SKIP_ENV_VAR = "DEV10X_SKIP_CMD_VALIDATION"

SKILL_TOOL_EQUIVALENTS: dict[str, str] = {
    "Dev10x:git": "push_safe",
    "Dev10x:gh-pr-create": "create_pr",
    "Dev10x:gh-pr-merge": "merge_pr",
    "Dev10x:git-groom": "rebase_groom",
    "Dev10x:gh-pr-monitor": "ci_check_status",
    "Dev10x:py-test": "run_tests",
    "Dev10x:git-alias-setup": "setup_aliases",
    "Dev10x:git-worktree": "create_worktree",
}

_CLAUDE_MCP_NAME_RE = re.compile(r"mcp__plugin_Dev10x_(cli|db)__(\w+)")
_SKILL_NAME = r"(Dev10x:[\w-]+)"
_INVOKE_SKILL_RE = re.compile(rf"Invoke `Skill\({_SKILL_NAME}\)`\.")
_IF_SKILL_FAILS_RE = re.compile(rf"If Skill\({_SKILL_NAME}\) (?:fails|is unavailable),\s*(\w)")
_BACKTICK_SKILL_RE = re.compile(rf"`Skill\({_SKILL_NAME}\)`")
_BARE_SKILL_RE = re.compile(rf"Skill\({_SKILL_NAME}\)")
_SLASH_SKILL_RE = re.compile(rf"/{_SKILL_NAME}")

_CODEX_PHRASES: tuple[tuple[str, str], ...] = (
    (
        "If you are inside a skill that instructed this command, file an issue at",
        "If Dev10x guidance told you to run this command, file an issue at",
    ),
    ("— the skill needs updating.", "— the guidance needs updating."),
    (
        "Re-invoke the skill with the right parameters before escalating.",
        "Re-call the MCP tool with the right parameters before escalating.",
    ),
    (
        "reconnect via `/mcp`",
        "restart the Codex session so the Dev10x MCP servers reconnect (`/mcp` lists them)",
    ),
    ("must not be edited by Claude.", "must not be edited by the agent."),
)

_TEMPLATE_FIELD_RE = re.compile(r"\{(\w+)\}")

CODEX_CHAIN_TEMPLATE = (
    "⚠️  {shape} blocked — permission friction risk.\n\n"
    "Dev10x runs one simple command per shell call, so Codex's approval\n"
    "rules and the Dev10x guardrails see each command on its own. A chain\n"
    "hides `{tail_cmd}` behind `{head_cmd}`.\n\n"
    "Split into separate shell calls instead.\n"
)

CODEX_REDIRECT_THEN_POSITIONAL_TEMPLATE = (
    "⚠️  Redirect before positional args blocked — permission friction risk.\n\n"
    "`{cmd} ... {redirect} {after}` puts the redirect in the middle of the\n"
    "command. Dev10x keeps redirects last so the command reads as one\n"
    "simple command for Codex's approval rules and the Dev10x guardrails.\n\n"
    "Move the redirect to the end of the command:\n"
    "    {cmd} {before} {after} {redirect}\n"
)

CODEX_SHELL_LOOP_WRAP_TEMPLATE = (
    "⚠️  Shell {wrapper} wraps an allowed command (`{inner}`) — permission friction risk.\n\n"
    "The call starts with `{wrapper}`, not `{inner}`, so a rule that approves\n"
    "`{inner}` does not cover it, and the Dev10x guardrails cannot see each\n"
    "iteration on its own.\n\n"
    "Use one shell call per iteration instead.\n"
    "Send them together in one turn so they run side by side and each\n"
    "matches its own approval rule.\n\n"
    "Example: send N separate shell calls in one turn, each running\n"
    "`{inner} ...` with the iteration value substituted in.\n"
)

CODEX_OVERRIDE_HINT = (
    f"\n\n⚠️  Do NOT use {SKIP_ENV_VAR} as a shortcut to silence this block. "
    "It is not an escape hatch for an agent reacting to a hook message.\n\n"
    "The correct response is the Dev10x skill or MCP tool named above. When "
    "neither is available in Codex yet, apply the manual guardrails and ask "
    "the user before running anything this hook still blocks.\n\n"
    "ONLY when a documented Dev10x procedure legitimately needs the raw "
    "command and every MCP alternative is exhausted, prefix it with a "
    "rationale string of at least 20 chars:\n"
    f'  {SKIP_ENV_VAR}="<reason for bypass>" <command>\n\n'
    f"The boolean form ({SKIP_ENV_VAR}=true) is rejected (GH-226)."
)

CODEX_MCP_UNAVAILABLE_HINT = (
    "\n\n⚠️  If the Dev10x MCP tools are missing from your tool list, "
    "the Dev10x `cli` MCP server is not connected. Ask the user to check "
    "`/mcp` and restart the Codex session. Do NOT use "
    f"{SKIP_ENV_VAR} as a workaround.\n\n"
    "While you wait, READ-ONLY `gh api` calls are NOT blocked and are "
    "the sanctioned fallback for gathering state (GH-1173 F2):\n"
    "  gh api repos/<owner>/<repo>/pulls/<n>\n"
    "  gh api repos/<owner>/<repo>/issues/<n>\n"
    "  gh api graphql -f query='...'   # e.g. reviewThreads state\n"
    "Only state-CHANGING operations must wait for the MCP tool — a "
    "write is what these guardrails exist to gate."
)

CODEX_UNRATIONALIZED_SKIP_MSG = f"""\
⛔  Un-rationalized {SKIP_ENV_VAR} bypass — rejected.

The boolean form ({SKIP_ENV_VAR}=true / =1 / =yes) is not accepted.
It was being used as a procedural escape hatch instead of as a
deliberate, documented exception.

Before reaching for this flag, exhaust the alternatives the hook is
steering toward:

  1. Call the Dev10x MCP tool named in the block message — it
     enforces the guardrails the raw command bypasses.
  2. If a temp-file path is the issue, create it with the
     `mcp__cli__mktmp` tool — never a silent bypass.
  3. If the Dev10x MCP server is unavailable, ask the user to
     restart the Codex session — do NOT skip validation instead.

ONLY when the above are genuinely depleted and a documented Dev10x
procedure legitimately needs the raw command, prefix it with a
rationale string of at least 20 chars explaining why:

  {SKIP_ENV_VAR}="<reason: which procedure, what alternative failed>" <command>

The rationale is recorded by the hook so the escape hatch stays
auditable."""


def codex_tool_name(tool: str) -> str:
    return _CLAUDE_MCP_NAME_RE.sub(r"mcp__\1__\2", tool)


def codex_tool_for_skill(skill: str) -> str | None:
    short_name = SKILL_TOOL_EQUIVALENTS.get(to_codex_casing(skill))
    return f"mcp__cli__{short_name}" if short_name else None


def _replace_invoke_skill(match: re.Match[str]) -> str:
    if skill := codex_skill_for(match.group(1)):
        return f"Use the `{skill}` skill."
    if tool := codex_tool_for_skill(match.group(1)):
        return f"Call the MCP tool `{tool}`."
    return f"The `{match.group(1)}` workflow is {NOT_AVAILABLE_IN_CODEX}."


def _replace_if_skill_fails(match: re.Match[str]) -> str:
    replacement = codex_skill_for(match.group(1)) or codex_tool_for_skill(match.group(1))
    if replacement:
        return f"If `{replacement}` fails, {match.group(2)}"
    return match.group(2).upper()


def _replace_backtick_skill(match: re.Match[str]) -> str:
    replacement = codex_skill_for(match.group(1)) or codex_tool_for_skill(match.group(1))
    return f"`{replacement}`" if replacement else f"`{match.group(1)}` ({NOT_AVAILABLE_IN_CODEX})"


def _replace_bare_skill(match: re.Match[str]) -> str:
    replacement = codex_skill_for(match.group(1)) or codex_tool_for_skill(match.group(1))
    return f"`{replacement}`" if replacement else f"{match.group(1)} ({NOT_AVAILABLE_IN_CODEX})"


def _replace_slash_skill(match: re.Match[str]) -> str:
    if skill := codex_skill_for(match.group(1)):
        return f"the `{skill}` skill"
    if tool := codex_tool_for_skill(match.group(1)):
        return f"the `{tool}` MCP tool"
    return f"{match.group(1)} ({NOT_AVAILABLE_IN_CODEX})"


def _claude_footers() -> tuple[tuple[str, str], ...]:
    from dev10x.validators.skill_redirect import (
        MCP_UNAVAILABLE_HINT,
        OVERRIDE_HINT,
        UNRATIONALIZED_SKIP_MSG,
    )

    return (
        (UNRATIONALIZED_SKIP_MSG, CODEX_UNRATIONALIZED_SKIP_MSG),
        (MCP_UNAVAILABLE_HINT, CODEX_MCP_UNAVAILABLE_HINT),
        (OVERRIDE_HINT, CODEX_OVERRIDE_HINT),
    )


def template_pattern(template: str) -> re.Pattern[str]:
    seen: set[str] = set()
    parts: list[str] = []
    position = 0
    for match in _TEMPLATE_FIELD_RE.finditer(template):
        name = match.group(1)
        parts.append(re.escape(template[position : match.start()]))
        parts.append(f"(?P={name})" if name in seen else f"(?P<{name}>.+?)")
        seen.add(name)
        position = match.end()
    parts.append(re.escape(template[position:]))
    return re.compile("".join(parts), re.DOTALL)


def _chain_template(shape: str) -> str:
    return CODEX_CHAIN_TEMPLATE.replace("{shape}", shape)


@functools.cache
def _claude_templates() -> tuple[tuple[re.Pattern[str], str], ...]:
    from dev10x.validators.prefix_friction import (
        NEWLINE_CHAIN_MSG,
        OR_CHAIN_MSG,
        REDIRECT_THEN_POSITIONAL_MSG,
        SEMICOLON_CHAIN_MSG,
        SHELL_LOOP_WRAP_MSG,
    )

    return tuple(
        (template_pattern(claude_template), codex_template)
        for claude_template, codex_template in (
            (SEMICOLON_CHAIN_MSG, _chain_template("`;` chain")),
            (OR_CHAIN_MSG, _chain_template("`||` chain")),
            (NEWLINE_CHAIN_MSG, _chain_template("Bare-newline chain")),
            (REDIRECT_THEN_POSITIONAL_MSG, CODEX_REDIRECT_THEN_POSITIONAL_TEMPLATE),
            (SHELL_LOOP_WRAP_MSG, CODEX_SHELL_LOOP_WRAP_TEMPLATE),
        )
    )


def _rewrite_claude_templates(message: str) -> str:
    for pattern, codex_template in _claude_templates():
        message = pattern.sub(lambda match: codex_template.format(**match.groupdict()), message)
    return message


def adapt_message_for_codex(message: str) -> str:
    message = _rewrite_claude_templates(message)
    for claude_text, codex_text in (*_claude_footers(), *_CODEX_PHRASES):
        message = message.replace(claude_text, codex_text)
    message = message.replace(CLAUDE_ISSUE_REPO, CODEX_ISSUE_REPO)
    message = codex_tool_name(to_codex_casing(message))
    message = _INVOKE_SKILL_RE.sub(_replace_invoke_skill, message)
    message = _IF_SKILL_FAILS_RE.sub(_replace_if_skill_fails, message)
    message = _BACKTICK_SKILL_RE.sub(_replace_backtick_skill, message)
    message = _BARE_SKILL_RE.sub(_replace_bare_skill, message)
    return _SLASH_SKILL_RE.sub(_replace_slash_skill, message)


def format_codex_skill_block(*, label: str, comp: Compensation) -> str:
    skill = codex_skill_for(comp.skill)
    tool = codex_tool_for_skill(comp.skill)
    file_issue_hint = (
        f"\n\nIf Dev10x guidance told you to run this command, file an issue at "
        f"{CODEX_ISSUE_REPO} — the guidance needs updating."
    )
    if skill:
        tool_line = f"\n  Or call the MCP tool `{tool}` directly." if tool else ""
        head = (
            f"⛔  `{label}` blocked — use the Dev10x skill instead.\n\n"
            f"  Skill: `{skill}`{tool_line}\n\n"
            f"Why: Raw CLI bypasses guardrails that the Dev10x workflow\n"
            f"enforces ({comp.guardrails})."
        )
        fallback_intro = "If the skill is unavailable, apply these guardrails manually:"
        unavailable_hint = CODEX_MCP_UNAVAILABLE_HINT if tool else ""
    elif tool:
        head = (
            f"⛔  `{label}` blocked — use the Dev10x MCP tool instead.\n\n"
            f"  Tool: `{tool}`\n\n"
            f"Why: Raw CLI bypasses guardrails that the Dev10x workflow\n"
            f"enforces ({comp.guardrails})."
        )
        fallback_intro = "If the tool is unavailable, apply these guardrails manually:"
        unavailable_hint = CODEX_MCP_UNAVAILABLE_HINT
    else:
        head = (
            f"⛔  `{label}` blocked — the Dev10x `{comp.skill}` workflow is\n"
            f"{NOT_AVAILABLE_IN_CODEX}.\n\n"
            f"Why: Raw CLI bypasses guardrails that workflow enforces\n"
            f"({comp.guardrails})."
        )
        fallback_intro = "Apply these guardrails manually instead:"
        unavailable_hint = ""
    guidance = (
        f"{fallback_intro}\n{comp.fallback}"
        if comp.fallback
        else "No manual procedure is documented — ask the user how to proceed."
    )
    return adapt_message_for_codex(
        f"{head}\n\n{guidance}{unavailable_hint}{file_issue_hint}{CODEX_OVERRIDE_HINT}"
    )
