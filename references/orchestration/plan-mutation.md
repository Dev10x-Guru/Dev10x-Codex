# Plan Mutation and Out-of-Order Execution

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
