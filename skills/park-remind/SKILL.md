---
name: Dev10x:park-remind
description: >
  Schedule a Slack reminder — so deferred items appear when you are
  clearing messages, not buried in a file you might not open.
  TRIGGER when: deferring work that should resurface via Slack
  notification later.
  DO NOT TRIGGER when: deferring to code or project storage (use
  Dev10x:park-todo), or routing to the best destination automatically
  (use Dev10x:park).
user-invocable: true
invocation-name: Dev10x:park-remind
allowed-tools:
  - Bash(${CLAUDE_PLUGIN_ROOT}/skills/slack/slack-notify.py:*)
  - Bash(/tmp/claude/bin/mktmp.sh:*)
  - Write(/tmp/claude/slack/**)
---

# Dev10x:park-remind — Slack DM Reminder

**Announce:** "Using Dev10x:park-remind to send a Slack reminder to yourself."

## Orchestration

This skill follows `references/task-orchestration.md` patterns.
Create a task at invocation, mark completed when done:

**REQUIRED: Create a task at invocation.** Execute at startup:

1. `TaskCreate(subject="Schedule Slack reminder", activeForm="Scheduling reminder")`

Mark completed when done: `TaskUpdate(taskId, status="completed")`

## Overview

Send a self-DM via Slack with a deferred item, formatted with session
context so you know where to pick it up.

## Prerequisites

- Slack token available (env `SLACK_TOKEN` or system keyring)
- `slack-notify.py` accessible at `${CLAUDE_PLUGIN_ROOT}/skills/slack/slack-notify.py`

## Workflow

### 1. Gather context

```bash
git branch --show-current
basename "$(git rev-parse --show-toplevel)"
date +%Y-%m-%d
```

Extract from branch name:
- Ticket ID (pattern: `username/TICKET-ID/[worktree/]description`)
- Project name (from repo root basename)

### 2. Format message

Build the reminder message:

```
🔖 Deferred from session [YYYY-MM-DD]
Project: <project-name> | Branch: <branch-name>

<user's deferred item text>
```

If the user provided a URL or file reference, include it on a
separate line after the item text.

### 3. Send DM

For multi-line messages, write the formatted text to a unique temp file
using the Write tool first, then pass it via command substitution:

```bash
/tmp/claude/bin/mktmp.sh slack remind-msg .txt
```
Write content to the returned path using Write tool, then:
```bash
${CLAUDE_PLUGIN_ROOT}/skills/slack/slack-notify.py \
  --remind "$(cat <unique-path>)"
```

Do NOT use heredoc (`cat <<'EOF'`) to build the message inline —
the bash security hook blocks it. Always use Write tool → temp file
→ `$(cat ...)` for multi-line content.

### 4. Confirm

Report to user: "Sent reminder to your Slack DMs."

## Standalone Usage

When invoked directly: `/Dev10x:park-remind "message text"`

Parse the argument as the item text. Gather context and send.

## Used By

- `Dev10x:park` — when user picks "Slack DM to self"
