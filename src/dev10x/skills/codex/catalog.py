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


def codex_skill_for(skill: str) -> str | None:
    name = skill.removeprefix("Dev10x:")
    return f"$Dev10x:{name}" if name in VERIFIED_SKILLS else None
