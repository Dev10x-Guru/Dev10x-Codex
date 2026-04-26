# Essential Conventions

Universal rules for every session. Detailed guides live in
`references/` and load on-demand via skills.

## Branch & PR Targeting

- **Feature PRs** target the detected base branch — `detect-base-branch.sh`
  prefers `develop`/`development`, falls back to `main`/`master`/`trunk`
- **Release PRs** target `main` only via merge from `develop`
- Branch format: `username/TICKET-ID/short-description`
- Worktree branch format: `username/TICKET-ID/worktree-name/short-description`
- **Self-motivated work** (no ticket): Use `username/short-description` and
  set `Fixes: none — self-motivated` in PR body (see `git-pr.md`)

## Commit Format

- Title: `<gitmoji> <TICKET-ID> <outcome-focused description>`
- Max 72 characters per line (title and body)
- Outcome-focused: "Enable X" not "Add X" — describe what
  the change enables, not what was implemented
- One logical change per commit (atomic commits)
- No "Co-Authored-By: Claude" footer
- Full format guide: `references/git-commits.md`

## PR Body

- First paragraph: JTBD Job Story (`**When** ... **wants to** ...
  **so** ... **can** ...`)
- Optional: Compact commit list (one line per commit)
- Last line: `Fixes:` link (issue URL or `none — self-motivated`)
- Do NOT add extra separators (`---`) between Job Story and
  commit list — `create-pr.sh` template handles separators
- Full guide: `references/git-pr.md`

## Decision Gates & Orchestration

Skills with blocking decision points MUST use `AskUserQuestion` tool calls,
never plain text questions. This ensures:
- Execution blocks until the user responds (not auto-progressed)
- Options are clickable and structured (not free-text)
- The skill's documented flow is respected

Mark every decision gate in SKILL.md with:
**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text)

Plain text questions allow agents to silently substitute default answers,
breaking skill orchestration. See `.claude/rules/skill-gates.md` for pattern.

This rule applies **globally** — not only inside loaded skills. When
presenting A/B design choices, architectural trade-offs, or strategy
options between skill invocations, use `AskUserQuestion` with structured
options. Queue decisions per `references/task-orchestration.md` (Batched
Decision Queue pattern) and present them in a single batch when all
tasks are blocked.

## Reference Documents

| Document | Topic | Loaded by |
|----------|-------|-----------|
| `references/git-commits.md` | Commit format, gitmoji, atomic commits | `Dev10x:git-commit` skill |
| `references/git-jtbd.md` | Job Story format, anti-patterns | `Dev10x:jtbd` skill |
| `references/git-pr.md` | PR body, grooming, review feedback | `Dev10x:gh-pr-create` skill |
| `references/review-guidelines.md` | Review workflow, threads, summaries | `Dev10x:gh-pr-review` skill |
| `references/review-checks-common.md` | False positive prevention, verification | Review agent specs |
