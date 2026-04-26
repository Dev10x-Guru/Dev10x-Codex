---
name: Dev10x-park-todo
description: Use when deferring work to code or project-level storage — so items resurface when editing nearby code or starting a new session in the same project, instead of being forgotten.
---

# Dev10x:park-todo — Persistent Code/Project Deferrals

**Announce:** "Using Dev10x:park-todo to [add TODO/FIXME to code | update
project TODO list]."

## Overview

Write deferred items to persistent storage where they will be
rediscovered by humans or Claude in the right context.

## Modes

### 1. Inline Code (TODO / FIXME)

When a specific file and location are relevant, insert a comment
directly in the code:

- `# TODO: message` — actionable, expected soon (this PR, next session)
- `# FIXME: message` — known issue, no timeline, boy scout rule applies

**How to insert:**

1. Read the target file
2. Use Edit to insert the comment at the appropriate line
3. Report what was added and where

**Example:**

```python
# TODO: Configure webhook secret from dashboard before going live
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
```

### 2. Project TODO File

When no specific file is relevant, append to `.claude/TODO.md` in the
current repository root.

**Format:**

```markdown
## YYYY-MM-DD — branch: username/TICKET-ID/short-desc

- [ ] Item description
- [ ] Another item with context or link
```

**How to append:**

1. Read `.claude/TODO.md` if it exists
2. Check if a section for today's date + current branch already exists
3. If yes, append the new item to that section
4. If no, create a new section header and add the item
5. Write the updated file

**If `.claude/TODO.md` does not exist, create it with a header:**

```markdown
# Project TODO — Deferred Items

Items deferred from Claude sessions. Review at session start.

## YYYY-MM-DD — branch: username/TICKET-ID/short-desc

- [ ] First deferred item
```

## Context Gathering

When invoked, auto-detect:
- Current date: `date +%Y-%m-%d`
- Current branch: `git branch --show-current`
- Repository root: `git rev-parse --show-toplevel`

## Review Mode Redirect

If the user asks about **existing** deferred items (e.g., "what's deferred",
"check for open items", "what do we have from yesterday"), invoke
`Dev10x:park-discover` instead of this skill. This skill is for *writing*
deferrals; `Dev10x:park-discover` is for *reading them back*.

## Used By

- `Dev10x:park` — when user picks "project TODO" or "inline code"
- `Dev10x:session-wrap-up` — Phase 1 scans `.claude/TODO.md` for existing items
