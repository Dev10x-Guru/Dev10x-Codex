---
name: Dev10x:scope
invocation-name: Dev10x:scope
description: >
  Base scoping skill for technical research and architecture design.
  Provides reusable scoping workflow for investigating codebases,
  designing solutions, and documenting decisions.
  TRIGGER when: performing technical research or architecture design
  without a specific tracker integration.
  DO NOT TRIGGER when: scoping a Linear ticket (use Dev10x:ticket-scope),
  documenting an ADR (use Dev10x:adr), or scoping a project (use
  Dev10x:project-scope).
user-invocable: false
allowed-tools:
  - Agent
  - WebFetch
  - Grep
  - Glob
  - Read
  - Bash(java -jar:*)
  - AskUserQuestion
  - TaskCreate
  - TaskUpdate
---

# Dev10x:scope — Base Technical Scoping

## Overview

Foundational scoping skill that provides reusable research and
architecture design workflows. Not directly invocable — extended by:

- `Dev10x:ticket-scope` — for scoping Linear tickets
- `Dev10x:adr` — for creating Architecture Decision Records

## Orchestration

This skill follows `references/task-orchestration.md` patterns.

**Auto-advance:** Complete each phase, immediately start the next.
Never pause between phases.

**REQUIRED: Create tasks before ANY work.** Execute these
`TaskCreate` calls at startup:

1. `TaskCreate(subject="Gather technical context", activeForm="Gathering context")`
2. `TaskCreate(subject="Design solution architecture", activeForm="Designing solution")`
3. `TaskCreate(subject="Create implementation plan", activeForm="Planning implementation")`
4. `TaskCreate(subject="Document architecture and decisions", activeForm="Documenting")`
5. `TaskCreate(subject="Validate against principles", activeForm="Validating design")`

Set sequential dependencies. Update status as each completes.

**Background exploration at startup:** Immediately on invocation,
launch a background Explore agent to pre-fetch codebase context
for the topic. This agent runs concurrently while tasks are
created and the user is interviewed — results are ready by the
time Phase 1 needs them. See "Startup: Background Exploration"
below.

**Parallel research in Phase 1:** Dispatch Explore subagents for
independent research paths (external docs, codebase patterns,
test expectations) — collect results before moving to Phase 2.

**Decision gate after Phase 2:** Queue a decision for supervisor
review of the proposed architecture before creating the
implementation plan. If no other tasks are running, present
immediately.

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text, call spec: [ask-design-approval.md](./tool-calls/ask-design-approval.md)).
Options:
- Proceed to implementation plan (Recommended) — Design looks good, create actionable steps
- Revise design — I have corrections to the architecture
- More research needed — Need to explore additional patterns

## Startup: Background Exploration

**Launch immediately on invocation, before creating tasks or
asking the user any questions.** This pre-fetches codebase
context so it is ready when Phase 1 needs it.

```
Agent(subagent_type="Explore",
    model="haiku",
    description="Pre-fetch codebase context for [topic]",
    prompt="""Explore the codebase for patterns related to [topic].
    Return:
    - Relevant file paths and their purpose
    - Existing patterns and conventions in this area
    - Components that may need to change
    - Test files covering related functionality
    Keep response concise — 10-20 key findings.""",
    run_in_background=true)
```

Store the agent ID. When Phase 1 begins (after tasks are
created), wait for the agent to complete and merge its
findings into Phase 1.3 (Explore Existing Codebase).

If the agent is still running when Phase 1.3 starts, wait
for it rather than dispatching a duplicate Explore agent.

## Core Scoping Workflow

### Phase 1: Context Gathering

**Goal:** Understand the problem space before proposing solutions.

Dispatch parallel Explore subagents for independent research:

```
Agent(subagent_type="Explore",
    description="Research external documentation",
    prompt="Fetch and summarize relevant docs for [topic]. Return: key concepts, APIs, constraints.",
    run_in_background=true)
Agent(subagent_type="Explore",
    description="Find codebase patterns",
    prompt="Search for similar components in [repo]. Return: pattern names, file paths, signatures.",
    run_in_background=true)
```

Collect results, then proceed through sub-steps:

#### 1.1 Identify Starting Point

