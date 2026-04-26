---
name: Dev10x:gh-pr-respond
description: >
  Validate and respond to PR review comments. Handles single comment
  (with follow-up offer) or batch mode for all unaddressed comments on
  a PR/review. Orchestrates Dev10x:gh-pr-triage and Dev10x:gh-pr-fixup.
  TRIGGER when: PR has review comments that need responses or fixes.
  DO NOT TRIGGER when: no review comments exist, or user wants to
  create a new PR (use Dev10x:gh-pr-create).
user-invocable: true
invocation-name: Dev10x:gh-pr-respond
allowed-tools:
  - AskUserQuestion
  - mcp__plugin_Dev10x_cli__pr_comment_reply
  - Bash(gh:*)
  - Skill(Dev10x:gh-pr-triage)
  - Skill(Dev10x:gh-pr-fixup)
  - Skill(Dev10x:git-groom)
  - Skill(Dev10x:gh-pr-monitor)
  - Skill(Dev10x:git)
  - Skill(Dev10x:gh-pr-merge)
---

# Respond to PR Review Comments

## Orchestration

This skill follows `references/task-orchestration.md` patterns.

**Auto-advance:** Complete each step, immediately start the next.
Never pause to ask "should I continue?" between steps.

**REQUIRED: Create tasks before ANY work.** Execute these
`TaskCreate` calls at startup based on the detected mode:

**Mode A (single):**
1. `TaskCreate(subject="Process comment r{id}", activeForm="Processing comment")`
2. `TaskCreate(subject="Hide obsolete comment", activeForm="Hiding comment")`
3. `TaskCreate(subject="Check remaining comments", activeForm="Checking remaining")`

**Mode B (batch):**
1. `TaskCreate(subject="Collect unaddressed comments", activeForm="Collecting comments")`
2. `TaskCreate(subject=f"Triage {N} comments", activeForm="Triaging comments")`
3. `TaskCreate(subject="Get user approval", activeForm="Awaiting approval")`
4. `TaskCreate(subject="Execute approved responses", activeForm="Executing responses")`
5. `TaskCreate(subject="Resolve threads", activeForm="Resolving threads")`
6. `TaskCreate(subject="Hide obsolete comments", activeForm="Hiding comments")`
7. `TaskCreate(subject="Summary", activeForm="Summarizing")`

Set dependencies and update status as each completes.

**Nested-mode exemption:** When invoked as a nested skill within
a parent orchestrator (e.g., via `Skill()` from `Dev10x:work-on`),
startup task creation is optional — at most 1 summary task. See
`references/task-orchestration.md` § Delegated Invocation Exception.

**Parallel triage (Mode B Step 2):** Dispatch up to 4 triage
subagents concurrently to reduce processing time. Each subagent
receives only its comment context and returns verdict + draft
reply.

**Batched decisions:** Thread resolution decisions are queued
and presented as a batch after all responses are posted.

## Playbook

This skill is playbook-powered. The workflow steps are defined in
`references/playbook.yaml` with two plays: `single` (Mode A) and
`batch` (Mode B).

**Loading order** (see `references/config-resolution.md`):
1. `.claude/Dev10x/playbooks/gh-pr-respond.yaml` (project-local)
2. `~/.claude/memory/Dev10x/playbooks/gh-pr-respond.yaml` (global + repo match)
3. `~/.claude/projects/<project>/memory/playbooks/gh-pr-respond.yaml` (legacy)
4. `${CLAUDE_PLUGIN_ROOT}/skills/gh-pr-respond/references/playbook.yaml`

Customize with `/Dev10x:playbook edit gh-pr-respond <play>`.

## Decision Gates

This skill has 6 **blocking decision gates** where execution
MUST pause for user input via the `AskUserQuestion` tool.

**Plain text questions are NOT acceptable** — they don't block
execution, don't provide clickable options, and break the
structured decision flow the user relies on.

Gates numbered by insertion order; execution order differs by mode.

| # | Location | Purpose |
|---|----------|---------|
| 1 | Mode A, Step 1b | Confirm thread resolution |
| 2 | Mode A, Step 3 | Continue / batch / stop |
| 3 | Mode B, Step 3 | Approve / review / skip batch |
| 4 | Mode B, Step 5 | Resolve threads confirmation |
| 5 | Post-Response Continuation | Groom + push + monitor / Push only / Stop |
| 6 | Mode B, Step 5b / Mode A, Step 1c | Hide obsolete comments |

