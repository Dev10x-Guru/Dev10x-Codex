---
name: Dev10x-work-on
description: Start work on any input — ticket URL, PR link, Slack thread, Sentry issue, or free text. Classifies inputs, gathers context in parallel, builds a supervisor-approved task list, and executes adaptively with pause/resume support.
---

# Dev10x:work-on — Adaptive Work Orchestrator

## Overview

This skill turns any combination of inputs into a structured,
supervisor-approved work plan. It runs in four phases:

1. **Parse & Classify** — identify what each input is
2. **Gather** — fetch context from all sources in parallel
3. **Plan** — build a task list for supervisor approval
4. **Execute** — work through tasks, expanding epics on demand

The supervisor sees progress via `TaskList`, can approve/edit
the plan, and can pause at any point with `Dev10x:session-wrap-up`.

**Rule: ALWAYS use `TaskCreate`** — even for single-task work.
The visible task list is the supervisor's interface for adding
new tasks mid-session. Skipping it removes that capability.

## Prerequisites

| Capability | Required for | Tool |
|------------|-------------|------|
| GitHub CLI | GitHub issues, PRs | `gh` CLI |
| Linear MCP | Linear tickets | `mcp__claude_ai_Linear__*` |
| JIRA | JIRA tickets | `Dev10x:jira` plugin + `JIRA_TENANT` env var + keyring |
| Sentry MCP | Sentry issues | `mcp__sentry__*` |
| Slack MCP | Slack threads | `mcp__claude_ai_Slack__*` |

Not all are required — only those matching the input types.

## When to Use

- User provides any combination of: ticket URL/ID, PR link, Slack
  thread, Sentry link, or free text description
- User wants to start structured work with progress tracking
- User wants comprehensive context before starting

---

## Phase 1: Parse & Classify

Accept the user's arguments as a space-separated list. Each
argument is classified independently:

| Pattern | Type | Action |
|---------|------|--------|
| `https://github.com/.../issues/N` | `github-issue` | Extract repo + issue number |
| `https://github.com/.../pull/N` | `github-pr` | Extract repo + PR number |
| `https://linear.app/.../issue/XXX-N/...` | `linear-ticket` | Extract ticket ID (e.g., `TEAM-133`) |
| `https://.*slack.com/archives/C.../p...` | `slack-thread` | Store channel + timestamp |
| `https://sentry.io/.../issues/N` | `sentry-issue` | Extract issue ID |
| `https://*.sentry.io/issues/N` | `sentry-issue` | Extract issue ID |
| `https://...atlassian.net/browse/XX-N` | `jira-ticket` | Extract ticket ID |
| `GH-N` | `github-issue` | Route to `detect-tracker.sh` |
| `TEAM-N` (Linear prefix) | `linear-ticket` | Route to `detect-tracker.sh` |
| `JIRA-N` | `jira-ticket` | Route to `detect-tracker.sh` |
| `#N` (bare number) | `github-pr` | Resolve against current repo |
| Anything else | `note` | Store as free-text context |

For ticket IDs, run the tracker detector (from `Dev10x:gh` skill):
```bash
$HOME/.codex/skills/gh/scripts/detect-tracker.sh "$TICKET_ID"
```
Parse `TRACKER`, `TICKET_NUMBER`, and `FIXES_URL` from output.

Each classified input becomes a **source** entry with its type and
extracted identifiers. Collect all sources into a list for Phase 2.

---

## Phase 2: Gather (Quick & Parallel)

Fetch context from all sources **in parallel** — no supervisor
interaction needed. Use parallel tool calls or Agent subagents.

### Fetch Dispatch

