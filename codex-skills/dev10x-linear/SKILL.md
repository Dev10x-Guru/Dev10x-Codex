---
name: Dev10x-linear
description: Linear issue tracker operations via MCP tools. Get, create, update issues and list comments. Documentation-only skill — no scripts.
---

# Dev10x:linear — Linear Issue Tracker

Documentation-only skill centralizing Linear MCP tool references.
No scripts — all operations use MCP tools directly.

## Operation Mapping

| Operation | MCP Tool | Parameters |
|-----------|----------|------------|
| Get issue | `mcp__claude_ai_Linear__get_issue` | `id: "TEAM-133"` |
| List issues | `mcp__claude_ai_Linear__list_issues` | `team: "your-team-uuid"` |
| Create/update issue | `mcp__claude_ai_Linear__save_issue` | `id: "TEAM-133", state: "In Progress"` |
| List comments | `mcp__claude_ai_Linear__list_comments` | `issueId: "TEAM-133"` |
| Create comment | `mcp__claude_ai_Linear__create_comment` | `issueId: "TEAM-133", body: "..."` |
| List statuses | `mcp__claude_ai_Linear__list_issue_statuses` | `team: "your-team-uuid"` |
| Get status | `mcp__claude_ai_Linear__get_issue_status` | `id: "STATUS_UUID"` |
| List labels | `mcp__claude_ai_Linear__list_issue_labels` | `team: "your-team-uuid"` |
| Create label | `mcp__claude_ai_Linear__create_issue_label` | `team: "your-team-uuid", name: "label"` |

## Team IDs

| Team | UUID |
|------|------|
| YOUR_TEAM | `your-team-uuid` |

Replace `your-team-uuid` with the UUID from your Linear workspace settings.
To find it: Settings → Teams → select your team → the UUID is in the URL.

## URL Template

```
https://linear.app/your-org/issue/{TICKET_ID}
```

Example: `https://linear.app/your-org/issue/TEAM-133`

Replace `your-org` with your Linear organization slug.

## Prerequisite Check

Before using Linear MCP tools, verify availability:

1. Check if any `mcp__claude_ai_Linear__*` or `mcp__plugin_linear_linear__*` tool is available
2. If not available, inform the user:
   ```
   Linear MCP is not enabled. Please enable the Linear MCP server
   in your Claude Code settings to use this skill.
   ```
3. Do not proceed if Linear MCP is unavailable

## Searching for JTBD in Ticket

To find an existing Job Story on a Linear ticket:

1. Get issue: `mcp__claude_ai_Linear__get_issue(id: "TEAM-133")`
2. Search the description for `**When**` / `**I want to**` / `**so I can**` pattern
3. If not found, list comments: `mcp__claude_ai_Linear__list_comments(issueId: "TEAM-133")`
4. Search each comment body for the same pattern
5. Return the first match, or empty if none found

## MCP Tool Variants

Two MCP server configurations may provide Linear tools:

| Provider | Tool prefix | Notes |
|----------|-------------|-------|
| Claude AI (cloud) | `mcp__claude_ai_Linear__` | Available in Claude Code web/desktop |
| Plugin (local) | `mcp__plugin_linear_linear__` | Requires local MCP server config |

Both provide the same operations. Check for either prefix when
verifying availability.
