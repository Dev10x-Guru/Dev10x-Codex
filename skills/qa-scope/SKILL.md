---
name: Dev10x:qa-scope
description: >
  Analyze a PR for QA needs, check e2e coverage gaps, and create QA
  sub-tickets when manual testing or new e2e tests are needed.
  TRIGGER when: PR needs QA analysis for coverage gaps or manual test
  requirements.
  DO NOT TRIGGER when: executing QA test cases (use Dev10x:qa-self),
  or PR has no user-facing changes.
user-invocable: true
invocation-name: Dev10x:qa-scope
allowed-tools:
  - Bash(gh pr diff:*)
  - Bash(gh pr view:*)
  - Bash(gh repo view:*)
  - Bash(grep:*)
  - mcp__claude_ai_Linear__list_issues
  - mcp__claude_ai_Linear__get_issue
  - mcp__claude_ai_Linear__save_issue
---

# QA Scope - PR Quality Assurance Assessment

## Orchestration

This skill follows `references/task-orchestration.md` patterns.
Create a task at invocation, mark completed when done:

**REQUIRED: Create a task at invocation.** Execute at startup:

1. `TaskCreate(subject="Analyze PR for QA needs", activeForm="Analyzing QA scope")`

Mark completed when done: `TaskUpdate(taskId, status="completed")`

## Overview

Analyzes a PR for QA needs by assessing regression risk, checking existing e2e
test coverage in app-e2e, identifying gaps, and creating QA sub-tickets in Linear
when manual testing or new e2e scenarios are needed.

**Use when:**
- A PR is ready for merge and needs QA assessment
- You want to check if a change needs manual QA testing
- `/Dev10x:gh-pr-monitor` triggers Phase 2.5 (automatic)

**Do NOT use for:**
- Test-only PRs (no production code changes)
- Documentation-only changes
- CI/config changes with no runtime impact

## Prerequisites

**Required:**
- PR number, URL, or branch name (will auto-detect from current branch)

**Available context:**
- `/work/example/app-e2e/` — E2E test repository
- Linear MCP — ticket and team management
- GitHub CLI — PR details

## Workflow

### Phase 1: Gather PR Context

#### 1.1 Identify PR

Accept input as PR URL, PR number, or auto-detect from current branch:

```bash
# Auto-detect from current branch
PR_NUMBER=$(gh pr view --json number -q '.number')
REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner')
PR_URL=$(gh pr view --json url -q '.url')
BRANCH=$(git branch --show-current)
```

#### 1.2 Extract Ticket ID

Parse ticket ID from branch name following `username/TICKET-ID/[worktree/]description` convention:

```bash
TICKET_ID=$(echo "$BRANCH" | grep -oP '[A-Z]+-\d+')
```

#### 1.3 Fetch PR Diff

```bash
gh pr diff $PR_NUMBER
```

Identify changed modules by examining file paths in the diff. Map each changed
file to its bounded context (e.g., `src/payments/` → payments, `src/square_oauth/` → square_oauth).

#### 1.4 Fetch Linear Ticket

Use Linear MCP to retrieve:
- Title and description
- Parent ticket (if sub-ticket)
- Labels and team
- Related tickets

**Store the Linear issue ID** — it will be used as `parent` when creating the QA sub-ticket in Phase 5.1. Look up by the ticket identifier parsed in Step 1.2 (e.g. search for `JIRA-5345` or `PAY-133`).

#### 1.5 Check for Existing QA Sub-Tickets

Before doing any risk assessment, check if QA work already exists:

1. Use Linear MCP `list_issues` to find sub-tickets with "QA" in the title under the parent ticket
2. If existing QA tickets are found → list them in the assessment and note "QA already tracked"
3. Check if the PR has 100% unit test coverage for all new code paths

If existing QA tickets cover the changed area AND unit tests are comprehensive,
set the recommendation to "No new ticket needed" and skip to Phase 4 presentation.