| Source type | Fetch method |
|-------------|-------------|
| `github-issue` | `Dev10x:gh` script: `gh-issue-get.sh "$NUMBER" "$REPO"` |
| `github-pr` | `gh pr view $NUMBER --repo $REPO --json title,body,headRefName,state,mergedAt,reviews` |
| `linear-ticket` | `mcp__claude_ai_Linear__get_issue(issueId: "$ID")` — extract title, body, parent, relations, comments |
| `jira-ticket` | `Dev10x:jira` script: `jira-get.sh "$ID"` |
| `slack-thread` | `mcp__claude_ai_Slack__slack_read_thread(channelId, threadTs)` |
| `sentry-issue` | `mcp__sentry__get_issue_details(issueId)` — extract error, frequency, stack trace |
| `note` | No fetch needed — pass through |

### Cross-Reference Expansion (One Level)

After the initial fetch, scan all gathered text for references
to other sources. Add them to the sources list and fetch:

- **PR body** mentions `Fixes: GH-N` or `Fixes: TEAM-N` → fetch that ticket
- **Ticket body** contains Sentry URL → fetch that Sentry issue
- **Ticket body** mentions PR `#N` or branch name → fetch that PR
- **Linear ticket** has parent or relations → fetch related tickets
- **Ticket comments** contain any of the above patterns → fetch

Do NOT expand beyond one level — keep the gathering phase fast.

### Output: Context Summary

Present a structured summary of everything gathered:

```markdown
## Context Summary

### Sources (N gathered)
- [github-issue] GH-15: Title here (OPEN)
- [slack-thread] #channel-name: 5 messages
- [sentry-issue] #12345: ErrorType — 145 events in 7 days
- [note] "check the retry logic"

### Cross-References Found
- [sentry-issue] #67890 (from ticket body)
- [github-pr] #42: PR title (merged)

### Key Details
[Brief synthesis: what the work is about, who reported it,
severity if applicable, related context from Slack/Sentry]
```

---

## Phase 3: Plan (Lightweight Steps)

Build a **high-level task list** using `TaskCreate`. **This is
mandatory** — always create at least one task, even when the work
seems trivial. The task list is the supervisor's interface for
tracking progress and adding new tasks during the session.

The plan is adapted based on what was gathered — not a fixed
template.

### Step Types

- **Detailed** — small, immediately executable (2-5 min).
  Created with `metadata: {"type": "detailed"}`.
- **Epic** — placeholder for a phase expanded when reached.
  Created with `metadata: {"type": "epic"}`. Description says
  what the phase accomplishes, not how.

### Generating the Plan

Examine the gathered context and construct a task list. Use these
heuristics to decide which tasks to include:

**Always include (if a ticket was found):**
- Set up workspace (branch or worktree) — detailed
- Draft Job Story — detailed

**Include based on context:**

| Context signal | Tasks to add |
|---------------|-------------|
| Ticket with implementation work | Design approach (epic), Implement (epic), Verify (epic) |
| Sentry issue found | Reproduce issue (detailed), Investigate root cause (epic) |
| PR already exists | Fetch PR context (detailed), Address review comments (epic) |
| Multiple related tickets | Synthesize requirements (detailed) |
| Slack thread with discussion | Summarize key decisions (detailed) |

**Always include at the end:**
- Create PR & ensure CI passes — epic
- Self-review & request human review — epic
- Verify acceptance criteria — detailed (see below)

### Acceptance Criteria Verification

The **last task** in every plan verifies the work is shippable
or ready for handover. Read the acceptance criteria YAML file:

```
$HOME/.codex/projects/<project>/memory/acceptance-criteria.yaml
```

**Determine the work type** from the gathered context:

| Context | Work type |
|---------|-----------|
| Ticket with implementation | `feature` |
| Sentry/bug ticket | `bugfix` |
| PR with review comments | `pr-continuation` |
| No ticket, no PR | `local-only` |
| Sentry/Slack only, no fix planned | `investigation` |

**YAML schema:**

```yaml
# acceptance-criteria.yaml
defaults:
  feature:
    criteria: "PR approved, CI passes, ready to merge"
  bugfix:
    criteria: "PR approved, CI passes, regression covered"
  pr-continuation:
    criteria: "Re-review requested, CI green"
  local-only:
    criteria: "Changes verified locally"
  investigation:
    criteria: "Findings documented, next steps clear"
overrides: {}  # populated when user persists a choice
```

