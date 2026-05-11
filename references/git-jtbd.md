# JTBD Job Story Guidelines

Rules for writing Job Stories used in PR titles, PR descriptions,
commit messages, and issue tickets.

> **Scope**: This format governs Job Stories in commits and PR descriptions.
> It also applies to issue titles and tickets.
> **Critical dependency**: Release notes parsing requires precise JTBD
> voice format with an explicit third-person actor and beneficiary.
> First-person "I want to" / "so I can" breaks stakeholder clarity and
> automated release notes collection.
> Skills may define their own output formats in `references/`
> documents. If a skill's reference doc diverges from this format,
> verify the skill output is not used for PR/commit descriptions.

## Format

```
**When** [situation], **[actor] wants to** [motivation], **so [beneficiary] can** [expected outcome].
```

One sentence. No bullet points. No implementation details.

## Language and Localization

Write Job Stories and user-story prose in the project or ticket language.
For English projects, use the English format shown above. For localized
projects, translate the structural labels and prose consistently.

When a story, ticket, or acceptance criterion uses Gherkin-derived
keywords such as `Feature`, `Scenario`, `Given`, `When`, `Then`, `And`,
or `But`, use Cucumber's official language reference instead of
inventing translations:
https://cucumber.io/docs/gherkin/languages/

Feature-file-style blocks must include the matching `# language: <code>`
header from the Cucumber language table.

## Voice Requirement

Job Stories must name the actor and beneficiary in third person.
First-person voice ("I want to", "so I can") is incorrect:

| Form | Example | Status |
|------|---------|--------|
| Correct | **the developer wants to** have Claude config copied | REQUIRED |
| Correct | **so reviewers can** catch issues | REQUIRED |
| Wrong | **I want to** have Claude config copied | WRONG |
| Wrong | **so I can** catch issues | WRONG |
| Wrong | **they want to** catch issues | WRONG |

Use role, customer, team, or system names that make the stakeholder
visible at a glance: `**the Carolina customer wants to** ... **so their
clients can** ...`.

## Key Principles

### 1. No Personas — Focus on Situation

Job stories replace "As a [persona]..." with the **situation** — the
context that creates the need.

### 2. Situation Over Implementation

The "When" clause describes the real-world context, not UI interactions.

- Good: "When reviewing PRs without automated code quality checks"
- Bad:  "When clicking the review button"

### 3. Motivation Reveals Anxiety

The "wants to" clause captures what the named actor is trying to
accomplish.

- Good: "the reviewer wants to have Claude review code automatically"
- Bad:  "I want a new workflow file"

### 4. Expected Outcome Shows Value

The "so [beneficiary] can" clause describes the measurable benefit or
the problem that goes away. It should contrast with the current broken
state.

- Good: "so reviewers can catch regressions before they reach production"
- Bad:  "so the system has reviews"

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Technical language | Not understandable by stakeholders | Use business/domain language |
| Solution-focused "When" | Prescribes implementation | Describe the real-world trigger |
| CLI/command-invocation "When" | "When running `make release-features`" prescribes the tool | Describe the real-world trigger: "When a feature release produces skipped version numbers" |
| Vague outcome | Not testable | Be specific about what improves |
| No contrast with current state | Unclear why it matters | Show what's wrong today |
| Solution-focused "wants to" | "the reviewer wants to see X on separate lines" names the UI change, not the need | Describe the motivation: "the reviewer wants to quickly triage incoming notifications" |
| Solution-focused "wants to" (infra) | "the developer wants to use stable, version-independent paths" names the technical fix, not the need | Describe the user motivation: "the developer wants to run skills without repeated permission prompts" |

## Title Writing Principle

Shift the perspective from what changed in the code to what it
enables for the user. The "so [beneficiary] can" clause captures the
outcome.

### Common patterns

| Change type | Bad (implementation) | Good (outcome) |
|---|---|---|
| New skill | `Add git-worktree skill` | `Enable isolated workspace creation` |
| Hook | `Add bash validation hook` | `Prevent unsafe shell commands` |
| Config | `Add shellcheck workflow` | `Catch shell script errors in CI` |
| Bug fix | `Fix heredoc detection regex` | `Prevent false positives on commit messages` |
| Refactor | `Extract naming logic to module` | `Enable reusable skill naming across tools` |
| Docs | `Add review guidelines rule file` | `Standardize code review workflow` |
| Release | `Bump version to 1.2.0` | `Release skill naming + review features` |

### The "rename test"

If your title reads like a git diff summary, rewrite it. Ask:
*"What can the user do now that they couldn't before?"* — that
answer is your title.

## Examples

### Skill Feature
**When** starting work on a new feature branch, **the developer wants to**
create an isolated worktree automatically, **so the developer can** avoid
cross-indexing conflicts between branches in the IDE.

### Code Review
**When** reviewing PRs without automated checks, **the reviewer wants to**
have Claude review code for quality and patterns, **so the reviewer can**
catch regressions before they reach production.

### Bug Fix
**When** committing changes with heredoc syntax, **the developer wants**
the security hook to recognize safe patterns, **so the developer can**
commit without false positive blocks disrupting the workflow.

### Documentation
**When** onboarding a new contributor, **the maintainer wants to** have
clear rules for naming skills, **so contributors can** follow conventions without
reading every existing skill directory.

### Release
**When** a batch of features is ready, **the release manager wants to**
publish a semver release, **so users can** pin to a stable version and get
predictable updates.
