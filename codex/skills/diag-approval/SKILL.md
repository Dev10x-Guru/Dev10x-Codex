---
name: diag-approval
description: 'Use right after manually approving a permission prompt — the way $Dev10x:diag-friction is used after a prompt is refused — so the approval you just gave becomes a pre-approval everywhere, or you learn why a skill, a rewrite or a directory setting fixes it better, without retyping the command. TRIGGER when: the supervisor approved a prompt and says "diag approval", "remember that approval", "make that stop prompting", or invokes $Dev10x:diag-approval. DO NOT TRIGGER when: the prompt was refused (use Dev10x:diag-friction), or no tool call prompted recently.'
metadata:
  upstream: skills/diag-approval/SKILL.md
---

> **Running in Codex.** Generated from `skills/diag-approval/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/skills/diag-approval/`.
> **Not supported in Codex yet**: this skill depends on Claude Code features Codex lacks (Dev10x-Codex#10). Use it from Claude Code; Codex runs it only when invoked by name.

# Dev10x:diag-approval

**Announce:** "Using Dev10x:diag-approval to turn the approval you just
gave into a pre-approval."

## Orchestration

This skill follows `references/task-orchestration.md` patterns.

**REQUIRED: Create a task at invocation.** Execute at startup:

1. `TaskCreate(subject="Diagnose the approved prompt", activeForm="Diagnosing approval")`

Mark it `completed` on every terminal branch, including "nothing
prompted" and "None of these".

## Workflow

### Step 1: Identify the approved call

An argument wins: `$Dev10x:diag-approval <command>` uses the argument
verbatim and skips to Step 2.

Otherwise, collect **candidates**: tool calls since the supervisor's
previous message that showed a permission prompt and then ran (not
refused), newest first, at most three. Take each in the form triage
needs:

| Tool | Target to hand over |
|------|---------------------|
| `Bash` | the full `command` string, exactly as sent |
| `mcp__*` | the full tool name, e.g. `mcp__server__tool` |
| `Read` / `Edit` / `Write` | `Read(<path>)` / `Edit(<path>)` with the file path |
| `WebFetch` | `WebFetch(domain:<host>)` |

Copy the call; do not reconstruct it from memory. A Bash command
retyped "close enough" loses the quoting or chaining that caused the
prompt, and triage then grants a rule for a shape that never
prompted.

- **No candidates**: say nothing prompted since the last message,
  close the task and stop. Do not guess a target.
- **One candidate**: use it and skip the question below.
- **Two or three candidates**: **REQUIRED: Call `AskUserQuestion`**
  (do NOT use plain text, call spec:
  [ask-candidate.md](tool-calls/ask-candidate.md)). Picking the wrong
  call grants the wrong rule everywhere. Options:
  - `<newest candidate>` (Recommended): the newest prompt is the one
    the supervisor most likely just approved.
  - `<each older candidate>`, newest first.
  - None of these: stop without granting anything.

### Step 2: Delegate

1. `$Dev10x:permission-grant (args: "<target>")`

`Dev10x:permission-grant` owns triage, the confirmation gate, the
write and the verification. Do not call `permission_grant` from here.
Skipping its triage is exactly the shortcut that grants a rule a skill
or a rewrite would have fixed better.

### Step 3: Close

Read the outcome from `Dev10x:permission-grant`'s final report, which
names the branch it took, and finish with one line:

- **Granted**: the rule and how many files received it.
- **A non-`grant` verdict**: the approval treated a symptom, not a
  missing rule. Repeat the recommended fix, so the next time the
  supervisor sees the prompt they know which route to take.
- **Cancel or Dry run**: say nothing was written.
