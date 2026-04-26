# Skill Orchestration: Formatting as Intent Signal

Markdown formatting controls how Claude agents interpret task
specifications. This guide clarifies the distinction between mandatory
and advisory patterns in skill definitions.

## Numbered Lists = Instructions

When a skill's Orchestration section lists multiple `TaskCreate` or
`TaskUpdate` calls in a **numbered list**, they are interpreted as
blocking requirements that must execute before other work begins.

**Pattern:**
```markdown
**REQUIRED: Create tasks before ANY work.** Execute these
`TaskCreate` calls at startup:

1. `TaskCreate(subject="Step 1", activeForm="Working on Step 1")`
2. `TaskCreate(subject="Step 2", activeForm="Working on Step 2")`
```

**Effect:** Agents read numbered lists as ordered instructions and
execute them sequentially.

## Code Blocks = Examples Only

When the same task specifications appear in a **fenced code block**
(triple backticks), they are interpreted as illustrative examples,
not mandatory requirements.

**Anti-pattern:**
```markdown
**Task tracking:** Create tasks for each step:

\`\`\`
TaskCreate(subject="Step 1", activeForm="Working on Step 1")
TaskCreate(subject="Step 2", activeForm="Working on Step 2")
\`\`\`
```

**Effect:** Agents may skip code-block instructions, treating them as
non-binding examples.

## Enforcement Language

Pair numbered lists with explicit intent markers to remove ambiguity:

| Marker | Usage | Rationale |
|--------|-------|-----------|
| `REQUIRED:` | Tasks that block all downstream work | Highest precedence |
| `MANDATORY:` | Non-negotiable setup steps | Policy/constraint |
| `ALWAYS` | Repeating conditions across phases | Consistency |
| `DO NOT SKIP` | Steps with critical side effects | Safety |

**Example:**
```markdown
**REQUIRED: Create tasks before ANY work.** Execute these
`TaskCreate` calls at startup:

1. `TaskCreate(subject="Verify state", activeForm="Verifying")`
```

## Why Formatting Matters

Claude agents process Markdown structure as semantic information:
- **Numbered lists** trigger sequential-instruction parsing
- **Code blocks** trigger example/illustration parsing
- **Intent markers** add explicit constraints to the prompt context

This distinction arises naturally from Claude's instruction processing,
not from explicit code changes.

## Migration Example

**Before (code block—reads as example):**
```markdown
When writing multi-step skills, include task tracking:

\`\`\`
TaskCreate(subject="Phase 1: Gather", activeForm="Gathering")
TaskCreate(subject="Phase 2: Plan", activeForm="Planning")
\`\`\`
```

**After (numbered list + REQUIRED):**
```markdown
**REQUIRED: Create tasks before ANY work.** Execute these
`TaskCreate` calls at startup:

1. `TaskCreate(subject="Phase 1: Gather", activeForm="Gathering")`
2. `TaskCreate(subject="Phase 2: Plan", activeForm="Planning")`
```

## Bundled Call Spec References

When a tool call has complex parameters (e.g., `AskUserQuestion` with
multiple options, previews, or nested structure), preserve the full
call specification in a separate file under `tool-calls/` in the skill
directory. Reference it inline from the enforcement marker:

```markdown
**REQUIRED: Call `AskUserQuestion`** (do NOT use plain text, call spec:
[ask-strategy.md](./tool-calls/ask-strategy.md)).
Options:
- Fixup (Recommended) — Small targeted fixes
- Full restructure — Reset and rebuild from scratch
```

The `tool-calls/ask-strategy.md` file contains the full JSON-like call:

```markdown
# Decision Gate: Strategy Selection

\`\`\`
AskUserQuestion(questions=[{
    question: "Which strategy?",
    header: "Strategy",
    options: [
        {label: "Fixup (Recommended)",
         description: "Small targeted fixes",
         preview: "git commit --fixup=<sha>"},
        ...
    ],
    multiSelect: false
}])
\`\`\`
```

**When to bundle:** Create a `tool-calls/` file when the full call
spec exceeds ~5 lines (complex options, previews, metadata). Do NOT
create files for trivial one-line calls like `TaskUpdate(taskId,
status="completed")` — the inline enforcement text is sufficient.

**Naming convention:**
- `ask-<purpose>.md` for `AskUserQuestion` gates
- `update-<purpose>.md` for complex `TaskUpdate` calls with metadata

## Reference

See `references/task-orchestration.md` for full orchestration patterns,
including auto-advance, batched decisions, and tier guidance.

See `.claude/agents/reviewer-skill.md` item 14a for review checklist
enforcement of this pattern.
