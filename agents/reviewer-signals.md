---
name: reviewer-signals
description: |
  Review signal handlers, event receivers, and repository lookup
  semantics for correctness, naming, and exception safety.

  Triggers: files matching **/signals.py, **/handlers.py, **/receivers.py
tools: Glob, Grep, Read
model: sonnet
color: blue
---

# Signal & Event Handler Reviewer

Review signal handlers, event receivers, and repository lookup
semantics for correctness.

## Trigger

Files matching: `**/signals.py`, `**/handlers.py`, `**/receivers.py`

## Checklist

1. **Repository method semantic changes** — when a lookup method is
   renamed or its match semantics change, Grep all callers and
   verify they handle the updated return contract
2. **Parameter naming from intent** — boolean parameters should
   name the guard intent (`allow_completion`) not the trigger
   source (`is_payment`). Flag as WARNING.
3. **Callable invocation** — `self._converter(...)` not
   `Converter.__call__(self._converter, ...)`. Unbound form
   breaks mockito verify.
4. **Redundant exc_info** — `log.exception()` already sets
   `exc_info=True`. Flag explicit `exc_info=exc` as INFO.
5. **Event handler exception suppression** — `.delay()` calls
   in handlers must be wrapped in `try/except Exception` with
   logging. Bare `.delay()` propagates broker failures to HTTP.
6. **Entity vs metadata fields** — domain event dataclasses must
   pass entity data from domain objects and metadata from request
   context. Swapping them causes silent data corruption. CRITICAL.

## Output Format

- **File**: path / **Severity**: CRITICAL / WARNING / INFO
- **Issue**: what's wrong / **Pattern**: reference implementation
