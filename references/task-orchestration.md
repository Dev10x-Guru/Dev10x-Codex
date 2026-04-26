# Task Orchestration Patterns

Shared reference for skills that manage multi-step workflows.
Skills reference this document; it is not loaded by default.

## Auto-Advance — Universal Rule

This rule applies to ALL skills, regardless of tier. It is the
single most important orchestration pattern.

**Always auto-advance.** Complete a step or task, immediately
start the next. Never pause to ask "should I continue?", "ready
for the next step?", or wait for the user to say "go" / "next" /
"continue". The invocation of the skill is the authorization to
proceed through all its steps.

```
TaskUpdate(taskId=current, status="completed")
TaskUpdate(taskId=next, status="in_progress")
# Begin next task work immediately — no pause
```

**Routine confirmations are not decisions** — skip progress
acknowledgments and "looks good?" checks. Keep going.

### Batched Decision Queue

When a task hits a genuine A/B decision that cannot be inferred
from context, do NOT interrupt the user immediately. Instead:

1. **Queue the decision** — record it in task metadata:
   ```
   TaskUpdate(taskId, status="pending",
       metadata={"decision_needed": "Which strategy: fixup vs restructure?",
                 "options": ["Fixup", "Full restructure", "Mass rewrite"]})
   ```
2. **Move to the next unblocked task** — continue advancing on
   any task that doesn't require this decision.
3. **Only interrupt when fully blocked** — when NO tasks can
   advance further without user input, collect ALL queued
   decisions into a single `AskUserQuestion` batch:
   ```
   AskUserQuestion(questions=[
       {question: "git-groom: Which restructuring strategy?",
        header: "Strategy", options: [...], multiSelect: false},
       {question: "scope: Approve context findings?",
        header: "Findings", options: [...], multiSelect: false},
       {question: "PR: Which comments to address?",
        header: "Comments", options: [...], multiSelect: true},
   ])
   ```
4. **Unblock and resume** — after the user answers, update all
   relevant tasks and resume auto-advancing.

**Why batch?** The supervisor should be able to step away, come
back to answer all pending decisions at once, then step away
again confident that maximum progress will happen before the
next interruption. One batch of 3 questions is better than 3
separate interruptions spaced minutes apart.

**AskUserQuestion supports 1-4 questions per call.** If more
than 4 decisions are queued, prioritize by dependency order —
ask decisions that unblock the most downstream work first.

**Always queue, never ask inline.** Even single-task skills
must queue their decisions rather than asking immediately. The
skill does not know whether other skills or agents are running
in parallel with their own pending decisions. The orchestrator
(session or work-on) collects all queued decisions and presents
them as a batch. This ensures the supervisor is interrupted
once with N questions, not N times with 1 question each.

## Mandatory Task Tracking — Universal Rule

**Every skill MUST use TaskCreate** — even single-step skills.
The task list is the supervisor's interface for tracking,
expanding, and coordinating work across skills and agents.

A skill with one step creates one task. The supervisor can then
split it into two, add follow-up tasks, or let other skills
contribute tasks to the same plan. Without TaskCreate, the
skill becomes invisible to the orchestration layer.

```
# Even a simple skill like git-alias-setup:
TaskCreate(subject="Configure git aliases",
    activeForm="Configuring git aliases")
# ... do work ...
TaskUpdate(taskId, status="completed")
```

### Delegated Invocation Exception (Nested-Mode Exemption)

When a skill is invoked as a subtask of a parent orchestrator (e.g.,
`Dev10x:work-on`), internal `TaskCreate` calls MAY be skipped or
reduced to at most **1 summary task**. The parent orchestrator owns
the task lifecycle and has already created tasks that track the child
skill's progress. Duplicate task trees add clutter without value.

**Detection:** A skill is running in nested mode when:
- It was invoked via the `Skill` tool from another skill's flow
- A parent task list already exists (check via `TaskList`)
- The skill received `--unattended` or similar delegation flags

