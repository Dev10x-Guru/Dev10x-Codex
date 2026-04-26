---
name: Dev10x-session-tasks
description: Use when tracking in-session work items — so open loops are visible and triageable before session end without losing track of parallel work.
---

# Dev10x:session-tasks — In-Session Task Tracking

**Announce:** "Using Dev10x:session-tasks to [show/add/update] session tasks."

## Overview

Thin wrapper around Claude's `TaskCreate`/`TaskUpdate`/`TaskList` tools
for tracking work items within the current session.

## Auto-Advance

After creating tasks via this skill, **immediately start
executing the first pending task**. Do not pause to ask
"should I start?" or wait for the user to say "go". The act
of creating the task list is the authorization to begin.

```
TaskCreate(subject="Task 1", ...)
TaskCreate(subject="Task 2", ...)
TaskUpdate(taskId=task1, status="in_progress")
# Begin working on Task 1 immediately
```

This follows the universal auto-advance rule from
`references/task-orchestration.md`.

## Commands

### Show tasks

Use `TaskList` to display all current tasks grouped by status.
Present as a markdown table:

| # | Status | Task |
|---|--------|------|
| 1 | in_progress | Implement checkout feature |
| 2 | pending | Create PR for TICKET-42 |
| 3 | completed | Add webhook endpoint |

### Add task

Use `TaskCreate` with:
- `subject`: short task title
- `description`: context, file paths, or links if available

### Update task

Use `TaskUpdate` with the task ID and new `status`:
- `in_progress` — currently working on
- `completed` — done
- `pending` — deferred within this session

## Used By

- `Dev10x:park` — when user picks "keep for this session"
- `Dev10x:session-wrap-up` — Phase 1 auto-scan reads the task list
