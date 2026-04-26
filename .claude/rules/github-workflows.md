---
paths:
  - ".github/workflows/**/*.yml"
  - ".github/workflows/**/*.yaml"
---

# GitHub Workflow Guidelines

Rules for GitHub Actions workflow files.

## Claude Code Workflows

This repository uses four Claude-powered workflows:

1. **claude.yml** - Interactive assistant triggered by @claude mentions
2. **claude-code-review.yml** - Automated PR code reviews
3. **claude-memory-review.yml** - Post-PR lessons learned analysis
4. **claude-pr-hygiene.yml** - PR metadata quality check on
   `opened` / `ready_for_review`

## Multi-Agent Architecture

The code review workflow (`claude-code-review.yml`) uses a
domain-routed architecture:

- **Orchestrator prompt** classifies changed files and dispatches
  to domain-specific agent specs in `.claude/agents/`
- **Agent specs** contain focused checklists and reference rules
  on demand from `.claude/rules/`
- **Cross-cutting checks** in `review-checks-common.md` apply to
  all domains

See `.claude/rules/INDEX.md` for the full architecture.

## Shared Guidelines

Review guidelines are centralized in:
- `references/review-guidelines.md` (workflow)
- `references/review-checks-common.md` (cross-cutting checks)
- `.claude/agents/*.md` (domain-specific checklists)

Workflows should reference these files rather than duplicating content.

## Workflow Optimization

- Keep prompts minimal — reference agent specs and rules on demand
- Add `Read` tool to `claude_args` so Claude can load files on-demand
- Use context variables for dynamic values (repository, PR number)
- Only load agent specs for domains with changed files

## Conditional Execution Pattern

### Two-Layer Filtering

1. **Event-level filtering** (`paths:`) — prevents workflow from
   queuing, saving GitHub Actions minutes
2. **Step-level conditional** (`if:`) — skips steps when no relevant
   files changed, providing additional safety

## Concurrency Groups

All PR-triggered workflows use concurrency groups to prevent duplicate
runs when multiple events fire in quick succession.

### Pattern

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

Apply to all PR-triggered workflows running expensive operations.

*Why?* When `ready_for_review` and `synchronize` events fire within
seconds, workflows listening to both fire twice — wasting CI minutes.

## Code Review Workflow Scope

The `claude-code-review.yml` workflow excludes **only** Claude-specific
workflows to prevent recursive review loops:

```yaml
paths:
  - "!.github/workflows/claude*.yml"
```

**All other workflow files are reviewed.** When modifying
Claude-excluded workflows, ensure manual review.

### Documentation in Review Scope

The review workflow also triggers on documentation changes:

```yaml
paths:
  - "CLAUDE.md"
  - ".claude/rules/**/*.md"
  - ".claude/agents/**/*.md"
```

## Hardcoded Branch Names Are a Bug

When a workflow step hardcodes a branch name, it will fail for PRs
that target a different branch.

```yaml
# BAD — fails for release PRs targeting main
run: git checkout develop

# GOOD — uses the PR's actual base branch
run: git checkout "${{ github.event.pull_request.base.ref }}"
```

## Branch Creation Idempotency

Use `git checkout -B` instead of `git checkout -b` so re-runs
don't fail on an existing branch.

```bash
# BAD — fails on re-run
git checkout -b "my-branch-$PR_NUMBER"

# GOOD — idempotent
git checkout -B "my-branch-$PR_NUMBER"
```

## Security

- Never expose secrets in prompts or logs
- Use `${{ secrets.* }}` for sensitive values
- Limit tool permissions to what's necessary
