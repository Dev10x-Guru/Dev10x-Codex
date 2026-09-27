---
name: Dev10x:scope
invocation-name: Dev10x:scope
description: >
  Base scoping skill for technical research and architecture design.
  Provides reusable scoping workflow for investigating codebases,
  designing solutions, and documenting decisions.
  TRIGGER when: performing technical research or architecture design
  without a specific tracker integration.
  DO NOT TRIGGER when: scoping a Linear ticket (use Dev10x:ticket-scope),
  documenting an ADR (use Dev10x:adr), or scoping a project (use
  Dev10x:project-scope).
user-invocable: false
allowed-tools:
  - Agent
  - WebFetch
  - Grep
  - Glob
  - Read
  - Bash(java -jar:*)
  - AskUserQuestion
  - TaskCreate
  - TaskUpdate
---

# Dev10x:scope — Base Technical Scoping

Foundational scoping skill providing reusable research and
architecture-design workflows. Not directly invocable — extended
by `Dev10x:ticket-scope`, `Dev10x:adr`, `Dev10x:project-scope`,
`Dev10x:project-audit`.

## Instructions

The full workflow — research phases, design passes, ADR
formatting, diagram rendering, decision documentation — lives in
[`instructions.md`](instructions.md).

When this skill is invoked (directly or via an extension skill),
Read `instructions.md` now and follow it end-to-end.
