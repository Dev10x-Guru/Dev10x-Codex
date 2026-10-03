---
name: qa-self
description: 'Execute QA test cases on staging using headless Playwright, capture screenshot and video evidence, upload to Linear, and post structured results. TRIGGER when: QA ticket has test cases to execute against staging and evidence is needed. DO NOT TRIGGER when: analyzing PR for QA needs (use Dev10x:qa-scope), or running unit/integration tests (use test skill).'
metadata:
  upstream: skills/qa-self/SKILL.md
---

> **Running in Codex.** Generated from `skills/qa-self/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/qa-self/`.
> Not yet verified in Codex (tracked in Dev10x-Codex#24): expect gaps and confirm before any step that writes to GitHub or rewrites history.

# Self-QA — Automated Staging Test Execution

Execute QA regression test cases on staging using headless
Playwright, capture screenshot and video evidence, and post
structured results to Linear.

## Instructions

The full workflow — test case discovery, Playwright execution,
evidence capture, Linear upload, result formatting — lives in
[`instructions.md`](instructions.md).

When this skill is invoked, Read `instructions.md` now and
follow it end-to-end. `TaskCreate` calls documented there are
REQUIRED.

**End-to-end read enforcement (GH-166, GH-1279): this file may
not fit in one `Read`.** At ~60 KB it sits close enough to the
token cap a single call returns that a truncated `PARTIAL view`
is likely, and an agent that stops at the first page is working
from part of the contract while believing it holds all of it.

Keep issuing `Read(offset=…)` until you have reached the final
line. Do NOT substitute `Grep` or a single `Read(limit=…)` for
the missing pages — the two blocking gates below live in the
body, and a truncated read drops them silently.

If you did not see the last line of the file, you have not read
the contract.

## Gates

Two blocking gates in `instructions.md` are enforced with
`AskUserQuestion` — never a plain-text question:

1. **Test-failure recovery** (Phase 3) — fix and retry / skip the
   failing case / abort.
2. **Evidence review** (Phase 4.4) — approve the upload / re-capture /
   abort. Artifacts are verified by
   `scripts/verify-evidence.py` (Phase 4.1) and reviewed **locally**
   before anything reaches Linear: evidence trails on a ticket are
   append-only, so a bad take can only be superseded, never withdrawn.
