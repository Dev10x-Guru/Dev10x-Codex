---
name: git-groom
description: 'Restructure, polish, and clean up git commit history in the current branch before merging. Creates atomic, well-organized commits that tell a clear story. TRIGGER when: branch is ready for merge and commit history needs cleanup (squash fixups, reorder, reword). DO NOT TRIGGER when: branch has clean history already, or splitting individual commits (use Dev10x:git-commit-split).'
metadata:
  upstream: skills/git-groom/SKILL.md
---

> **Running in Codex.** Generated from `skills/git-groom/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/git-groom/`.

# Git Branch History Grooming

Restructure, polish, and clean up git commit history before
merging. Produces atomic, well-organized commits with outcome-
focused titles (JTBD style).

## Instructions

The full workflow — strategy selection gate, mass rewrite vs
interactive rebase, fixup autosquash, force-push safety — lives
in [`instructions.md`](instructions.md).

When this skill is invoked, Read `instructions.md` now and
follow it end-to-end. The strategy `AskUserQuestion` gate
documented there is REQUIRED.

## Legacy script path warning (GH-97)

This skill MUST be invoked via `$Dev10x:git-groom`.
Direct script invocation is unsupported and the historical
path `~/.claude/skills/dx:git/scripts/git-rebase-groom.sh`
no longer exists (it predates the current plugin layout).
Audit sessions show agents reaching for that path from
muscle memory, then falling back to raw
`git -c sequence.editor=... rebase -i --autosquash` when it
ENOENTs. Neither path is correct — both bypass the safety
checks this skill wraps around `git rebase` (protected-branch
guard, autosquash sanity, force-push-with-lease). If you see
the ENOENT, the corrective action is to invoke the skill,
not to retry the script.
