# Task Reconciliation and Script Operations

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
