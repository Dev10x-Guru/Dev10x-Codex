# Dev10x for Codex — Session Guidance

Dev10x adds two MCP servers (`cli`, `db`) and PreToolUse guardrail
hooks to this session. Prefer the MCP tools over raw `git` / `gh`:
they return structured results and enforce the same safety checks
the hooks would otherwise block you on.

## Prefer these MCP tools

| Task | MCP tool |
|------|----------|
| Push a branch (protected-branch + force-push checks) | `mcp__cli__push_safe` |
| Non-interactive rebase / autosquash | `mcp__cli__rebase_groom` |
| Open a pull request (Job Story body, `Fixes:` trailer) | `mcp__cli__create_pr` |
| Read a pull request | `mcp__cli__pr_get` |
| Edit a pull request / mark ready | `mcp__cli__update_pr`, `mcp__cli__pr_ready` |
| Wait on CI and read the verdict | `mcp__cli__ci_check_status` |
| Merge a pull request | `mcp__cli__merge_pr` |
| Read / create / edit / close issues | `mcp__cli__issue_get`, `mcp__cli__issue_create`, `mcp__cli__issue_edit`, `mcp__cli__issue_close` |
| Create a temp file (commit messages, PR bodies) | `mcp__cli__mktmp` |
| Configure the git base-branch aliases | `mcp__cli__setup_aliases` |
| Read-only SQL | `mcp__db__query` |

A write through an MCP tool is a request, not a receipt: re-read the
field you changed (for example `pr_get` after `update_pr`) before
relying on it.

## Guardrail hooks

A Dev10x PreToolUse hook validates every shell command before it
runs. When it blocks one, the message names the MCP tool to use or,
where no Codex equivalent exists yet, the manual guardrails to apply.
Follow it — do not retry the same command in a different spelling.

Commonly blocked shapes:

- Chaining (`cmd1 && cmd2`), `$(...)` substitution, heredocs and
  `python -c` — run separate commands and write files instead.
- `git push --force` / `-f` and pushes to protected branches — use
  `mcp__cli__push_safe`; after a rebase, `--force-with-lease` only.
- `git commit -m` — write the message to a file from
  `mcp__cli__mktmp` (namespace `git`) and run `git commit -F <path>`.
  Use a gitmoji prefix, the ticket ID from the branch, and keep lines
  under 72 characters.
- `gh pr view`, `gh pr create`, `gh pr merge`, `gh issue ...` — use
  the matching MCP tool above.

Never prefix a command with `DEV10X_SKIP_CMD_VALIDATION` to get past
a block. Read-only `gh api` calls stay available if the MCP server is
disconnected; ask the user to restart the session for writes.
