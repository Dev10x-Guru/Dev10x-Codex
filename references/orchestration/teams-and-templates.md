# Teams and Orchestration Templates

## Pattern 5: Teams for Heavy Parallelism

Use `TeamCreate` when multiple agents need to coordinate on
shared state or when work products must be merged. Teams are
heavier than ad-hoc agents — use only when:

- 3+ independent implementation tasks exist
- Each task produces files that don't conflict
- A merge/review step follows

For most skill workflows, parallel `Agent` calls with
`run_in_background=true` are sufficient.

## Pattern 6: Full Orchestration Template

For Tier "Full" skills, structure the SKILL.md like this:

```markdown
## Phase 1: Gather Context

TaskCreate(subject="Gather context", activeForm="Gathering context")

[Dispatch parallel subagents for research]
[Collect results, summarize]

TaskUpdate(taskId, status="completed")

## Phase 2: Plan

TaskCreate(subject="Build execution plan", activeForm="Planning")

[Generate sub-tasks via TaskCreate]
[Set dependencies via TaskUpdate addBlockedBy]

AskUserQuestion: Approve plan? (Approve / Edit)

TaskUpdate(taskId, status="completed")

## Phase 3+: Execute

[Auto-advance through tasks]
[Expand epics into sub-tasks when reached]
[Mutate plan if scope changes]
[Dispatch subagents for independent work]

## Final: Verify

[Check acceptance criteria]
[Report completion]
```

## Pattern 7: Lightweight Orchestration Template

For Tier "Light" skills, use a single task with status updates:

```markdown
TaskCreate(subject="Create PR for TICKET-123",
    description="Validate state, generate body, run checks, push",
    activeForm="Creating PR")

### Step 1: Validate
[Auto — script call]

### Step 2: Generate PR body
[Auto — template + Job Story]

### Step 3: Decision gate
AskUserQuestion: Approve PR title and body? (Approve / Edit)

### Step 4: Pre-PR checks
[Auto — script call, activeForm="Running pre-PR checks"]

### Step 5: Push and create
[Auto — script call]

TaskUpdate(taskId, status="completed")
```
