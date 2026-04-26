---
name: Dev10x-slack
description: Send notifications to Slack channels with support for threads, file uploads, message updates, and user group mentions.
---

# Dev10x:slack — Slack Notifications

**Announce:** "Using Dev10x:slack to send a Slack notification."

## Overview

Post messages, upload files, reply in threads, update or delete
messages, and send self-DM reminders — all from Claude Code. The
script resolves user group mentions automatically from your config.

## First-Time Setup

If no Slack token is found, walk the user through setup using
AskUserQuestion:

**Step 1 — Token storage method:**

| Option | Pros | Cons |
|--------|------|------|
| System keyring (recommended) | Secure, persists across sessions | Requires `secret-tool` |
| `SLACK_TOKEN` env var | Simple, works everywhere | Must set per-session |
| Config file token | Always available | Plaintext on disk |

For **keyring** (recommended):
```bash
secret-tool store --label="Slack Bot Token" service slack key bot_token
```

For **env var**: add `export SLACK_TOKEN=xoxb-...` to shell profile.

**Step 2 — User token vs bot token:**

- `xoxb-` (bot token): Posts as a named bot. Requires the app to be
  added to each channel. Set `bot_username` in config.
- `xoxp-` (user token): Posts as yourself. No username override.
  Broader permissions but tied to your account.

The script auto-detects the token type from its prefix.

## Configuration

Create `$HOME/.codex/memory/slack-config.yaml`:

```yaml
# Your Slack user ID (for --remind self-DMs)
self_user_id: U040B2ES3N2

# Display name when posting with a bot token (xoxb-)
bot_username: Claude AI

# User group mention resolution (@name → <!subteam^ID>)
user_groups:
  "@dev-team": "<!subteam^S0123456789>"
  "@qa-team": "<!subteam^S9876543210>"
```

All fields are optional. The script works without a config file —
user group mentions and self-DMs just won't resolve.

## Usage

### Send a message

```bash
$HOME/.codex/skills/Dev10x-slack/slack-notify.py \
  --channel CHANNEL_ID \
  --message "Your message here"
```

### Reply in a thread

```bash
$HOME/.codex/skills/Dev10x-slack/slack-notify.py \
  --channel CHANNEL_ID \
  --thread-ts 1770113637.855309 \
  --message "Thread reply"
```

**Extracting thread info from a Slack URL:**
- URL format: `https://WORKSPACE.slack.com/archives/<CHANNEL>/p<TS>`
- Insert `.` before the last 6 digits of the timestamp
  (e.g., `p1770113637855309` → `1770113637.855309`)

### Upload files

```bash
$HOME/.codex/skills/Dev10x-slack/slack-notify.py \
  --channel CHANNEL_ID \
  --files screenshot.png report.pdf \
  --message "Optional comment"
```

### Update a message

```bash
$HOME/.codex/skills/Dev10x-slack/slack-notify.py \
  --channel CHANNEL_ID \
  --update MESSAGE_TS \
  --message "Revised content"
```

### Delete a message

```bash
$HOME/.codex/skills/Dev10x-slack/slack-notify.py \
  --channel CHANNEL_ID \
  --delete MESSAGE_TS
```

### Send a self-DM reminder

```bash
$HOME/.codex/skills/Dev10x-slack/slack-notify.py \
  --remind "Follow up on PR #1234"
```

Requires `self_user_id` in config or `SLACK_SELF_USER_ID` env var.

### Additional flags

| Flag | Effect |
|------|--------|
| `--broadcast` | Also post thread reply to channel |
| `--reactions emoji1 emoji2` | Add emoji reactions after posting |
| `--unfurl` | Enable link previews |
| `--message-file PATH` | Read message body from a file |
| `--verbose` | Show debug output |

## MCP Integration

**MCP for reads, this script for sends.** The MCP Slack tools are
better for searching channels, looking up users, and reading threads.
Use this script for all posting operations — it handles user group
resolution and bot identity consistently.

### Mention Syntax

- **User:** `<@USER_ID>` (e.g., `<@U040B2ES3N2>`)
- **Group:** `<!subteam^GROUP_ID>` (auto-resolved from config)
- **Plain `@name`** does NOT notify anyone — always use ID syntax.

To discover user IDs, use MCP `slack_search_users` tool.

## Slack Formatting Tips

- Slack supports: `*bold*`, `_italic_`, `~strike~`, `` `code` ``,
  ` ```code block``` `, `>quote`, bullet lists
- Slack does NOT support: markdown tables (use code blocks),
  headings (#), `[text](url)` links — use `<url|text>` instead

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `not_in_channel` | Bot not added to channel | Add bot via channel settings → Integrations |
| `channel_not_found` | Wrong channel ID | Verify ID in Slack |
| `No Slack token found` | No token configured | Run first-time setup above |
| `missing_scope` | Token lacks required permissions | Add scope in Slack app settings |
| `cant_delete_message` | Trying to delete another user's msg | Bot can only delete its own messages |

## Integration with Other Skills

This script is used by:
- **Dev10x:park-remind** — sends deferred-item DMs to yourself
- **Dev10x:gh-pr-monitor** — posts PR review notifications

For multi-line messages, use the Write tool to create a temp file,
then pass via `--message-file` or `$(cat /tmp/msg.txt)`. Do NOT use
heredoc (`cat <<'EOF'`) — the bash security hook blocks it.