**Behavior in nested mode:**
- Startup `TaskCreate` calls are OPTIONAL (at most 1 summary task)
- The parent orchestrator provides progress visibility
- Decision gates (AskUserQuestion) may be auto-resolved per the
  parent's unattended policy

When running as a top-level invocation (user types `/skill-name`),
`TaskCreate` is mandatory as documented above.

### Startup Gate (Full and Standard tiers)

Skills that list multiple `TaskCreate` calls in their
Orchestration section MUST execute all of them **before any
other work begins**. This is a blocking prerequisite, not
an illustration. If you find yourself reading files, calling
APIs, or analyzing data without having created the documented
tasks first, STOP and create them now.

When writing a skill's Orchestration section, use a numbered
list of `TaskCreate` calls (not a fenced code block). Code
blocks read as examples; numbered lists read as instructions.

### Complexity Tiers (guidance, not opt-out)

Tiers guide HOW MUCH orchestration a skill adds, not WHETHER
it participates. All tiers use TaskCreate + auto-advance.

| Tier | When | Additional patterns | Example skills |
|------|------|---------------------|----------------|
| **Full** | 4+ phases, 10+ min, decisions | TaskCreate per phase, AskUserQuestion gates, subagent dispatch, batched decisions | work-on, git-groom, gh-pr-respond, scope, qa-self |
| **Standard** | 3-6 steps, some decisions | TaskCreate per major step, AskUserQuestion for key choices | git-commit, gh-pr-create, gh-pr-review |
| **Minimal** | 1-2 steps, no decisions | Single TaskCreate, auto-advance, no gates | git-alias-setup, gh-pr-bookmark, park-todo |

## Pattern 1: Out-of-Order Execution

When the current task is blocked (waiting for user input, CI,
external dependency), check whether the next unblocked task can
start:

```
# Current task blocked — find next unblocked
TaskUpdate(taskId=current, status="pending", metadata={"blocked": "reason"})
tasks = TaskList()
next = first task where status="pending" AND blockedBy is empty
TaskUpdate(taskId=next, status="in_progress")
```

Return to the blocked task once the blocker resolves. Examples:
- Waiting for CI? Start self-review meanwhile.
- Waiting for user decision on approach? Draft the Job Story.
- External API timeout? Skip to documentation task.

## Pattern 2: Plan Mutation

Plans are living documents. When new information changes the
scope, mutate the plan rather than restarting:

```
# Add a task discovered mid-execution
TaskCreate(subject="Handle edge case X", ...)
TaskUpdate(taskId=new, addBlockedBy=[current])

# Remove a task that's no longer needed
TaskUpdate(taskId=obsolete, status="deleted")

# Reorder by updating dependencies
TaskUpdate(taskId=task_a, addBlockedBy=[task_b])
```

Announce mutations briefly: "Adding task for edge case X
discovered during implementation."

## Pattern 3: AskUserQuestion for Decisions

Replace all plain-text y/n questions with `AskUserQuestion`.
This gives the user structured widgets instead of free-text
input.

### When to use AskUserQuestion

| Scenario | Use AskUserQuestion? |
|----------|---------------------|
| A/B choice (strategy, approach) | Yes — options with descriptions |
| Approval gate (plan, PR body) | Yes — Approve / Edit / Skip |
| Error recovery (retry, skip, abort) | Yes — with context in descriptions |
| Free-text input (commit message body) | No — plain text is better |
| Confirmation of auto-detected value | Yes — Confirm / Change |

### Widget patterns

**Binary choice with preview:**
```
AskUserQuestion(questions=[{
    question: "Which commit restructuring strategy?",
    header: "Strategy",
    options: [
        {label: "Fixup (Recommended)", description: "Small targeted fixes to specific commits", preview: "git commit --fixup=<sha>\ngit rebase -i --autosquash"},
        {label: "Full restructure", description: "Reset and rebuild commit history from scratch"},
        {label: "Mass rewrite", description: "Non-interactive message rewrite from JSON config"},
    ],
    multiSelect: false
}])
```

