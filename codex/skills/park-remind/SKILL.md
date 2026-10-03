---
name: park-remind
description: 'Schedule a Slack reminder — so deferred items appear when you are clearing messages, not buried in a file you might not open. TRIGGER when: deferring work that should resurface via Slack notification later. DO NOT TRIGGER when: deferring to code or project storage (use Dev10x:park-todo), or routing to the best destination automatically (use Dev10x:park).'
metadata:
  upstream: skills/park-remind/SKILL.md
---

> **Running in Codex.** Generated from `skills/park-remind/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/park-remind/`.
> Not yet verified in Codex (tracked in Dev10x-Codex#24): expect gaps and confirm before any step that writes to GitHub or rewrites history.

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
context so you know where to pick it up. After the DM is sent, append
a pointer entry to the project task index so
`Dev10x:park-discover` can surface it locally without a Slack search
(GH-85).

## Prerequisites

- Slack token available (env `SLACK_TOKEN` or system keyring)
- `slack-notify.py` accessible at `<plugin-root>/skills/slack/slack-notify.py`

## Workflow

### 1. Gather context

```bash
git branch --show-current
```

```bash
git rev-parse --show-toplevel
```

Each in a single Bash call — no `;` chaining, no subshells.
Extract from the branch name:
- Ticket ID (pattern: `username/TICKET-ID/[worktree/]description`)
- Project name (from the toplevel basename)

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

```
mcp__cli__mktmp(namespace="slack", prefix="remind-msg", ext=".txt")
```

Write content to the returned path using Write tool, then:
```bash
<plugin-root>/skills/slack/slack-notify.py \
  --remind "$(cat <unique-path>)"
```

Do NOT use heredoc (`cat <<'EOF'`) to build the message inline —
the bash security hook blocks it. Always use Write tool → temp file
→ `$(cat ...)` for multi-line content.

### 4. Append to the task index

After Slack confirms delivery, append a pointer entry using the
schema documented in `Dev10x:park-todo` § Task Index Append:

```
mcp__cli__task_index_append(entry={
    "subject": "<item text, single line>",
    "status": "pending",
    "source": "slack-reminder",
    "created_at": "<YYYY-MM-DD>",
    "metadata": {
        "branch": "<current-branch>",
        "slack_ts": "<timestamp returned by slack-notify>",
        "slack_permalink": "<permalink returned by slack-notify>",
    },
})
```

The Slack DM remains the authoritative content; the index entry is
the local pointer that `Dev10x:park-discover` reads without a network
round-trip.

The tool creates the store on first use and appends under a lock, so
there is nothing to create or preserve by hand. Do NOT Write/Edit the
store — ADR-0018 D5 rehomed it out of the repo precisely so no
Write/Edit consent gate fires on a deferral.

### 5. Confirm

Report to user: "Sent reminder to your Slack DMs and indexed in the
project task index."

## Standalone Usage

When invoked directly: `$Dev10x:park-remind "message text"`

Parse the argument as the item text. Gather context and send.

## Used By

- `Dev10x:park` — when user picks "Slack DM to self"
