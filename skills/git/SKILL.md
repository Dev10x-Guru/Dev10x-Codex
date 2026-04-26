---
name: Dev10x:git
description: >
  Use before running git push or git rebase — so force-pushes to
  protected branches are blocked and non-interactive rebases run unattended
  without manual editor approval prompts.
  TRIGGER when: running git push or git rebase operations.
  DO NOT TRIGGER when: other git operations (commit, status, log, diff)
  that don't need push/rebase safety.
user-invocable: true
invocation-name: Dev10x:git
allowed-tools:
  - mcp__plugin_Dev10x_cli__push_safe
  - Bash(${CLAUDE_PLUGIN_ROOT}/skills/git/scripts/git-push-safe.sh:*)
  - Bash(${CLAUDE_PLUGIN_ROOT}/skills/git/scripts/git-rebase-groom.sh:*)
  - Bash(${CLAUDE_PLUGIN_ROOT}/skills/git/scripts/git-seq-editor.sh:*)
  - Bash(git reset --soft:*)
  - Bash(git push --force-with-lease:*)
  - Bash(/tmp/claude/bin/mktmp.sh:*)
  - Write(/tmp/claude/git/**)
---

**Announce:** "Using Dev10x:git to [push / groom commits]."

# Dev10x:git — Hardened Git Operations

Provides hardened scripts for safe git push and non-interactive rebase.
Add the `allowed-tools` entries to your project's `settings.local.json`
to pre-approve the scripts without per-call prompts.

## Orchestration

This skill follows `references/task-orchestration.md` patterns.
Create a task at invocation, mark completed when done:

**REQUIRED: Create a task at invocation.** Execute at startup:

1. `TaskCreate(subject="Safe git push", activeForm="Pushing safely")`

Mark completed when done: `TaskUpdate(taskId, status="completed")`

## Safe Push

**Primary: MCP tool call** (no permission friction):

```
mcp__plugin_Dev10x_cli__push_safe(flags="[flags]", remote="origin", refspec="branch")
```

MCP calls avoid `Bash()` allow-rule matching and provide
structured responses. Use the MCP tool as the default for
all push operations.

**Fallback: wrapper script** (when MCP server is unavailable):

```bash
${CLAUDE_PLUGIN_ROOT}/skills/git/scripts/git-push-safe.sh [flags] [remote] [refspec]
# Do NOT pass "push" — the script runs `git push` itself.
# Example: git-push-safe.sh -u origin feature-branch
```

Default protected branches: `main master`

To extend the list, set `GIT_PROTECTED_BRANCHES` before calling:

```bash
GIT_PROTECTED_BRANCHES="main master staging" \
  ${CLAUDE_PLUGIN_ROOT}/skills/git/scripts/git-push-safe.sh --force-with-lease
```

`--force-with-lease` is always allowed (verifies the remote has not
diverged before overwriting). `--force` and `-f` are blocked on
protected branches.

## Non-Interactive Rebase

Two scripts power fully automated rebases:

- **`git-seq-editor.sh`** — replaces `GIT_SEQUENCE_EDITOR`; reads the
  rebase todo from the path in `GROOM_SEQ_FILE` env var.
- **`git-rebase-groom.sh`** — convenience wrapper that sets
  `GIT_SEQUENCE_EDITOR` and `GIT_EDITOR=true`, then runs
  `git rebase -i <base-ref>`. Takes `<seq-file> <base-ref>` args.

### Usage

1. Create a unique temp file for the rebase sequence:

```bash
/tmp/claude/bin/mktmp.sh git rebase-seq .txt
```

Store the returned path (e.g., `/tmp/claude/git/rebase-seq.a7b3c9.txt`).

2. Write the rebase todo (oldest commit first) to that file using
   the Write tool:

```
Write <unique-path>:
pick abc1234 First commit
pick def5678 Second commit
fixup fed9876 fixup! Second commit
```

**Note:** The Write tool requires reading a file before writing to it.
For a new file, `mktmp.sh` already created it (empty), so Read it first,
then Write the sequence content.

3. Run the rebase with the sequence file as the first argument:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/git/scripts/git-rebase-groom.sh <unique-path> <base-ref>
```

### Sequence file ordering

The sequence file must list commits **oldest at the top, newest at the
bottom** — the same order `git rebase -i` expects. Use `tac` to
reverse `git log` output:

```bash
git log --oneline <base>..HEAD | tac
```

### SHA staleness

After each rebase pass all commit SHAs change. Always re-run
`git log --oneline <base>..HEAD` after each pass and use fresh SHAs
when writing the next sequence file.

## Branch Comparison Aliases

Use git aliases instead of embedding `$(git merge-base ...)` in
commands. The `$(...)` substitution creates compound commands that
break Claude Code permission prefix matching, causing unnecessary
permission prompts.

| Alias                | Equivalent                                                     |
|----------------------|----------------------------------------------------------------|
| `git develop-log`    | `git log --oneline $(git merge-base develop HEAD)..HEAD`       |
| `git develop-diff`   | `git diff $(git merge-base develop HEAD)..HEAD`                |
| `git develop-rebase` | `git rebase -i --autosquash $(git merge-base develop HEAD)`    |

The alias name includes the base branch. When a different base is
needed (e.g., `trunk`), add a parallel set: `trunk-log`, `trunk-diff`,
`trunk-rebase`.

**Never use `$(git merge-base ...)` inline** — always use the alias.

## settings.local.json wiring

Add to your project's `.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(${CLAUDE_PLUGIN_ROOT}/skills/git/scripts/git-push-safe.sh:*)",
      "Bash(${CLAUDE_PLUGIN_ROOT}/skills/git/scripts/git-rebase-groom.sh:*)",
      "Bash(${CLAUDE_PLUGIN_ROOT}/skills/git/scripts/git-seq-editor.sh:*)",
      "Bash(git reset --soft:*)",
      "Bash(git push --force-with-lease:*)",
      "Bash(/tmp/claude/bin/mktmp.sh:*)",
      "Write(/tmp/claude/git/**)"
    ]
  }
}
```
