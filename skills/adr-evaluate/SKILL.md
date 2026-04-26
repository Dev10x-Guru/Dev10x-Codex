---
name: Dev10x:adr-evaluate
description: >
  Orchestrate adversarial evaluation of architectural options using
  domain-specific architect agents and produce ranked ADR drafts.
  TRIGGER when: evaluating design decisions with multiple competing
  approaches, running architecture trade-off analysis, or needing
  structured multi-perspective evaluation.
  DO NOT TRIGGER when: creating a simple ADR (use Dev10x:adr),
  or making code changes without architecture impact.
user-invocable: true
invocation-name: Dev10x:adr-evaluate
allowed-tools:
  - Agent
  - Glob
  - Grep
  - Read
  - AskUserQuestion
---

# ADR Evaluation Skill

Orchestrate adversarial discussion between architect agents to
evaluate architectural options and produce ranked ADR drafts.

## Input

The user provides:
- **Topic:** what decision needs to be made
- **ADR Number:** the target ADR number (optional)
- **Options:** 2-4 options to evaluate
- **Agent assignments:** which architect agent advocates for each
  option (optional — auto-assigned based on domain)

## Available Architect Agents

| Agent | Domain |
|-------|--------|
| `architect-api` | API design, schema, real-time |
| `architect-db` | Database, schema, multi-tenant |
| `architect-domain` | DDD, aggregates, bounded contexts |
| `architect-frontend` | Components, state, SSR, testing |
| `architect-infra` | Deployment, CI/CD, Docker, observability |

## Workflow

### Phase 1: Dispatch Advocates

For each option, launch the assigned architect agent as a parallel
subagent:

```
Agent(subagent_type="general-purpose",
    model="opus",                       # Design tier — architecture evaluation
    description="Advocate for Option N",
    prompt="""You are advocating for: [Option N — description]

    Context:
    - [Topic description]
    - [Relevant existing ADRs]
    - [Current code state summary]

    Your task:
    1. Read all relevant source files in the codebase
    2. Find evidence supporting your assigned option
    3. Count concrete metrics (models, files, LOC, patterns)
    4. Identify 3-5 arguments WITH file:line citations
    5. Identify risks of NOT choosing your option
    6. Be honest about weaknesses of your position

    Output format:
    ## Arguments for [Option N]
    1. [Argument with file:path evidence]

    ## Metrics
    - [Concrete counts and measurements]

    ## Risks of Alternatives
    - [What goes wrong if NOT chosen]

    ## Acknowledged Weaknesses
    - [Honest downsides]""",
    run_in_background=true)
```

### Phase 2: Synthesize

After all advocates return, launch the `adr-reviewer` agent with
all collected arguments. The reviewer:

1. Fact-checks at least 3 claims per advocate (reads cited files)
2. Identifies consensus points and genuine trade-offs
3. Ranks options by: architecture alignment, migration effort,
   long-term maintainability, team feasibility
4. Drafts ADR following project template

**Reviewer agent skip (acceptable):** When the main agent has
already accumulated sufficient codebase context from prior
research and advocate agents, it may perform the synthesis
inline without launching the `adr-reviewer` sub-agent. This
avoids an unnecessary round-trip while preserving the option
for complex evaluations where independent fact-checking adds
value.

### Phase 3: Present

Present the draft ADR to the user with:
- Ranked recommendation and confidence level
- Key trade-offs identified
- Unverified claims flagged
- Suggested next steps

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
Options:
- Accept recommendation
- Choose a different option
- Request deeper analysis on specific aspect
- Revise options and re-evaluate

## Usage Example

```
/Dev10x:adr-evaluate

Topic: State management approach for the dashboard
ADR Number: 025

Options to evaluate:
1. Server-side state via load functions
2. Client-side reactive store
3. Hybrid with server-first, client cache

Agent assignments:
- architect-frontend (Option 1): SSR patterns
- architect-frontend (Option 2): reactivity patterns
- architect-api (Option 3): data loading
```
