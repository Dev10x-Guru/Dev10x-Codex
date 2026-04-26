---
name: Dev10x-git-groom
description: Restructure, polish, and clean up git commit history in the current branch before merging. Creates atomic, well-organized commits that tell a clear story.
---

# Git Branch History Grooming

## Overview

This skill helps restructure, polish, and clean up git commit history in the current branch before merging. Use it to create atomic, well-organized commits that tell a clear story.

**Guiding Principle:** When rewriting commit titles, shift the perspective from what changed in the code to what it enables for the user. Describe the user-facing outcome, not the implementation detail. E.g., `Enable automatic terminal discovery` not `Add DEVICES_READ to Square OAuth scopes`.

**When to use this skill:**
- After receiving review feedback that requires changes across multiple commits
- When commits have become messy during development
- Before creating a PR to ensure clean history
- When CI blocks merge due to fixup commits

## Workflow

### Phase 1: Analyze Current State

```bash
# View commits in current branch (relative to base)
git log --oneline develop..HEAD

# See what files changed in each commit
git log --oneline --stat develop..HEAD

# Identify the base commit for rebasing
git merge-base develop HEAD
```

**SHA Staleness Warning:** Record SHAs at analysis time only for planning.
Before writing any execution scripts (message files, sequence editor),
always re-run `git log --oneline <base>..HEAD` to get the current SHAs.
Any commit (rebase, amend, reset) changes all descendant SHAs. Using
analysis-time SHAs in execution scripts will silently target wrong commits.

### Phase 2: Choose Strategy

#### Strategy A: Fixup Commits (for small targeted changes)

Use when making small fixes to specific commits:

```bash
# Create a fixup commit targeting a specific commit
git add <files>
git commit --fixup=<target-commit-sha>

# Simple autosquash (fixup commits only, no reordering):
GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash $(git merge-base develop HEAD)

# Custom sequence (reordering, message rewrites, splits):
# 1. Create unique seq file: /tmp/claude/bin/mktmp.sh git rebase-seq .txt
# 2. Write sequence to the returned path
# 3. Run: $HOME/.codex/skills/Dev10x-git/scripts/git-rebase-groom.sh <path> develop
```

**Key insight:** For pure autosquash (squashing fixup commits into their targets), use `GIT_SEQUENCE_EDITOR=true` directly — it accepts git's auto-generated todo as-is. The rebase script (`git-rebase-groom.sh`) replaces the todo with your sequence file, so commits not listed in the file are dropped. Only use the script when you need custom sequence control.

#### Strategy B: Full Restructure (for major reorganization)

Use when commits need complete reorganization:

```bash
# Soft reset to base, keeping all changes staged
git reset --soft <base-commit>

# Now selectively create new atomic commits
git reset HEAD  # Unstage everything
git add -p      # Interactively stage hunks
git commit -m "First logical change"
# Repeat for each logical unit
```

#### Strategy D: Non-Interactive Mass Rewrite (for bulk message updates)

Use when rewriting many commit messages without structural changes (no
splits, squashes, or file renames beyond what the commits already have).
Fully automatable — no interactive editor required.

**Use the script** (single permission approval, runs unattended):
```bash
/tmp/claude/bin/mktmp.sh git groom-config .json
```
Write the config to the returned path, then run:
```bash
$HOME/.codex/skills/Dev10x-git-groom/scripts/mass-rewrite.py <config-path>
```
The script creates its own isolated workdir under `/tmp/claude/git/`.

Config format:
```json
{
  "base": "develop",
  "commits": {
    "abc1234": "New outcome-focused message",
    "def5678": {
      "message": "New message with file renames",
      "renames": [["old/path/file.md", "new/path/file.md"]]
    }
  }
}
```

The script validates SHAs against the current log before doing anything,
prints a preview of all commits (marking which will be rewritten), then
runs the full rebase unattended. See the script docstring for details.

**Manual steps (reference / fallback):** The script implements the
following steps — useful to understand internals or when the script
cannot be used.

**Step 1:** Re-check current SHAs (never use analysis-time SHAs):
```bash
git log --oneline $(git merge-base develop HEAD)..HEAD
```

**Step 2:** Create an isolated workdir for this groom session:
```bash
/tmp/claude/bin/mktmp.sh -d git groom
```
Store the returned path as `$WORKDIR`.

**Step 3:** Write one message file per commit to rewrite using the Write tool:

```
Write $WORKDIR/msgs/<7-char-sha>:
Enable user login with HMAC session auth
```

Repeat for each commit needing a new message. The Write tool creates
parent directories as needed.

**Step 4:** Write the complete rebase sequence using the Write tool:

```bash
/tmp/claude/bin/mktmp.sh git rebase-seq .txt
```

