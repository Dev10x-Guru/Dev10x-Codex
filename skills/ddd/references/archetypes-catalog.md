# Software Archetypes Catalog

> Based on [Software-Archetypes/archetypes](https://github.com/Software-Archetypes/archetypes)
> (Pilimon & Słota) and classical sources (Coad/North/Mayfield, Fowler).
>
> Archetypes are NOT frameworks. They are recurring structural patterns
> that appear across domains. Recognizing them prevents reinventing
> solved problems.

## Pattern Recognition Table

| Signal in the domain | Archetype | Core idea |
|---|---|---|
| Flat config struct with N fields, mixed semantics (rates + fractions + percentages) | **Pricing** | Price is the result of running a pipeline of composable rules, not a property of a thing |
| Raw `number` used for money, duration, weight, or ratios without unit safety | **Quantity** | Typed value objects with units prevent the "is 5 five percent or five dollars?" bug |
| Entity that is sometimes a person, sometimes a company, sometimes a department | **Party** | Universal Party with assigned Roles — one model for all organizational entities |
| "What resources are available when?" / "Can we schedule X at time Y?" | **Availability** | Time-slotted resource management with capacity, blocking, and overlaps |
| Items arranged in a hierarchy with composition and pricing | **Product** | Composite tree of configurable items that get priced through a pipeline |
| "Queue this work" / "Process in order" / "First come first served" | **Waitlist** | Priority queue with fairness rules and capacity constraints |
| Complex conditional business rules that vary by context | **Rules** | Condition trees (AND/OR/NOT) evaluated against a context, returning actions |
| "Choose valid combinations" / "This option requires that option" | **Configurator** | Constraint satisfaction — SAT-like validation of feature/option combinations |
| "Assign N tasks to M workers optimally" | **GAP** | Generalized Assignment Problem — optimization under resource constraints |
| "Plan says X, reality says Y" | **Plan vs Execution** | Parallel structures for intended vs actual, with variance tracking |
| Tracking debits/credits, balances, or financial flows | **Accounting** | Double-entry ledger with immutable transactions |

## How to Apply an Archetype

### Step 1: Recognize the pattern

Don't look for the archetype name in the domain language. Look for
the **structural shape**. The domain expert says "rate card"; you
recognize "composable pricing pipeline."

### Step 2: Map domain concepts to archetype concepts

| Archetype concept | Domain concept |
|---|---|
| PricingRule | EffortAllocationRule, DayRate, PriceModifier |
| Product | EstimateNode |
| Money | Money { amount, currency } |
| Pipeline Stage | PERT → Effort → Rates → Modifiers |

### Step 3: Validate the mapping preserves semantics

- Does every domain behavior map to an archetype operation?
- Does the archetype introduce unnecessary concepts?
- Is the pipeline/composition order explicit and correct?

### Step 4: Identify the seam

Every archetype has a natural **seam** — the point where the
archetype's generic structure meets domain-specific logic.

For Pricing: the seam is at `basePrice`. Everything above is
strategy-specific. Everything below (modifiers, tax, aggregation)
is universal.

### Step 5: Stress-test the seam

Ask: "If I add a new product type / rule type / calculation stage,
does the seam hold?" If yes, the archetype is correctly applied.
If not, the seam is in the wrong place.

## Pricing Archetype — Deep Dive

This is the most commonly applied archetype in estimation domains.
See `references/pricing-pipeline.md` for the full specification.

**Key principle:** A price is not a property of a thing. It's the
result of running a pipeline of composable policies over that thing.

**When the flat struct smells bad:**
- Adding a new pricing factor means changing the type signature
- Rates, fractions, and percentages are all `number` with no safety
- Calculation order is baked into procedural code, not data
- Override granularity requires `Partial<T>` with N optional fields

**When the pipeline is the answer:**
- New factors are rule instances (data, not code)
- Each rule is independently typed, validated, and testable
- Pipeline order is explicit in `rule.order` — visible, reorderable
- Overrides operate at rule granularity (add/remove/modify one rule)

## Quantity Archetype — Deep Dive

**Key principle:** Never use raw `number` where a unit is implied.

```typescript
// BAD: what unit is amount? dollars? days? percent?
function calculate(amount: number): number

// GOOD: types enforce semantics
function calculate(effort: Effort): Money
```

Domain model uses `Ratio` (0..1) internally. UI converts to percent
(0..100) at the boundary. This prevents the classic bugs:
- "Is 5 five percent (0.05) or five hundred percent (5.0)?"
- "Is this amount in PLN or EUR?"
- "Is this 10 days or 10 hours?"

## When NOT to Apply an Archetype

- When the problem is genuinely unique to the domain (rare)
- When the archetype adds more complexity than it solves
- When the team doesn't understand the archetype (training first)
- When applying it would require rewriting stable, working code
  that isn't blocking any extension (if it ain't broke...)

The test: **"Does recognizing this archetype simplify the model, or
does it complicate it?"** If it simplifies — apply. If it
complicates — the match is wrong; look for a different archetype
or accept that this is domain-specific.
