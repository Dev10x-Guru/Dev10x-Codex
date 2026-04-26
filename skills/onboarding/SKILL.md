---
name: Dev10x:onboarding
description: >
  Guided discovery of Dev10x capabilities for new users. Interactive
  tour through skill families, git setup, PR pipeline, session
  management, and customization — adapted to experience level.
  TRIGGER when: user is new to Dev10x, asks what it can do, or
  wants a walkthrough of available capabilities.
  DO NOT TRIGGER when: user already knows what skill to use, or
  is asking about a specific feature (use that skill directly).
user-invocable: true
invocation-name: Dev10x:onboarding
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
  - TaskCreate
  - TaskUpdate
  - Skill
---

# Dev10x:onboarding — Guided Discovery

## Overview

Interactive walkthrough that introduces Dev10x capabilities to
new users in under 10 minutes. Detects existing configuration
and adapts the tour to skip already-done steps.

## Orchestration

**REQUIRED: Create tasks before ANY work.** Execute at startup:

1. `TaskCreate(subject="Detect user context", activeForm="Detecting context")`
2. `TaskCreate(subject="Guided tour", activeForm="Walking through capabilities")`
3. `TaskCreate(subject="Setup assistance", activeForm="Setting up")`

## Phase 1: Detect User Context

Gather information to adapt the tour:

### 1.1 Experience Level

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
Options:
- New to Claude Code — First time using Claude Code or AI coding tools
- Know Claude Code, new to Dev10x — Familiar with Claude Code but not this plugin
- Returning user — Used Dev10x before, want a refresher

### 1.2 Configuration Detection

Check what's already set up (skip configured items in tour):

| Check | Command | Configured if |
|-------|---------|---------------|
| Git aliases | `git config alias.develop-log` | Non-empty output |
| SKILLS.md | `test -f ~/.claude/SKILLS.md` | File exists |
| Memory files | `ls ~/.claude/projects/*/memory/*.md 2>/dev/null` | Files found |
| Global Dev10x config | `ls ~/.claude/memory/Dev10x/ 2>/dev/null` | Directory exists |
| Playbook overrides | `ls ~/.claude/memory/Dev10x/playbooks/*.yaml .claude/Dev10x/playbooks/*.yaml 2>/dev/null` | Files found |
| Worktree context | `test -f .git` | `.git` is file = worktree |

### 1.3 Project Detection

Determine the project type from the repo:

```bash
# Check for common markers
test -f pyproject.toml     # Python project
test -f package.json       # Node/frontend project
test -f Cargo.toml         # Rust project
ls *.sln 2>/dev/null       # .NET project
```

Store the detected project type for later tour adaptation.

## Phase 2: Guided Tour

Walk through Dev10x capability families. For each section,
show a brief explanation and the key skills to try.

### 2.1 Skill Discovery

```
Dev10x organizes 75+ skills into families:

Pipeline — End-to-end ticket-to-merge workflow
  /Dev10x:work-on <ticket-url>  ← Start here for any task

Git — Atomic commits with gitmoji and JTBD titles
  /Dev10x:git-commit

PR — Full PR lifecycle with CI monitoring
  /Dev10x:gh-pr-create → /Dev10x:gh-pr-monitor

Session — Track work, defer items, resume later
  /Dev10x:session-wrap-up → /Dev10x:park-discover

To see all skills: check ~/.claude/SKILLS.md
To regenerate: /Dev10x:skill-index
```

### 2.2 Git Workflow Setup

**Skip if:** Git aliases already configured (from Phase 1).

```
Dev10x uses git aliases to avoid permission friction:
  git develop-log   — commits since diverging from develop
  git develop-diff  — diff since diverging from develop
  git develop-rebase — interactive rebase onto develop
```

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
Options:
- Set up aliases now (Recommended) — Run /Dev10x:git-alias-setup
- Skip — I'll set them up later

If user chooses setup:
```
Skill(skill="Dev10x:git-alias-setup")
```

### 2.3 PR Pipeline Demo

Brief explanation of the shipping pipeline:

```
The Dev10x PR pipeline automates the full shipping flow:

1. /Dev10x:git-commit    — Gitmoji + JTBD commit message
2. /Dev10x:gh-pr-create  — Draft PR with Job Story
3. /Dev10x:gh-pr-monitor — Background CI + review monitoring
4. /Dev10x:git-groom     — Clean commit history
5. /Dev10x:gh-pr-respond — Address review comments

Or use /Dev10x:work-on <ticket> for the full pipeline
from a single command.
```

### 2.4 Session Management

```
Dev10x tracks your work across sessions:

- /Dev10x:session-wrap-up — Save open work before closing
- /Dev10x:park            — Defer a task to the right place
- /Dev10x:park-discover   — Find deferred items at session start

Memory files persist context across conversations.
```

### 2.5 Customization

**Skip if:** Playbook overrides already exist (from Phase 1).

```
Customize Dev10x behavior per project:

- Playbooks: Override workflow steps
  /Dev10x:playbook edit work-on feature

- Memory: Teach Dev10x about your project
  Save project context, feedback, and references

- CLAUDE.md: Project-level instructions
  Loaded every session for this repo
```

### 2.6 Tour Summary

Present what was covered and suggest next steps:

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
Options:
- Start working — I have a task to begin (Recommended)
- Explore more — Show me additional capabilities
- Set up customization — Help me configure playbooks/memory

## Phase 3: Setup Assistance (Optional)

Only runs if user chose "Set up customization" or "Explore more"
in the tour summary.

### If "Explore more":

Show additional capability families:
- Testing: `/test`, `/test:fix-flaky`, `/Dev10x:qa-scope`
- Architecture: `/Dev10x:adr-evaluate`, `/Dev10x:scope`
- Operations: `/Dev10x:investigate`, `/triage-sentry`
- Reports: `/work:daily`, `/work:weekly`

### If "Set up customization":

Guide through:
1. Creating a playbook override for their most-used workflow
2. Setting up project memory with key context
3. Reviewing CLAUDE.md for project-specific instructions

Each step uses `AskUserQuestion` to confirm before proceeding.