*Why?* Recommending a new QA ticket without checking existing ones causes redundant work.
Unit test coverage at 100% on a guard clause / defensive check (no UI impact) often
makes a separate QA ticket unnecessary. Turn 16 of the PAY-58 pr:monitor session.

### Phase 2: Assess QA Risk

Classify the change into a risk level based on what was changed.

#### Risk Classification Matrix

| Risk Level | Criteria | QA Action |
|------------|----------|-----------|
| **Low** | Config-only, docs, test-only, CI changes | No QA ticket needed |
| **Medium** | New scope/permission, refactoring with tests, admin changes | QA regression ticket |
| **High** | Payment flow changes, new features, DB migrations, external API changes | QA regression + e2e coverage ticket |

#### Decision Factors

Evaluate each factor and aggregate:

| Factor | Risk Contribution |
|--------|------------------|
| Touches `payments/` or money calculation code | +High |
| Modifies external API integrations (Square, Motor, PartsTech) | +High |
| Includes DB migrations | +Medium-High |
| Changes OAuth scopes or authentication | +Medium-High |
| Adds new user-facing feature | +High |
| Refactors existing code with full test coverage | +Medium |
| Modifies admin/config only | +Medium |
| Test-only or config-only changes | Low (stop here) |
| PR has 100% unit test coverage for new code | Reduces risk one level |

#### Risk Reduction

- Full unit test coverage for all new code paths → reduce risk by one level
- Changes isolated to a single module with no cross-cutting concerns → reduce risk by one level
- Existing e2e coverage already exercises the changed path → reduce risk by one level

### Phase 3: Check E2E Coverage

Reference the coverage map at `references/e2e-coverage-map.md` to quickly identify
relevant e2e tests without searching the entire app-e2e repo.

#### 3.1 Map Changed Modules to E2E Features

For each changed app-pos module, look up the corresponding e2e feature files,
tags, and step definitions in the coverage map.

#### 3.2 Search for Existing Coverage

Search `/work/example/app-e2e/features/` for scenarios that exercise the changed code paths:

```bash
# Search feature files for relevant keywords
grep -r "keyword" /work/example/app-e2e/features/ --include="*.feature"

# Search step definitions for relevant steps
grep -r "keyword" /work/example/app-e2e/features/steps/ --include="*.py"

# Check page objects for relevant UI interactions
grep -r "keyword" /work/example/app-e2e/tests/pages/ --include="*.py"
```

#### 3.3 Identify Gaps

Compare what the PR changes against what existing e2e tests cover:

- **Covered:** existing scenarios test the changed behavior → note which ones
- **Partially covered:** existing scenarios test related but not exact behavior → note gaps
- **Not covered:** no existing e2e scenarios for the changed area → flag for new tests

### Phase 4: Present Assessment

Format and present the QA verdict to the user for approval before creating any tickets.

#### Verdict Format

```
QA Assessment for PR #<number>

Risk: <Low | Medium | High>
Reason: <1-line summary of why this risk level>

Changed Modules:
  - <module 1> (<risk contribution>)
  - <module 2> (<risk contribution>)

E2E Coverage:
  Existing: <what's already covered>
  Gap: <what's missing>
  Gap: <what's missing>

Recommendation: <No QA needed | QA regression ticket | QA regression + e2e ticket>

Regression Test Cases:
  1. <test case>
  2. <test case>
  3. <test case>

New E2E Scenarios Needed:
  1. <scenario description>
  2. <scenario description>

Create QA sub-ticket? (y/n)
```

Use `AskUserQuestion` to get approval:
- **"Create QA sub-ticket"** → proceed to Phase 5
- **"Skip QA"** → end with summary
- **"Edit assessment"** → let user modify before creating

#### Pre-Creation Check: Search for Existing QA Tickets

Before creating a new ticket, check if one already exists:

1. Use Linear MCP `list_issues` to find sub-tickets with "QA" in the
   title under the parent ticket
