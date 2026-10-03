---
name: ticket-scope
description: 'Scope Linear tickets with technical research and architecture design. Extends the base scope skill with Linear ticket integration, story point estimation, and acceptance criteria formatting. TRIGGER when: preparing to implement a Linear ticket — scoping technical approach, estimating story points, or writing acceptance criteria. DO NOT TRIGGER when: scoping non-Linear tickets, multi-ticket projects (use Dev10x:project-scope), or new domain areas (use Dev10x:ddd first).'
metadata:
  upstream: skills/ticket-scope/SKILL.md
---

> **Running in Codex.** Generated from `skills/ticket-scope/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/ticket-scope/`.
> Reviewed for Codex but not yet run end to end in it: confirm before any step that writes to GitHub or rewrites history.

# Ticket Scope — Linear Ticket Scoping Skill

Create comprehensive technical scoping documents for Linear
tickets. Extends the base `Dev10x:scope` skill with Linear-
specific workflows (ticket fetch, comment back, story point
estimation, acceptance criteria).

## Instructions

The full workflow — ticket fetch, context gathering, research
loop, story point sizing, AC generation, comment writeback —
lives in [`instructions.md`](instructions.md).

**REQUIRED before ANY other tool call:** Read
[`instructions.md`](instructions.md) end-to-end. The
orchestration contract (TaskCreate calls, phase ordering,
AskUserQuestion gates, mandatory delegations like
`$Dev10x:jtbd` and template selection) lives there —
not in this SKILL.md. Skipping the read causes downstream
phase bypasses (GH-26, GH-27, GH-28).

**Self-check after the read:** Confirm you can name the
six TaskCreate subjects, the Phase 4b skill delegation,
and the Phase 5.1 templates before fetching the ticket.
If you cannot, re-read the file. Do NOT proceed to
`mcp__cli__issue_get` (or any other tool)
until the read is complete.
