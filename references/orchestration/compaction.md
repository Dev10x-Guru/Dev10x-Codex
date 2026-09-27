# Pattern 8: Progress Compaction

Long-running orchestrations (10+ tasks, multiple phases) accumulate
completed-task detail that consumes context window without aiding
future steps. Compact completed work into a brief status summary
so the agent can focus context budget on remaining tasks.

## When to Compact

Compact after completing a **phase boundary** or a **batch of 4+
related tasks**. Do not compact after every single task — the
overhead outweighs the benefit for small batches.

| Trigger | Example |
|---------|---------|
| Phase boundary | Phase 2 (Gather) complete, entering Phase 3 |
| Epic completion | All 5 sub-tasks of "Implement changes" done |
| Context pressure | Agent notices degraded recall of earlier steps |

## What to Compact

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

## How Skills Reference Compaction

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

## Integration with Existing Patterns

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