**Multi-select for batch operations:**
```
AskUserQuestion(questions=[{
    question: "Which review comments should I address?",
    header: "Comments",
    options: [
        {label: "r101 — Use SubFactory", description: "VALID: Change LazyFunction to SubFactory in fakers.py:21"},
        {label: "r102 — Randomize values", description: "VALID: Use Faker() for all fields"},
        {label: "r103 — TYPE_CHECKING", description: "INVALID: 38+ files use this pattern"},
    ],
    multiSelect: true
}])
```

**Error recovery:**
```
AskUserQuestion(questions=[{
    question: "Tests failed. How to proceed?",
    header: "Recovery",
    options: [
        {label: "Fix and retry (Recommended)", description: "Adjust the script and re-run"},
        {label: "Skip this test case", description: "Mark as skipped, continue with remaining"},
        {label: "Abort", description: "Stop QA execution entirely"},
    ],
    multiSelect: false
}])
```

## Pattern 4: Subagent Dispatch

Use subagents to reduce main-session token usage. Feed them
only the context they need; receive only the summary back.

### When to dispatch subagents

| Scenario | Dispatch? |
|----------|-----------|
| Research/exploration (docs, codebase) | Yes — Explore agent |
| Independent triage (N items, no shared state) | Yes — parallel general agents |
| Sequential execution (rebase, ordered commits) | No — run inline |
| Quick lookup (single file read, one grep) | No — direct tool call |

### Dispatch pattern

```
Agent(
    subagent_type="Explore",
    description="Research payment retry patterns",
    prompt="""
    Context: We're implementing retry logic for Square payments.
    The current code is in src/payments/square_client.py.

    Find:
    1. Existing retry patterns in the codebase
    2. Square API documentation on idempotency
    3. Test patterns for retry scenarios

    Return: A summary of patterns found with file paths and
    line numbers. Do not return full file contents.
    """
)
```

**Key principles:**
- Include only relevant context in the prompt (not full conversation)
- Ask for summary output, not raw data
- Use `run_in_background=true` when you have other work to do
- Use `isolation="worktree"` when the agent needs to modify files
- **Specify `model:` explicitly** for generic-purpose agents —
  see `.claude/rules/model-selection.md` for the tier framework:
  `haiku` for monitoring/gathering, `sonnet` for analysis,
  `opus` for code review and architecture decisions

### Parallel dispatch

When N items need independent processing, spawn agents in a
single tool-call block:

```
# Triage 4 PR comments in parallel
Agent(description="Triage comment r101", prompt="...", run_in_background=true)
Agent(description="Triage comment r102", prompt="...", run_in_background=true)
Agent(description="Triage comment r103", prompt="...", run_in_background=true)
Agent(description="Triage comment r104", prompt="...", run_in_background=true)
```

Collect results as notifications arrive. Update tasks accordingly.

### Subagent Dispatch Patterns: Wave-Based Orchestration

When orchestrating multiple independent analysis phases, structure
work into logical waves with explicit task dependencies:

**Wave structure:**
1. **Setup (sequential)**: Create tasks, detect context, initialize state
2. **Wave 1 (parallel)**: Independent analysis phases with no inter-phase dependencies
3. **Wave 2 (parallel)**: Analysis phases dependent on Wave 1 output
4. **Synthesis (sequential)**: Consolidate findings, present decisions to user

**Task dependency annotation:**
```markdown
Set dependencies:
- Task 1→2→3: Sequential setup chain (prerequisite context)
- Task 4 and 5: Blocked by task 3 (Wave 1 — independent, run in parallel)
- Task 6, 7, 8: All blocked by task 4 (Wave 2 — run in parallel after Phase 1 output)
- Task 9: Blocked by tasks 4, 5, 6, 7, 8 (Synthesis — depends on all analysis)
```