Each gate is marked with **REQUIRED: `AskUserQuestion`** in the
step description. If you see that marker, you MUST call the
`AskUserQuestion` tool — never substitute with inline text.

**Compaction-safe gate checklist** — re-inject after compaction:

1. Gate 1 (thread resolution): `AskUserQuestion` — MANDATORY
2. Gate 2 (continue/batch/stop): `AskUserQuestion` — MANDATORY
3. Gate 3 (approve batch): `AskUserQuestion` — MANDATORY
4. Gate 4 (resolve threads): `AskUserQuestion` — MANDATORY
5. Gate 5 (shipping pipeline): `AskUserQuestion` — MANDATORY
6. Gate 6 (hide comments): `AskUserQuestion` — MANDATORY
7. VALID comments: `Skill(Dev10x:gh-pr-fixup)` — NEVER inline,
   invoke immediately after triage verdict (no pause, no report)
8. Triage: `Skill(Dev10x:gh-pr-triage)` — NEVER inline, even
   for "obviously invalid" or bot-generated comments (GH-463)
9. Pre-action checkpoint: BEFORE any `Edit` or `git commit` on
   a reviewed file, verify a `Skill()` call preceded it
10. Merge: `Skill(Dev10x:gh-pr-merge)` — NEVER inline
    `gh pr merge` (GH-759 F3)

## Overview

This skill handles PR review comments end-to-end in two modes:

1. **Single comment mode** — Given a specific comment URL, process that one
   comment, then check for remaining unaddressed comments and offer to continue.
2. **Batch mode** — Given a PR URL or review URL, collect all unaddressed
   comments, triage them, and present a response plan for user approval.

Sub-skills:
- **`Dev10x:gh-pr-triage`** — Validate the comment against the codebase
- **`Dev10x:gh-pr-fixup`** — Implement the fix if the comment is valid

```
Dev10x:gh-pr-respond (this skill)
    ├── Dev10x:gh-pr-triage         → validate, reply if invalid (never auto-resolves)
    ├── resolve gate      → ask user to confirm thread resolution
    └── Dev10x:gh-pr-fixup  → implement fix, fixup commit, reply with ref
         └── Dev10x:git-fixup → create the fixup! commit
```

## Critical: Delegation is Mandatory

**Never manually implement a fix and post a reply via `gh api`
or MCP tool for VALID comments.** Always delegate the entire
lifecycle to `Dev10x:gh-pr-fixup` via `Skill()`, even if the
fix is trivial or already committed. The delegation is about
the *workflow boundary*, not just the code change — `gh-pr-fixup`
ensures atomic push+reply, proper fixup commit format, and
consistent thread management.

Similarly, never triage comments inline — always delegate to
`Dev10x:gh-pr-triage` via `Skill()`. Never run raw `git rebase`,
`git push`, or `gh pr checks --watch` — delegate to
`Dev10x:git-groom`, `Dev10x:git`, and `Dev10x:gh-pr-monitor`
respectively.

**Post-step self-check:** Before marking any VALID comment as
processed, verify that `Skill(Dev10x:gh-pr-fixup)` was called
for it — not `Edit` + `git commit` + `gh api`. If you used
raw commands instead of `Skill()`, STOP and redo the step with
proper delegation. Audit sessions show 3 of 4 invocations
bypass delegation under context pressure (GH-444).

**Pre-action intervention checkpoint:** If you are about to call
`Edit` on a file mentioned in a review comment, or about to run
`git commit`, STOP and ask yourself: "Did I invoke `Skill()`
for this?" If the answer is no, you are bypassing delegation.
The correct sequence is ALWAYS:
1. `Skill(Dev10x:gh-pr-triage)` → verdict
2. If VALID: `Skill(Dev10x:gh-pr-fixup)` → fix + commit + reply
3. Never: `Edit` → `git commit` → `gh api` (this is the bypass)

**Anti-pattern: "Stated-but-not-executed" bypass (GH-458).**
The most common bypass is acknowledging the delegation requirement
in your reasoning ("I need to call Skill(Dev10x:gh-pr-fixup)")
then proceeding to implement the fix inline anyway. Three audit
sessions caught this exact pattern — the agent says it will
delegate, then does the work itself. Stating intent is not
execution. Only a `Skill()` tool call counts as delegation.

