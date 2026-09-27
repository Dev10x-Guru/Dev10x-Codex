# Architecture Audit — Dev10x Plugin

**Date:** 2026-04-09
**Scope:** Full audit (Phases A-I) of `src/dev10x/` (~8,277 LOC, 903 tests)
**Coverage:** 15.66% (threshold: 38%)

## Status Update (2026-04-13)

### M3 Architecture Alignment — Largely Resolved

| # | Finding | Status | Evidence |
|---|---------|--------|----------|
| 5 | RuleEngine never used | RESOLVED | edit_validator.py and skill_redirect.py both delegate to RuleEngine |
| 6 | Duplicate YAML parsing | RESOLVED | config/loader.py is single parsing path with msgpack cache |
| 20 | Pipeline validators hardcode filter | OPEN | Per-validator filtering is by design — each handles different concerns |
| 21 | Plugin registration hardcoded | OPEN | Validators still imported directly |
| 22 | Config loading — 3 paths | RESOLVED | loader.py with TTL-based cache invalidation |
| 23 | Edit/Write rule classes | PARTIAL | RuleEngine splits by matcher but rule classes are unified |
| 30 | Leaked validation logic | OPEN | Architectural concern remains |
| 40 | Global mutable config cache | RESOLVED | loader.py uses TTL invalidation |

RuleEngine has 234 lines of tests. ConfigLoader has 228 lines.
The core architecture (RuleEngine + ConfigLoader + Config) is
tested and wired up. Remaining items (20, 21, 30) are pattern
improvements, not architectural gaps.

### M4 Pattern Adoption — Largely Resolved

| # | Finding | Status | Evidence |
|---|---------|--------|----------|
| 12 | Strategy pattern missing for pr_comments | RESOLVED | `_PR_COMMENT_ACTIONS` dict in github.py dispatches by action string |
| 20 | Pipeline validators hardcode filter | OPEN | Same as M3 — per-validator design |
| 23 | Edit/Write rules incompatible | PARTIAL | RuleEngine.evaluate() handles both via matcher field |

The pr_comments strategy dispatch was refactored to a dict-based
pattern. Template Method and Factory patterns remain open but are
lower priority without concrete regression risk.

### M5 Test Coverage — Threshold Met

Current coverage: **54.14%** (threshold: 38%).
The threshold has been exceeded by 16 percentage points.

Remaining 0% modules (not blocking threshold):
- `skills/audit/` (629 lines) — CLI audit scripts
- `skills/release/collect_prs.py` (213 lines) — release tool
- `mcp/tests/test_git.py` (77 lines) — test file in src/

### M6 Cross-Cutting Consistency — Partially Resolved

| # | Finding | Status | Evidence |
|---|---------|--------|----------|
| 9 | MCP return type inconsistency | RESOLVED | `Result[T]` type in domain/result.py; all github.py tools use ok()/err() |
| 10 | Error handling pattern mixing | PARTIAL | HookResult/HookAllow/HookRetry defined; not all hooks migrated |
| 22 | Config access — 3 patterns | RESOLVED | See M3 |

The `Result[T]` algebraic type and `HookResult.emit()` protocol
are in place. Adoption across all hooks is incremental — see
GH-826 for the migration plan.

### GH-826 Hook Error Handling — Convention Established

The `HookResult.emit()` / `HookAllow.emit()` / `HookRetry.emit()`
protocol in `domain/hook_input.py` is the canonical pattern:
- **Deny**: `HookResult(message=...).emit()` → JSON stderr + exit 2
- **Allow**: `HookAllow(message=...).emit()` → JSON stderr + exit 0
- **Pass-through**: `sys.exit(0)` → no output, exit 0

All denial paths in validators (edit_validator, skill_redirect,
prefix_friction, etc.) use `HookResult.emit()`. The `sys.exit(0)`
calls in session.py, skill.py, and task_plan_sync.py are correct
pass-through returns, not error handling inconsistencies.

---

## Executive Summary

The Dev10x plugin has strong foundational patterns (Chain of Responsibility
for validators, Strategy via Protocol, Repository for config/plan) but
suffers from three systemic issues:

1. **Concurrency safety gaps** — File race conditions in session state,
   settings.json, and plan persistence. Blocking subprocess calls in
   async MCP handlers.
2. **Orphaned architecture** — RuleEngine exists but is never used;
   validators and hooks duplicate its logic procedurally.
3. **Type safety gaps** — 24+ MCP tools return untyped dicts with
   inconsistent error shapes. Domain primitives (repo refs, ticket IDs,
   actions) are stringly-typed.

---

## Priority Matrix

### HIGH Impact

