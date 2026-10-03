---
name: skill-audit
description: 'Audit a session''s skill usage, compliance, and extract lessons learned. Default (lightweight): analyzes visible context inline and presents a disposition gate — no separate terminal needed for most audits. Forensic (--full or escalation): dispatches parallel subagents for deep transcript analysis — run from a separate terminal. TRIGGER when: session is complete and user wants usage review, or a skill didn''t behave as expected. DO NOT TRIGGER when: mid-session during active work, or user is asking about a specific skill''s documentation.'
metadata:
  upstream: skills/skill-audit/SKILL.md
---

> **Running in Codex.** Generated from `skills/skill-audit/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/skill-audit/`.
> Not yet verified in Codex (tracked in Dev10x-Codex#24): expect gaps and confirm before any step that writes to GitHub or rewrites history.

# Skill Audit

Analyze a Claude Code session transcript for skill compliance,
missed invocations, user corrections, and process improvements
worth persisting into skill definitions.

## Strategies

**Lightweight (default):** Works from visible conversation
context. No transcript extraction, no subagent fan-out. Presents
inline findings and a structured disposition gate. Runs in the
current session — no separate terminal needed.

**Forensic (`--full` or escalation):** Full transcript extraction
and Wave 1/2 subagent fan-out. Use when the lightweight path
cannot answer, or when the supervisor explicitly requests deep
analysis. Run from a separate terminal.

## Instructions

The full workflow — strategy selection, task creation, session
resolution, wave orchestration, phase references, and reporting —
lives in [`instructions.md`](instructions.md).

When this skill is invoked, Read `instructions.md` now and
follow it end-to-end. `TaskCreate` calls, `AskUserQuestion`
gates, and `Agent` dispatches documented there are REQUIRED.

**End-to-end read enforcement (GH-166, GH-1279): this file does
NOT fit in one `Read`.** The first call returns a truncated
`PARTIAL view`. Keep issuing `Read(offset=…)` until you reach the
final line — the decision gates listed below live in the tail, and
a truncated read drops them while looking complete. An auditor
reasoning from half a file produces confident wrong claims about
the skill it is auditing, which is the failure GH-1279 records.
If you did not see the last line, you have not read the contract.

## Decision Gates

Each gate below blocks execution until the user responds.
**REQUIRED: Call `AskUserQuestion`** — do NOT use plain text.

1. Phase 0 Step 0c — lightweight disposition (file / escalate /
   discard). Call spec:
   [`tool-calls/ask-early-insight.md`](tool-calls/ask-early-insight.md)
2. Forensic Step 1.1 — confirm the auto-resolved session file.
   Call spec:
   [`tool-calls/ask-session-confirm.md`](tool-calls/ask-session-confirm.md)
3. Phase 7 sub-step B — whether to report upstream
4. Phase 7 sub-step B2 — **where** to report: confirm the issue
   tracker(s) detected from each offending skill's owning plugin
   (GH-816). Call spec:
   [`tool-calls/ask-target-tracker.md`](tool-calls/ask-target-tracker.md)

Gates 1, 2, and 4 are ALWAYS_ASK — they fire at every friction
level, including `adaptive`.
