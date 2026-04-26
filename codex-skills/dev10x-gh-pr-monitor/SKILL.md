---
name: Dev10x-gh-pr-monitor
description: Launch a background agent to monitor PR CI checks and review comments, automatically address issues with fixup commits, and notify team when ready. Use after creating a PR to automate the entire review cycle.
---

# PR Review Monitor (Background Agent)

## Overview

This skill launches a **background agent** that autonomously monitors a PR
through its full lifecycle — CI checks, review comments, and team
notification. The user continues working while the agent handles everything.

**When to use this skill:**
- After creating a draft PR with `Dev10x-gh-pr-create`
- When you want to automate the PR review cycle without blocking your session

## Execution Model

```
User invokes Dev10x-gh-pr-monitor
    │
    ├── 1. Detect PR number, repo, URL
    ├── 2. Launch background Task agent
    ├── 3. Tell user: "Monitoring in background, output at {path}"
    │
    └── User continues working
            │
            └── Background agent runs autonomously:
                ├── Phase 0: JTBD Job Story check (autonomous)
                ├── Phase 1: CI monitoring (autonomous)
                ├── Phase 2: Comment handling (autonomous)
                ├── Phase 2.5: QA scope assessment (asks user)
                ├── Phase 2.7: Re-review notification (asks user)
                └── Phase 3: Notification (asks user first)
```

## Launch Instructions

When the user invokes `Dev10x-gh-pr-monitor`:

### Step 1: Detect PR context

Use the `Dev10x:gh-context` script to detect PR context in one call:

```bash
$HOME/.codex/skills/Dev10x-gh-context/scripts/gh-pr-detect.sh "$ARG"
# Parse PR_NUMBER, REPO, PR_URL, BRANCH from KEY=VALUE stdout
```

Pass `$ARG` as the skill argument (PR URL, bare number, or empty).
The script always fetches `BRANCH` via `gh pr view --json headRefName`
— never from local git — which is critical in multi-worktree setups.

If the script exits non-zero, tell the user and stop.

### Step 2: Check for poll mode

Read the state file at `/tmp/claude/pr-monitor/state-{pr_number}.json`
(if it exists). If the state file contains `phases_completed` that includes
**both** `phase0` and `phase3`, offer **lightweight polling** instead:

Use `AskUserQuestion`:
- **"Start polling (Recommended)"** — launches poll in a background shell
- **"Full agent"** — launches a full background agent as before

### Step 3: Launch background agent

Use the **Task tool** with these parameters:

```
subagent_type: "general-purpose"
run_in_background: true
max_turns: 200
description: "Monitor PR #{pr_number}"
prompt: <see "Agent Prompt Template" below, with variables filled in>
```

### Step 4: Report to user

Tell the user:
- PR monitor is running in the background
- Show the output file path from the Task result
- They can check progress anytime by reading that file
- The agent will ask for confirmation before posting notifications

---

## Agent Prompt Template

Fill in `{pr_number}`, `{repo}`, `{pr_url}`, `{branch}` and pass as
the prompt:

````
You are a PR monitoring agent running in the background.

**Target:** PR #{pr_number} in {repo}
**URL:** {pr_url}
**Branch:** {branch}

Your job: autonomously shepherd this PR from draft → CI passing →
comments addressed → review requested. Execute the early-exit check
first, then Phase 0, 1, 2, 2.5, and 3 in order.

---

## Early-Exit Check

Before running any phases, check if work has already been done by
reading the state file and comparing against current PR state.

1. Read `/tmp/claude/pr-monitor/state-{pr_number}.json` (if exists)
2. Fetch current PR state:
   ```bash
   gh pr checks {pr_number} --repo {repo} --json name,state,conclusion
   gh pr view {pr_number} --repo {repo} --json state,reviews,comments
   ```
3. Compare against saved state
4. If ALL match and no new data → exit with:
   "No changes since {last_checked}. Nothing to do."
5. If changed → run only the relevant phases
6. Skip phases listed in `phases_completed` from the state file

---

## Phase 0: JTBD Job Story Check

The PR body **must** start with a JTBD Job Story as its first paragraph.

1. Fetch the current PR body:
   ```bash
   gh pr view {pr_number} --json body -q '.body'
   ```

2. Check if the first paragraph matches the Job Story pattern:
   - Starts with `**When**` (bold "When")
   - Contains `**I want to**` and `**so I can**`

3. If a valid Job Story is present → skip to Phase 1.

4. If missing or malformed → generate one using the `Dev10x:ticket-jtbd` skill.

