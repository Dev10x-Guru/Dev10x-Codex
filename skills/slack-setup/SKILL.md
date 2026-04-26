---
name: Dev10x:slack-setup
description: >
  Guide the user through setting up their Slack integration —
  create a Slack app, configure scopes, store the token in the
  system keyring, and generate slack-config.yaml.
  TRIGGER when: setting up Slack integration for the first time, or
  reconfiguring Slack credentials.
  DO NOT TRIGGER when: Slack already configured and working, or
  sending messages (use Dev10x:slack).
user-invocable: true
invocation-name: Dev10x:slack-setup
allowed-tools:
  - AskUserQuestion
  - Bash(secret-tool:*)
  - Bash(security:*)
---

# Dev10x:slack-setup — Slack Integration Setup

**Announce:** "Using Dev10x:slack-setup to configure Slack integration."

## Orchestration

**REQUIRED: Create tasks before ANY work.** Execute at startup:

1. `TaskCreate(subject="Detect current Slack state", activeForm="Detecting state")`
2. `TaskCreate(subject="Guide Slack App creation", activeForm="Creating app")`
3. `TaskCreate(subject="Store token in keyring", activeForm="Storing token")`
4. `TaskCreate(subject="Generate slack-config.yaml", activeForm="Generating config")`
5. `TaskCreate(subject="Verify setup", activeForm="Verifying")`

## Step 1: Detect Current State

Check what's already configured:

1. Check if `~/.claude/memory/slack-config.yaml` exists
2. Try retrieving a token from the system keyring:
   - Linux: `secret-tool lookup service slack key bot_token`
   - macOS: `security find-generic-password -s slack -a bot_token -w`
3. Check if `SLACK_TOKEN` environment variable is set

**If token found and config exists** → report current state and
offer to reconfigure or exit.

**If partially configured** → resume from the missing step.

**If nothing configured** → proceed to Step 2.

## Step 2: Guide Slack App Creation

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
Options:
- Create a new Slack Bot (Recommended)
- Use an existing bot token
- Use a user token (xoxp-)

### New Bot Flow

Walk the user through creating a Slack App:

1. Direct them to https://api.slack.com/apps → "Create New App"
2. Choose "From scratch"
3. Name the app (suggest: "Claude AI" or "Dev10x Bot")
4. Select the workspace

### Required OAuth Scopes

Guide the user to add these **Bot Token Scopes** under
OAuth & Permissions:

| Scope | Used by |
|-------|---------|
| `chat:write` | Posting messages |
| `files:write` | Uploading screenshots/evidence |
| `reactions:write` | Adding emoji reactions |
| `conversations:join` | Auto-joining channels when posting |
| `users:read` | Resolving user mentions |

Optional scopes for DM reminders:
| Scope | Used by |
|-------|---------|
| `im:write` | Sending DM reminders to yourself |

After adding scopes, guide them to:
1. Install the app to the workspace
2. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

### Existing Token Flow

Ask the user to paste their token. Validate format:
- `xoxb-` → bot token (recommended)
- `xoxp-` → user token (works but limited)
- Anything else → invalid, ask again

## Step 3: Store Token in System Keyring

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
Options:
- System keyring (Recommended) — secure, persists across sessions
- Environment variable — must set each session
- Skip storage — manual setup later

### Keyring Storage

Detect the platform and store:

**Linux:**
```
secret-tool store --label="Slack Bot Token" service slack key bot_token
```
Then paste the token when prompted.

**macOS:**
```
security add-generic-password -s slack -a bot_token -w "<token>"
```

### Env Var Storage

Tell the user to add to their shell profile:
```
export SLACK_TOKEN="xoxb-your-token-here"
```

## Step 4: Generate slack-config.yaml

Create `~/.claude/memory/slack-config.yaml` with:

```yaml
self_user_id: ""  # Your Slack user ID (for DM reminders)
bot_username: "Claude AI"
user_groups: {}
```

**REQUIRED: Call `AskUserQuestion`** to gather:
- Their Slack user ID (guide: click profile → "..." → "Copy member ID")
- Preferred bot display name
- Any user group mentions to configure (e.g., `@team-leads` → `<!subteam^S123>`)

## Step 5: Verify Setup

Test the configuration:

1. Attempt to resolve the token (keyring or env)
2. If token found, offer to send a test message:

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
Options:
- Send test message to a channel
- Send test DM to myself
- Skip verification

Use `Dev10x:slack` skill to send the test message.

Report success or failure with actionable guidance.
