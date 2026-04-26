---
name: Dev10x:gh-pr-merge
description: >
  Validate all pre-merge conditions and execute PR merge.
  Checks unresolved threads, CI status, draft state, mergeability,
  working copy, fixup commits, and review approval before merging.
  TRIGGER when: PR is ready to merge and needs pre-merge validation.
  DO NOT TRIGGER when: PR is still draft, CI is failing, or review
  comments are unaddressed.
user-invocable: true
invocation-name: Dev10x:gh-pr-merge
allowed-tools:
  - Bash(gh pr view:*)
  - Bash(gh pr merge:*)
  - Bash(gh pr checks:*)
  - Bash(gh api graphql:*)
  - Bash(${CLAUDE_PLUGIN_ROOT}/skills/gh-pr-merge/scripts/:*)
  - Bash(gh repo view:*)
  - Bash(git status:*)
  - Bash(git log:*)
---

## Orchestration

This skill follows `references/task-orchestration.md` patterns.
Create a task at invocation, mark completed when done:

**REQUIRED: Create a task at invocation.** Execute at startup:

1. `TaskCreate(subject="Merge PR", activeForm="Merging PR")`

Mark completed when done: `TaskUpdate(taskId, status="completed")`

## Overview

Pre-merge validation gate that checks 8 conditions before
executing `gh pr merge`. Prevents premature merges like PR #633
(merged with 7 unaddressed review comments) and PRs #690-692
(merged with unaddressed top-level automated review comments).

## Merge Strategy Resolution

The merge strategy is resolved using the config resolution order
(see `references/config-resolution.md`):

1. **Global with repo matching** — read
   `~/.claude/memory/Dev10x/settings-pr-merge.yaml`, match current
   repo against `projects[].match` globs
2. **Legacy per-project** — read
   `~/.claude/projects/<project>/memory/settings-pr-merge.yaml`
   (deprecated; log notice if found)
3. **Default** — `squash`

### Config file format

**Global format** (preferred — one file for all repos):
```yaml
# ~/.claude/memory/Dev10x/settings-pr-merge.yaml
projects:
  - match: "Dev10x-Guru/*"
    strategy: rebase
    delete_branch: true
    solo_maintainer: true
  - match: "example-org/*"
    strategy: rebase
    delete_branch: true
    solo_maintainer: true
```

**Legacy format** (per-project, deprecated):
```yaml
# ~/.claude/projects/<project>/memory/settings-pr-merge.yaml
strategy: squash        # squash | rebase | merge
delete_branch: true     # delete remote branch after merge
solo_maintainer: false  # skip external approval requirement
```

All fields are optional. Defaults:
- `strategy`: `squash`
- `delete_branch`: `true`
- `solo_maintainer`: `false`

## Pre-Merge Validation Checks

Run ALL 8 checks before merging. Report results as a checklist.
If ANY check fails, refuse to merge and report which failed.

### Check 1: No unresolved review threads

Query GitHub GraphQL for unresolved review threads:

```bash
gh api graphql -f query='
  query($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $number) {
        reviewThreads(first: 100) {
          nodes {
            isResolved
            comments(first: 1) {
              nodes { body author { login } }
            }
          }
        }
      }
    }
  }
' -f owner=OWNER -f repo=REPO -F number=NUMBER
```

Count threads where `isResolved` is `false`. If any exist,
report the count and first comment of each unresolved thread.

### Check 1b: No unaddressed top-level PR comments (GH-698)

**REQUIRED:** This check MUST run after Check 1. Top-level PR
comments are invisible to the `reviewThreads` GraphQL query —
skipping this check silently misses automated review findings
(GH-728). Do NOT proceed to Check 2 until this script runs.

Top-level PR comments (posted via `gh pr comment`, not inline
review threads) are invisible to Check 1's `reviewThreads`
query. Automated reviewers (claude-review, hygiene-review)
post findings as top-level comments with severity markers.

```bash
${CLAUDE_PLUGIN_ROOT}/skills/gh-pr-merge/scripts/check-top-level-comments.sh \
  OWNER REPO NUMBER
```

The script returns a JSON array of unaddressed findings (empty
array = pass).

If any automated review comments contain unaddressed severity
markers (`REQUIRED`, `CRITICAL`, `BLOCKING`), report the count
and first line of each. A comment is considered "addressed" if
a subsequent comment replies to it (contains `Re:` or quotes
the finding).

**Heuristic for addressed comments:** Check if any later
comment in the thread references the automated comment's ID
or quotes its content. If no reply exists, the finding is
unaddressed.

### Check 1c: No unaddressed inline review comments (GH-760)

Inline review comments posted via `pulls/{n}/comments` are
invisible to both Check 1 (GraphQL `reviewThreads`) and
Check 1b (`issueComments`). Query them directly:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments \
  --jq '[.[] | select(.in_reply_to_id == null)
  | {id, user: .user.login, body: .body[:100], path}]'
