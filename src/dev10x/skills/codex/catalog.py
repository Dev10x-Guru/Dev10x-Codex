from __future__ import annotations

VERIFIED_SKILLS: frozenset[str] = frozenset(
    {
        "gh-context",
        "gh-pr-create",
        "gh-pr-fixup",
        "gh-pr-merge",
        "gh-pr-monitor",
        "gh-pr-respond",
        "gh-pr-triage",
        "git",
        "git-commit",
        "git-fixup",
        "git-groom",
        "git-worktree",
        "jtbd",
        "py-test",
        "ticket-branch",
    }
)

FOREMAN_ISSUE = 11
PERMISSION_FRICTION_ISSUE = 10
PLAN_MIRROR_ISSUE = 13
AUDIT_ISSUE = 17
IDE_ISSUE = 18

DEFERRED_SKILLS: dict[str, int] = {
    "foreman": FOREMAN_ISSUE,
    "afk": PERMISSION_FRICTION_ISSUE,
    "diag-friction": PERMISSION_FRICTION_ISSUE,
    "friction-setup": PERMISSION_FRICTION_ISSUE,
    "permission-investigator": PERMISSION_FRICTION_ISSUE,
    "plugin-doctor": PERMISSION_FRICTION_ISSUE,
    "plugin-maintenance": PERMISSION_FRICTION_ISSUE,
    "session-config-seed": PERMISSION_FRICTION_ISSUE,
    "upgrade-cleanup": PERMISSION_FRICTION_ISSUE,
    "plan-sync": PLAN_MIRROR_ISSUE,
    "audit-file": AUDIT_ISSUE,
    "context-audit": AUDIT_ISSUE,
    "project-audit": AUDIT_ISSUE,
    "skill-audit": AUDIT_ISSUE,
    "skill-audit-queue": AUDIT_ISSUE,
    "ide-normalize": IDE_ISSUE,
}

SKILL_CAVEATS: dict[str, str] = {
    "fanout": (
        "Codex agents share one working directory: give each item its own worktree from "
        "mcp__cli__create_worktree and disjoint files, or run the items one after another."
    ),
    "gh-review-setup": (
        "It sets up Claude-based GitHub Actions review, so the target repository needs an "
        "Anthropic API key secret."
    ),
    "jira": (
        "Creating issues needs an Atlassian MCP server configured in Codex; its tool names "
        "replace the mcp__claude_ai_Atlassian__* names used here."
    ),
    "linear": (
        "Needs a Linear MCP server configured in Codex; its tool names replace the "
        "mcp__claude_ai_Linear__* names used here."
    ),
    "memory-maintenance": (
        "It audits Claude Code memory under ~/.claude/; Codex memory and AGENTS.md files are "
        "not covered."
    ),
    "onboarding": (
        "Skip the permission-setup step: Codex approvals come from ~/.codex/rules/dev10x.rules "
        "(see the Dev10x-Codex docs/codex.md)."
    ),
    "skill-create": (
        "It creates Claude Code skills; Codex sees a new skill only after `dev10x skill "
        "codex-skills` regenerates codex/skills/."
    ),
    "skill-index": "It builds Claude Code's ~/.claude/SKILLS.md index, which Codex does not read.",
}


def codex_skill_for(skill: str) -> str | None:
    name = skill.removeprefix("Dev10x:")
    return f"$Dev10x:{name}" if name in VERIFIED_SKILLS else None