5. After the skill completes, verify the PR body now starts with the
   Job Story.

---

## Phase 1: CI Monitoring Loop

Repeat until all CI checks pass:

1. Check CI status:
   ```bash
   gh pr checks {pr_number}
   ```

2. Parse results:
   - ALL PASSING → mark PR ready (`gh pr ready {pr_number}`) and go
     to Phase 2
   - PENDING → wait 30 seconds via `sleep 30`, then re-check
   - FAILURES → analyze and fix (see CI Failure Handling below)

3. After fixing CI failures, push and wait 30 seconds before
   re-checking.

### CI Failure Handling

| Failure Type | How to Fix |
|---|---|
| ruff/black/isort | Auto-format; commit and push |
| mypy | Add/fix type annotations |
| flake8 | Remove unused imports, fix style issues |
| gitlint (title > 72 chars) | Amend commit message |
| pytest failures | Read test, fix code or update expectations |
| Import errors | Update import paths |
| Coverage < 100% | Add tests for uncovered lines |

For each CI fix:
- Implement the fix
- Stage changes: `git add {files}`
- Create fixup commit targeting the appropriate original commit
- Push: `git push origin HEAD`

---

## Phase 2: Review Comment Monitoring Loop

Repeat until no unaddressed comments remain:

1. Delegate to `Dev10x:gh-pr-respond` in **batch mode** with the PR URL:
   ```
   Use the Skill tool: skill="Dev10x:gh-pr-respond", args="{pr_url}"
   ```

2. After all comments are addressed, return to Phase 1 (CI may re-run
   after pushes).

3. When Phase 1 passes AND no unaddressed comments remain → go to
   Phase 2.5.

### Exit condition for Phase 2 loop

Move to Phase 2.5 when ALL of these are true:
- All CI checks passing
- No unaddressed review comments
- PR has at least one approval OR no reviews yet

---

## Phase 2.5: QA Scope Assessment (REQUIRES USER CONFIRMATION)

This phase runs ONCE when Phase 2 completes. It delegates to the
`Dev10x:qa-scope` skill if available.

1. Invoke the Dev10x:qa-scope skill:
   ```
   Use the Skill tool: skill="Dev10x:qa-scope", args="{pr_number}"
   ```

   The Dev10x:qa-scope skill will:
   - Analyze the PR diff for QA risk (low/medium/high)
   - Check the project's e2e test directory for existing coverage
   - Present a QA assessment to the user via AskUserQuestion

2. Wait for the skill to complete before proceeding to Phase 3.

3. If Dev10x:qa-scope determines the change is low-risk (config-only,
   test-only, docs-only), it will skip ticket creation automatically.

**Note:** This phase only runs once per PR monitor session. If already
executed, skip directly to Phase 3.

---

## Phase 2.7: Re-review Notification (REQUIRES USER CONFIRMATION)

This phase runs when Phase 2 addressed review comments (i.e., at least
one reviewer requested changes and those changes have been pushed). Skip
if Phase 2 found no comments to address.

**Trigger:** PR had CHANGES_REQUESTED reviews AND fixup commits were
created to address them.

### Step 1: Identify reviewers who requested changes

```bash
gh pr view {pr_number} --json reviews \
  --jq '.reviews[] | select(.state=="CHANGES_REQUESTED") | .author.login'
```

### Step 2: Compose and format each notification

For each reviewer who requested changes, compose:
```
@{reviewer} please take another look
```

Format this as a Slack message suitable for posting.

### Step 3: Ask user for confirmation

Use `AskUserQuestion` showing the exact message that will be posted.

Options: "Post re-review notification" / "Skip".

### Step 4: Post the notification

If user approves, invoke `Skill("Dev10x:slack-review-request")` with the
composed message. The skill reads the project's Slack config and posts
to the configured channel.

Example invocation:
```
Skill("Dev10x:slack-review-request", args="--pr {pr_number} --repo {repo} --message '@{reviewer} please take another look'")
```

The Dev10x:slack-review-request skill will:
- Resolve the project's configured channel from userspace config
- Post the message to that channel
- Report the result back to the agent

---

## Phase 3: Notification (REQUIRES USER CONFIRMATION)

**CRITICAL: Do NOT post notifications without user confirmation.**

### Step 1: Prepare

Gather PR info, count open threads, verify readiness:

```bash
$HOME/.codex/skills/Dev10x-gh-pr-monitor/scripts/pr-notify.py \
  prepare --pr {pr_number} --repo {repo}
```