Write to the returned path:
```
pick <oldest-sha> First commit
exec git commit --amend -F $WORKDIR/msgs/<oldest-sha-short>
pick <sha> Second commit with git mv
exec git mv old/path new/path && git commit --amend -F $WORKDIR/msgs/<sha-short>
pick <newest-sha> Third commit (no rewrite needed)
```

Oldest commit at top.

**Step 5:** Run the non-interactive rebase:
```bash
$HOME/.codex/skills/Dev10x-git/scripts/git-rebase-groom.sh <seq-path> develop
```

`GIT_EDITOR="true"` suppresses the commit message editor for `--amend`
so the rebase runs fully unattended.

#### Strategy C: Interactive Rebase (for reordering/editing)

Use when you need to reorder, edit messages, or split commits:

```bash
git rebase -i <base-commit>
```

Commands in interactive rebase:
- `pick` - keep commit as-is
- `reword` - change commit message
- `edit` - stop to amend the commit
- `squash` - meld into previous commit (keep message)
- `fixup` - meld into previous commit (discard message)
- `drop` - remove commit

### Phase 3: Push Changes

```bash
# Force push with lease (safer than --force)
git push origin <branch> --force-with-lease
```

**Important:** `--force-with-lease` fails if someone else pushed to the branch, preventing accidental overwrites.

### Phase 4: Update PR References

After force-pushing groomed history, PR body and summary comment may
contain stale commit hashes.

1. Get the new commit hash(es): `git log --oneline develop..HEAD`
2. Update the PR body commit links with new hashes
3. Update the summary comment (first comment by the author) with new hashes
4. If the PR body has a Job Story, preserve it unchanged

This step is only needed when an open PR exists for the branch.

## Common Scenarios

### Scenario 1: Review Comments Need Fixes

```bash
# Make the fix
vim file.py

# Create fixup targeting the original commit
git add file.py
git commit --fixup=$(git log --oneline | grep "original message" | cut -d' ' -f1)

# Squash before pushing
git rebase -i --autosquash $(git merge-base develop HEAD)

# Push
git push --force-with-lease
```

### Scenario 2: CI Blocks Fixup Commits

Many repos have CI checks that block merging if fixup commits exist:

```bash
# Squash all fixup commits
git rebase -i --autosquash $(git merge-base develop HEAD)

# The editor opens with fixup commits already positioned - just save and exit
git push --force-with-lease
```

### Scenario 3: Split One Commit Into Two

```bash
git rebase -i <base>
# Mark the commit as 'edit'
# When rebase stops:
git reset HEAD^           # Undo the commit, keep changes
git add -p                # Stage first logical change
git commit -m "First part"
git add .                 # Stage remaining changes
git commit -m "Second part"
git rebase --continue
```

### Scenario 4: Combine Multiple Commits

```bash
git rebase -i <base>
# Keep first commit as 'pick'
# Change subsequent commits to 'squash' or 'fixup'
# Save and edit the combined commit message
```

## Best Practices

1. **Atomic commits**: Each commit should represent one logical change
2. **Meaningful messages**: Follow project conventions (gitmoji, ticket refs, etc.)
3. **Test before pushing**: Ensure each commit in history passes CI individually
4. **Communicate**: If others are working on the branch, coordinate before force pushing
5. **Backup first**: Create a backup branch before complex rewrites:
   ```bash
   git branch backup-before-rewrite
   ```

## Commit Message Conventions

Follow project standards. Common patterns:
- Gitmoji: `PAY-123 Add new feature`
- Conventional: `feat(payments): add new feature [PAY-123]`

Limit title to 72 characters. Add body for complex changes.

## Troubleshooting

### Rebase Conflicts

```bash
# Fix conflicts in files
vim conflicted-file.py

# Mark as resolved
git add conflicted-file.py

# Continue rebase
git rebase --continue

# Or abort if things go wrong
git rebase --abort
```

### Autosquash Fails on Cross-Commit Fixups

When a fixup commit modifies files that span multiple original commits
(e.g., service layer in commit A and mutation layer in commit B),
`--autosquash` places the fixup after one target but before the other.
This causes conflicts because the later commit's files don't exist yet
at that point in history.

**Symptom:** Rebase conflict immediately after autosquash reorders commits.

**Fix:** Abort and use Strategy B (soft reset) instead:

```bash
git rebase --abort
git reset --soft $(git merge-base develop HEAD)
git reset HEAD
# Recommit in clean atomic chunks
```

*Why?* Example: a fixup touching both `service.py` (commit 1)
and `mutations.py` (commit 3) failed autosquash. Strategy B resolved
it in one pass.

### exec Steps Leaving Staged Changes Halt Rebase

When using `exec` lines in an interactive rebase todo, each `exec` command
runs in the repo's working tree with the index from the previous step.
If an `exec git mv` stages a rename but does not commit it, the next
`exec` command (or the next `pick`) finds the index dirty and rebase halts:

