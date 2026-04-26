---
name: Dev10x-gh-pr-fixup
description: Implement a fix for a validated PR review comment, create a fixup! commit, push, and reply with the commit reference. Creates ONE fixup commit per comment.
---

# Implement Fix for PR Review Comment

## Overview

This skill handles implementing a fix for a PR review comment that has
already been validated as needing a code change. It:

1. Analyzes the comment to understand the requested change
2. Implements the fix in the codebase
3. Creates a `fixup!` commit targeting the original commit
4. Pushes the commit
5. Replies to the comment with the commit reference

**Critical rule: ONE fixup commit per PR comment.**

**When to use this skill:**
- Called by `Dev10x:gh-pr-respond` after `Dev10x:gh-pr-triage` returns `VALID`
- Standalone when you already know a comment needs a fix

## Input Requirements

1. **PR URL or Comment URL** — Full GitHub URL to the PR comment
   (e.g., `https://github.com/owner/repo/pull/123#discussion_r456`)
2. **Repository** — Owner/repo (extracted from URL or defaults to current repo)

**Optional additional context:**
- User may provide extra context after the URL
- Example: `Dev10x-gh-pr-fixup https://...#discussion_r456 The API now provides customer_url`

## Workflow

### Step 1: Parse Input and Fetch Comment Details

**Parse the comment URL:**
```
URL format: https://github.com/{owner}/{repo}/pull/{pr_number}#discussion_r{comment_id}
```

**Fetch the comment:**
```bash
$HOME/.codex/tools/gh-pr-comments.py get --comment-id {comment_id}
```

Extract:
- `body` — The comment text (the requested change)
- `path` — File path the comment is on
- `line` — Line number in the diff
- `original_line` — Original line number
- `diff_hunk` — The code context around the comment
- `commit_id` — The commit this comment refers to
- `user.login` — Who left the comment
- `html_url` — Direct link to comment

### Step 2: Analyze the Comment

Parse the comment to understand:

1. **Type of change requested:**
   - Code fix (bug, logic error)
   - Style/formatting issue
   - Naming improvement
   - Missing test coverage
   - Architectural suggestion

2. **Scope of change:**
   - Single line fix
   - Multi-line fix in same file
   - Changes across multiple files
   - Requires new tests

### Step 3: Check if Already Addressed

Before implementing, check if a previous fixup commit already addresses
this comment:

**Reuse existing fixup commit if:**
- The exact same code change was already made
- No additional code modifications are needed

**Create new fixup commit if:**
- Any code change is required (even small additions)
- The existing fix only partially addresses the concern

**When reusing a fixup:**
- Reply to the comment referencing the existing commit
- Tailor the reply text to address this comment's specific concern
- Skip Steps 4-6, go directly to Step 7

### Step 4: Implement the Fix

1. **Read the affected file(s):**
   ```bash
   Read tool with file_path and relevant line range
   ```

2. **Make the change:**
   - Use Edit tool for modifications
   - Follow existing code patterns
   - Maintain consistent style

3. **Run verification (if applicable):**

   **Python projects:**
   ```bash
   pytest {test_file} -x
   ```
   Note: `ruff format` and `ruff check --fix` run automatically via PostToolUse hook.

   **JavaScript/TypeScript projects:**
   ```bash
   npx prettier --write {file_path}
   npx eslint --fix {file_path}
   npx tsc --noEmit -p {tsconfig_path}
   npm test -- --testPathPattern="{test_pattern}" --no-coverage
   ```

### Step 5: Create Fixup Commit (delegate to commit:fixup)

**IMPORTANT:** Delegate to the `commit:fixup` skill.

```bash
# Stage the changes
git add {file_path}

# Delegate to commit:fixup skill (handles message format)
```

**Fixup commit format:**
```
fixup! {original_commit_subject}

Addresses review comment:
https://github.com/{owner}/{repo}/pull/{pr}#discussion_r{comment_id}
```

### Step 6: Push the Fixup Commit

```bash
git push origin HEAD
```

Get the commit hash for the reply:
```bash
commit_hash=$(git rev-parse --short HEAD)
full_hash=$(git rev-parse HEAD)
# Use PR-based URL so reviewers can comment on the diff within the PR context.
commit_url="https://github.com/{owner}/{repo}/pull/{pr_number}/commits/${full_hash}"
```

### Step 7: Reply to Comment Thread

Reply **in the review comment thread** (not as a top-level PR comment):

```bash
gh api --method POST \
  repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies \
  -f body="Fixed in [\`{short_hash}\`]({commit_url}) - {brief_explanation}"
```

**Reply format:**
```markdown
Fixed in [`{short_hash}`]({commit_url}) - {brief explanation of change}.
```

**When reusing a fixup for another comment:**
- Reference the same commit
- Tailor explanation to this comment's specific concern

## Error Handling

### Fix Causes Test Failure

If the fix breaks tests:
1. Revert: `git checkout -- {file_path}`
2. Reply asking for clarification:
   ```
   The suggested change causes test failures in `test_xyz`.
   Could you clarify the expected behavior?

   Error: {brief_error_message}
   ```

### Ambiguous Comment

If the comment is unclear:
1. Do not make changes
2. Reply asking for clarification:
   ```
   Could you clarify what change you'd like here?
   I see a few possible interpretations:
   1. {interpretation_1}
   2. {interpretation_2}
   ```

### Merge Conflict

If the file has changed since the comment was made:
1. Fetch latest: `git pull --rebase`
2. Re-analyze the comment in new context
3. Implement fix on current code

## Important Notes

- **One fixup per comment** — enforced by pre-commit hook
- **Comment link required** — every fixup commit must have exactly one
  comment thread link in body
- **Reply in thread** — use `gh api` to reply in thread, never
  `gh pr comment`
- **Never force push** — always regular push for fixup commits
- **Reuse only if identical** — only reuse a fixup if zero additional
  code changes needed
- **Discover project tooling** — check `Makefile`, `package.json`,
  or repo root for project-specific scripts

## Integration

```
Dev10x:gh-pr-monitor → Dev10x:gh-pr-respond (orchestrator)
                 ├── Dev10x:gh-pr-triage
                 └── Dev10x:gh-pr-fixup  ← this skill
                      └── commit:fixup
```

**Standalone usage:**
```bash
Dev10x-gh-pr-fixup https://github.com/owner/repo/pull/123#discussion_r456
```

**Called by Dev10x:gh-pr-respond:**
```
Dev10x:gh-pr-respond receives comment URL
  → delegates to Dev10x:gh-pr-triage → verdict: VALID
  → delegates to Dev10x:gh-pr-fixup (this skill)
  → fix implemented, pushed, replied
```

## Tool Reference

GitHub comment operations use `gh api` for REST calls and `gh api graphql`
for thread resolution. See `references/github_api.md` for full reference.