| # | Finding | Phase | Effort | Milestone |
|---|---------|-------|--------|-----------|
| 1 | Blocking subprocess.run() in async MCP handlers | E | M | Safety |
| 2 | Session state TOCTOU race condition | E | S | Safety |
| 3 | Settings.json read-modify-write without locking | E | M | Safety |
| 4 | Plan file concurrent modification race | E | M | Safety |
| 5 | RuleEngine declared but never used | D | M | Architecture |
| 6 | Duplicate YAML parsing (edit_validator vs config/loader) | D | M | Architecture |
| 7 | Dict-as-DTO: 24+ MCP tools return untyped dicts | C+H | M | Domain Model |
| 8 | Tell-Don't-Ask violations in session.py (36+ .get() calls) | B | M | Domain Model |
| 9 | MCP return type inconsistency (error shapes differ) | H | M | Consistency |
| 10 | Error handling pattern mixing in hooks | H | M | Consistency |
| 11 | N+1 API calls in pr_comments resolve | I | S | Performance |
| 12 | Strategy pattern missing for pr_comments action dispatch | F | M | Patterns |
| 13 | Domain RuleEngine & Plan — zero test coverage | G | L | Coverage |
| 14 | MCP servers — 11 untested tools | G | M | Coverage |
| 15 | Repository Reference (owner/repo) parsed 5 times | C | S | Domain Model |

### MEDIUM Impact

| # | Finding | Phase | Effort | Milestone |
|---|---------|-------|--------|-----------|
| 16 | Non-atomic session state persistence | E | M | Safety |
| 17 | Shared mutable validator cache (no sync) | E | S | Safety |
| 18 | Config loader TOCTOU on cache expiry | E | S | Safety |
| 19 | Permission merge non-atomic writes | E | M | Safety |
| 20 | Pipeline validators hardcode filter logic | D | M | Architecture |
| 21 | Plugin registration via hardcoded tuples | D | M | Architecture |
| 22 | Config loading inlined — 3 separate paths | D+H | M | Architecture |
| 23 | Edit/Write rules in two incompatible classes | D | M | Architecture |
| 24 | Anemic data models (Compensation, Rule) | B | M | Domain Model |
| 25 | Dict extraction in Plan (raw tool_input dicts) | B | M | Domain Model |
| 26 | Missing Task State Machine concept | B | M | Domain Model |
| 27 | Plan Metadata loosely typed dict | C | M | Domain Model |
| 28 | PR Action stringly-typed (get/list/reply/resolve) | C | S | Domain Model |
| 29 | Boolean blindness (team flag) | C | S | Domain Model |
| 30 | Leaked validation logic across layers | B | L | Architecture |
| 31 | Template Method partial in validators | A+F | M | Patterns |
| 32 | Validator correction logic duplication | F | M | Patterns |
| 33 | Hook Registration — partial Command pattern | F | M | Patterns |
| 34 | No structured logging anywhere | H | M | Consistency |
| 35 | Fallback format inconsistency (raw_output vs parse) | H | S | Consistency |
| 36 | Import organization inconsistency (inline imports) | H | S | Consistency |
| 37 | Config access pattern inconsistency | H | M | Consistency |
| 38 | Double subprocess in ruff_format | I | S | Performance |
| 39 | Nested loop in _gh_api arg building | I | M | Performance |
| 40 | Global mutable config cache (no invalidation) | I | S | Architecture |
| 41 | File coupling on plan.yaml (no coordination) | I | M | Safety |
| 42 | Session hooks — missing error path tests | G | M | Coverage |
| 43 | Commands layer — zero tests | G | M | Coverage |
| 44 | Config loading — edge case tests missing | G | S | Coverage |
| 45 | GitContext — minimal isolated tests | G | S | Coverage |
| 46 | Factory Method missing for Rule construction | A | M | Patterns |

---

## Milestone Proposals

### M1: Safety & Concurrency (Findings 1-4, 16-19, 41)

**Why first:** Race conditions can corrupt user settings and session
state. These are silent data-loss bugs in multi-session usage.

| Finding | Fix |
|---------|-----|
| Blocking subprocess in async MCP | Replace subprocess.run() with asyncio.create_subprocess_exec() |
| Session state TOCTOU | Atomic read-delete with file locking |
| Settings.json race | fcntl/flock advisory locks + atomic write-rename |
| Plan file race | Extend existing atomic write to include read-lock |
| Non-atomic session persistence | Write-temp-rename pattern (already used in plan.py) |
| Validator cache | threading.Lock or functools.lru_cache |
| Config loader TOCTOU | Atomic stat-then-read |
| Permission merge | Same atomic write pattern as settings.json |
| Plan.yaml coordination | Centralize through Plan domain object |

**Effort estimate:** M (collective)
**Blocking:** Must complete before M2 (domain changes touch same files)

### M2: Domain Model Strengthening (Findings 7-8, 15, 24-29)

