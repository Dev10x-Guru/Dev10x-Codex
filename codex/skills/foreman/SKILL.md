---
name: foreman
description: 'Unattended overnight delivery of a milestone/bundle queue — a two-tier harness (watchdog main session + cheap foreman overseer + work-on crew) that pre-flights permissions while the supervisor is still present, loops the queue, defers questionable scope to the end, survives quota-block rollovers, and self-audits its friction at dawn. Defaults to the adaptive auto-advance + afk gate policy (guided/strict on request) — never YOLO auto-mode. TRIGGER when: the supervisor is leaving (AFK / overnight / "ship these milestones while I sleep") with 1+ milestones or issue bundles queued for autonomous delivery. DO NOT TRIGGER when: single attended bundle (use Dev10x:work-on), parallel independent items while attended (use Dev10x:fanout), or only the gate policy is wanted (use Dev10x:afk).'
metadata:
  upstream: skills/foreman/SKILL.md
---

> **Running in Codex.** Generated from `skills/foreman/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/foreman/`.
> **Not supported in Codex yet**: this skill depends on Claude Code features Codex lacks (Dev10x-Codex#11). Use it from Claude Code; Codex runs it only when invoked by name.

# Dev10x:foreman — Overnight Milestone Delivery Harness

**Announce:** "Using Dev10x:foreman to pre-flight and run the
unattended delivery of [queue] while you're away."

The supervisor leaves the site; the foreman runs the crew; the
watchdog only restarts the foreman. In the morning the supervisor
reads the shift log — merged PRs, closed milestones, every decision
recorded, deferred scope commented on its issues.

## Instructions

The full workflow — Phase 0 pre-flight (the one-time permission
window), the two-tier night loop, stall/quota/base-movement
recovery, and the dawn self-audit — lives in
[`instructions.md`](instructions.md).

When this skill is invoked, Read `instructions.md` now and follow it
end-to-end. The Phase 0 `AskUserQuestion` gate (queue plan + model
mapping) and the pre-flight enumeration are REQUIRED — they are what
makes the night survivable. The Phase 0.3 gate-policy gate is an
override opportunity, not a question: the default is
`gate_preset: adaptive` + `gate_overlays: [afk]`, and a durable
policy already on disk is honored without asking (GH-944).

Before writing any crew or foreman prompt, also Read
[`references/tool-surface.md`](references/tool-surface.md): subagents
cannot call `Skill(...)` and reach MCP wrappers only via a
`ToolSearch` select-query, so crew workers stop at PR-open and the
merge gate stays with this top-level session.

When resuming a run whose previous session died — or when writing a
handover another session will read — Read
[`references/durability-envelope.md`](references/durability-envelope.md)
first: only pushed commits and issue comments survive a session
death, an inherited brief is a hypothesis until re-derived from
origin, and a foreman cannot spawn named teammates (GH-965).
