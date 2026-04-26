---
name: Dev10x-skill-create
description: Use when creating or improving a local skill and hitting friction — bash commands keep prompting for approval, the skill doesn't appear in MOTD, or it's unclear which frontmatter fields wire up invocability — so you get the Dev10x-specific setup right without hunting through existing skills for examples.
---

# Dev10x Skill Create

**Announce:** "Using Dev10x:skill-create to [create/improve] the `<name>` skill."

**Foundation:** Read `superpowers:writing-skills` first for TDD methodology,
CSO principles, and quality standards. This skill covers only the local
Dev10x conventions that sit on top of that foundation.

## Directory Layout

```
$HOME/.codex/skills/
  <namespace>:<skill-name>/
    SKILL.md            # required
    scripts/            # executable helpers (optional)
    references/         # markdown reference docs (optional)
```

Active namespaces: `my:`, `Dev10x:`, `ticket:`, `pr:`, `commit:`

## Frontmatter Template

```yaml
---
name: my-skill-name
description: Use when [situation trigger] so [what the user gains or stops suffering]
user-invocable: true          # include for user-invocable skills
invocation-name: skill-name   # short alias, no namespace prefix
allowed-tools:                # pre-approve bash commands (removes prompts)
  - Bash(git commit:*)
  - Bash($HOME/.codex/skills/<name>/scripts/:*)
---
```

| Field | When to use |
|---|---|
| `user-invocable: true` | Skill appears in MOTD and is callable via Skill tool |
| `invocation-name` | Short alias users type (e.g. `skill-create` → `/skill-create`) |
| `allowed-tools` | Pre-approve bash commands Claude needs; use `:*` for any args |

## Writing for User Gains (JTBD-influenced)

Descriptions, step rationale, and mistake consequences should communicate
**what changes for the user** — not what the skill covers or what steps do.

**Description:** situation + gain, not a feature list.

```
❌ Covers namespace conventions, user-invocable frontmatter, and MOTD registration.
✅ Use when bash commands keep prompting for approval or the skill won't appear
   in MOTD — so you get the wiring right without hunting existing skills.
```

**Step rationale:** what breaks without this step, not just what the step does.

```
❌ After creating or modifying any skill, regenerate the SKILLS.md index.
✅ Skills don't appear in session context until indexed. Regenerate so the
   new skill is discoverable at the next session start.
```

**Mistake consequence:** what the user can no longer do — not the technical cause.

```
❌ Forgot user-invocable: true → Skill won't appear in MOTD or be invocable.
✅ Forgot user-invocable: true → Skill exists but nobody can call it — silent failure.
```

## Announce Pattern

Every invocable skill MUST open with an announce line so Claude signals
which skill is running:

```markdown
**Announce:** "Using <skill-name> to [purpose matching the task]."
```

## Workflow

### 1. Scaffold

```bash
mkdir -p $HOME/.codex/skills/<namespace>-<skill-name>
```

Then create `SKILL.md` following the frontmatter template above.

### 2. Write

Follow `superpowers:writing-skills` RED-GREEN-REFACTOR:

- **RED** — document what Claude does wrong without the skill
- **GREEN** — write minimal skill addressing those specific failures
- **REFACTOR** — close loopholes found during testing

### 3. Validate Structure

```bash
$HOME/.codex/skills/Dev10x-skill-index/scripts/generate-all.sh --force
rg -n "<namespace>-<skill-name>" $HOME/.codex/SKILLS.md $HOME/.codex/.skills-menu.txt
```

This validates frontmatter parsing and confirms the new skill is indexable.

### 4. Register in MOTD

Skills don't appear in session context until indexed. Regenerate so the
new skill is discoverable at the next session start (run this if you skipped
step 3 or made additional edits):

```bash
$HOME/.codex/skills/Dev10x-skill-index/scripts/generate-motd.sh --force
```

## Patterns from Existing Skills

| Skill | Patterns to study |
|---|---|
| `Dev10x:git-worktree` | Step-numbered workflow, `allowed-tools`, templates |
| `Dev10x:ticket-create` | Prerequisites check, integration section |
| `Dev10x:skill-index` | Minimal skill that fully delegates to a script |
| `commit` | Multi-step workflow with explicit validation gates |

## Calling Other Skills

Use the **Skill tool** or a `REQUIRED: Use <skill-name>` instruction line.
Never `@`-force-load another skill file — it consumes context immediately.

```markdown
## Prerequisites
**REQUIRED:** Invoke `Dev10x:ticket-branch` before this workflow begins.
```

## Script Conventions

All scripts in `scripts/` must be executable so they can be invoked directly
and match the `Bash($HOME/.codex/skills/<name>/scripts/:*)` allow rule pattern.

### Making Scripts Executable

After creating any script in `scripts/`:

```bash
chmod +x $HOME/.codex/skills/<namespace>:<skill-name>/scripts/<script>
```

Or for all scripts in a skill at once:

```bash
chmod +x $HOME/.codex/skills/<namespace>:<skill-name>/scripts/*
```

### Shebang Selection

| Script type | Shebang | Invoke as |
|---|---|---|
| Python (any) | `#!/usr/bin/env -S uv run --script` + PEP 723 block | `$HOME/.codex/skills/.../script.py` |
| Shell | `#!/usr/bin/env bash` or `#!/bin/bash` | `$HOME/.codex/skills/.../script.sh` |

**PEP 723 block** (for uv scripts with dependencies):
```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["requests", "slack_sdk"]
# ///
```

### Invocation in SKILL.md

Call scripts directly — never prefix with `python3` or `bash`:

```bash
# ✅ Direct call — matches Bash($HOME/.codex/skills:*) allow rule
$HOME/.codex/skills/<name>/scripts/my-script.py --arg value

# ❌ Prefixed — command starts with python3, not $HOME/.codex/skills
python3 $HOME/.codex/skills/<name>/scripts/my-script.py --arg value
```

### Why Direct Invocation Matters

The `allowed-tools` entry `Bash($HOME/.codex/skills/<name>/scripts/:*)` only
pre-approves commands whose prefix is `$HOME/.codex/skills/...`. If the script
is invoked with `python3` or `bash` prefix, the prefix becomes `python3` or
`bash`, the allow rule doesn't match, and Claude prompts for approval on
every invocation.

## Common Mistakes

| Mistake | Consequence |
|---|---|
| Description lists features covered | Claude can't tell when to load it — skill never gets used |
| No `Announce:` line | User can't tell which skill is running when something goes wrong |
| Forgot `user-invocable: true` | Skill exists but nobody can call it — silent, invisible failure |
| MOTD not refreshed after creation | Skill missing from session context until next regeneration |
| `allowed-tools` without `:*` suffix | Every bash command in the workflow triggers an approval prompt |
| Script not marked executable | Direct invocation fails; `python3`/`bash` prefix breaks allow rule matching |
| `python3 $HOME/.codex/skills/...` in SKILL.md | Allow rule `Bash($HOME/.codex/skills:*)` doesn't match; prompts on every run |