**Why second:** Type safety prevents bugs introduced during M3/M4
refactoring.

| Finding | Fix |
|---------|-----|
| Dict-as-DTO returns | Create Result[T] = SuccessResult[T] \| ErrorResult |
| Tell-Don't-Ask in session.py | Move formatting to domain object methods |
| Repository Reference | NewType + parse factory, replace 5 split() calls |
| Anemic models | Add matching/validation methods to Rule, Compensation |
| Plan dict extraction | Create TaskInput, TaskUpdate typed params |
| Task State Machine | TaskStatus value object with transitions |
| Plan Metadata | Typed PlanMetadata dataclass |
| PR Action string | PRCommentAction enum |
| Boolean blindness | ReviewerType Literal["user", "team"] |

**Effort estimate:** M-L (collective)
**Blocking:** M1 must complete first (shared files)

### M3: Architecture Alignment (Findings 5-6, 20-23, 30, 40)

**Why third:** Unifies scattered logic into canonical paths before
adding more features.

| Finding | Fix |
|---------|-----|
| RuleEngine never used | Wire validators to use RuleEngine.evaluate() |
| Duplicate YAML parsing | Single Rule.from_yaml() factory |
| Pipeline filter hardcoding | Move filtering into RuleEngine |
| Config 3-path loading | Single ConfigService with caching |
| Hardcoded validator registry | Entry-point or decorator-based discovery |
| Edit/Write rule classes | Consolidate into single Rule hierarchy |
| Leaked validation logic | Route through RuleEngine |
| Global config cache | Integrate into ConfigService with TTL |

**Effort estimate:** L (collective)
**Blocking:** M2 must complete (needs typed domain objects)

### M4: Pattern Adoption (Findings 12, 31-33, 46)

**Why fourth:** Clean patterns build on unified architecture from M3.

| Finding | Fix |
|---------|-----|
| pr_comments if/elif | Strategy dict dispatch |
| Template Method partial | AbstractRule with evaluate() template |
| Validator correction duplication | Extract base correction formatter |
| Hook Command pattern | ToolCommand wrapper for audit logging |
| Factory Method | Rule.from_yaml(), Compensation.from_dict() |

**Effort estimate:** M (collective)

### M5: Test Coverage (Findings 13-14, 42-45)

**Why fifth:** Tests validate M1-M4 changes and prevent regressions.

| Finding | Fix |
|---------|-----|
| Domain RuleEngine & Plan | Unit tests for rule compilation, plan I/O |
| MCP servers (11 untested) | Complete tool coverage per GH-493 |
| Commands layer | Entry point tests for hook dispatch |
| Session error paths | Corrupted state, missing dirs, race conditions |
| Config edge cases | Malformed JSON, permission errors |
| GitContext | Non-git dirs, command failures |

**Effort estimate:** L (collective)
**Target:** Reach 38% coverage threshold, then 60%

### M6: Cross-Cutting Consistency (Findings 9-10, 34-37)

**Why last:** Polish pass after structural changes settle.

| Finding | Fix |
|---------|-----|
| MCP return type inconsistency | Standardize on Result[T] from M2 |
| Error handling mixing | Define HookResult protocol |
| No structured logging | Add structlog with context |
| Fallback format inconsistency | Unified parse-or-raw strategy |
| Import organization | Resolve circular deps, remove inline imports |
| Config access inconsistency | Resolved by M3 ConfigService |

**Effort estimate:** M (collective)

---

## Blocking Chain

```
M1 (Safety) ──> M2 (Domain) ──> M3 (Architecture) ──> M4 (Patterns)
                                                    └──> M5 (Coverage)
                                                    └──> M6 (Consistency)
```

M1 blocks M2 (shared files). M2 blocks M3 (typed objects needed).
M3 blocks M4, M5, M6 (stable architecture needed for patterns,
tests, and consistency).

---

## Strengths (What's Working Well)

- **Validator Chain of Responsibility** — Clean Protocol-based design
  with lazy loading and short-circuit evaluation
- **Atomic plan writes** — Plan.save() already uses write-temp-rename
- **Frozen dataclasses** — HookInput, Rule, Compensation prevent
  accidental mutation
- **LazyGroup CLI** — Efficient dynamic subcommand loading
- **Validator test coverage** — 8/10 validators have adequate tests
  (skill_redirect: 62 tests, prefix_friction: 32 tests)

---

## Metrics

| Metric | Current | After M1-M3 | After M4-M6 |
|--------|---------|-------------|-------------|
| Coverage | 15.66% | ~25% | ~50% |
| Typed MCP returns | 0/24 | 24/24 | 24/24 |
| Domain value objects | 3 | 10+ | 10+ |
| Race conditions | 8 | 0 | 0 |
| Duplicate logic sites | 6 | 1 | 0 |