## Preamble: Branch Location Check

Before processing comments, verify the PR branch is accessible
from the current working directory. In multi-worktree setups, the
PR branch may live in a different worktree than the active CWD.

**Step 0: Ensure worktree tool availability.**
Call `ToolSearch("select:EnterWorktree")` before any worktree
detection. If unavailable, warn and stop — do NOT silently fall
back to `git -C` (GH-759 F1). The `git -C` fallback cascades
across nested skills, breaking allow-rule matching.

1. Extract the PR branch name:
   ```bash
   gh pr view {pr_number} --repo {owner}/{repo} --json headRefName -q .headRefName
   ```
2. Check if the branch is checked out in the current worktree:
   ```bash
   git symbolic-ref --short HEAD
   ```
3. If the current branch does NOT match the PR branch:
   - Check `git worktree list` for the PR branch
   - If found in another worktree, use `EnterWorktree` to
     switch context. Do NOT use `git -C` as a workaround.
   - If not found anywhere, check it out:
     `git checkout {branch}`

This prevents wasted turns from file-not-found errors when
the agent reads files that exist only on the PR branch.

## Input Detection

Parse the input URL to determine the mode:

| Input pattern | Mode | Example |
|---|---|---|
| `...pull/123#discussion_r456` | Single | Specific comment URL |
| `...pull/123#pullrequestreview-789` | Batch (review) | All comments from that review |
| `...pull/123` | Batch (PR) | All unaddressed comments on PR |
| PR number only (e.g., `1164`) | Batch (PR) | All unaddressed comments on PR |

Extract `{owner}`, `{repo}`, `{pr_number}`, and optionally `{comment_id}`
or `{review_id}` from the URL.

**Optional additional context:**
- User may provide extra context after the URL
- Example: `/Dev10x:gh-pr-respond https://...#discussion_r456 Note that PR #1135 is merged`

---

## Mode A: Single Comment

**Trigger:** Input contains `#discussion_r{comment_id}`

### Step 1: Process the comment

**REQUIRED: Call `Skill(Dev10x:gh-pr-triage)`** — never triage
inline. Pass the comment URL (and any additional context).

**Per-comment enforcement (GH-463, GH-502):** This delegation
is mandatory for EVERY comment, including ones that appear
"obviously invalid" (e.g., bot-generated comments, trivially
wrong suggestions). The agent MUST NOT read the comment, judge
it inline, and post a reply directly. Even if you can determine
the verdict in 2 seconds, call `Skill(Dev10x:gh-pr-triage)` —
it ensures consistent reply format, audit trail, and workflow
state tracking. Three audit sessions (GH-463, GH-458, GH-502)
show the bypass happens when the agent rationalizes inline
triage as "equivalent" to skill delegation under context
pressure. It is not equivalent.

**Mandatory triage assertion (GH-502):** After processing each
comment, output this self-check before proceeding:

```
TRIAGE CHECK: comment r{id}
  Skill(Dev10x:gh-pr-triage) called: YES/NO
  Verdict: VALID/INVALID/QUESTION/OUT_OF_SCOPE
  If NO → STOP. Re-do with Skill() delegation.
```

If you cannot fill in "YES" for the Skill call, you have
bypassed delegation. Do not proceed — re-invoke the skill.

**Exception — author-confirmed validity:** If the PR author has
already replied to the comment explicitly acknowledging it as valid
(e.g., "good catch", "you're right", "will fix"), you MAY skip
triage and proceed directly to `Skill(Dev10x:gh-pr-fixup)` with
verdict `VALID`. This avoids redundant validation when the author
has already confirmed the comment warrants a fix. The skip applies
only when the author's reply is unambiguous — if there is any doubt,
delegate to triage as normal.

`Dev10x:gh-pr-triage` returns a verdict: `VALID`, `INVALID`, `QUESTION`, or `OUT_OF_SCOPE`.

- If **VALID** → **REQUIRED: Call `Skill(Dev10x:gh-pr-fixup)`
  immediately in the same turn** — do NOT report the verdict and
  wait for user input. The triage-to-fixup transition is atomic:
  verdict received → `Skill()` invoked, no pause between. Never
  implement fixes manually or post replies via raw `gh api`.
  The fixup skill handles the entire lifecycle: fix, commit, push,
  and reply.
