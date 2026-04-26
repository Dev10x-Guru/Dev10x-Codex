---
name: Dev10x:review
invocation-name: Dev10x:review
description: >
  Review your own branch changes before creating a PR. Reviews diff
  against base branch, runs automated checks, and produces structured
  findings with severity, file, line, and suggested fix. Works in
  attended (pick findings) or unattended (auto-advance to fixer) mode.
  TRIGGER when: reviewing own branch changes before PR creation, or
  self-reviewing code quality.
  DO NOT TRIGGER when: reviewing an external PR (use Dev10x:gh-pr-review),
  or no changes exist on the branch.
user-invocable: true
allowed-tools:
  - Bash(git log:*)
  - Bash(git diff:*)
  - Bash(git status:*)
  - Bash(git develop-log:*)
  - Bash(git develop-diff:*)
  - Bash(ruff check:*)
  - Bash(black --check:*)
  - Bash(mypy:*)
  - Bash(uv run:*)
  - Bash(/tmp/claude/bin/mktmp.sh:*)
  - Write(/tmp/claude/review/**)
  - AskUserQuestion
---

# Self-Review Branch

Review current branch changes against the base branch, applying project
review guidelines. Produces structured findings that `Dev10x:review-fix`
can consume to create fixup commits.

## Arguments

- `--unattended` — skip finding approval, auto-advance to
  `Dev10x:review-fix` for all actionable findings
- No arguments — attended mode, present findings for user approval

## When to Use

- Before creating a PR (self-review catches issues early)
- As the "Code review" step in the `work-on` shipping pipeline
- When asked to review your own changes

**Not for remote PR review** — use `Dev10x:gh-pr-review` to post
findings to GitHub.

## Orchestration

This skill follows `references/task-orchestration.md` patterns
(Tier: Standard).

**Auto-advance:** Complete each step and immediately start the next.
Never pause between steps to ask "should I continue?".

**REQUIRED: Create tasks before ANY work.** Execute these
`TaskCreate` calls at startup:

1. `TaskCreate(subject="Verify branch state", activeForm="Checking branch")`
2. `TaskCreate(subject="Run automated checks", activeForm="Running checks")`
3. `TaskCreate(subject="Review changed files", activeForm="Reviewing files")`
4. `TaskCreate(subject="Present findings", activeForm="Presenting findings")`

Set sequential dependencies.

**Nested-mode exemption:** When invoked as a nested skill within
a parent orchestrator (e.g., via `Skill()` from `Dev10x:work-on`),
startup task creation is optional — at most 1 summary task. The
parent provides progress visibility. See
`references/task-orchestration.md` § Delegated Invocation Exception.

## Workflow

### Step 1: Verify Branch State

1. Confirm inside a git repository
2. Detect base branch — use `git develop-log` alias to find commits
   ahead of develop. If alias fails, fall back to `origin/develop`
3. Verify branch has commits ahead of base (warn if nothing to review)
4. Check for uncommitted changes — warn but continue

### Step 2: Get Branch Diff

```bash
git develop-diff
```

Parse the diff to extract the list of changed files with their
change types (added, modified, deleted, renamed).

### Step 3: Run Automated Checks

Run in parallel where possible:

1. **Lint**: `ruff check` on changed Python files
2. **Format**: `black --check` on changed Python files
3. **Types**: `mypy` on changed Python files (if configured)

Collect any failures as findings with severity `ERROR` and
source `automated`.

### Step 4: Review Each Changed File

For each changed file in the diff:

1. Read the full file (current version)
2. Review the diff hunks for this file
3. Apply review guidelines:
   - `references/review-checks-common.md` — false positive prevention
   - `.claude/agents/reviewer-*.md` — domain-specific checks based
     on file type (see `.claude/rules/INDEX.md` for routing)
4. For each issue found, create a structured finding

**False Positive Prevention Gate** (from `review-checks-common.md`):
Before recording any finding, verify:
1. Does this violate a documented rule? (No rule = preference, skip)
2. Does this contradict an established codebase pattern?
3. Is this a quality improvement or just preference?
4. Did the author already fix this in a later commit?

### Step 5: Compile Findings

Each finding is a structured object:

```
Finding:
  severity: ERROR | WARNING | INFO
  source: automated | manual
  file: <path>
  line: <number>
  description: <what's wrong>
  suggested_fix: <code or guidance>
  category: <bug | security | architecture | style | test>
```

Write findings to a temp file for handoff:

```bash
/tmp/claude/bin/mktmp.sh review findings .json
```

Write the findings array as JSON to the temp file path.

### Step 6: Present Findings

**Unattended mode** (`--unattended`):
- Skip presentation
- Pass all `ERROR` and `WARNING` findings to `Dev10x:review-fix`
- Invoke: `Skill(skill="Dev10x:review-fix", args="<findings-file-path>")`
- Auto-advance after fixer completes

**Attended mode** (default):
- Present findings grouped by severity, then by file
- Show count: "Found N issues (X errors, Y warnings, Z info)"
- For each finding: severity, file:line, description, suggested fix

**When findings = 0:**

**REQUIRED: Call `AskUserQuestion`** even when no findings exist.
This confirms the clean review to the user and prevents silent
skip-through (GH-447 F5).

**Unattended mode exemption (GH-760 F6):** When invoked with
`--unattended` flag (e.g., from `Dev10x:work-on` shipping
pipeline), skip this gate and auto-advance. The parent
orchestrator already approved the work plan — pausing for
zero-findings confirmation adds friction without safety value.

**Attended mode** options:
- Continue (Recommended) — Proceed to next pipeline step
- Re-review — Run the review again with different scope

**When findings > 0:**

**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text).
Options:
- Fix all (Recommended) — Send all ERROR and WARNING findings to
  `Dev10x:review-fix`
- Pick findings — Review each finding and select which to fix
- Skip — No fixes, continue with pipeline

If "Pick findings": present each finding with fix/skip choice,
collect approved findings, then invoke `Dev10x:review-fix`.

If "Fix all" or after picking: invoke `Dev10x:review-fix` with
the findings file path.

### Step 7: Summary

Report:
- Total findings by severity
- Which were sent to fixer (if any)
- Any deferred findings (INFO severity or user-skipped)

## Findings Format (Handoff Protocol)

The JSON findings file is the contract between `Dev10x:review`
and `Dev10x:review-fix`:

```json
[
  {
    "severity": "WARNING",
    "source": "manual",
    "file": "src/auth/middleware.py",
    "line": 42,
    "description": "Missing type annotation on return value",
    "suggested_fix": "def validate(self, token: str) -> bool:",
    "category": "style"
  }
]
```

Both skills must agree on this format. The fixer reads the file
path passed as its argument.

## Integration

```
work-on shipping pipeline
└─ Dev10x:review          ← this skill (reviewer)
   └─ Dev10x:review-fix   ← fixer (consumes findings)
      └─ git commit fixup!  ← one fixup commit per finding
```

Complements:
- `Dev10x:gh-pr-review` — posts findings to GitHub (remote PRs)
- `Dev10x:gh-pr-respond` — responds to PR review comments
