---
name: gh-pr-create
description: 'Create a GitHub pull request for the current branch with issue tracker integration (GitHub Issues, Linear, or JIRA). Sources or generates a JTBD Job Story for the PR description, extracts ticket info from branch name, pushes the branch, creates a draft PR with Job Story, commit list, and issue tracker link, posts summary comment, and opens in browser. TRIGGER when: branch is ready for PR creation, user says "create PR". DO NOT TRIGGER when: PR already exists (use Dev10x:gh-pr-respond or Dev10x:gh-pr-monitor instead), or user just wants to push changes.'
metadata:
  upstream: skills/gh-pr-create/SKILL.md
---

> **Running in Codex.** Generated from `skills/gh-pr-create/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/gh-pr-create/`.

# Create Pull Request for Ticket

Create a GitHub pull request for the current branch with issue
tracker integration (GitHub Issues, Linear, or JIRA). Handles
pushing the branch, generating Job Story + commit list body,
creating the PR, posting summary comments, and opening it in
the browser. Supports update mode for existing PRs.

## Instructions

The full workflow — branch push, Job Story sourcing, PR body
template, ticket detection, preview gate, summary comment —
lives in [`instructions.md`](instructions.md).

When this skill is invoked, Read `instructions.md` now and
follow it end-to-end. `TaskCreate` and `AskUserQuestion` calls
documented there are REQUIRED (unless invoked with
`--unattended`, which auto-advances the preview gate).

**End-to-end read enforcement (GH-166):** Consume
`instructions.md` via a full `Read` of the file. Do NOT use
`Grep`, partial `Read(offset=...)`, or token-budget skimming
to locate specific steps — the push-then-create order, the
ticket-detection fallbacks, the Job Story sourcing rules, and
the summary-comment side effects are scattered across the
document. Partial reads that skip later sections routinely
miss guardrails added after the read window.
