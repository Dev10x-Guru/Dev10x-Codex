# Hook Overhead Baseline

**Date:** 2026-04-23
**Source:** `/tmp/Dev10x/logs/hooks-2026-04-23.jsonl`
**Window:** 2026-04-23 04:55Z – 17:17Z (~12h20m of active use)
**Sample size:** 3,921 records (2,221 wrap + 1,692 body + audit)

---

## Summary

| Metric | Value |
|--------|-------|
| Total wrap wall-time (all hooks, all calls) | **115.3 s** |
| Total body work-time (feature functions) | 21.0 s |
| **Startup / wrapper overhead (wrap − body)** | **94.3 s (82 %)** |
| Wrap records | 2,221 |
| Blocks | 58 (2.6 % of wrap records) |
| Active sessions (distinct `session_id`) | 1 *(data quality issue — see below)* |

82 % of all hook wall-clock time is spent in `uv run --script`
cold-start and interpreter boot, not in the validators themselves.
Every tool call on the critical path eats ~50 ms before Claude sees
the result.

---

## Per-hook breakdown (wrap phase)

| Entry | Calls | Total wrap (ms) | Avg (ms) | Body total (ms) | Overhead / call |
|---|---:|---:|---:|---:|---:|
| `validate-bash` | 973 | 52,692 | 54 | 17,777 | **36 ms** |
| `task-plan-sync` | 416 | 19,109 | 46 | — *(no body)* | ~46 ms |
| `ruff-format` | 258 | 13,234 | 51 | 1,449 | **46 ms** |
| `validate-edit-write` | 258 | 12,299 | 48 | — *(no body)* | ~48 ms |
| `skill-pre` | 92 | 4,685 | 51 | — | ~51 ms |
| `skill-post` | 92 | 4,645 | 50 | — | ~50 ms |
| `session-stop` | 85 | 5,353 | 63 | ~1,059 (persist) | ~51 ms |
| `session-start` | 36 | 2,435 | 68 | ~489 (aliases) | ~54 ms |
| `precompact-context` | 12 | 739 | 62 | — | ~62 ms |

### Percentile detail for top hooks

| Hook | n | min | p50 | p95 | max |
|---|---:|---:|---:|---:|---:|
| `validate-bash` wrap | 978 | 43 | 56 | 60 | 69 |
| `validate-bash` body | 978 | 14 | 19 | 21 | 29 |
| `task-plan-sync` wrap | 416 | 35 | 47 | 52 | 121 |
| `validate-edit-write` wrap | 258 | 38 | 49 | 54 | 60 |

Distribution is tight (p50 ≈ p95), which confirms the cost is a
flat per-invocation startup tax, not workload-dependent.

---

## Cost attribution

Per-call overhead breaks down roughly as:

- **~40 ms** — `uv run --script` resolution + venv activation
- **~5–10 ms** — Python interpreter + stdlib imports
- **Body work**: 18 ms for `validate-bash`, <5 ms for everything else

`validate-bash` is the only hook where real validation work
dominates (body:wrap ≈ 1:3). All others are ≥ 10× overhead-to-work.

---

## Data quality gaps

The JSONL log is missing information needed for richer analysis:

1. **`session_id` empty in every record** — 3,921 rows all collapse
   to "1 session"; real number is likely 30–40 for a day like this.
   Cannot compute per-session cost, cannot correlate hook runs to
   user activity bursts.
2. **`event` field null on all wrap records** — only body records
   carry it. Cannot build PreToolUse vs PostToolUse breakdowns
   directly from wrap phase.
3. **Block reason missing** — all 58 blocks serialise with no
   `reason` / `message`, so we cannot tell which rule fired. Makes
   noise-rule triage blind.

---

## Extrapolated daily impact

At this rate (115 s wrap-time per 12.5 h of active use):

- **~4 min/day** of wall-time goes to hook startup across a
  working day.
- Concentrated on the critical path: every `Bash` call adds ~54 ms,
  every `Edit`/`Write` adds ~50 ms × 2 (ruff-format +
  validate-edit-write) = **100 ms per file edit**.
- At 258 edits/day that is **26 s of pure user-perceived latency
  added to tool responses**.

---

## Top opportunities

1. **Collapse per-tool-call validators into a long-running daemon.**
   A persistent Python worker per session, talking over unix
   socket, eliminates the 40 ms uv-start cost for `validate-bash`,
   `validate-edit-write`, `ruff-format`, `task-plan-sync`. Target:
   drop p50 wrap from 55 ms → <10 ms.

2. **Debounce `task-plan-sync`.** 416 invocations (34 % of all
   validator calls) is aggressive. Evaluate whether
   PostToolUse-only or time-based throttling preserves correctness.

3. **Fix the audit schema.** Populate `session_id`, `event`, and
   block `reason` in wrap records before the next baseline is
   taken — otherwise we cannot measure improvements meaningfully.

4. **Explore native compilation** for `validate-bash` only (highest
   call volume). PyInstaller or a Go rewrite would cut overhead to
   <5 ms; validator logic is small and stable.

Full proposal lives in the companion scope memo (next doc) and
tracking ticket.
