# Git Commit & Branch Guidelines

Standards for commits and branches in this repository.

## Branch Targeting Policy

- **Feature PRs**: Always target `develop` branch
- **Release PRs**: Target `main` only via merge from `develop`
- **CLI rule**: Always pass `--base develop` to `gh pr create` — a
  `PreToolUse` hook blocks the command if this flag is missing

*Why?* Feature work should always target `develop` to ensure all
quality gates (Claude Code Review, CI) run as expected.

## Branch Naming Convention

Format: `username/TICKET-ID/short-description`
Worktree: `username/TICKET-ID/worktree-name/short-description`

Examples:
- `janusz/GH-7/add-semver-releases`
- `maria/GH-42/fix-hook-validation`
- `janusz/PAY-133/app-pos-7/fix-motor-timeout` (worktree)

## Commit Message Format

### Structure

```
<gitmoji> <TICKET-ID> <short description>

<problem explanation - what was wrong and why it needed fixing>

Solution:
- <change 1>
- <change 2>

Fixes: <TICKET-ID>
```

### Title Writing Principle

Focus on what the change **enables**, not what it changes in code.
See `git-jtbd.md` for comprehensive Job Story format and examples.

**User-facing features** (required):
- Bad: `Add validate command to plugin CLI` (implementation)
- Good: `Enable plugin validation before publishing` (outcome)

**Meta-work** (docs, tooling — preferred but not required):
- Acceptable: `Add missing shellcheck workflow`
- Also good: `Prevent shell script regressions in CI`

### Rules

1. **Title line**: Max 72 characters (gitmoji + space + ticket + space + description)
2. **Body lines**: Max 72 characters each
3. **Gitmoji**: Use emoji character, not `:code:` format
4. **No co-authoring**: Never add "Co-Authored-By: Claude" footer

### Gitmoji Reference

| Emoji | Code | Use for |
|-------|------|---------|
| ✅ | `:white_check_mark:` | Adding/fixing tests |
| 🐛 | `:bug:` | Bug fixes |
| ♻️ | `:recycle:` | Refactoring |
| ✨ | `:sparkles:` | New features |
| 📝 | `:memo:` | Documentation |
| 🔒 | `:lock:` | Security fixes |
| ⚡ | `:zap:` | Performance |
| 🔧 | `:wrench:` | Configuration |
| 🔖 | `:bookmark:` | Version bumps |
| 🩹 | `:adhesive_bandage:` | Simple/minor fixes |
| 🔥 | `:fire:` | Removing code/files |

### Example Commit

```
🐛 GH-7 Fix hook validation for heredoc commands

validate-bash-security.py rejects heredoc syntax used by the
commit skill, causing false positives on every commit.

Solution:
- Allow cat <<'EOF' pattern when target is a temp file
- Add test case for heredoc commit messages

Fixes: GH-7
```

## Atomic Commits

Each commit should represent **one logical change**:

- ✅ One feature, one commit
- ✅ One bug fix, one commit
- ✅ One refactoring, one commit
- ❌ Multiple unrelated changes in one commit
- ❌ Half-finished work in a commit

### Commit Ordering

When a feature touches multiple layers, commit in dependency order:

1. Utilities/helpers (no dependencies)
2. Configuration and infrastructure
3. Core implementation
4. Documentation and rules
5. Tests

For PR and branch grooming guidelines, see `git-pr.md`.
