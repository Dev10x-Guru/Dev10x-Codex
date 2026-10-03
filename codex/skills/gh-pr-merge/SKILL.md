---
name: gh-pr-merge
description: 'Validate all pre-merge conditions and execute PR merge. Checks unresolved threads, CI status, draft state, mergeability, working copy, fixup commits, Fixes-linked scope delivery, and review approval before merging. TRIGGER when: PR is ready to merge and needs pre-merge validation. DO NOT TRIGGER when: PR is still draft, CI is failing, or review comments are unaddressed.'
metadata:
  upstream: skills/gh-pr-merge/SKILL.md
---

> **Running in Codex.** Generated from `skills/gh-pr-merge/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/gh-pr-merge/`.

# Merge PR

Pre-merge validation gate that checks 9 conditions before
executing `gh pr merge`. Prevents premature merges by verifying
unresolved threads, CI, draft state, mergeability, working copy,
fixup commits, Fixes-linked scope delivery, and review approval.

## Instructions

The full workflow — 9 pre-merge checks, strategy selection from
project settings, merge execution, post-merge verification —
lives in [`instructions.md`](instructions.md).

When this skill is invoked, Read `instructions.md` now and
follow it end-to-end. `TaskCreate` and `AskUserQuestion` calls
documented there are REQUIRED.

## Skill Wrapper is Mandatory (GH-152)

**Hard rule:** Do NOT call `gh pr merge` directly. Every PR
merge MUST go through `$Dev10x:gh-pr-merge` so the
9-check pre-merge gate (unresolved threads, top-level
comments, inline review comments, Fixes-linked scope
delivery, CI buckets, draft state, mergeability, working
copy, review approval) runs. Audit
GH-152 caught a session where the agent ran
`gh pr merge <N> --rebase --delete-branch` directly after
partially reading this SKILL.md — only the CI check was
performed inline, every other check was skipped.

The PreToolUse hook blocks raw `gh pr merge` (extends the
existing blocks on `git commit`, `git push`, and `git
checkout -b`). The skill executes Step 5 via
`mcp__cli__merge_pr` (GH-232) — symmetric to
`create_pr` / `push_safe` — so the documented flow ships
through a structured MCP tool, not a caller-level bypass.