If `open_threads > 0`, return to Phase 2 to address them first.

*Why?* Reviewers should only be pinged when the PR is fully ready.

### Step 2: Ask user for confirmation

Use `AskUserQuestion`:
- Question: "PR #{pr_number} is ready for review. Post notification?"
- Show the formatted message from the prepare output
- Options: "Post notification" / "Skip notification"

### Step 3: Execute (if user approves)

If user approves, execute three delegated steps in sequence:

**Step 3a: Assign GitHub reviewers**

```
Skill("Dev10x:gh-pr-request-review", args="--pr {pr_number} --repo {repo}")
```

The Dev10x:gh-pr-request-review skill will:
- Read the project's GitHub config for default reviewers
- Assign them via `gh pr edit --add-reviewer`
- Report results back to the agent

**Step 3b: Post Slack review notification**

```
Skill("Dev10x:slack-review-request", args="--pr {pr_number} --repo {repo}")
```

The Dev10x:slack-review-request skill will:
- Read the project's Slack config (channel, mentions)
- Format the review notification message
- Post to the configured Slack channel
- Report results back to the agent

**Step 3c: Update PR checklist**

```bash
$HOME/.codex/skills/Dev10x-gh-pr-monitor/scripts/pr-notify.py \
  send --pr {pr_number} --repo {repo} \
  --skip-slack --skip-reviewers
```

This call runs checklist-only mode — no Slack posting, no reviewer
assignment (those were handled by the delegated skills above).

### Step 4: Execute (if user declines)

If user declines the notification, run checklist-only:

```bash
$HOME/.codex/skills/Dev10x-gh-pr-monitor/scripts/pr-notify.py \
  send --pr {pr_number} --repo {repo} \
  --skip-slack --skip-reviewers
```

### Step 5: Report final status

Report: CI status, comments addressed, notification sent/skipped, GitHub
reviewers assigned, Slack notification posted.

````

---

## Important Rules

- **Autonomous execution**: Phase 1 and Phase 2 run without asking the
  user. Phase 2.5 (QA) and Phase 3 (notification) need confirmation.
- **One fixup per comment**: Each review comment gets exactly one fixup
  commit.
- **Poll interval**: Wait 30 seconds between CI checks and comment checks.
- **Max CI retries**: If CI fails 5 times in a row on the same issue,
  stop and report the problem.
- **Never force push**: Always use regular `git push origin HEAD`.
- **Working directory**: Use `gh pr view {pr_number} --repo {repo}
  --json headRefName` to get the branch. Never hardcode a working
  directory — the PR branch may live in a different worktree.

---

## Integration with Other Skills

1. **Dev10x:gh-pr-create** — Use before this skill to create the draft PR
2. **Dev10x:ticket-jtbd** — Delegated to by the agent in Phase 0
3. **Dev10x:gh-pr-respond** — Delegated to by the agent for review comments (Phase 2)
4. **Dev10x:qa-scope** — Delegated to by the agent for QA risk assessment (Phase 2.5)
5. **Dev10x:gh-pr-request-review** — Delegated to by the agent in Phase 3 (GitHub reviewer assignment)
6. **Dev10x:slack-review-request** — Delegated to by the agent in Phase 2.7 and Phase 3 (Slack notifications)
7. **pr-notify.py** — Phase 3 helper script (checklist update only)

## Delegation Pattern

```
Dev10x-gh-pr-monitor (this skill — launches background agent)
    │
    └── Background Task Agent
        │
        ├── Phase 0: JTBD Job Story check
        │       ├── Fetch PR body, check first paragraph
        │       └── If missing → Skill("Dev10x:ticket-jtbd") to generate
        │
        ├── Phase 1: CI monitoring (handled directly by agent)
        │
        ├── Phase 2: Comment monitoring
        │       └── Skill("Dev10x:gh-pr-respond", args="{pr_url}") — batch mode
        │
        ├── Phase 2.5: QA scope assessment
        │       └── Skill("Dev10x:qa-scope")
        │
        ├── Phase 2.7: Re-review notification (after comments addressed)
        │       ├── AskUserQuestion → confirm notification
        │       └── Skill("Dev10x:slack-review-request") → post to Slack
        │
        └── Phase 3: Notification (initial review request)
                ├── AskUserQuestion → confirm message
                └── If approved, execute three delegated steps:
                    ├── Skill("Dev10x:gh-pr-request-review") → assign GitHub reviewers
                    ├── Skill("Dev10x:slack-review-request") → post Slack notification
                    └── pr-notify.py send (checklist-only mode)
```