**If the file is absent** on first use, use the hardcoded
defaults above — do not fail or skip the verification step.
Create the file only when the user persists a non-default
choice.

**Resolve criteria** in this order:
1. Check `overrides` for a matching `work_type` with
   `persist: false` — use if found, then **remove** the entry
2. Check `overrides` for a matching `work_type` with
   `persist: true` — use if found
3. Fall back to `defaults[work_type].criteria` from the file
4. If the file is absent or the work type has no entry, use
   the hardcoded defaults above

**Present the criteria** when building the plan. Show the
resolved criteria in the final task description. If the user
has persistent overrides from past sessions, present them
as choices alongside the default:

```
Acceptance criteria for this feature work:
- PR is approved, CI passes, ready to merge (Default)
- PR created and CI green, skip review (Your past choice)
- Different criteria this time
```

If the user picks a non-default option, ask whether to
persist it (`AskUserQuestion` with "Always" / "Just this
time"). Update the YAML file accordingly:
- `persist: true` → add to `overrides` for future sessions
- `persist: false` → add with `persist: false`; the skill
  removes consumed one-time overrides after use

### Example Plans

**Feature from ticket:**
```
1. [detailed] Set up workspace (branch, worktree)
2. [detailed] Draft Job Story
3. [epic]     Design implementation approach
4. [epic]     Implement changes
5. [epic]     Verify (tests, lint)
6. [epic]     Create PR & ensure CI passes
7. [epic]     Self-review & request human review
8. [detailed] Verify acceptance criteria met
```

**Bug fix from Sentry + ticket:**
```
1. [detailed] Set up workspace
2. [detailed] Reproduce the issue locally
3. [epic]     Investigate root cause
4. [epic]     Implement fix
5. [epic]     Verify fix (tests, regression)
6. [epic]     Create PR & ensure CI passes
7. [epic]     Self-review & request human review
8. [detailed] Verify acceptance criteria met
```

**PR continuation:**
```
1. [detailed] Fetch PR and review context
2. [epic]     Address review comments
3. [epic]     Verify changes pass CI
4. [epic]     Self-review & request human review
5. [detailed] Verify acceptance criteria met
```

**Local-only work (no ticket, no PR):**
```
1. [detailed] Summarize the work from gathered context
2. [epic]     Implement changes
3. [epic]     Verify
4. [detailed] Decide: create ticket, create PR, or done
5. [epic]     Self-review & request human review (if PR created)
6. [detailed] Verify acceptance criteria met
```

### Supervisor Approval Gate

Present the plan as a numbered list.

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).

1. `AskUserQuestion(questions=[{question: "How would you like to proceed with the work plan?", header: "Plan", options: [{label: "Approve (Recommended)", description: "Start execution immediately"}, {label: "Edit", description: "Describe what to change (add/remove/reorder steps)"}], multiSelect: false}])`

After approval, set task dependencies where appropriate (use
`TaskUpdate` with `addBlockedBy`). Mark the first task as
`in_progress` and begin Phase 4.

---

## Phase 4: Execute (Adaptive, Auto-Advance)

Work through the approved task list. Update task status via
`TaskUpdate` as work progresses.

### Auto-Advance Rule

**Complete a task → immediately start the next.** Do not pause
between tasks to ask "should I continue?" or wait for the user
to say "go" / "next" / "continue". The approved plan is the
authorization to proceed.

**Only pause for genuine decisions** — A/B choices where the
user's preference is unknown and cannot be inferred from
context. Routine confirmations are not decisions.

**If blocked on the current task** (waiting for user input,
external dependency, CI), check whether the next unblocked
task can start. Examples:
- Waiting for CI? Start self-review in parallel.
- Waiting for user input on approach? Create the branch or
  draft the Job Story meanwhile.