Determine what you're scoping:
- **External input** (URL, documentation, API docs)
- **Codebase exploration** (find patterns, understand current state)
- **Problem statement** (user-defined requirements)

#### 1.2 Research External Resources

If external documentation is relevant:

1. Fetch documentation using WebFetch
2. Extract key concepts, APIs, patterns
3. Note requirements, constraints, best practices
4. Identify integration points with existing code

#### 1.3 Explore Existing Codebase

Search for related patterns and implementations:

```bash
# Find similar patterns
Grep: "class.*Creator|Service|Handler"
Glob: "src/**/client/*.py"

# Read existing implementations
Read: Similar service files
Read: Related tests for behavior expectations
```

**Key questions:**
- What patterns exist for similar functionality?
- What components already exist that we can reuse?
- What naming conventions are used?
- How is dependency injection configured?

#### 1.4 Identify Components

Document what exists vs. what's needed:

| Category | Existing | New/Modified |
|----------|----------|--------------|
| **Repositories** | List existing | List new |
| **Services** | List existing | List new |
| **DTOs** | List existing | List new |
| **Models** | List existing | List new |
| **APIs** | List existing | List new |

Mark phase transition: `TaskUpdate(taskId=gather_task, status="completed")` then `TaskUpdate(taskId=design_task, status="in_progress")`

### Phase 2: Solution Design

**Goal:** Design architecture that follows existing patterns.

#### 2.1 Follow Existing Patterns

**CRITICAL:** Always follow established patterns in the codebase.

1. Search for similar components: `Grep "class.*Service"`
2. Read the pattern: Read existing service file
3. Extract the structure (e.g., Entry Point → Service → Client)
4. Apply to new component with same layering

#### 2.1b Design It Twice (Competitive Multi-Agent Exploration)

After gathering requirements, spawn 3 parallel design agents with
competing constraints. Each agent produces an independent proposal.
A synthesis step then compares them before the user sees anything.

**Launch 3 agents concurrently:**

```
Agent(subagent_type="Explore", model="opus",
    description="Design: Minimize complexity",
    prompt="""Design [feature] with the constraint: minimize
    complexity. Prefer fewest components, simplest data model,
    least code. Return: component list, data flow, trade-offs.""",
    run_in_background=true)

Agent(subagent_type="Explore", model="opus",
    description="Design: Maximize flexibility",
    prompt="""Design [feature] with the constraint: maximize
    flexibility for future extension. Use abstractions, plugin
    points, and extension interfaces. Return: component list,
    data flow, trade-offs.""",
    run_in_background=true)

Agent(subagent_type="Explore", model="opus",
    description="Design: Optimize for existing patterns",
    prompt="""Design [feature] to match the existing codebase
    patterns as closely as possible. Reuse existing abstractions,
    follow established conventions. Return: component list,
    data flow, trade-offs.""",
    run_in_background=true)
```

**After all three return**, synthesize:
1. Identify common structure across proposals
2. Note where they diverge and why
3. Recommend: best single approach OR a hybrid
4. Present synthesis as the proposed design in Phase 2.3

**Skip Design It Twice when:**
- Work is a bug fix or simple config change (no design needed)
- Implementation path is already clearly defined from Phase 1
- User passes `--quick` argument to the skill

#### 2.2 Apply Design Principles