- If **not VALID** → `Dev10x:gh-pr-triage` has posted a reply but has NOT resolved the
  thread. Ask the user whether to resolve it (see Step 1b).

### Step 1b: Confirm thread resolution (non-VALID only)

When `Dev10x:gh-pr-triage` returns INVALID, QUESTION, or OUT_OF_SCOPE, present the
verdict and reason to the user and ask for confirmation before resolving:

```
Comment r{comment_id} on {path}:{line}:
  Verdict: {verdict}
  Reason: {reason}
  Reply posted: ✅

Resolve this thread?
```

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
This blocks execution until the user responds. Options:
- **"Resolve"** — Resolve the thread via GraphQL
- **"Leave open"** — Keep the thread open (reply already posted)

### Step 1c: Hide obsolete comment (optional)

If the thread was resolved in Step 1b, offer to minimize the root
comment to reduce PR conversation noise:

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
Options:
- **"Hide"** — Minimize the comment via GraphQL `minimizeComment`
  with classifier `OUTDATED`
- **"Skip"** — Leave the comment visible

**Skip this gate** if the thread was left open in Step 1b.

When hiding, use the comment's `node_id` (not numeric `id`).
Write the GraphQL mutation to a temp file and reference it with
`-F query=@file` to avoid shell quoting issues with `$` variables:
```bash
# Write mutation to temp file (use mcp__plugin_Dev10x_cli__mktmp)
# Then invoke:
gh api graphql -F query=@/tmp/claude/gh/minimize.graphql \
  -f id='{node_id}' -f classifier='OUTDATED'
```

See `references/github_api.md` § Hiding (Minimizing) Comments.

### Step 2: Check for remaining comments

After processing the single comment, check for other unaddressed root comments:

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  | jq '[.[] | select(.in_reply_to_id == null)]'
```

### Step 3: Offer to continue

If unaddressed comments remain, present them to the user:

```
Processed comment r{comment_id} → {verdict}

{N} unaddressed comment(s) remaining:
1. {author} on {path}:{line} — "{first_line_of_body}"
2. {author} on {path}:{line} — "{first_line_of_body}"

Continue to the next one?
```

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
This blocks execution until the user decides how to proceed. Options:
- **"Next comment"** — Process the next unaddressed comment (loop back to Step 1)
- **"Switch to batch mode"** — Triage all remaining and present a plan (jump to Mode B Step 2)
- **"Stop"** — End

---

## Mode B: Batch (PR or Review)

**Trigger:** Input is a PR URL, review URL, or PR number (no `#discussion_r`)

### Step 1: Collect unaddressed comments

**For a PR URL or number:**
```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  | jq '[.[] | select(.in_reply_to_id == null)]'
```

**For a review URL** (`#pullrequestreview-{review_id}`):
Filter to only comments from that review (match `pull_request_review_id`).

**Always check the review body for findings**, even when inline
comments exist. CI hygiene reviews from `claude[bot]` commonly
produce body-only findings, and inline threads may already be
resolved while the body contains unaddressed items.

**Body-only review handling:**

1. Extract the review body via
   `gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews`
   filtered by `review_id` (or scan all reviews if no review ID)
2. **Parse individual findings** from the body. Findings are
   identified by these patterns:
   - Bullet points starting with severity markers:
     `CRITICAL:`, `BLOCKING:`, `INFO:`, `WARNING:`, `NIT:`
   - Numbered items (`1.`, `2.`, etc.) with file:line references
   - Markdown list items (`- ` or `* `) that reference specific
     code locations (e.g., `mutations.py:115`)
   - Bold-prefixed items (`**[BLOCKING]**`, `**[INFO]**`)
3. Create one **synthetic comment** per parsed finding. Each
   synthetic comment carries:
   - `body`: the finding text (one bullet/item)
   - `path`: extracted file path (if present in the finding)
   - `line`: extracted line number (if present)
   - `review_id`: the parent review ID
   - `is_body_finding`: `true` (distinguishes from inline comments)
4. If the body contains no parseable findings but has non-empty
   text, treat the entire body as a single synthetic comment
   (fallback for unstructured review bodies)
