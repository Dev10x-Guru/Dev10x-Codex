---
name: playbook
description: 'View and customize playbooks (step-by-step procedures) for any orchestration skill. List playbook-powered skills, inspect plays, edit steps through a guided flow, or reset to defaults. TRIGGER when: user wants to view, edit, or customize playbook workflows for skills. DO NOT TRIGGER when: executing a playbook-powered skill (handled automatically by Dev10x:work-on or other orchestrators).'
metadata:
  upstream: skills/playbook/SKILL.md
---

> **Running in Codex.** Generated from `skills/playbook/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/playbook/`.
> Not yet verified in Codex (tracked in Dev10x-Codex#24): expect gaps and confirm before any step that writes to GitHub or rewrites history.

# Dev10x:playbook — Playbook Manager

Guided interface for viewing and customizing playbook YAML files
(`references/playbook.yaml` within any playbook-powered skill)
so users never need to edit raw YAML.

## Instructions

The full workflow — discovery, inspection, guided edit flow,
reset to defaults, tier resolution — lives in
[`instructions.md`](instructions.md).

When this skill is invoked, Read `instructions.md` now and
follow it end-to-end. `TaskCreate` calls and `AskUserQuestion`
gates documented there are REQUIRED.
