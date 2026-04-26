---
name: Dev10x-gh-pr-respond
description: Validate and respond to PR review comments. Handles single comment (with follow-up offer) or batch mode for all unaddressed comments on a PR/review. Orchestrates Dev10x:gh-pr-triage and Dev10x:gh-pr-fixup.
---

# Respond to PR Review Comments

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
         └── commit:fixup → create the fixup! commit
```

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
- Example: `Dev10x-gh-pr-respond https://...#discussion_r456 Note that PR #1135 is merged`

---

## Mode A: Single Comment

**Trigger:** Input contains `#discussion_r{comment_id}`

### Step 1: Process the comment

Delegate to `Dev10x:gh-pr-triage` with the comment URL (and any additional context).

`Dev10x:gh-pr-triage` returns a verdict: `VALID`, `INVALID`, `QUESTION`, or `OUT_OF_SCOPE`.

- If **VALID** → delegate to `Dev10x:gh-pr-fixup` to implement fix, commit, push,
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

Use `AskUserQuestion` with options:
- **"Resolve"** — Resolve the thread via GraphQL
- **"Leave open"** — Keep the thread open (reply already posted)

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

Use `AskUserQuestion` with options:
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

If no unaddressed comments found → report "No unaddressed comments" and stop.

### Step 2: Triage all comments

For each unaddressed comment, run `Dev10x:gh-pr-triage` **investigation only** (do NOT
post replies or resolve threads yet). Produce a verdict and draft response for
each.

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

Use `AskUserQuestion`:
- **"Approve all"** — Execute all proposed responses
- **"Review one-by-one"** — Present each for individual approval (like Mode A)
- **"Skip"** — Cancel batch

The user may also provide corrections in free text (e.g., "Comment 2 is not
valid, we use DataclassField" or "Comment 4: make it a question to the
reviewer").

### Step 4: Execute approved responses

For each approved comment:

- **VALID** → delegate to `Dev10x:gh-pr-fixup` (one fixup commit per comment)
- **INVALID / QUESTION / OUT_OF_SCOPE** → post reply using `gh api`:
  ```bash
  gh api --method POST \
    repos/{owner}/{repo}/pulls/{pr_number}/comments/{id}/replies \
    -f body="{reply}"
  ```
  Do **NOT** resolve the thread automatically.

Report progress after each comment is processed.

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

Use `AskUserQuestion` with options:
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

### Step 6: Summary

After all comments are processed, report:

```
Batch complete: {N} comments processed
- {x} VALID (fixup commits created)
- {y} INVALID (replied)
- {z} QUESTION (answered)
- {w} OUT_OF_SCOPE (acknowledged)
- {r} threads resolved (user-confirmed)
- {u} threads left open
```

---

## Tools

Use `gh api` for PR comment operations:

| Operation | Command |
|---|---|
| List comments | `gh api repos/{owner}/{repo}/pulls/{N}/comments` |
| Filter root only | `\| jq '[.[] \| select(.in_reply_to_id == null)]'` |
| Fetch one comment | `gh api repos/{owner}/{repo}/pulls/comments/{id}` |
| Reply to thread | `gh api --method POST repos/{owner}/{repo}/pulls/{N}/comments/{id}/replies -f body="..."` |
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
            └── summary
```

## Integration

```
Dev10x:gh-pr-monitor → Dev10x:gh-pr-respond (this skill)
                 ├── Dev10x:gh-pr-triage
                 └── Dev10x:gh-pr-fixup
                      └── commit:fixup
```

**Standalone usage:**
```bash
# Single comment
Dev10x-gh-pr-respond https://github.com/owner/repo/pull/123#discussion_r456

# Single comment with context
Dev10x-gh-pr-respond https://github.com/owner/repo/pull/123#discussion_r456 Note that PR #1135 is merged

# Batch — all unaddressed comments on PR
Dev10x-gh-pr-respond https://github.com/owner/repo/pull/123

# Batch — all comments from a specific review
Dev10x-gh-pr-respond https://github.com/owner/repo/pull/123#pullrequestreview-789

# Batch — PR number only
Dev10x-gh-pr-respond 1164
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
- Filtering and querying
