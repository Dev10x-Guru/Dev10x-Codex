---
name: Dev10x:skill-reinforcement
description: >
  Remind the agent about available skills when it uses CLI commands
  that should be handled by skills or MCP tools instead. Reads
  conversation context to identify the offending command, matches
  it against a command-to-skill map, and outputs a firm reinforcement
  message pointing to the correct skill.
  TRIGGER when: user sees agent using CLI instead of a skill, user
  rejects a command that should have been a skill, or user says
  "use the skills".
  DO NOT TRIGGER when: agent is already using skills correctly,
  or the CLI command has no skill equivalent.
user-invocable: true
invocation-name: Dev10x:skill-reinforcement
allowed-tools:
  - Read(~/.claude/SKILLS.md)
  - Read(${CLAUDE_PLUGIN_ROOT}/skills/skill-reinforcement/references/*)
  - Read(${CLAUDE_PLUGIN_ROOT}/src/dev10x/validators/command-skill-map.yaml)
---

# Dev10x:skill-reinforcement

Quick reinforcement nudge when an agent reaches for CLI commands
instead of using available skills or MCP tools.

## When to Use

Invoke this skill when:
- The agent ran a CLI command that a skill already handles
- You rejected a command and want the agent to use a skill instead
- You approved a command but want to reinforce the skill habit
- You want to say "use the skills" with a structured response

## Orchestration

**REQUIRED: Create a task at invocation.** Execute at startup:

1. `TaskCreate(subject="Reinforce skill usage", activeForm="Reinforcing")`

Mark completed when done: `TaskUpdate(taskId, status="completed")`

## Instructions

### Step 1: Identify the offending command

Scan the recent conversation for the CLI command that triggered
this invocation. Look for:
- The most recent `Bash` tool call that was rejected or approved
- Any command the user flagged as wrong
- If the user provided arguments (e.g., `/Dev10x:skill-reinforcement kubectl`),
  use that as the command identifier

Store the command string for matching.

### Step 2: Match against command-skill map

Read the command-skill mapping from the canonical location:
`${CLAUDE_PLUGIN_ROOT}/src/dev10x/validators/command-skill-map.yaml`.

The YAML in `skills/skill-reinforcement/references/command-skill-map.yaml`
is a legacy copy — prefer the hook's YAML which is the single
source of truth.

Match the identified command against the `patterns` list in each
mapping entry. Use prefix matching — if the command starts with
any pattern in the list, it matches that entry.

If no match is found in the map, fall back to Step 3.

### Step 2b: Check workflow context

If a pattern match is found but the command appears to be a valid
part of the currently active skill's documented workflow, check
whether the skill says to **delegate** for this case:

- Read the active skill's SKILL.md (if identifiable from context)
- Check if the command matches a delegation point marked with
  `REQUIRED: Skill()` — a command can be valid syntax within
  a skill but still a violation if the skill mandates delegation
  to a sub-skill for that operation
- Example: `gh api --method POST .../replies` is documented in
  `gh-pr-respond` but the skill requires VALID comments to go
  through `Dev10x:gh-pr-fixup` — using the raw API is a violation

If the command is a delegation bypass, treat it as a match and
output the reinforcement pointing to the correct sub-skill.

### Step 3: Fall back to SKILLS.md

If no direct mapping exists, read `~/.claude/SKILLS.md` and scan
skill descriptions from the system-reminder context to find the
best match based on the command's purpose.

### Step 4: Output reinforcement message

Output a firm, concise reinforcement message with these sections:

1. **Command detected:** — the CLI command that was identified
2. **Use instead:** — skill invocation name and one-line description
3. **Why:** — reason from the map entry (if available)
4. **How to invoke:** — `Skill("<skill-name>")` call syntax.
   For MCP tools, add: "Call this as an MCP tool call, NOT as a
   Bash command. MCP tool names are tool interface identifiers,
   never shell executables. Example:
   `mcp__plugin_Dev10x_cli__mktmp(namespace='git',
   prefix='commit-msg', ext='.txt')` — not
   `mcp__plugin_Dev10x_cli__mktmp git commit-msg .txt`."
5. **Related skills:** — from the map entry (if available)

If multiple skills could apply, list all of them ranked by
relevance.

### Step 4b: Respect user rejection

**If the user explicitly rejected the command** (denied the Bash
tool call), do NOT conclude "no violation found" and resume the
rejected workflow. A user rejection overrides documentation
matching — even if the command appears valid within the skill,
the user's denial takes precedence. Instead, ask the user what
they expected if no skill match is found.

### Step 5: Reinforce the general principle

End with a brief reminder:

> Always check if a skill or MCP tool exists before reaching for
> CLI commands. Skills provide consistent behavior, proper tool
> declarations, and avoid permission friction.

## Examples

### Example 1: kubectl usage

**User:** `/Dev10x:skill-reinforcement`
(after agent ran `kubectl get pods -n staging`)

**Output:**
```
## Skill Reinforcement

**Command detected:** `kubectl get pods -n staging`
**Use instead:** `/Dev10x:k8s` — Kubernetes operations via
aws-vault authenticated kubectl

**Why:** Direct kubectl calls bypass aws-vault authentication
and may fail or use wrong credentials.

**How to invoke:**
Skill("Dev10x:k8s")
```

### Example 2: direct git push

**User:** `/Dev10x:skill-reinforcement`
(after agent ran `git push origin feature-branch`)

**Output:**
```
## Skill Reinforcement

**Command detected:** `git push origin feature-branch`
**Use instead:** `/Dev10x:git` — Safe git push with
protected branch checks

**Why:** Direct git push bypasses force-push protection
on develop/main branches.

**How to invoke:**
Skill("Dev10x:git")
```

### Example 3: no match found

**User:** `/Dev10x:skill-reinforcement`
(after agent ran `curl https://api.example.com/health`)

**Output:**
```
## Skill Reinforcement

**Command detected:** `curl https://api.example.com/health`
**No direct skill match found.**

Available skills that might help:
- `/Dev10x:k8s` — if checking service health in k8s
- `/Dev10x:investigate` — if investigating a bug report

Check ~/.claude/SKILLS.md for the full list of available skills.
```
