# Skill Implementation Patterns

The codebase supports two distinct skill patterns. Review expectations differ
based on which pattern a skill uses.

## Pattern 1: Script-Based Skills

Directory contains `scripts/` with executable implementations.

**Characteristics**:
- SKILL.md provides overview and usage
- Actual implementation in `scripts/` (shell, Python, etc.)
- Examples: `gh-pr-create`, `git-commit`, `git-groom`

**Reviewer expectations** (from `reviewer-skill.md`):
- Items 4, 5, 6: Script existence, permissions, error handling
- Item 8: `allowed-tools` must declare `Bash(...)` entries
- Item 32: Output format validation

**Flag as CRITICAL if missing**: Actual implementation scripts

## Pattern 2: Orchestration-Based Skills

Directory contains only SKILL.md; Claude interprets and executes the workflow.

**Characteristics**:
- SKILL.md documents a multi-step workflow
- Claude reads and executes each step
- External tools called via `allowed-tools` declarations
- Examples: `gh-pr-request-review`, `park`

**Reviewer expectations** (from `reviewer-skill.md`):
- Items 4, 5: Do NOT apply (no scripts expected)
- Item 8: **Critical** — all external tool calls must be in `allowed-tools`
- Items 15c, 19: Config schema and decision gate enforcement
- Item 14a: Orchestration list formatting in SKILL.md

**Flag as CRITICAL if missing**: `allowed-tools` declarations for external
tools or decision gates; will cause per-invocation approval prompts.

## Pattern 3: Skills with Reference Files

Some orchestration-based skills include documentation or workflow files
in a `references/` subdirectory.

**Characteristics**:
- Playbook files (`playbook.yaml`) define multi-mode workflows separately
- API documentation files (`.md`) provide implementation details for steps
- Loaded and referenced by the skill itself and SKILL.md
- Users may customize via 3-tier resolution
  (see `references/config-resolution.md`)

**Reviewer expectations**:
- Verify YAML syntax and structure for playbook files
- Cross-check playbook play names against SKILL.md mode detection
- Confirm all referenced doc sections exist and match SKILL.md description
- See `.claude/rules/playbook-pattern.md` for full pattern guidance

**Flag as CRITICAL if missing**: Referenced playbook or doc files that
SKILL.md explicitly names; will cause runtime errors during execution.

## Pattern Detection

Determine which pattern applies:
1. Check if skill directory contains `scripts/` subdirectory
   - Yes → Script-based; apply Items 4, 5, 6, 32
   - No → Continue to step 2
2. Check if SKILL.md references local paths like `${CLAUDE_PLUGIN_ROOT}/skills/...`
   - Yes → Script-based; likely missing scripts directory
   - No → Proceed to step 3
3. Check if SKILL.md references `references/playbook.yaml` or `references/*.md`
   - Yes → Pattern 3 (reference files); see `.claude/rules/playbook-pattern.md`
   - No → Continue to step 4
4. Check if SKILL.md references external binaries or `~/.claude/tools/` only
   - Yes + no `scripts/` + no `references/` → Orchestration-based (Pattern 2)
   - No → Ambiguous; flag as INFO for author clarification

## Permission Friction Prevention

Skills invoking external tools (scripts, MCP servers) must declare them in
`allowed-tools:` front matter. Missing declarations trigger per-invocation
approval prompts on **every run**, breaking skill usability. See
`mcp-tools.md` "Common Mistakes" section and `reviewer-skill.md` item 8 for
prevention patterns. CLAUDE.md § External Tool Declarations has detailed
requirements.
