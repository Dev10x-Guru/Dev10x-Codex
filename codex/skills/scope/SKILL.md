---
name: scope
description: 'Base scoping skill for technical research and architecture design. Provides reusable scoping workflow for investigating codebases, designing solutions, and documenting decisions. TRIGGER when: performing technical research or architecture design without a specific tracker integration. DO NOT TRIGGER when: scoping a Linear ticket (use Dev10x:ticket-scope), documenting an ADR (use Dev10x:adr), or scoping a project (use Dev10x:project-scope).'
metadata:
  upstream: skills/scope/SKILL.md
---

> **Running in Codex.** Generated from `skills/scope/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/scope/`.
> Reviewed for Codex but not yet run end to end in it: confirm before any step that writes to GitHub or rewrites history.

# Dev10x:scope — Base Technical Scoping

Foundational scoping skill providing reusable research and
architecture-design workflows. Not directly invocable — extended
by `Dev10x:ticket-scope`, `Dev10x:adr`, `Dev10x:project-scope`,
`Dev10x:project-audit`.

## Instructions

The full workflow — research phases, design passes, ADR
formatting, diagram rendering, decision documentation — lives in
[`instructions.md`](instructions.md).

When this skill is invoked (directly or via an extension skill),
Read `instructions.md` now and follow it end-to-end.
