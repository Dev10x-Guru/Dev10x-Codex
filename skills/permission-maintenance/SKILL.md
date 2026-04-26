---
name: Dev10x:permission-maintenance
description: >
  Maintain Claude Code permissions — update plugin version paths, ensure
  base permissions, merge worktree rules, generalize session-specific args,
  audit for friction-causing patterns via the permission-auditor agent,
  and clean redundant rules from project settings files.
  TRIGGER when: plugin version changes, permission prompts keep appearing,
  or user asks to fix permission friction.
  DO NOT TRIGGER when: permissions are working correctly, or user is
  asking about non-permission configuration.
user-invocable: true
invocation-name: Dev10x:permission-maintenance
allowed-tools:
  - Bash(${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/scripts/:*)
  - Agent(Dev10x:permission-auditor)
---

# Permission Maintenance

**Announce:** "Using permission-maintenance to maintain Claude Code
permission settings across all projects."

## Orchestration

This skill follows `references/task-orchestration.md` patterns.

**Auto-advance:** Complete each step, immediately start the next.
Run dry-run first, then apply — no pause between steps.

**REQUIRED: Create tasks before ANY work.** Execute these
`TaskCreate` calls at startup:

1. `TaskCreate(subject="Update version paths", activeForm="Updating paths")`
2. `TaskCreate(subject="Ensure base permissions", activeForm="Ensuring base perms")`
3. `TaskCreate(subject="Generalize session-specific permissions", activeForm="Generalizing perms")`
4. `TaskCreate(subject="Merge worktree permissions", activeForm="Merging worktree perms")`
5. `TaskCreate(subject="Audit permissions for friction", activeForm="Auditing permissions")`
6. `TaskCreate(subject="Clean project files", activeForm="Cleaning project files")`

Set sequential dependencies. Mark each step `in_progress` when
starting and `completed` when done. Steps that produce no
changes (dry-run shows no diff) should still be marked
`completed` with a note in the description.

## When to Use

- After installing a new Dev10x plugin version
- When `Bash()` allow rules fail because paths reference an old version
- After `claude plugin update`
- When worktree sessions accumulate useful permissions the main project lacks
- When permissions contain session-specific args (ticket IDs, PR numbers) that should be generalized for future sessions
- When you suspect allow rules cause friction by permitting script calls that should use skills instead

## First-Time Setup

Initialize userspace config with your project roots:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/scripts/update-paths.py --init
```

Then edit `~/.claude/skills/Dev10x:permission-maintenance/projects.yaml`
to add your project roots.

## Workflow

### 1. Update version paths

1. Dry run first to preview changes:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/scripts/update-paths.py --dry-run
```

2. Apply updates:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/scripts/update-paths.py
```

### 2. Ensure base permissions

Add missing base permissions (gh CLI, /tmp/claude paths, git ops, MCP
tools) to all settings files. The base set is defined in `projects.yaml`
under `base_permissions:`.

1. Dry run:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/scripts/update-paths.py --ensure-base --dry-run
```

2. Apply:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/scripts/update-paths.py --ensure-base
```

### 3. Generalize session-specific permissions

Replace permission rules containing session-specific arguments (ticket
IDs, PR numbers, temp file hashes) with generalized wildcard patterns
that work across future sessions.

1. Dry run to preview generalizations:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/scripts/update-paths.py --generalize --dry-run
```

2. Apply generalizations:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/scripts/update-paths.py --generalize
```

**What gets generalized:**
- `detect-tracker.sh PAY-123` → `detect-tracker.sh *` (ticket IDs)
- `gh-pr-detect.sh 42` → `gh-pr-detect.sh *` (PR numbers)
- `gh-issue-get.sh 15` → `gh-issue-get.sh *` (issue numbers)
- `generate-commit-list.sh 42` → `generate-commit-list.sh *` (PR args)
- `/tmp/claude/git/msg.AbCdEf.txt` → `/tmp/claude/git/**` (temp hashes)

### 4. Merge worktree permissions

Worktrees accumulate allow rules during sessions that the main project
never sees. This script collects stable permissions from all worktrees
and merges them back.

1. Dry run to preview:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/scripts/merge-worktree-permissions.py --dry-run
```

2. Apply merge:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/scripts/merge-worktree-permissions.py
```

Session-specific noise (temp file hashes, inline conditionals, ticket-
specific script args) is filtered out automatically. Only stable,
reusable permissions are merged.

### 5. Audit permissions for friction

Dispatch the `permission-auditor` agent to perform a comprehensive
7-phase security and friction audit. The agent analyzes:

- Overly broad allow rules that should be narrowed
- Script-call permissions that should use skills instead
- Missing deny rules for destructive operations
- Dead rules blocked by hooks
- Hardcoded paths in instruction files

**Invoke:** Launch the `permission-auditor` agent via:

```
Agent(subagent_type="Dev10x:permission-auditor",
    description="Audit permission settings",
    prompt="Audit all Claude Code permission settings for security
    gaps, overly broad rules, and friction-causing patterns.
    Pay special attention to allow rules that permit direct script
    calls when equivalent skills exist — these cause friction and
    should be replaced with Skill() invocations or blocked.")
```

The agent produces a severity-categorized report with specific fix
proposals. Review and apply selectively.

### 6. Clean project files

Strip redundant rules from project `settings.local.json` files that are
now covered by global `~/.claude/settings.json`. Also flags rules
containing leaked secrets (env vars with plaintext credential values).

1. Dry run to preview:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/scripts/clean-project-files.py --dry-run
```

2. Apply cleanup:

```bash
${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/scripts/clean-project-files.py
```

**What gets cleaned:**
- Exact duplicates of global rules
- Rules covered by global wildcard patterns (MCP families, plugin path wildcards)
- Old plugin version paths (any version older than current)
- Env-prefixed session noise (`GIT_SEQUENCE_EDITOR=*`, `DATABASE_URL=*`, etc.)
- Shell control flow fragments (`do`, `done`, `fi`, `for`, `while`, etc.)
- Double-slash path typos (`Read(//work/...)`)

**Leaked secret detection:** Rules containing plaintext credentials
(e.g., `LINEAR_KEY=lin_api_...`) are flagged with warnings so users
know they were persisted in settings files and can rotate them.

## Configuration

The script looks for `projects.yaml` in two locations (first wins):
1. `~/.claude/skills/Dev10x:permission-maintenance/projects.yaml` (userspace)
2. `${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/projects.yaml` (plugin default)

The userspace config is user-specific and not tracked in git.
The plugin default ships with empty roots as a template.

## Options

### update-paths.py

| Flag | Purpose |
|------|---------|
| `--dry-run` | Preview changes without writing |
| `--version X.Y.Z` | Target a specific version instead of latest |
| `--init` | Copy plugin default config to userspace for customization |
| `--ensure-base` | Add missing base permissions from projects.yaml |
| `--generalize` | Replace session-specific args with wildcard patterns |

### merge-worktree-permissions.py

| Flag | Purpose |
|------|---------|
| `--dry-run` | Preview what would be merged without writing |

### clean-project-files.py

| Flag | Purpose |
|------|---------|
| `--dry-run` | Preview what would be cleaned without writing |
