---
name: fanout
description: 'Process multiple independent work items as a worktree-isolated swarm — each item runs the full Dev10x:work-on lifecycle inside its own background Agent with isolation="worktree". Honors dependencies, minimizes conflicts, auto-advances by default. TRIGGER when: 2+ independent work items need parallel processing (PRs, issues, tickets). DO NOT TRIGGER when: single task or sequential dependency chain (use Dev10x:work-on); already running as a swarm child (see recursive-fanout guard).'
metadata:
  upstream: skills/fanout/SKILL.md
---

> **Running in Codex.** Generated from `skills/fanout/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/fanout/`.
> Reviewed for Codex but not yet run end to end in it: confirm before any step that writes to GitHub or rewrites history.
> **In Codex:** Codex agents share one working directory: give each item its own worktree from mcp__cli__create_worktree and disjoint files, or run the items one after another.

# Dev10x:fanout — Parallel Work Stream Orchestrator

Close multiple open loops in parallel while honoring
dependencies and minimizing conflicts. Each item runs its full
pipeline — no collapsed shipping sequence.

## Instructions

The full workflow — 6-phase execution model, permission-aware
dispatch, parallel group management, completion gate — lives in
[`instructions.md`](instructions.md).

When this skill is invoked, Read `instructions.md` now and
follow it end-to-end. `TaskCreate` calls and the Strategy
`AskUserQuestion` gate documented there are REQUIRED.

**End-to-end read enforcement (GH-166, GH-1279): this file does
NOT fit in one `Read`.** The first call returns a truncated
`PARTIAL view` and stops around line 1209 of 1451. Keep issuing
`Read(offset=…)` until you reach the final line — the tail holds
the teardown decision tree and the Phase 5 comment-resolution
gate, and a truncated read drops both while looking complete.
If you did not see the last line, you have not read the contract.