```
error: cannot rebase: Your index contains uncommitted changes.
```

**Symptom:** Rebase stops mid-run on a commit that involves `git mv`.

**Fix:** Chain all operations for a single commit into **one `exec` line**
using `&&` so the index is clean before the next `pick`:

```
exec git mv old/path/A new/path/A && git mv old/path/B new/path/B && git commit --amend -F $WORKDIR/msgs/<sha>
```

Never use separate `exec git mv` lines for the same commit amendment.

### GIT_SEQUENCE_EDITOR file must be oldest-first

`git rebase -i` expects commits listed **oldest at the top, newest at the
bottom** — the opposite of `git log` default output (newest first).

**Symptom:** Immediate modify/delete conflict on files added in later commits
(e.g., `package.json deleted in HEAD and modified in <sha>`).

**Fix:** Reverse `git log` order when building the sequence file:

```bash
git log --oneline <base>..HEAD | tac  # tac reverses line order
```

Verify: the **first line** of the sequence file must be the **oldest** commit SHA.

### Stale SHAs in multi-pass rebases

After each rebase pass all commit SHAs change. A sequence file written before
pass 1 contains stale SHAs that will silently pick the wrong commits in pass 2.

**Symptom:** A commit gets the wrong message (e.g., Makefile commit gets the
Docker commit's name because the stale SHA pointed elsewhere).

**Fix:** Always run `git log --oneline <base>..HEAD` after each rebase pass
and use the fresh SHAs when writing the next sequence file.

### git-rebase-groom.sh Drops Commits on Autosquash

`git-rebase-groom.sh` uses a custom `GIT_SEQUENCE_EDITOR` that
replaces the rebase todo with the contents of
`$GROOM_SEQ_FILE`. If the sequence file
doesn't list ALL commits, the missing ones are dropped.

**Symptom:** After running `git-rebase-groom.sh`, only a subset
of commits remain in history.

**Fix:** For simple autosquash (no custom reordering), skip the
script entirely:

```bash
GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash $(git merge-base develop HEAD)
```

Use `git-rebase-groom.sh` only when you need custom sequence
control (message rewrites, splits, reordering).

### Files Excluded by Global ~/.gitignore in Soft Reset

When using Strategy B (soft reset + recommit), files tracked in the
original branch may be ignored by the user's global `~/.gitignore`
(e.g. `.nvmrc`, `.DS_Store`). `git add <file>` silently skips them,
causing the commit to be incomplete.

**Symptom:** Script exits with error mid-run; a commit is missing
expected files that appear in the backup but not in the new history.

**Diagnose:**
```bash
git check-ignore -v <file>   # shows which gitignore rule is blocking
```

**Fix:** Use `git add -f` to force-add the file:
```bash
git add -f apps/web/.nvmrc
```

Add the `-f` flag to every `git add` call in the recommit script
for files that are in the global gitignore.

### `$()` Subshells Cause Permission Friction

When calling skill scripts, never wrap arguments in `$()` subshells:

```bash
# BAD — $() changes the effective command prefix, breaking allow rules
BASE=$(git merge-base develop HEAD)
$HOME/.codex/skills/Dev10x-git/scripts/git-rebase-groom.sh "$BASE"

# GOOD — pass branch name directly, script resolves merge-base internally
$HOME/.codex/skills/Dev10x-git/scripts/git-rebase-groom.sh develop
```

**Symptom:** Every invocation prompts for permission even though the
script path matches an existing `Bash($HOME/.codex/skills:*)` allow rule.

**Why?** `settings.local.json` allow rules match the command prefix.
`BASE=$(git merge-base develop HEAD) && script` has prefix `BASE=...`,
not `$HOME/.codex/skills/...`. Even a standalone `git merge-base` before
the script is unnecessary friction — the script accepts branch names.

*Source:* Prior sessions: 3 consecutive user corrections to eliminate
`$()` from the grooming workflow.

### Recover from Bad Rewrite

```bash
# Find the previous HEAD position
git reflog

# Reset to before the rewrite
git reset --hard HEAD@{n}
```

## Integration with Other Skills

### Dev10x:git-commit-split

When the user asks to split a specific commit mid-session (e.g. "Split
<sha>"), invoke the `Dev10x:git-commit-split` skill rather than handling it inline.
`Dev10x:git-commit-split` provides the canonical workflow with dependency-order
guidance and commit message conventions.

```
User: "Split 835fc34"
-> Invoke Skill(Dev10x:git-commit-split) before proceeding
```

## Integration with PR Workflow

1. Create fixup commits as you address review comments
2. Reply to each comment with "Fixed in commit <sha>"
3. Before final push, squash all fixups: `git rebase -i --autosquash`
4. Force push to trigger fresh CI run
5. CI should now pass (no fixup commits blocking merge)
