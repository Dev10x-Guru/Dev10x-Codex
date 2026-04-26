# Development

## Test locally without installing

```bash
claude --plugin-dir /path/to/Dev10x
```

## Validate plugin structure

```bash
claude plugin validate /path/to/Dev10x
```

## Run tests

```bash
uv run --extra dev pytest           # all tests with coverage
uv run --extra dev pytest -x        # stop on first failure
uv run --extra dev pytest -k "test_name"  # filter by name
```

## Lint and format

```bash
uv run ruff check .                 # lint
uv run ruff format --check .        # format check
uv run ruff format .                # auto-format
```

## Project structure

| Directory | Purpose |
|-----------|---------|
| `src/dev10x/` | Python package — CLI, validators, hooks, MCP servers |
| `tests/` | Unified test suite (mirrors `src/`) |
| `skills/` | 67 skill definitions (SKILL.md + optional scripts) |
| `agents/` | 21 plugin-distributed sub-agent specs |
| `hooks/` | 14 hook scripts across 5 lifecycle events |
| `servers/` | MCP server entry points |
| `commands/` | Slash command definitions |
| `references/` | Shared docs (git, review, JTBD guides) |
| `bin/` | Release and CI helper scripts |
| `.claude-plugin/` | Plugin manifest (`plugin.json`) |
| `.claude/rules/` | Always-loaded essentials + path-scoped rules |
| `.claude/agents/` | Internal domain-specific reviewer agents |

## MCP servers

The plugin exposes tools via MCP servers registered in
`.claude-plugin/plugin.json`:

- **`cli`** — Git operations, PR management, tracker detection,
  worktree creation, temporary files
- **`db`** — Safe read-only database queries

See `.claude/rules/mcp-tools.md` for the full tool inventory
and naming conventions.

## Adding a new skill

1. Create `skills/<name>/SKILL.md` with frontmatter
2. Use `Dev10x:<name>` as the invocation name
3. Declare external tools in `allowed-tools:` frontmatter
4. Add scripts under `skills/<name>/scripts/` if needed
5. Run `claude plugin validate` to check structure

See `.claude/rules/skill-naming.md` for naming conventions and
`.claude/rules/skill-patterns.md` for the two skill patterns
(script-based vs orchestration-based).

## Adding a new hook

Hooks live in `hooks/scripts/` and are registered in
`hooks/hooks.json`. Supported lifecycle events:

| Event | When it fires |
|-------|--------------|
| `SessionStart` | Session begins |
| `PreToolUse` | Before a tool executes |
| `PostToolUse` | After a tool executes |
| `PreCompact` | Before context compaction |
| `Stop` | Session ends |

See `.claude/rules/hook-input-patterns.md` for safe input
parsing patterns.

## Release process

```bash
bin/release.sh patch    # bump version, tag, push
bin/release.sh minor
```

Releases merge `develop` → `main` and create a GitHub release.

[Back to README](../README.md)
