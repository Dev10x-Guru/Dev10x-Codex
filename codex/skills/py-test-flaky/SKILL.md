---
name: py-test-flaky
description: 'Investigate a flaky Python test and hand the fix off to Dev10x:work-on as a fully scoped ticket. Reproduces the failure, identifies the root cause, drafts the proposed patch in the ticket description (not in the working tree), files the ticket via Dev10x:ticket-create, then invokes Dev10x:work-on so branching, implementation, py-test gate, self-review, PR creation, monitor, and review-comment triage all run through the standard delivery pipeline. TRIGGER when: user reports a flaky pytest test, a test is marked `@pytest.mark.flaky`, or a pytest case fails intermittently in CI. DO NOT TRIGGER when: test failure is deterministic, a non-pytest framework is in use, or the fix is already committed.'
metadata:
  upstream: skills/py-test-flaky/SKILL.md
---

> **Running in Codex.** Generated from `skills/py-test-flaky/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/py-test-flaky/`.
> Reviewed for Codex but not yet run end to end in it: confirm before any step that writes to GitHub or rewrites history.

# Fix Flaky Python Test

Investigate a flaky pytest test, scope the fix as a ticket,
and hand delivery off to `Dev10x:work-on`. This skill is a
narrow *investigator + ticket scoper* — it does NOT mutate
the working tree, create a branch, commit, or open a PR
itself. All delivery work runs through `Dev10x:work-on` so
flaky-test fixes ship with the same coverage gate, self-
review, PR monitor, and bot-comment triage as any other
ticket of comparable scope.

## Instructions

The full workflow — 5 steps covering reproduction, root-cause
analysis, draft patch, ticket creation, and hand off to
`Dev10x:work-on` — lives in [`instructions.md`](instructions.md).

When this skill is invoked, Read `instructions.md` now and
follow it end-to-end. `AskUserQuestion` gates documented there
are REQUIRED.
