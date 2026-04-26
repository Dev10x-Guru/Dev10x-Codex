---
name: Dev10x-git-alias-setup
description: Set up git aliases that reduce permission friction by wrapping $(git merge-base ...) subshells into stable command prefixes.
---

**Announce:** "Using Dev10x:git-alias-setup to configure branch-comparison aliases."

# Dev10x:git-alias-setup — Git Alias Configuration

Configures global git aliases that wrap `$(git merge-base ...)` subshells.
Without these aliases, commands like `git log $(git merge-base develop HEAD)..HEAD`
trigger extra permission prompts because the `$()` substitution shifts
the Bash command prefix.

## Usage

Run the setup script:

```bash
$HOME/.codex/skills/Dev10x-git-alias-setup/scripts/git-alias-setup.sh
```

## Aliases Configured

Each base branch gets three aliases: `{base}-log`, `{base}-diff`, `{base}-rebase`.

| Alias                | Equivalent                                                  |
|----------------------|-------------------------------------------------------------|
| `git develop-log`    | `git log --oneline $(git merge-base develop HEAD)..HEAD`    |
| `git develop-diff`   | `git diff $(git merge-base develop HEAD)..HEAD`             |
| `git develop-rebase` | `git rebase -i --autosquash $(git merge-base develop HEAD)` |
| `git development-log`    | `git log --oneline $(git merge-base development HEAD)..HEAD`    |
| `git development-diff`   | `git diff $(git merge-base development HEAD)..HEAD`             |
| `git development-rebase` | `git rebase -i --autosquash $(git merge-base development HEAD)` |
| `git trunk-log`      | `git log --oneline $(git merge-base trunk HEAD)..HEAD`      |
| `git trunk-diff`     | `git diff $(git merge-base trunk HEAD)..HEAD`               |
| `git trunk-rebase`   | `git rebase -i --autosquash $(git merge-base trunk HEAD)`   |

## When to Use

The session start hook checks for these aliases automatically.
If they are missing, it will suggest running this skill.

After setup, use `git {base}-log` instead of the full subshell form
in all git operations to avoid permission friction.

## Scope

Aliases are set globally (`--global`) so they persist across all
repositories and sessions.
