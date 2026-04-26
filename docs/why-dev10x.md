# Why Dev10x

## Who is Dev10x for?

Dev10x is for **developers who already use Claude Code** and want
to ship code faster with less babysitting. If you spend your day
in a terminal, write code for a living, and want your AI to handle
the shipping pipeline while you focus on design decisions — this
is for you.

**Good fit:**
- Software engineers using Claude Code on real projects
- Tech leads who review PRs and want consistent quality
- Solo maintainers who need to move fast without cutting corners
- Teams that want repeatable workflows across developers

**Not a fit:**
- Non-technical users looking for no-code AI tools
- Developers who don't use Claude Code
- Teams looking for AI strategy consulting or training courses

## What problems does Dev10x solve?

### Permission friction kills autonomy

Every ad-hoc bash command triggers a permission prompt. Every
prompt pulls you back to the terminal. Dev10x solves this with
67 pre-approved skills that match allow rules — zero interruptions
during normal workflows.

### Progress is invisible

You walk away and come back to a wall of terminal output. Dev10x
provides task lists you can check at a glance, background CI
monitoring, and artifacts (commit messages, PR descriptions) sized
for a phone screen.

### Shipping is manual and inconsistent

Without guardrails, AI produces inconsistent commit messages,
missing ticket references, and PRs without context. Dev10x
enforces gitmoji conventions, JTBD Job Stories, ticket linking,
and atomic commits — automatically.

### Context is lost between sessions

Each new session starts from scratch. Dev10x preserves context
through session memory, PR bookmarks, and deferred work parking
so you pick up exactly where you left off.

## How does Dev10x compare to alternatives?

### vs. Manual Claude Code (no plugin)

| Aspect | Manual | With Dev10x |
|--------|--------|-------------|
| Permission prompts per session | 15-30+ | Near zero |
| Commit message quality | Inconsistent | Gitmoji + JTBD enforced |
| PR lifecycle | Manual commands | Automated pipeline |
| Session continuity | Lost | Preserved |
| Code review | Ad-hoc | Domain-routed, 5+ agents |

### vs. AI coding courses (10xDevs, AI Managers)

Courses teach you *how* to work with AI. Dev10x *does* the work.

| Aspect | Courses | Dev10x |
|--------|---------|--------|
| Time to value | 5-6 weeks + implementation | Immediate |
| Cost | $780-$4,990 | Free (open-source) |
| Output | Knowledge | Working pipeline |
| Maintenance | You build and maintain | Community-maintained |
| Customization | Build from scratch | Override via playbooks |

These are complementary, not competing. Courses provide context
for *why* agent-driven workflows matter. Dev10x provides the
*execution layer* that makes it real.

### vs. Other Claude Code plugins/skills

Most Claude Code skills are individual commands. Dev10x is a
**complete pipeline** — 67 skills that chain together from ticket
to merged PR, with hooks that teach the AI to self-correct and
a playbook system that adapts to your project.

| Aspect | Individual skills | Dev10x |
|--------|-------------------|--------|
| Scope | Single command | Full lifecycle |
| Guardrails | None | 14 hooks, self-correcting |
| Consistency | Per-author | Enforced conventions |
| Orchestration | Manual chaining | Automated pipelines |
| Customization | Fork and edit | Playbook overrides |

## When should you use Dev10x?

**Start with Dev10x when:**
- You're shipping code through PRs regularly
- You want consistent commit and PR quality
- You're tired of approving permission prompts
- You work on a team (or solo) and want repeatable workflows

**Skip Dev10x when:**
- You're exploring or learning (not shipping)
- You don't use GitHub for PRs
- You prefer full manual control over every git operation
- Your project doesn't use conventional commits or PR workflows

## What does the pipeline look like?

```
Ticket → Scope → Branch → Implement → Test → Review →
Commit → PR → CI → Groom → Merge
```

Each step is a skill. Each skill produces a precise artifact.
Each artifact is readable in 10 seconds. You supervise in
5-minute windows. The AI handles the rest.

[Back to README](../README.md) |
[Installation](installation.md) |
[Development](development.md)