**When to use wave-based orchestration:**
- Multiple independent analysis phases (e.g., 5+ parallel subagents)
- Partial dependencies between phases (some are independent, others depend on earlier outputs)
- Long-running workflows where parallelization saves significant time
- Example: `Dev10x:skill-audit` with 5 parallel analysis phases + dependency on Phase 1 output

## Fanout Execution (Multiple Items)

When executing a plan with multiple independent items (fanout), each item
MUST execute the **full orchestration pipeline** — not a collapsed subset.
Fanout does NOT exempt individual items from verification, grooming, or
review guardrails.

**Anti-pattern (PROHIBITED):**
```
for each issue:
  branch → edit → commit → push → create-pr   # 5 steps
```

This collapses the pipeline and skips:
- Verification (design review, implementation review)
- Grooming (commit message validation, fixup handling)
- Re-review (CI must run after grooming, pre-merge checks)

**Required pattern:**
```
for each issue:
  full play → branch → design → implement → verify →
  review → commit → groom → update → ready → verify-acc   # 12+ steps
```

**Why:** Evidence from audit session 05d49f11 showed that agents
rationalized pipeline collapse under fanout: "parallel processing
optimizes by reducing steps." This assumption was wrong. Each issue
requires independent verification and review. Parallel execution
(via Agent with `run_in_background=true`) is orthogonal to the
pipeline length — parallelizing execution does NOT justify skipping
steps.

**Phase reference pattern:**
Create a "Phase Reference" section in SKILL.md that documents each phase's
inputs, outputs, and instructions. This section can be pasted verbatim into
subagent prompts without modification:

```markdown
## Phase Reference

### Phase 1 (Output file: <PHASE1_OUTPUT>)
[Phase 1 instructions and acceptance criteria]

### Phase 2 (Output file: <PHASE2_OUTPUT>)
[Phase 2 instructions and acceptance criteria]

## Synthesis (Phase 6)
[Synthesis instructions]
Read all output files from phases 1-5 to synthesize findings.
```

Subagents receive only the relevant phase section, reducing prompt size and
improving focus.

**Cross-phase dependency handling:**
When a synthesis phase reads output from earlier phases, verify the dependency
list includes all upstream phase tasks. Example: If synthesis reads `<PHASE1_OUTPUT>`,
task 4 (Phase 1) must be in the synthesis task's `blockedBy` list.

### Permission-Aware Parallel Dispatch

When executing parallel work streams, classify each task **before dispatch**
to avoid Write/Edit tool failures in background agents:

| Task type | Write/Edit needed? | Dispatch method |
|-----------|-------------------|-----------------|
| Issue implementation | Yes | Main session via `Skill()` |
| PR with code fixes | Yes | Main session via `Skill()` |
| Conflict resolution | Yes | Main session via `Skill()` |
| PR ready-to-merge | No | Background `Agent()` OK |
| CI monitoring | No | Background `Agent()` OK |
| Investigation/analysis | No | Background `Agent()` OK |

**Decision rule**: If a task MAY create or edit files, it MUST run in the main
session via `Skill()`. Background agents are only safe for read-only operations
due to `bypassPermissions` non-propagation.

**Example**: A `fanout` skill routes a PR with unaddressed review comments
to `Skill()` for inline fixes, but routes a CI-green PR with no comments to
background `Agent()` for merge monitoring.

See `.claude/rules/essentials.md` "Permission & Tool Availability Limits"
for the complete constraint specification.

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

## Pattern 8: Progress Compaction

Long-running orchestrations (10+ tasks, multiple phases) accumulate
completed-task detail that consumes context window without aiding
future steps. Compact completed work into a brief status summary
so the agent can focus context budget on remaining tasks.

### When to Compact

Compact after completing a **phase boundary** or a **batch of 4+
related tasks**. Do not compact after every single task — the
overhead outweighs the benefit for small batches.

| Trigger | Example |
|---------|---------|
| Phase boundary | Phase 2 (Gather) complete, entering Phase 3 |
| Epic completion | All 5 sub-tasks of "Implement changes" done |
| Context pressure | Agent notices degraded recall of earlier steps |

