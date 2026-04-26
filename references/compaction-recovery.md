# Compaction Recovery Context

Injected by the PreCompact hook when a persisted plan exists.
This file provides the skill routing table and recovery
instructions that survive context compaction.

## Skill Routing Table

Actions that MUST use skill delegation (never raw CLI):

1. commit → `Skill(Dev10x:git-commit)`
2. create PR → `Skill(Dev10x:gh-pr-create)`
3. monitor CI → `Skill(Dev10x:gh-pr-monitor)`
4. push → `Skill(Dev10x:git)`
5. groom → `Skill(Dev10x:git-groom)`
6. branch → `Skill(Dev10x:ticket-branch)`
7. verify acceptance → `Skill(Dev10x:verify-acc-dod)`

## Recovery Instructions

After context compaction:

1. Call `TaskList` to verify task state matches the persisted
   plan below
2. If tasks are missing, recreate them from the persisted list
3. Resume execution from the first non-completed task
4. Use the routing table above for all shipping actions
5. If the plan context includes a `work_type`, use the
   corresponding playbook play for epic expansion