2. If an existing QA ticket covers the changed area, note it in the
   assessment and ask whether a new ticket is needed or the existing
   one is sufficient
3. If the existing ticket is On Hold or Out of Scope, it may still be
   referenced from the PR description without creating a duplicate

*Why?* PAY-616 session found QA-202 (On Hold) covering the same
domain. Creating a duplicate would be noisy and confusing.

### Phase 5: Create QA Sub-Ticket (if approved)

#### 5.1 Determine Ticket Structure

Create the QA ticket as a sub-ticket of the PR's Linear ticket. Use the Linear
issue ID retrieved in Step 1.4 as the `parent` parameter. This links the QA
ticket to the feature ticket in Linear's hierarchy.

#### 5.2 Create Linear Ticket

**Ticket destination routing** — choose based on user instruction:

| User says | Destination | How |
|-----------|-------------|-----|
| (default, no instruction) | Linear **QA** team | `team: "QA"` (id: `c89229e5-8aeb-4934-8575-aa9f18c22e99`) |
| "JIRA team ticket" | Linear **JIRA Sync** team | `team: "JIRA Sync"` (id: `0c456d25-e332-4210-992e-65f668a5080e`) — auto-syncs to Jira application |
| "JIRA ticket" (no "team") | Jira application directly | Use Jira REST API with credentials from MEMORY.md |

Use Linear MCP `create_issue`:

```
Team: <see routing table above>
Title: QA: <PR ticket title>
Parent: <PR's Linear issue ID from Step 1.4>
Description: <structured test plan — see format below>
```

#### 5.3 Ticket Description Format

```markdown
## Context

PR: <PR URL>
Ticket: <parent ticket ID and title>
Risk: <level>

## Changed Areas

- <module>: <what changed>

## Regression Test Cases

- [ ] <test case 1>
- [ ] <test case 2>
- [ ] <test case 3>

## E2E Coverage Gaps

Existing coverage: <summary>

New scenarios needed:
- [ ] <scenario 1>
- [ ] <scenario 2>

## Related Resources

- <links to relevant admin pages, API docs, Square docs, etc.>
```

#### 5.4 Ask About Assignment

Use `AskUserQuestion` to ask who to assign:
- Suggest Nicholas (default QA resource) or let user pick

#### 5.5 Report Completion

Output the created ticket ID and URL.

## Integration with Other Skills

```
Dev10x:qa-scope
├── Uses: Linear MCP (ticket data, create sub-ticket)
├── Uses: GitHub CLI (PR diff, PR details)
├── Reads: /work/example/app-e2e/ (e2e coverage check)
├── References: references/e2e-coverage-map.md
├── Called by: pr:monitor (Phase 2.5)
└── Standalone: /qa-scope <PR URL or number>
```

## Example Usage

### Standalone

```
/qa-scope https://github.com/example-org/app-pos/pull/1169
/qa-scope 1169
/qa-scope              # auto-detect from current branch
```

### Via pr:monitor

Triggered automatically in Phase 2.5 when CI passes and PR has approval.

### Example Output

```
QA Assessment for PR #1169

Risk: Medium
Reason: Adds new Square OAuth scope (DEVICES_READ) — changes external API authorization

Changed Modules:
  - square_oauth/ (OAuth scope change → Medium-High)

E2E Coverage:
  Existing: square.feature covers invoice + payment link flows
  Gap: No terminal device pairing/listing tests
  Gap: No OAuth re-authorization flow tests

Recommendation: Create QA regression ticket

Regression Test Cases:
  1. Verify existing Square OAuth authorization still works
  2. Verify legacy token refresh includes new scope
  3. Verify terminal checkout flow unaffected
  4. Verify new OAuth authorization includes DEVICES_READ

New E2E Scenarios Needed:
  1. OAuth re-authorization flow after scope change
  2. Terminal device listing in POS settings

Create QA sub-ticket? (y/n)
```