5. Merge synthetic comments with any inline comments collected
   above, then continue to Step 2 (triage)

**Replying to body findings:** Since body findings have no inline
comment thread, replies are posted as top-level PR comments via:
```bash
gh api --method POST \
  repos/{owner}/{repo}/issues/{pr_number}/comments \
  -f body="Re: {finding_summary}\n\n{reply}"
```

If no inline comments AND no review body findings found → report
"No unaddressed comments" and stop.

### Step 2: Triage all comments (parallel)

Mark phase transition: `TaskUpdate(taskId=triage_task, status="in_progress")`

**REQUIRED: Dispatch parallel triage subagents.** Do NOT triage
comments sequentially in the main thread. Execute these steps:

1. Group comments into batches of up to 4
2. For each batch, dispatch all subagents in a **single tool-call
   block** using `Agent()` with `run_in_background=true`
3. Each subagent receives only its comment context (file, line,
   body, surrounding code) and returns: verdict, reason (1
   sentence), draft reply (2-3 sentences)
4. Collect results as notifications arrive
5. If more than 4 comments, dispatch the next batch as agents
   complete

**DO NOT SKIP parallel dispatch.** Sequential inline triage
defeats the purpose of this step — it increases processing time
linearly and blocks the main thread. Even for 2 comments, use
parallel agents. Each subagent MUST invoke
`Skill(Dev10x:gh-pr-triage)` — never inline the triage logic
within the subagent prompt itself (GH-502).

**Mandatory delegation in subagent prompt (GH-759 F2):**
Include this instruction in every triage subagent prompt:
"You MUST invoke `Skill(Dev10x:gh-pr-triage)` with the
comment URL. Never investigate inline or post replies
directly." Without this explicit instruction, subagents
bypass the skill and triage inline — 3 of 3 subagents
did so in the session that produced this finding.

Mark phase transition: `TaskUpdate(taskId=triage_task, status="completed")`

Present the full plan to the user as a table:

```
Found {N} unaddressed comments on PR #{pr_number}:

| # | Author | File:Line | Summary | Verdict | Proposed Response |
|---|--------|-----------|---------|---------|-------------------|
| 1 | mike   | sender.py:19 | Use SubFactory | VALID | Change LazyFunction → SubFactory |
| 2 | mike   | fakers.py:21 | Randomize values | VALID | Use Faker() for all fields |
| 3 | claude[bot] | dto.py:5 | TYPE_CHECKING | INVALID | 38+ files use this pattern |
| 4 | claude[bot] | tasks.py:12 | Missing type ann | INVALID | mypy infers from assignment |

Approve all, or specify which to modify/skip?
```

### Step 3: Get user approval

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
This blocks execution until the user approves the batch plan. Options:
- **"Approve all"** — Execute all proposed responses
- **"Review one-by-one"** — Present each for individual approval (like Mode A)
- **"Skip"** — Cancel batch

