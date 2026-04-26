---
name: Dev10x-scope
description: Base scoping skill for technical research and architecture design. Provides reusable scoping workflow for investigating codebases, designing solutions, and documenting decisions. Used as foundation by Dev10x:ticket-scope (Linear tickets) and Dev10x:adr (Architecture Decision Records).
---

# Dev10x:scope — Base Technical Scoping

## Overview

Foundational scoping skill that provides reusable research and
architecture design workflows. Not directly invocable — extended by:

- `Dev10x:ticket-scope` — for scoping Linear tickets
- `Dev10x:adr` — for creating Architecture Decision Records

## Core Scoping Workflow

### Phase 1: Context Gathering

**Goal:** Understand the problem space before proposing solutions.

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

### Phase 2: Solution Design

**Goal:** Design architecture that follows existing patterns.

#### 2.1 Follow Existing Patterns

**CRITICAL:** Always follow established patterns in the codebase.

1. Search for similar components: `Grep "class.*Service"`
2. Read the pattern: Read existing service file
3. Extract the structure (e.g., Entry Point → Service → Client)
4. Apply to new component with same layering

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
