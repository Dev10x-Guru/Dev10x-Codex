# Skill Tool Invocation Syntax

Reference for the Skill tool invocation pattern in skill definitions.

## Named Parameter Syntax

The Skill tool REQUIRES named parameters: `skill=` and `args=`.

**Correct:**
```python
Skill(skill="Dev10x:audit-report", args="path/to/findings.json")
Skill(skill="Dev10x:gh-pr-create", args="--title 'My PR'")
```

**Incorrect (positional arguments — runtime error):**
```python
Skill(Dev10x:audit-report, args="path/to/findings.json")
Skill("Dev10x:gh-pr-create", "--title 'My PR'")
```

## Invocation Name Lookup

When a skill delegates to another skill via `Skill()`:

1. **Use the `name:` field** from the target skill's SKILL.md, not
   the directory name or `invocation-name:` alias.
   - Directory: `skills/audit-report/`
   - SKILL.md `name:`: `Dev10x:audit-report` ✓
   - Bash invocation: `Skill(skill="Dev10x:audit-report", ...)`

2. **Alias handling**: If the skill defines `invocation-name:`, both
   names work at CLI/skill invocation, but the `name:` is the
   canonical form.

## Path Conventions in args=

Temporary file paths for findings or intermediate data:

- **Session temp**: `/tmp/claude/skill-audit/findings-*.json`
  - Scoped to a single session
  - Declared in source skill's `allowed-tools: [Read(/tmp/claude/skill-audit/**)]`
  - Delegated skill reads from same path: `Skill(args="/tmp/claude/skill-audit/findings.json")`

- **Memory cache**: `~/.claude/projects/<project>/memory/`
  - Persists across sessions
  - Use for cross-session state (audit history, patterns learned)

## Cross-Skill Delegation Checklist

When Phase N delegates to another skill:

1. ✓ Skill invocation uses `skill=` and `args=` named parameters
2. ✓ Target skill's `name:` field matches the `skill=` argument
3. ✓ Both source and delegated skills declare `allowed-tools` coverage:
   - Source: `Write(/tmp/claude/<namespace>/findings.*)`
   - Delegated: `Read(/tmp/claude/<namespace>/findings.*)`
4. ✓ Findings file path is deterministic (no dynamic uuids that won't match)
5. ✓ Task created in Orchestration for the delegation phase

## Error Messages

**Runtime error on first invocation:**
```
Skill tool invocation error: missing required parameter 'skill'
```

→ Check that `skill=` is present and uses the quoted skill name.

**Skill not found:**
```
Skill 'Dev10x:nonexistent' not registered
```

→ Verify the skill's `name:` field in its SKILL.md; check spelling.
