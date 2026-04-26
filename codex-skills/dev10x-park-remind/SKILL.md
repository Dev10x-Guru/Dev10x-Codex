---
name: Dev10x-park-remind
description: Use when you need a reminder to surface in Slack later — so deferred items appear when you are clearing messages, not buried in a file you might not open.
---

# Dev10x:park-remind — Slack DM Reminder

**Announce:** "Using Dev10x:park-remind to send a Slack reminder to yourself."

## Overview

Send a self-DM via Slack with a deferred item, formatted with session
context so you know where to pick it up.

## Prerequisites

- Slack token available (env `SLACK_TOKEN` or system keyring)
- `slack-notify.py` accessible at `$HOME/.codex/skills/Dev10x-slack/slack-notify.py`

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
$HOME/.codex/skills/Dev10x-slack/slack-notify.py \
  --remind "$(cat <unique-path>)"
```

Do NOT use heredoc (`cat <<'EOF'`) to build the message inline —
the bash security hook blocks it. Always use Write tool → temp file
→ `$(cat ...)` for multi-line content.

### 4. Confirm

Report to user: "Sent reminder to your Slack DMs."

## Standalone Usage

When invoked directly: `Dev10x-park-remind "message text"`

Parse the argument as the item text. Gather context and send.

## Used By

- `Dev10x:park` — when user picks "Slack DM to self"
