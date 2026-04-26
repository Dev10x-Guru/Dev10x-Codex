# Model & Effort Selection for Agent Dispatch

Guide for choosing the right model and reasoning effort when
dispatching sub-agents from skills.

## Decision Framework

Match model capability to task complexity. Over-provisioning
wastes tokens; under-provisioning produces poor results.

| Tier | Model | When to use |
|------|-------|-------------|
| **Monitor** | `haiku` | CI polling, status checks, log watching |
| **Gather** | `haiku` | Context fetching, API calls, data collection |
| **Replicate** | `haiku`/`sonnet` | Replicating existing patterns, boilerplate, mechanical transforms |
| **Analyze** | `sonnet` | Pattern matching, triage, test validation |
| **Review** | `opus` | Code review, PR review, architecture review |
| **Design** | `opus` | New classes/components, architecture decisions, complex design |
| **Investigate** | `opus` | Root cause analysis, deep debugging, cross-system tracing |

## Applying the Framework

### Named agents (agent specs in `agents/`)

Set `model:` in the agent spec frontmatter. The model applies
automatically whenever the agent is dispatched:

```yaml
model: sonnet   # Most review and analysis agents
model: opus     # Architecture advisors, deep investigation
```

### Generic-purpose agents (dispatched from skills)

Specify `model:` explicitly in the Agent call. Without it,
the agent inherits the session default (often Opus), which
is wasteful for simple tasks:

```
Agent(
    subagent_type="general-purpose",
    model="haiku",
    description="Fetch issue context",
    prompt="...",
    run_in_background=true
)
```

### Skills that skip model selection

If a skill dispatches a generic-purpose agent without specifying
`model:`, it runs at the session default. This is acceptable
ONLY for **Design** and **Investigate** tier tasks that need
the most capable model. All other tiers MUST specify the model
explicitly to avoid wasting tokens on simple tasks.

## Current Assignments

### Agent specs (`agents/`)

| Model | Agents |
|-------|--------|
| `sonnet` | All reviewer-*, architect-*, adr-reviewer, permission-auditor, pytest-tester, pytest-test-writer, infrastructure-investigator |
| `opus` | code-reviewer, architecture-advisor, issue-investigator |

### Skills with generic-purpose dispatch

| Skill | Tier | Model |
|-------|------|-------|
| `gh-pr-monitor` | Monitor | `haiku` |
| `work-on` (Phase 2 gather) | Gather | `haiku` |
| `skill-audit` (Wave 1+2) | Analyze | `sonnet` |
| `adr-evaluate` (architects) | Design | `opus` |

## User Overrides via Playbooks

Users can override model assignments per project by adding
`model:` to playbook steps. See `references/model-tiers.md`
for the full user-facing guide including examples.

Override resolution order:
1. Step-level `model:` in user playbook override (highest)
2. Step-level `model:` in default playbook
3. Skill's hardcoded model (SKILL.md Agent dispatch)
4. Agent spec `model:` frontmatter (named agents)
5. Session default model (lowest)

When executing a playbook step with `model:`, use that model
for any agent dispatch during the step instead of the skill's
hardcoded default.

## When to Revisit

- Adding a new agent spec → choose model per tier table
- Adding agent dispatch to a skill → specify model explicitly
- Task proves too complex for its tier → promote one tier up
- User reports cost concerns → point to `references/model-tiers.md`