**YAGNI (You Aren't Gonna Need It):**
- Don't return data that won't be used
- Prefer void methods over rich return types unless needed
- Remove unused fields from responses

**SRP (Single Responsibility Principle):**
- Each component has one job
- Entry point loads/validates, service orchestrates, client
  calls external API

**Clean Architecture:**
- Keep frameworks at edges
- Business logic independent of infrastructure
- Dependency inversion (depend on abstractions)

#### 2.3 Design Components

For each new component, define:

```
Component: [Name]
Location: [File path]
Responsibility: [Single sentence]
Pattern: [Reference to existing pattern]
Signature: [Method signatures with types]
Dependencies: [What it needs injected]
```

After design, queue the approval decision (see Orchestration
section above). Auto-advance to Phase 3 after approval.

Mark phase transition: `TaskUpdate(taskId=design_task, status="completed")` then `TaskUpdate(taskId=plan_task, status="in_progress")`

### Phase 3: Implementation Planning

**Goal:** Create actionable implementation steps.

#### 3.1 Order Steps Logically

Consider dependencies between steps:
1. Types/DTOs first (no dependencies)
2. Client layer (depends on types)
3. Service layer (depends on client)
4. Entry point (depends on service)
5. Tests (depends on implementation)

#### 3.2 Include Code References

Each step should include:
- **File path:** Where to make changes
- **Pattern reference:** Link to similar existing code
- **Code example:** Skeleton or key signatures

#### 3.3 Identify Risks

**Technical Risks:**
- Breaking changes
- Performance implications
- Security considerations
- Data integrity

**Mitigation strategies** for each risk.

Mark phase transition: `TaskUpdate(taskId=plan_task, status="completed")` then `TaskUpdate(taskId=doc_task, status="in_progress")`

### Phase 4: Documentation

**Goal:** Create clear, actionable documentation.

#### 4.1 Document Architecture

Create diagrams when helpful:
- Component diagrams (what talks to what)
- Sequence diagrams (flow of operations)
- Data flow diagrams (how data moves)

**PlantUML for diagrams** (bundled with this skill):
```bash
java -jar skills/scope/bin/plantuml.jar diagram.puml
```

#### 4.2 Document Decisions

For significant decisions, document:
- **Context:** Why we needed to decide
- **Decision:** What we chose
- **Consequences:** What becomes easier/harder
- **Alternatives:** What we considered and rejected

Mark phase transition: `TaskUpdate(taskId=doc_task, status="completed")` then `TaskUpdate(taskId=validate_task, status="in_progress")`

### Phase 5: Review and Iterate

**Goal:** Refine based on feedback.

#### 5.1 User Feedback Loop

Present findings to user and incorporate corrections:
- Architecture adjustments
- Pattern corrections
- Business context additions
- YAGNI simplifications

#### 5.2 Validate Against Principles

Before finalizing, check:
- [ ] Follows existing codebase patterns?
- [ ] YAGNI applied (no unused features)?
- [ ] SRP maintained (single responsibility)?
- [ ] Clean Architecture respected?
- [ ] Dependencies properly ordered?
- [ ] Risks identified and mitigated?

## Scoping Checklist

### Context
- [ ] Problem understood
- [ ] External resources reviewed (if any)
- [ ] Existing code patterns identified
- [ ] Reusable components found

### Design
- [ ] Follows existing patterns
- [ ] YAGNI applied
- [ ] SRP maintained
- [ ] Components clearly defined
- [ ] Dependencies identified

### Implementation
- [ ] Steps ordered logically
- [ ] File paths specified
- [ ] Pattern references included
- [ ] Code examples provided
- [ ] Tests considered

### Documentation
- [ ] Architecture documented
- [ ] Decisions explained
- [ ] Diagrams created (if helpful)
- [ ] Risks listed with mitigations

### Review
- [ ] User feedback incorporated
- [ ] Principles validated
- [ ] Ready for implementation

## Integration Points

This skill is extended by:

### Dev10x:ticket-scope
Adds:
- Linear ticket integration
- Ticket creation/updates
- Story point estimation
- Acceptance criteria format

### Dev10x:adr
Adds:
- ADR format and numbering
- Decision record structure
- Alternatives considered section
- Consequences documentation
- Diagram generation workflow

### Dev10x:jtbd
Provides:
- JTBD Job Story drafting methodology
- Context gathering from tickets and PR diffs
- Attended and unattended drafting modes
- Used by extending skills (Dev10x:ticket-scope, Dev10x:work-on, pr:create)

## Key Learnings from Practice

### Pattern Following is Critical

When designing new components, find and follow existing patterns:

1. Search for similar components: `Grep "class.*Service"`
2. Read the pattern: Read existing service file
3. Extract the structure: Entry Point → Service → Client
4. Apply to new component with same layering

### User Corrections Are Valuable

User corrections reveal:
- Business context not visible in code
- Organizational preferences
- Future plans affecting design
- Domain knowledge gaps

Always incorporate corrections and update documentation.

### YAGNI Reduces Complexity

When unsure if a feature is needed:
- Start without it
- Add when actually needed
- Remove unused code

### Diagrams Aid Understanding

Visual diagrams help communicate:
- Component relationships
- Data flow
- Sequence of operations

Use PlantUML for consistent, version-controlled diagrams.
