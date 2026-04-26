---
name: Dev10x-slack-review-request
description: Post a Slack review request for a PR using per-project config (channel, mentions). Reads configuration from userspace YAML.
---

# Slack Review Request

Post a review notification to the project's configured Slack channel
with appropriate team and user mentions.

## Config

Configuration lives in `$HOME/.codex/memory/slack-config-code-review-requests.yaml`:

```yaml
default_action: ask  # "skip" or "ask" for unconfigured projects

projects:
  my-app:
    channel: C0EXAMPLE01    # Slack channel ID
    mentions:               # resolved via slack-config.yaml
      - "@backend-team"     # user group → <!subteam^ID>
      - "@alice"            # user → <@SLACK_ID>

  internal-tools:
    skip: true              # no Slack notification
```

Mentions are resolved against `$HOME/.codex/memory/slack-config.yaml`
`user_groups` and `users` mappings.

### Per-Project Actions

- **Configured**: Use `channel` and `mentions` from config; fetch PR
  details; format message with JTBD if present; ask user for confirmation.
- **`skip: true`**: Report "Slack notification skipped" and done.
- **Unconfigured** (matches `default_action: ask`): Ask user for
  channel and mentions interactively. If user provides them, proceed;
  otherwise done.
- **Unconfigured** (matches `default_action: skip`): Skip silently.

## Flow

### Step 1: Prepare

Resolve project config and format the Slack message:

```bash
$HOME/.codex/skills/Dev10x-slack-review-request/scripts/slack-review-request.py \
  prepare --pr {pr_number} --repo {repo}
```

Output is JSON with keys:
- `skip`: boolean — project is configured to skip
- `ask`: boolean — no config found; user input required
- `channel`: Slack channel ID (or null)
- `message`: formatted Slack message (or null)
- `reason`: short explanation if skip or ask

### Step 2: Handle Result

Check the `prepare` output:

- **If `skip=true`**: Report "Slack notification skipped for
  {repo}" and done. Do not ask user.

- **If `ask=true`**: Use `AskUserQuestion` to ask for:
  - Slack channel ID (required)
  - Mentions as space-separated @names (optional)

  If user provides a channel, resolve mentions and update config
  (optional — may save to YAML for future use). Then proceed to
  Step 3 with resolved config.

  If user declines, done.

- **Otherwise**: Continue to Step 3 with resolved config.

### Step 3: Confirm with User

Use `AskUserQuestion` to show:
- **Title**: "Review Slack message before posting"
- **Content**: the formatted message (from Step 1 output)
- **Options**: "Post to Slack" / "Skip"

If user chooses "Skip", done. If "Post to Slack", proceed to Step 4.

### Step 4: Send

Write the message to a temporary file, then invoke the send command:

```bash
$HOME/.codex/skills/Dev10x-slack-review-request/scripts/slack-review-request.py \
  send --channel {channel} --message-file {temp_file}
```

Clean up the temp file.

Report success: channel ID, thread timestamp (if available).

## Integration

This skill is invoked by `Dev10x:gh-pr-monitor` Phase 3 (after GitHub
reviewer assignment) to post the Slack notification. It handles only
Slack posting — no GitHub API calls.

For re-review notifications (Phase 2.7 in `Dev10x:gh-pr-monitor`), the
calling skill composes a custom message (e.g., "@reviewer please take
another look") and invokes this skill with `--message` directly,
skipping the `prepare` step.

## Message Format

Messages include:
- **Mentions** (if any): prepended to the first line before "Please review"
- **Review link**: formatted as `<url|my-app#42>`
- **PR title**: on next line
- **JTBD** (if present in PR body): extracted from first `**When**`
  paragraph and formatted as a blockquote

Example output:

```
<!subteam^S0EXAMPLE> <@U0ALICE> Please review <https://github.com/org/my-app/pull/42|my-app#42>
Fix payment routing
> *When* a customer uses a new card, *wants to* bypass 3D Secure, *so*
> *can* complete checkout faster.
```

## Usage

### Direct invocation (user-facing)

```
Dev10x-slack-review-request                     # uses current branch PR
Dev10x-slack-review-request --manual            # force config review
```

### Programmatic (from other skills)

```
Skill("Dev10x:slack-review-request",
  args={
    "pr_number": 42,
    "repo": "org/my-app",
    "ask_if_unconfigured": true,
  }
)
```

## See Also

- `Dev10x:gh-pr-monitor` — calls this skill in Phase 3 (review request workflow)
- `slack-config.yaml` — mention resolution mappings