```

Filter for bot users with unaddressed severity markers
(`CRITICAL`, `BLOCKING`, `REQUIRED`). A comment is
addressed if a reply exists (same `in_reply_to_id`).
If unaddressed findings remain, report them and block
merge.

### Check 2: CI checks passing

```bash
gh pr checks NUMBER --json name,state,bucket
```

All required checks must have `bucket` of `pass`. No checks
should be `PENDING` or `IN_PROGRESS`. Report any failing or
pending checks by name.

**Pending CI delegation (GH-775):** If any checks are `PENDING`
or `IN_PROGRESS`, do NOT poll inline with `sleep` + `gh pr
checks`. Instead, delegate to `Skill(Dev10x:gh-pr-monitor)` to
wait for CI to complete, then retry the merge validation from
Check 1. The monitor skill handles CI polling, failure fixing,
and re-checking reliably — inline sleep loops bypass these
guardrails.

**Infrastructure failure override (GH-730):** If a check
fails with an infrastructure error (API billing outage,
OIDC token validation failure, external service unavailable),
the failure is non-code-related. In this case:

**REQUIRED: Call `AskUserQuestion`** before proceeding:
- Question: "CI check `{check-name}` failed due to an
  infrastructure issue: `{error-summary}`. This is not
  caused by the code change. Merge anyway?"
- Options: "Merge anyway" / "Abort — fix CI first"

Infrastructure failure signals: "Credit balance is too low",
"OIDC token validation", "Resource not accessible by
integration". Never auto-classify — show the error to the
user and let them decide.

### Check 3: PR is not in draft

```bash
gh pr view NUMBER --json isDraft
```

If `isDraft` is `true`, report that the PR must be marked
ready before merging.

### Check 4: No merge conflicts

```bash
gh pr view NUMBER --json mergeable
```

The `mergeable` field must be `MERGEABLE`. If `CONFLICTING`,
report that merge conflicts must be resolved first.

### Check 5: Working copy is clean

```bash
git status --porcelain
```

If output is non-empty, report uncommitted changes that must
be committed or stashed before merging.

### Check 6: No fixup/squash commits remaining

```bash
git log --oneline origin/develop..HEAD
```

Scan commit subjects for `fixup!` or `squash!` prefixes.
If any exist, report that commit history must be groomed
first (via `Dev10x:git-groom`).

### Check 7: Review approval

```bash
gh pr view NUMBER --json reviewDecision
```

Check that `reviewDecision` is `APPROVED`.

**Solo-maintainer override:** If `solo_maintainer: true` in
config, skip this check entirely. Solo maintainers do not
require external approval.

## Execution Flow

### Step 1: Detect PR

Detect the current PR using the branch name:

```bash
gh pr view --json number,headRefName,baseRefName
```

If no PR exists for the current branch, report and stop.
Extract owner/repo from `gh repo view --json owner,name`.

### Step 2: Load merge strategy config

Read the per-project config file. If it does not exist, use
defaults (`strategy: squash`, `delete_branch: true`,
`solo_maintainer: false`).

### Step 3: Run all 8 validation checks

Run checks in parallel where possible (checks 1-4 use `gh`
commands, check 5-6 use `git` commands). Collect all results
before reporting. **Check 1b MUST be run as a separate step
after Check 1** — it calls `check-top-level-comments.sh` and
is NOT part of the GraphQL batch (GH-728).

### Step 4: Report validation results

Present results as a checklist:

```
## Pre-Merge Validation

- [x] No unresolved review threads (0 unresolved)
- [x] No unaddressed automated review comments (0 found)
- [x] CI checks passing (12/12 green)
- [x] PR is not in draft
- [x] No merge conflicts (MERGEABLE)
- [x] Working copy is clean
- [x] No fixup/squash commits (8 clean commits)
- [x] Review approved (or solo-maintainer override)
```

If any check fails, show `[ ]` with failure details:

```
- [ ] CI checks passing (2 failing: lint, type-check)
```

### Step 5: Merge or refuse

**All checks pass:** Execute merge with configured strategy:

```bash
gh pr merge NUMBER --repo OWNER/REPO --STRATEGY --delete-branch
```

Where `--STRATEGY` is one of `--squash`, `--rebase`, or
`--merge` based on config.

**Worktree safety (GH-773):** Always include `--repo OWNER/REPO`
in the merge command. Without it, `gh pr merge` tries to check
out the base branch locally, which fails in worktree setups
where the base branch is already checked out in another
worktree (`fatal: 'develop' is already used by worktree`).
The `--repo` flag bypasses local checkout entirely. Detect
the repo via `gh repo view --json nameWithOwner -q
.nameWithOwner`.

If `delete_branch` is `false`, omit `--delete-branch`.

**Any check fails:** Do NOT merge. Report which checks failed
and what action is needed to resolve each one. Suggest the
appropriate skill for remediation:

| Failed check | Remediation |
|-------------|-------------|
| Unresolved threads | `Dev10x:gh-pr-respond` |
| Unaddressed automated comments | Review and address findings |
| CI failing | `Dev10x:gh-pr-monitor` |
| Still in draft | `gh pr ready` |
| Merge conflicts | Rebase onto base branch |
| Dirty working copy | `Dev10x:git-commit` |
| Fixup commits | `Dev10x:git-groom` |
| No approval | Request review |

### Step 6: Confirm merge

After successful merge, report:

```
PR #NUMBER merged via STRATEGY into BASE_BRANCH.
Remote branch deleted: yes/no
```

## Auto-Advance Behavior

This skill is designed to auto-advance in shipping pipelines.
After a successful merge, the calling skill should proceed
immediately to the next step (typically acceptance criteria
verification). No confirmation gate after merge.

If merge fails (e.g., branch protection rules), report the
error and let the calling skill decide how to proceed.

## Important Notes

- Never merge without running ALL 8 checks first
- Never bypass checks even if "it looks fine" — the only
  exception is the infrastructure failure override (Check 2)
  which still requires explicit user confirmation via
  `AskUserQuestion` (GH-730)
- The solo-maintainer override only skips check 8 (approval),
  not the other 7 checks
- This skill must NOT be called from background agents
  (`Dev10x:gh-pr-monitor` explicitly forbids merge operations)
- Always use `gh pr merge` (not `git merge`) to ensure GitHub
  records the merge event properly