- Stuck on a sub-task? Mark it `pending` with a note and
  advance to the next unblocked task in the list.

Return to the blocked task once the blocker resolves.

### Executing Detailed Tasks

Run the task directly. Common detailed tasks delegate to skills:

| Task | Delegated to |
|------|-------------|
| Set up workspace (branch) | `Dev10x:ticket-branch` skill |
| Set up workspace (worktree) | `Dev10x:git-worktree` skill |
| Draft Job Story | `Dev10x:jtbd` skill (attended mode) |
| Update ticket status | Linear MCP (see references/team-info.md) |
| Fetch PR context | `gh pr view` + `gh pr diff` |
| Create PR | `Dev10x:gh-pr-create` skill |
| Monitor CI | `Dev10x:gh-pr-monitor` skill |

After completing a detailed task, mark it `completed` via
`TaskUpdate` and move to the next task.

### Expanding Epic Tasks

When reaching an epic task:

1. **Read the epic description** and the gathered context
2. **Generate sub-tasks** — break the epic into detailed steps.
   This may involve:
   - Reading code to understand scope
   - `AskUserQuestion` for A/B decisions (e.g., "approach X
     vs approach Y?") — but only when the choice genuinely
     cannot be inferred from context
   - Follow-up information gathering
3. **Present sub-tasks** briefly (inline, not a new approval
   gate) and begin executing immediately. Only ask for
   approval if the expansion reveals unexpected scope or
   trade-offs the supervisor should weigh in on.
4. **Check for parallelism** — if sub-tasks are independent,
   ask the supervisor before launching parallel agents
5. **Execute sub-tasks**, marking each completed as they finish.
   Auto-advance between sub-tasks (same rule as top-level).
6. **Mark the epic completed** when all sub-tasks are done

### Parallelism Policy

| Phase | Parallelism | Approval needed? |
|-------|------------|-----------------|
| Phase 2 (Gather) | Auto-parallel | No |
| Phase 4 (detailed tasks) | Sequential | No |
| Phase 4 (epic sub-tasks) | Parallel if independent | Yes — ask supervisor |

When asking about parallelism, present which tasks would run
concurrently and why they're independent:

```
Tasks 4a and 4b are independent (different files, no shared state).
Run them in parallel?
- Yes, launch parallel agents (Recommended)
- No, run sequentially
```

### Skill Delegation During Execution

**Workspace setup:**
- If in main repo (`.git` is directory): offer "Work here" or
  "New worktree" via `AskUserQuestion`
- If in worktree (`.git` is file): offer "Work here" or
  "New worktree"
- For worktree path: compute branch name, invoke `Dev10x:git-worktree`
  skill. Do NOT invoke `Dev10x:ticket-branch` first — `Dev10x:git-worktree`
  creates the branch internally; calling `Dev10x:ticket-branch` first
  creates a duplicate branch in the main repo.
- For work-here path: delegate to `Dev10x:ticket-branch` skill

**Job Story drafting:**
- MUST invoke `Skill(Dev10x:jtbd)` explicitly — never draft inline
- Pass gathered context to avoid redundant API calls
- If approved, write back to the ticket:

| Tracker | Write-back |
|---------|-----------|
| GitHub | `gh issue comment` |
| Linear | Prepend to description via `save_issue` |
| JIRA | `jira-update.sh` |

**Ticket status update (Linear only):**
1. Get statuses: `list_issue_statuses(teamId)` from
   references/team-info.md
2. Find "In Progress" (type `started`)
3. Update: `save_issue(id, stateId)`
4. Skip if already "In Progress"; warn if "Done"/"Canceled"

---

## Pause/Resume

At any pause signal ("wrap up", "pause", "that's enough for
today", end-of-session):

1. Invoke `Dev10x:session-wrap-up` — it reads `TaskList` and discovers all
   open tasks automatically
2. `Dev10x:session-wrap-up` handles routing each open item (PR bookmark,
   TODO.md, Slack DM, etc.)
3. The task list itself serves as resume context — when the user
   resumes work, they can invoke `Dev10x:discover` to find deferred
   items and `Dev10x:tasks` to see the saved task list

No custom bookmarking needed — leverage existing `Dev10x:session-wrap-up`
and `Dev10x:park` infrastructure.

---

## Important Notes

- **Always create tasks via `TaskCreate`** — never skip the task
  list, even for single-step work. The supervisor uses it to add
  new tasks mid-session.
- Always verify ticket exists before creating a branch
- If ticket is "Done"/"Canceled" (Linear) or "closed" (GitHub),
  warn the user before proceeding
- Handle errors gracefully — if a fetch fails, continue with
  what was gathered and note the failure in the context summary
- Linear team UUID is in `references/team-info.md` (template)
- After completing work, use `Dev10x:gh-pr-create` to create the PR
- Do not modify ticket description or add comments unless the
  user explicitly approves (e.g., Job Story write-back)

## Resources

### references/team-info.md

Linear team configuration template: UUID, status mappings,
branch naming, Sentry integration patterns.

---

## Examples

### Example 1: Single Ticket URL

**User:** `Dev10x-work-on https://github.com/org/repo/issues/15`

**Phase 1:** Classify → `github-issue`, repo=`org/repo`, number=15

**Phase 2:** Fetch issue. Body mentions Sentry URL → fetch Sentry
issue. Body mentions PR #42 → fetch PR. Produce context summary.

**Phase 3:** Build plan:
```
1. [detailed] Set up workspace
2. [detailed] Draft Job Story
3. [epic]     Design implementation approach
4. [epic]     Implement changes
5. [epic]     Verify
6. [epic]     Create PR & ensure CI passes
7. [epic]     Self-review & request human review
8. [detailed] Verify acceptance criteria met
```
Supervisor approves.

**Phase 4:** Auto-advance through tasks 1-8, expanding epics
as reached. No pauses between tasks unless a genuine decision
is needed.

### Example 2: Multiple Inputs

**User:** `Dev10x-work-on TEAM-133 https://slack.com/archives/C123/p456 "check the retry logic"`

**Phase 1:** Classify →
- `linear-ticket` TEAM-133
- `slack-thread` C123/p456
- `note` "check the retry logic"

**Phase 2:** Fetch all three in parallel. Linear ticket links to
Sentry issue → fetch that too. Produce context summary with 4
sources.

**Phase 3:** Build plan (adapted — Sentry issue means
"Reproduce" task added):
```
1. [detailed] Set up workspace
2. [detailed] Reproduce the Sentry error locally
3. [detailed] Draft Job Story
4. [epic]     Investigate root cause
5. [epic]     Implement fix
6. [epic]     Verify fix
7. [epic]     Create PR & ensure CI passes
8. [epic]     Self-review & request human review
9. [detailed] Verify acceptance criteria met
```

### Example 3: PR Continuation

**User:** `Dev10x-work-on https://github.com/org/repo/pull/42`

**Phase 1:** Classify → `github-pr`, number=42

**Phase 2:** Fetch PR. Body has `Fixes: GH-15` → fetch issue.
PR has 3 review comments → note them.

**Phase 3:** Build plan:
```
1. [detailed] Fetch review comments and understand feedback
2. [epic]     Address review comments
3. [epic]     Verify CI passes
4. [epic]     Self-review & request human review
5. [detailed] Verify acceptance criteria met
```

### Example 4: Mid-Workflow Pause

User is at task 4 of 7 and says "let's wrap up for today".

1. Skill detects pause signal
2. Invokes `Dev10x:session-wrap-up`
3. `Dev10x:session-wrap-up` reads `TaskList` — sees 3 pending tasks
4. Routes each via `Dev10x:park` (e.g., PR bookmark, TODO.md)
5. Session ends with bookmark saved

Next session: user runs `Dev10x:discover` to find bookmarks and
resume where they left off.
