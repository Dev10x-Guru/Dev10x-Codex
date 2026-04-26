---
name: Dev10x-jtbd
description: Pure JTBD story drafting skill. Gathers context from issue tracker tickets, parent tickets, and PR diffs to craft a situation-driven Job Story with explicit actor and beneficiary. Returns the draft string with no side effects. Used as a foundation by ticket write layers, PR creation, release notes, and commit title derivation skills.
---

# Dev10x:jtbd — Pure Job Story Drafting

## Overview

This is the **foundational JTBD skill** that provides reusable context
gathering and story drafting. It is NOT directly invocable by users —
instead, it is used as a base by other skills:

- **ticket write layer** — drafts and applies the story to a target (PR,
  Linear ticket, JIRA ticket)
- **PR creation skill** — sources or generates a Job Story for the PR
  description
- **ticket work-on skill** — drafts a story early when starting work on a
  ticket
- **ticket scoping skill** — drafts a story during the architecture phase
- **release-notes skill** — generates missing stories in unattended mode
- **commit skill** — derives outcome-focused titles from the "so X can" clause

## Interface Contract

```
INPUTS:
  ticket_id: str | None      — e.g. FEAT-519, BUG-234, ENG-300
  pr_number: int | None      — GitHub PR number
  context: dict | None       — Pre-gathered context (avoids redundant API calls)
  mode: attended | unattended — attended = user approval; unattended = return draft

OUTPUT:
  story: str — "**When** ... **[actor] wants to** ... **so [beneficiary] can** ..."
               Empty string if user rejects (attended mode)

SIDE EFFECTS: None.
```

Callers pass whatever context they already have via `context` to skip
redundant API calls. If `context` is None, the skill gathers it fresh.

## Workflow

### Step 1: Gather Context

Collect information from available sources in parallel. Skip sources
the caller already provided via the `context` parameter.

**A. PR details (if `pr_number` provided):**
```bash
gh pr view {PR_NUMBER} --json title,body,headRefName
gh pr diff {PR_NUMBER}
```

**B. Issue ticket (if `ticket_id` provided):**
Use the available issue tracker tool (Linear MCP, JIRA REST API, etc.)
to get:
- Title and description
- Parent ticket ID (if any)

**C. Parent ticket (if exists):**
Use the issue tracker tool with the parent ID to get:
- The business context and original request
- Who requested it and why
- Linked Slack threads or comments (often contain the real user voice)

The parent ticket is critical — it usually contains the *why* behind
the technical sub-task. The sub-task (linked to the PR) contains the
*how*.

### Step 2: Identify the Situation

From the gathered context, extract:

1. **Who experiences the situation?** (not a persona — a role in context)
   - Look at: parent ticket description, user quotes, who filed it
   - Example: "a merchant", "a billing admin", "the ops team"

2. **Who benefits from the outcome?** (may differ from the actor above)
   - Sometimes the actor who triggers the action and the beneficiary are
     different roles — e.g., the billing admin sends the invoice SMS, but
     the customer is the one who benefits from paying via phone
   - Look at: what changes for whom, who is the downstream beneficiary

3. **What triggers the need?** (the real-world moment)
   - Look at: parent ticket description, user quotes
   - Example: "processes a bank transfer", "runs end-of-month payroll"

4. **What's wrong today?** (the current pain)
   - Look at: why was the ticket created, what workaround exists
   - Example: "forced to select 'Other'", "calculation times out"

### Step 3: Draft the Job Story

**Format:**
```
**When** [situation], **[actor] wants to** [motivation], **so [beneficiary] can** [expected outcome].
```

