# Skill Pipelines Reference

Composable chains for common development workflows. Each step maps to
a skill invocation — invoke the full chain via `Dev10x:work-on`, or
enter at any step independently.

## Pipelines

### 1. Shipping Pipeline (ticket to merged PR)

The core loop: from a ticket to code on `develop`.

```
scope → branch → jtbd → implement → verify → review → commit → PR → CI → respond → groom → request
```

| Step | Skill | Input | Output |
|------|-------|-------|--------|
| Scope ticket | `Dev10x:ticket-scope` | ticket ID | Architecture notes, ticket updated |
| Create branch | `Dev10x:ticket-branch` | ticket ID + title | Named branch checked out |
| Draft Job Story | `Dev10x:jtbd` | ticket ID | JTBD Job Story |
| Implement | _(code)_ | task description | Changed files |
| Verify | _(test runner)_ | changed files | Pass/fail |
| Review changes | `Dev10x:review` | branch diff | Review findings |
| Fix review issues | `Dev10x:review-fix` | review findings | Fixed files |
| Commit | `Dev10x:git-commit` | staged changes | Atomic commit |
| Create PR | `Dev10x:gh-pr-create` | branch + commits | Draft PR URL |
| Monitor CI | `Dev10x:gh-pr-monitor` | PR number | Green CI, ready PR |
| Address comments | `Dev10x:gh-pr-respond` | PR URL | Comments resolved |
| Groom history | `Dev10x:git-groom` | branch commits | Squashed/rebased branch |
| Request review | `Dev10x:gh-pr-request-review` | PR number | Reviewers assigned |

**Full pipeline via orchestrator:**
```
Skill(skill="Dev10x:work-on", args="TICKET-ID")
```

**Enter at any step** — each skill accepts its listed input directly.

---

### 2. PR Continuation Pipeline (resume after review)

For resuming work on an existing PR that received review comments.

```
fetch comments → address → fixup → CI → groom → ready
```

| Step | Skill | Input | Output |
|------|-------|-------|--------|
| Fetch and address | `Dev10x:gh-pr-respond` | PR URL | Comments resolved, fixup commits |
| Monitor CI | `Dev10x:gh-pr-monitor` | PR number | Green CI |
| Groom history | `Dev10x:git-groom` | branch | Clean history |

**Via orchestrator:**
```
Skill(skill="Dev10x:work-on", args="https://github.com/owner/repo/pull/N")
```

---

### 3. Investigation Pipeline (bug or incident)

For investigating a bug, error, or unexpected behavior.

```
gather → investigate → document → decide
```

| Step | Skill | Input | Output |
|------|-------|-------|--------|
| Gather context | `Dev10x:gh-context` | issue/PR/Sentry URL | Context summary |
| Investigate | `Dev10x:investigate` | error + context | Root cause hypothesis |
| Document findings | _(write notes or ticket comment)_ | findings | Ticket updated |
| Decide | _(ADR or ticket scope)_ | findings | Decision recorded |

**Via orchestrator:**
```
Skill(skill="Dev10x:work-on", args="SENTRY-URL TICKET-ID")
```

---

### 4. Architecture Decision Pipeline

For evaluating a significant design choice.

```
scope → draft ADR → evaluate → record
```

| Step | Skill | Input | Output |
|------|-------|-------|--------|
| Scope decision | `Dev10x:scope` | topic | Options identified |
| Draft ADR | `Dev10x:adr` | options | ADR document |
| Evaluate options | `Dev10x:adr-evaluate` | ADR + codebase | Ranked options with trade-offs |
| Record | _(commit ADR)_ | final choice | Committed ADR |

---

### 5. Deferred Work Pipeline (park and resume)

For capturing work that can't happen now.

```
park → discover → resume
```

| Step | Skill | Input | Output |
|------|-------|-------|--------|
| Park item | `Dev10x:park` | description | Parked entry |
| Park with reminder | `Dev10x:park-remind` | description + trigger | Parked with reminder |
| Discover parked | `Dev10x:park-discover` | _(none)_ | List of parked items |
| Resume item | `Dev10x:work-on` | parked item description | Active work stream |

---

## Standalone Invocation

Each skill in a pipeline can be invoked independently. Prerequisites:

| Skill | Prerequisites |
|-------|--------------|
| `Dev10x:ticket-branch` | On `develop` or `main`, clean working tree |
| `Dev10x:git-commit` | Staged changes, feature branch |
| `Dev10x:gh-pr-create` | Branch pushed, commits ahead of base |
| `Dev10x:gh-pr-monitor` | Draft PR exists |
| `Dev10x:gh-pr-respond` | PR with unresolved review threads |
| `Dev10x:git-groom` | Feature branch with multiple commits |
| `Dev10x:gh-pr-request-review` | PR in ready state |

**Example: enter pipeline at commit step**
```
/Dev10x:git-commit
```

**Example: enter pipeline at PR creation**
```
/Dev10x:gh-pr-create
```

**Example: resume at CI monitoring after a manual push**
```
/Dev10x:gh-pr-monitor 123
```

---

## Pipeline Composition via work-on

`Dev10x:work-on` detects the work type from its inputs and selects
the matching pipeline automatically:

| Input type | Pipeline selected |
|-----------|-----------------|
| Ticket URL or ID | Shipping pipeline |
| PR URL | PR continuation pipeline |
| Sentry URL + ticket | Investigation pipeline |
| Free text only | Local-only (no branch required) |

The playbook system (`Dev10x:playbook`) defines each pipeline as a
play with named steps. User overrides follow the 3-tier resolution
in `references/config-resolution.md` (global preferred:
`~/.claude/memory/Dev10x/playbooks/work-on.yaml`).

See `references/task-orchestration.md` for orchestration patterns
and `.claude/rules/model-selection.md` for model assignments per step.