The user may also provide corrections in free text (e.g., "Comment 2 is not
valid, we use DataclassField" or "Comment 4: make it a question to the
reviewer").

### Step 4: Execute approved responses

Mark phase transition: `TaskUpdate(taskId=execute_task, status="in_progress")`

For each approved comment:

- **VALID** → **REQUIRED: Call `Skill(Dev10x:gh-pr-fixup)`
  immediately after verdict** — do NOT report the verdict and
  wait for user input between comments. The triage-to-fixup
  transition is atomic: verdict received → `Skill()` invoked,
  no pause. Never manually implement fixes or post replies via
  raw commands. The fixup skill handles the entire lifecycle
  (one fixup commit per comment).
- **INVALID / QUESTION / OUT_OF_SCOPE** → post reply using MCP tool:
  ```
  mcp__plugin_Dev10x_cli__pr_comment_reply(
      pr_number={pr_number},
      comment_id={id},
      body="{reply}"
  )
  ```
  Do **NOT** resolve the thread automatically.

Report progress after each comment is processed.

Mark phase transition: `TaskUpdate(taskId=execute_task, status="completed")` then `TaskUpdate(taskId=resolve_task, status="in_progress")`

### Step 5: Thread resolution confirmation

After all replies are posted for non-VALID comments, collect threads that
could be resolved and present them individually to the user for confirmation.

**CRITICAL: Never auto-resolve threads.** The user supervising the PR review
needs to verify each triage decision. Auto-resolving hides threads on GitHub,
forcing the user to search through collapsed conversations.

Present each thread with its verdict and reason:

```
{N} threads replied to but not yet resolved:

1. r{id} on {path}:{line} — {verdict}: {reason}
   → Reply posted: "{first_line_of_reply}..."

2. r{id} on {path}:{line} — {verdict}: {reason}
   → Reply posted: "{first_line_of_reply}..."

Resolve these threads?
```

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
This blocks execution until the user confirms which threads
to resolve. Options:
- **"Resolve all"** — Resolve all listed threads
- **"Review one-by-one"** — Confirm each thread individually
- **"Leave all open"** — Keep all threads open (replies already posted)

**If "Review one-by-one":** For each thread, present:
```
r{id} on {path}:{line}
  Verdict: {verdict}
  Reason: {reason}
  Reply: "{reply_excerpt}"

Resolve this thread?
```
Options: "Resolve" / "Leave open"

**After confirmation**, resolve only the user-approved threads via GraphQL.

### Step 5b: Hide obsolete comments (optional)

After resolving threads, offer to minimize the resolved comments
to reduce PR conversation noise. This hides comment bodies on
GitHub, showing "This comment was marked as outdated" instead.

**Skip this step** if no threads were resolved in Step 5.

Collect all resolved threads' root comment `node_id` values:

```bash
gh api graphql -f query='
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100) {
        nodes {
          isResolved
          comments(first: 1) {
            nodes { id databaseId path body }
          }
        }
      }
    }
  }
}' -f owner='{owner}' -f repo='{repo}' -F pr={pr_number} \
  --jq '[.data.repository.pullRequest.reviewThreads.nodes[]
        | select(.isResolved)
        | .comments.nodes[0]]'
```

Present the resolved comments:

```
{N} resolved thread(s) can be hidden:

1. r{databaseId} on {path}:{line} — "{first_line_of_body}..."
2. r{databaseId} on {path}:{line} — "{first_line_of_body}..."

Hide these comments?
```

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
Options:
- **"Hide all resolved" (Recommended)** — Minimize all resolved
  thread root comments with classifier `OUTDATED`
- **"Review one-by-one"** — Confirm each comment individually
- **"Skip"** — Leave all comments visible

**If "Review one-by-one":** For each comment, present:
```
r{databaseId} on {path}:{line}
  Body: "{body_excerpt}"
  Thread: resolved ✅

Hide this comment?
```
Options: "Hide" / "Skip"

**After confirmation**, minimize approved comments via GraphQL:
```bash
gh api graphql -f query='
mutation($id: ID!, $classifier: ReportedContentClassifiers!) {
  minimizeComment(input: {
    subjectId: $id, classifier: $classifier
  }) {
    minimizedComment { isMinimized minimizedReason }
  }
}' -f id='{node_id}' -f classifier='OUTDATED'
```

See `references/github_api.md` § Hiding (Minimizing) Comments.

### Step 6: Summary

After all comments are processed, report:

```
Batch complete: {N} comments processed
- {x} VALID (fixup commits created)
- {y} INVALID (replied)
- {z} QUESTION (answered)
- {w} OUT_OF_SCOPE (acknowledged)
- {r} threads resolved (user-confirmed)
- {h} comments hidden (minimized)
- {u} threads left open
```

---

## Post-Response Continuation

After all comments are processed (Mode A or Mode B), if fixup commits
were created during this session, offer to continue the full shipping
pipeline.

### Parent Context Detection

**Before offering the shipping pipeline, check if a parent
orchestrator (e.g., `Dev10x:work-on`) is managing the shipping
sequence.** When invoked as a delegated skill via `Skill()` from
a parent that has its own shipping pipeline tasks (groom, push,
monitor, ready), skip the Post-Response Continuation gate entirely
and return control to the parent. The parent's remaining tasks
cover the same steps — running them here creates duplicates.

**Detection heuristic:** Call `TaskList`. If tasks exist with
subjects matching the parent's shipping pipeline (e.g., "Groom
commit history", "Monitor CI", "Mark PR ready"), a parent
orchestrator owns the pipeline. Return without offering the
continuation gate.

**When no parent is detected** (standalone invocation), proceed
with the gate below.

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
Options:
- **"Full shipping pipeline" (Recommended)** — Execute the complete
  post-response shipping sequence. **REQUIRED: Use `Skill()` for
  each step** — never run raw git/gh commands directly:
  1. `Skill(Dev10x:git-groom)` — squash fixup commits
  2. `Skill(Dev10x:git)` — push with `--force-with-lease`
  3. `Skill(Dev10x:gh-pr-monitor)` — watch CI after force push
  4. **CI guard (GH-684):** Only after CI passes, run
     `gh pr ready` to mark the PR ready for review. Do NOT
     run `gh pr ready` before CI is green — this was the #1
     bypass pattern: marking ready then discovering CI failures.
     Also verify no unresolved review threads remain before
     marking ready.
  5. If CI passes and no new comments → merge via
     `Skill(Dev10x:gh-pr-merge)` — NEVER raw `gh pr merge`
     (GH-759 F3). The skill validates 8 pre-merge conditions
     including unaddressed review comments that raw merge
     bypasses.
- **"Groom + push only"** — Groom and push, but stop before
  monitoring and merge
- **"Stop"** — End without pushing

This eliminates the manual multi-step chain that was required
after every respond session. The full pipeline handles the entire
groom → push → ready → monitor → merge lifecycle.

**Skip this gate** if no fixup commits were created (e.g., all
comments were INVALID and only replies were posted).

**Solo-maintainer mode:** When the project playbook defines a
solo-maintainer override (no external reviewers), the full
pipeline auto-merges after CI passes without waiting for
external approval.

---

## Tools

Use `gh api` for PR comment operations:

| Operation | Command |
|---|---|
| List comments | `gh api repos/{owner}/{repo}/pulls/{N}/comments` |
| Filter root only | `\| jq '[.[] \| select(.in_reply_to_id == null)]'` |
| Fetch one comment | `gh api repos/{owner}/{repo}/pulls/comments/{id}` |
| Reply to thread | `mcp__plugin_Dev10x_cli__pr_comment_reply(pr_number=N, comment_id=ID, body="...")` |
| Resolve thread | See `references/github_api.md` GraphQL section |

---

## Decision Flow

```
Input URL
    │
    ├─ Has #discussion_r{id} ──► MODE A (single)
    │       │
    │       ├── Dev10x:gh-pr-triage → verdict
    │       ├── if VALID → Dev10x:gh-pr-fixup
    │       ├── if not VALID → reply posted, ask user to resolve
    │       ├── if resolved → offer to hide (minimize) comment
    │       ├── check remaining
    │       └── offer: next / batch / stop
    │
    └─ PR URL / review URL / number ──► MODE B (batch)
            │
            ├── collect unaddressed comments
            ├── triage all (draft, don't post)
            ├── present plan table
            ├── get user approval
            ├── execute approved responses (reply only, no resolve)
            ├── collect non-VALID threads → ask user to confirm resolution
            ├── hide resolved comments → ask user to confirm hiding
            └── summary
```

## Integration

```
Dev10x:gh-pr-monitor → Dev10x:gh-pr-respond (this skill)
                 ├── Dev10x:gh-pr-triage
                 └── Dev10x:gh-pr-fixup
                      └── Dev10x:git-fixup
```

**Standalone usage:**
```bash
# Single comment
/Dev10x:gh-pr-respond https://github.com/owner/repo/pull/123#discussion_r456

# Single comment with context
/Dev10x:gh-pr-respond https://github.com/owner/repo/pull/123#discussion_r456 Note that PR #1135 is merged

# Batch — all unaddressed comments on PR
/Dev10x:gh-pr-respond https://github.com/owner/repo/pull/123

# Batch — all comments from a specific review
/Dev10x:gh-pr-respond https://github.com/owner/repo/pull/123#pullrequestreview-789

# Batch — PR number only
/Dev10x:gh-pr-respond 1164
```

**Called by Dev10x:gh-pr-monitor:**
```
Dev10x:gh-pr-monitor detects new comments →
  delegate to Dev10x:gh-pr-respond with PR URL (batch mode)
```

## References

### references/github_api.md

Contains GitHub API documentation for:
- Listing PR comments
- Fetching single comments
- Creating replies
- Resolving review threads (GraphQL)
- Hiding (minimizing) comments (GraphQL)
- Filtering and querying