**Rules:**
- Use **business language**, not technical language
- The "When" describes a real-world moment, not a UI interaction
- Always name the actor explicitly — never use "I", "we", or "they"
- The actor ("wants to") and beneficiary ("so X can") may be **different
  roles** — name both explicitly when they differ (e.g., "the billing admin
  wants to send the customer an SMS, so the customer can pay immediately")
- The "so [beneficiary] can" should contrast with the current broken state
- One sentence. No bullet points. No implementation details.
- See `references/job-story-format.md` for detailed guidance

### Subject Selection by PR Type

The actor in "wants to" varies depending on the type of change:

| PR Type | Actor | Example |
|---------|-------|---------|
| User-facing feature | End user role: merchant, customer, admin | "the cashier wants to select 'ACH' as the payment method..." |
| Refactoring / preparatory | Developer implementing the next step | "the developer wants to reuse the notification infrastructure..." |
| Bug fix | Role experiencing the bug | "the payroll manager wants the calculation to complete reliably..." |
| Internal tooling | Ops/engineering team member | "the ops team wants to see revenue broken down by channel..." |
| Infrastructure | Developer deploying or maintaining | "the developer wants to cancel stale workflow runs..." |

**Actor ≠ Beneficiary:** When the person taking the action differs from the
person who gains the benefit, name both explicitly:
> "the billing admin wants to send the customer an SMS with the payment link,
> so the customer can pay immediately from their phone"

**Anti-pattern for refactoring PRs:** Do not use the end user as
actor for purely internal refactoring. The end user does not care how
the code is organized. The developer who needs to build on the
refactored code is the correct actor.

**Bug fix stories**: Focus on the specific broken entity (e.g., "stale
background job"), not the monitoring symptom that surfaced it (e.g.,
"error alerts in Sentry"). The "When" should describe the real-world
situation where the bug manifests, not the developer's experience of
discovering it.

### Anti-pattern: Pseudo-Business Value

The biggest risk with JTBD stories is writing something that *sounds*
business-y but is really technical dress-up. If the story doesn't
answer "why is this worth spending money on?", it's friction — not
value.

**Red flags in a draft:**

| Red flag | Why it's wrong | Fix |
|----------|---------------|-----|
| Technical scheduling as "When" | "When upgrading EKS" — business doesn't care about infrastructure timelines | Use the recurring business activity: "When releasing new features" |
| Technical mechanism as motivation | "configure probes with the right semantics" | Name what actually changes: "detect failed deployments" |
| Over-specific role when a generic term works | "merchants" when the check protects all users equally | Use "user experience" — don't narrow without reason |
| Implementation detail as benefit | "avoid misrouted traffic during restarts" | State the real outcome: "prevent broken releases from degrading UX" |
| `I want to` when the actor is ambiguous | "I" doesn't identify the stakeholder | Prefer a named role ("the merchant", "the DevOps team"); `I want to` is fine as a fallback when the actor is clear from context |

**The "why spend money" test:** Read the draft aloud. If a non-technical
stakeholder would respond "so what?" or "why do I care?", the story
is still too technical. Keep peeling layers until you hit something
that connects to user impact, revenue risk, or operational cost.

**Example — infrastructure PR (before and after):**

Before (technical dress-up):
> **When** deploying the app to Kubernetes, **I want to** have dedicated
> liveness, readiness, and startup endpoints, **so I can** configure
> probes with the right semantics and avoid misrouted traffic.

After (real business value):
> **When** releasing new features, **the DevOps team wants to**
> detect failed deployments through substantive health checks rather
> than superficial ones, **so they can** prevent broken releases from
> degrading the user experience.

The first version describes *what* the code does. The second explains
*why anyone should care*. The difference: substantive vs superficial
checks (the real improvement), and preventing UX degradation (the
real cost of not doing it).

### Step 4: Present or Return

**Attended mode** — present the draft and ask for approval:

```
Job Story draft:

**When** a merchant processes an ACH bank transfer for an order,
**the cashier wants to** select "ACH" as the payment method,
**so the merchant can** accurately reconcile bank transfer transactions
instead of grouping them under "Other".

Accept? (y/edit/n)
```

If **edit**: ask what to change and iterate.
If **n**: return empty string.
If **y**: return the story string.

**Unattended mode** — return the draft directly without user
interaction. The caller decides what to do with it.

## Context Gathering Strategy

The quality of a Job Story depends on finding the **business voice** —
the original request that motivated the technical work. Follow this
hierarchy:

```
Best context sources (in priority order):
1. User quotes in parent ticket ("@sarah said: enterprise clients all pay via ACH")
2. Parent ticket description (business request)
3. Sub-task ticket description (technical scope)
4. PR diff (what actually changed)
5. PR title (last resort)
```

**If no parent ticket exists**, the ticket description itself is the
source. Look for user quotes, Slack links, or "requested by" mentions.

**If no ticket exists** (branch without ticket ID), use the PR diff
and title to infer the situation. Ask the user for business context
if unclear (attended mode) or make best effort (unattended mode).

## Integration Points

This skill is designed to be composed by other skills:

### Ticket write layer
The write layer. Invokes `Dev10x:jtbd` in attended mode, then writes the
approved story to a target (PR description, issue tracker ticket).

### PR creation skill
Sources an existing story or invokes `Dev10x:jtbd` to generate one. The
story becomes the first paragraph of the PR body.

### Ticket work-on skill
Invokes `Dev10x:jtbd` in attended mode using ticket context already
gathered. If approved, prepends the story to the ticket description.

### Ticket scoping skill
Invokes `Dev10x:jtbd` in attended mode. The approved story is included
in the scoping document under a `## Job Story` section.

### Release-notes skill
Invokes `Dev10x:jtbd` in **unattended** mode for PRs missing a story.
The caller batches multiple drafts and presents them all for approval.

### Commit skill
Invokes `Dev10x:jtbd` in **unattended** mode to derive an outcome-focused
commit title from the "so X can" clause. Only for first commits on
feature/bug branches.

### PR monitor skill
Delegates to the ticket write layer when a PR is missing its Job Story.

## Examples

### Example 1: Feature with parent ticket context

**Domain:** E-commerce SaaS

**Context found:**
- FEAT-401 (sub-task): "Add ACH to PaymentMethod enum"
- FEAT-398 (parent): "Support ACH bank transfer payments"
- User quote in parent: "@sarah said: enterprise clients all pay via ACH,
  they keep asking for it"

**Output:**
> **When** a merchant processes an ACH bank transfer for an order, **the
> cashier wants to** select "ACH" as the payment method, **so the merchant
> can** accurately reconcile bank transfer transactions instead of grouping
> them under "Other".

### Example 2: Feature with different actor and beneficiary

**Domain:** SaaS billing

**Context found:**
- BILL-230: "Send invoice link via SMS after invoice is created"
- The billing admin initiates the invoice; the customer receives and pays

**Output:**
> **When** a merchant sends an invoice for a completed order, **the billing
> admin wants to** send the customer an SMS with the payment link, **so the
> customer can** pay immediately from their phone without needing email
> access.

Note: Actor (billing admin) and beneficiary (customer) are explicitly named
because they differ — this immediately communicates who does what and who
gains.

### Example 3: Bug fix

**Domain:** HR / Payroll SaaS

**Context found:**
- BUG-500: "Payroll calculation times out during month-end run"
- Parent: "Payroll failures at month-end closing"

**Output:**
> **When** running payroll during month-end closing, **the payroll manager
> wants** the calculation to complete reliably, **so the finance team can**
> avoid missed pay dates and manual correction workflows.

### Example 4: Internal tooling

**Domain:** Analytics / Operations

**Context found:**
- OPS-300: "Add revenue breakdown by channel to admin dashboard"
- No parent ticket

**Output:**
> **When** preparing the quarterly business review, **the operations team
> wants to** see revenue broken down by acquisition channel and region,
> **so they can** identify underperforming channels and adjust budget
> allocation without exporting to spreadsheets.

### Example 5: Refactoring / preparatory work

**Domain:** SaaS notifications

**Context found:**
- FEAT-230 (sub-task): "Move notification dispatch to shared infrastructure"
- PR diff: extracts email sender into a generic outbox, promotes to a
  standalone module

**Output:**
> **When** implementing SMS billing notifications, **the developer wants
> to** reuse the existing notification infrastructure for new delivery
> channels, **so they can** add SMS without rebuilding retry and scheduling
> logic from scratch.

Note: The developer is the actor because this PR is preparatory
refactoring — the end user is not affected until the SMS feature ships.
