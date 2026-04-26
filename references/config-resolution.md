# Configuration Resolution

Central reference for Dev10x configuration file paths, resolution
order, and project mapping format.

## Three-Tier Resolution

All Dev10x configuration files follow a consistent resolution order:

| Priority | Location | Scope | Committed? |
|----------|----------|-------|------------|
| 1 (highest) | `.claude/Dev10x/` | Project-local | No (gitignored) |
| 2 | `~/.claude/memory/Dev10x/` | Global with repo mapping | N/A (user home) |
| 3 (deprecated) | `~/.claude/projects/<project>/memory/` | Per-project | N/A (user home) |
| 4 (lowest) | `${CLAUDE_PLUGIN_ROOT}/skills/*/references/` | Plugin defaults | Yes (plugin repo) |

**Tier 1 — Project-local** (`.claude/Dev10x/`):
Runtime and session data. Highest priority for truly project-specific
overrides that should not be shared across repos. Gitignored.

**Tier 2 — Global with repo mapping** (`~/.claude/memory/Dev10x/`):
Single file serves multiple projects via `projects[].match` globs.
Preferred for overrides that apply to several repos (e.g., all
ExampleCorp repos share the same shipping pipeline).

**Tier 3 — Legacy per-project** (`~/.claude/projects/<project>/memory/`):
Deprecated. Existing files still work as fallback. New overrides
should use Tier 2 instead. Skills that find files here should log
a deprecation notice.

**Tier 4 — Plugin defaults** (`${CLAUDE_PLUGIN_ROOT}/skills/*/references/`):
Shipped with the plugin. Used when no user override exists.

## Project Mapping Format

Global config files (Tier 2) use a `projects` list with glob
matching on the repo's `nameWithOwner` (e.g., `org/repo`).
Match uses standard Unix glob syntax (`fnmatch`): `*` matches any
string, `?` matches a single character, `[seq]` matches any character
in *seq*.

```yaml
projects:
  - match: "Dev10x-Guru/dev10x-claude"
    # config specific to this repo

  - match: "org/*"
    # config shared across all ExampleCorp repos
```

**Resolution within Tier 2:**
1. Get current repo: `git remote get-url origin` → extract `owner/repo`
2. Walk the `projects` list — first `match` glob that fits selects
   the config block
3. If no match, skip Tier 2 (fall through to Tier 3 or 4)

This follows the same pattern as `gitmoji.yaml` project overrides.

## Configuration Files

### Playbooks

| Tier | Path | Format |
|------|------|--------|
| 1 | `.claude/Dev10x/playbooks/<key>.yaml` | Standard playbook YAML |
| 2 | `~/.claude/memory/Dev10x/playbooks/<key>.yaml` | Playbook + `projects` mapping |
| 3 | `~/.claude/projects/<project>/memory/playbooks/<key>.yaml` | Standard playbook YAML (deprecated) |
| 4 | `${CLAUDE_PLUGIN_ROOT}/skills/<key>/references/playbook.yaml` | Default playbook |

**Global playbook format** (Tier 2):

```yaml
# ~/.claude/memory/Dev10x/playbooks/work-on.yaml

fragments:
  shipping-pipeline-solo:
    - subject: Code review
      type: detailed
      skills: [dev10x:review, dev10x:review-fix]
    # ...

projects:
  - match: "Dev10x-Guru/dev10x-claude"
    active_modes: [solo-maintainer]
    overrides:
      - play: feature
        steps:
          - subject: Set up workspace
            type: detailed
            skills: [dev10x:ticket-branch]
          # ...

  - match: "example-org/*"
    active_modes: [solo-maintainer]
    overrides:
      - play: feature
        steps: [...]
```

**Backward compatibility:** When resolving a playbook, check Tier 1
first, then Tier 2 with repo matching, then Tier 3 (legacy). If a
Tier 3 file is found, log: "Legacy playbook found at per-project
path. Consider migrating to ~/.claude/memory/Dev10x/playbooks/."

### Session Config

| Tier | Path | Notes |
|------|------|-------|
| 1 only | `.claude/Dev10x/session.yaml` | Session-scoped, not shared |

Session config is always project-local. It contains runtime state
(friction level, active modes) that is session-specific.

### PR Merge Settings

| Tier | Path | Format |
|------|------|--------|
| 2 | `~/.claude/memory/Dev10x/settings-pr-merge.yaml` | Settings + `projects` mapping |
| 3 | `~/.claude/projects/<project>/memory/settings-pr-merge.yaml` | Flat settings (deprecated) |

**Global format** (Tier 2):

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

### Acceptance Criteria

Already uses global format:

| Tier | Path |
|------|------|
| 2 | `~/.claude/memory/Dev10x/dod-acceptance-criteria.yaml` |
| 4 | Plugin defaults (hardcoded in skill) |

### Gitmoji Overrides

Already uses global format:

| Tier | Path |
|------|------|
| 2 | `~/.claude/memory/Dev10x/gitmoji.yaml` |
| 4 | `${CLAUDE_PLUGIN_ROOT}/skills/git-commit/references/gitmoji-defaults.yaml` |

### Database Schema

| Tier | Path |
|------|------|
| 2 | `~/.claude/memory/Dev10x/db-<name>-schema.md` |
| 3 | `~/.claude/projects/<project>/memory/db-<name>-schema.md` (deprecated) |

### GitHub Reviewers

Already uses global format:

| Tier | Path |
|------|------|
| 2 | `~/.claude/memory/Dev10x/github-reviewers-config.yaml` |

## Migrating Per-Project Overrides

To migrate an existing per-project playbook to the global format:

1. Read the per-project file:
   `~/.claude/projects/<project>/memory/playbooks/work-on.yaml`
2. Wrap its content under a `projects` entry in the global file:
   `~/.claude/memory/Dev10x/playbooks/work-on.yaml`
3. Add a `match` glob for the repo
4. If multiple repos share the same config, add multiple `match`
   entries or use wildcards
5. Delete the per-project file

## Skills That Reference These Paths

| Skill | Config type | Tiers used |
|-------|------------|------------|
| `Dev10x:work-on` | playbook, session | 1, 2, 3, 4 |
| `Dev10x:playbook` | playbook | 1, 2, 3, 4 |
| `Dev10x:gh-pr-respond` | playbook | 2, 3, 4 |
| `Dev10x:release-notes` | playbook | 2, 3, 4 |
| `Dev10x:investigate` | playbook | 2, 3, 4 |
| `Dev10x:gh-pr-merge` | settings | 2, 3 |
| `Dev10x:verify-acc-dod` | acceptance criteria | 2, 4 |
| `Dev10x:git-commit` | gitmoji | 2, 4 |
| `Dev10x:gh-pr-request-review` | reviewers | 2 |
| `Dev10x:db` | schema | 2, 3 |
| `Dev10x:fanout` | session | 1 |
