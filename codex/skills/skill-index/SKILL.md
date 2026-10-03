---
name: skill-index
description: 'Generate a family-grouped, adaptive-density skill index. Scans local skills and all installed plugins, groups by families.yaml, hides orchestration deps via hidden.yaml, and writes ~/.claude/SKILLS.md (≤45 lines, ≤300 chars/line). TRIGGER when: regenerating SKILLS.md after adding, removing, or renaming skills. DO NOT TRIGGER when: viewing the existing skill index, or editing individual skills.'
metadata:
  upstream: skills/skill-index/SKILL.md
---

> **Running in Codex.** Generated from `skills/skill-index/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/skill-index/`.
> Reviewed for Codex but not yet run end to end in it: confirm before any step that writes to GitHub or rewrites history.
> **In Codex:** It builds Claude Code's ~/.claude/SKILLS.md index, which Codex does not read.

## Orchestration

This skill follows `references/task-orchestration.md` patterns.
Create a task at invocation, mark completed when done:

**REQUIRED: Create a task at invocation.** Execute at startup:

1. `TaskCreate(subject="Generate skill index", activeForm="Generating index")`

Mark completed when done: `TaskUpdate(taskId, status="completed")`

## Instructions

Regenerate both skill index files by running the generator script:

```bash
<plugin-root>/skills/skill-index/scripts/generate-all.sh --force
```

Then display the generated files to the user:

```bash
cat ~/.claude/SKILLS.md
cat ~/.claude/.skills-menu.txt
```
