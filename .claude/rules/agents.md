---
paths:
  - "agents/**"
---

# Plugin-Distributed Agent Specs

Rules for authoring and maintaining sub-agent specifications in the
`agents/` directory—distinct from internal review agents.

## Directory Purpose

| Directory | Purpose | Audience |
|-----------|---------|----------|
| `.claude/agents/` | Internal review-only agent checklists | Code review automation |
| `agents/` | Plugin-distributed operational specs | End users / skill workflows |

## Sizing & Structure

Plugin-distributed agents (in `agents/`) have a **200-line budget** and must
include full phase logic and examples, as opposed to internal review agents
(`.claude/agents/`) which are ~50-line checklists.

**Structure template:**
- Phase 1: Initial prompt/context
- Phase 2: Analysis/exploration
- Phase 3: Plan or decision point
- Examples and use cases
- Tool definitions (if custom)

## When to Use Each Directory

**Create in `.claude/agents/`** if the spec is:
- A code review checklist (scoped to changed files)
- Triggered by CI/automation
- ≤ 50 lines
- Examples: `reviewer-skill.md`, `reviewer-infra.md`

**Create in `agents/`** if the spec is:
- A user-invoked sub-agent for a workflow
- Shipped as part of the plugin distribution
- ≤ 200 lines (including examples)
- Examples: `permission-auditor.md`

## File Naming

Use the feature name as-is: `agents/permission-auditor.md`, `agents/audit-deps.md`.
Do NOT add a `Dev10x-` prefix to the filename.

## Linking from Skills

Reference distributed agents in skill definitions via `SKILL.md`:
```yaml
agents:
  - agents/permission-auditor.md
```

See `.claude/rules/skill-naming.md` for invocation name conventions.