### What to Compact

Produce a structured summary that preserves decision outcomes and
artifacts while discarding intermediate detail:

```
TaskUpdate(taskId=phaseTask, status="completed",
    metadata={
        "compacted": true,
        "summary": "Phase 2: Gathered 4 sources — GH-15 (open, "
                   "feature request), Sentry #12345 (145 events), "
                   "Slack thread (3 action items), PR #42 (merged). "
                   "Cross-ref: Sentry #67890 from ticket body.",
        "artifacts": ["context-summary.md"],
        "decisions": ["work_type=bugfix", "workspace=worktree"]
    })
```

**Preserve:**
- Decisions made and their rationale
- File paths created or modified
- Artifact references (PR URLs, branch names, file paths)
- Error states that affect downstream tasks

**Discard:**
- Raw API responses and full file contents
- Intermediate exploration steps
- Verbose tool output already captured in artifacts

### How Skills Reference Compaction

Skills that run 10+ tasks SHOULD include a compaction step in
their play templates. Add it as a `detailed` step after each
phase boundary:

```yaml
# In playbook.yaml
steps:
  - subject: "Gather context"
    type: epic
    steps: [...]
  - subject: "Compact: Gather phase"
    type: detailed
    prompt: >
      Summarize completed gather tasks into a single
      TaskUpdate with compacted metadata. Preserve
      decisions, artifacts, and error states.
    condition: "len(completed_tasks) >= 4"
```

### Integration with Existing Patterns

- **Auto-advance**: Compaction is a task like any other — complete
  it and immediately advance to the next task. No pause.
- **Batched decisions**: Compaction never introduces a decision
  gate. It is always automatic.
- **Plan mutation**: If compaction reveals a completed task was
  actually incomplete (e.g., missing artifact), mutate the plan
  to re-add it rather than silently skipping.
- **Subagent dispatch**: Subagent results are natural compaction
  points — the summary returned by a subagent IS the compacted
  form. Do not re-expand subagent output after receiving it.

## Script Operations as Named Steps

Skills reference scripts by path. When mentioning a script in
task descriptions, use a descriptive operation name:

| Operation | Script | Used by |
|-----------|--------|---------|
| Detect tracker | `gh-context/scripts/detect-tracker.sh` | work-on, gh-pr-create, ticket-jtbd |
| Detect PR context | `gh-context/scripts/gh-pr-detect.sh` | gh-context, gh-pr-create, gh-pr-monitor |
| Safe git push | `git/scripts/git-push-safe.sh` | git, git-groom |
| Non-interactive rebase | `git/scripts/git-rebase-groom.sh` | git, git-groom |
| Pre-PR quality checks | `gh-pr-create/scripts/pre-pr-checks.sh` | gh-pr-create |
| Slack notify | `slack/slack-notify.py` | slack, park-remind |
| Safe DB query | `db-psql/scripts/db.sh` | db-psql, db |
| Run Playwright | `playwright/scripts/run-playwright.sh` | playwright, qa-self |

This mapping helps subagents understand which operations are
available without reading full SKILL.md files.

---

## Pattern 9: Task Reconciliation After Delegation

When a parent skill (e.g., `work-on`) delegates to a child
skill (e.g., `gh-pr-respond`) that runs its own task pipeline,
the parent must reconcile task state after the child returns.

**Problem:** Child skills may create overlapping tasks (groom,
push, monitor) that duplicate the parent's remaining pipeline.
Without reconciliation, parent tasks stay `pending` and the
completion gate never fires.

**Protocol:**
1. After delegated skill returns, call `TaskList`
2. Match child-completed actions to parent's remaining tasks
   by subject/action (not task ID)
3. Mark fulfilled parent tasks as `completed`
4. Resume parent pipeline from the first unresolved task

**Child skill responsibility:** When invoked as a delegate
(detected via `TaskList` showing a parent pipeline), child
skills SHOULD skip their own shipping pipeline and return
control. See `gh-pr-respond` § Parent Context Detection.
