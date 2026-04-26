# Job Story Format Reference

Source: https://jtbd.info/replacing-the-user-story-with-the-job-story-af7cdee10c27

## Format

**When** [situation], **[actor] wants to** [motivation], **so [beneficiary] can** [expected outcome].

The actor and beneficiary may be the same or different roles. Always name them
explicitly — never use "I", "we", or "they".

## Key Principles

### 1. No Personas — Focus on Situation

User stories start with "As a [persona]..." which creates assumptions about
the user. Job stories replace the persona with the **situation** — the context
that creates the need. The same situation can apply to different people.

### 2. Situation Over Implementation

The "When" clause describes the real-world context that triggers the need.
It should be specific enough to be testable but not prescribe a solution.

Good: "When a merchant processes an ACH bank transfer for an order"
Bad:  "When clicking the payment type dropdown"

### 3. Motivation Reveals Anxiety

The "wants to" clause captures what the actor is trying to accomplish.
It often reveals an underlying anxiety or frustration with the current state.

Good: "the cashier wants to select 'ACH' as the payment method"
Bad:  "wants a new enum value"

### 4. Expected Outcome Shows Value

The "so [beneficiary] can" clause describes the measurable benefit or the
problem that goes away. This is what makes the story testable.

Good: "so the merchant can accurately reconcile bank transfer transactions instead of grouping them under 'Other'"
Bad:  "so the system supports ACH"

### 5. Name Actors Explicitly

Prefer role names over "I", "we", or "they" — a named persona ("the
merchant", "the billing admin") adds context at a glance. `I want to`
is acceptable as a fallback when the actor is obvious from context.
When the actor who triggers the action differs from the beneficiary
who gains the value, name both:

Good: "the billing admin wants to send the customer an SMS, so the customer can pay"
Bad:  "I want to send them an SMS, so they can pay"

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Technical language | Not understandable by stakeholders | Use business/domain language |
| Solution-focused "When" | Prescribes implementation | Describe the real-world trigger |
| Vague outcome | Not testable | Be specific about what improves |
| No contrast with current state | Unclear why it matters | Show what's wrong today |
| Using "I"/"they" when the actor is ambiguous | Hides who is impacted | Prefer a named role: "the cashier", "the customer"; `I want to` is fine when context is clear |
| Same actor when roles differ | Hides multi-stakeholder flow | Name both actor and beneficiary when they differ |

## Examples

### Payment Method (e-commerce SaaS)
**When** a merchant processes an ACH bank transfer for an order, **the cashier
wants to** select "ACH" as the payment method, **so the merchant can**
accurately reconcile bank transfer transactions instead of grouping them
under "Other".

### Multi-actor: Invoice SMS (actor ≠ beneficiary)
**When** a merchant sends an invoice for a completed order, **the billing
admin wants to** send the customer an SMS with the payment link, **so the
customer can** pay immediately from their phone without needing email access.

### Performance Fix (SaaS dashboard)
**When** the order list is opened during peak hours, **the support agent
wants to** see results within 2 seconds, **so they can** serve customers
without awkward delays.

### Integration (operations SaaS)
**When** a work item is completed and approved, **the operations manager
wants** the system to automatically sync the record to the accounting system,
**so they can** avoid manual double-entry and reconciliation errors at
month-end.

### Reporting (analytics)
**When** preparing the quarterly business review, **the operations team
wants to** filter revenue by acquisition channel, **so they can** identify
which channels are growing and adjust budget allocation accordingly.
