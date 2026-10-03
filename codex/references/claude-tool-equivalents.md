# Claude Code tools in Codex

Dev10x skills are written for Claude Code and translated for Codex by
`dev10x skill codex-skills`.
The translation rewrites names it can map exactly — MCP tools become
`mcp__cli__<tool>`, skill calls become `$Dev10x:<skill>`, the plugin
root becomes `<plugin-root>`.
Tool *behaviour* cannot be rewritten mechanically, so when a skill
names a Claude Code tool, use the Codex equivalent below.

## Asking the user — `AskUserQuestion`

Use `request_user_input` when it is listed in your tools for this turn.
Ask the same question with the same options, and keep the option
marked `(Recommended)` first.

- `multiSelect: true` — say in the question that several options may
  be chosen.
- `preview` fields — show the preview text in your message before
  asking.
- Several questions in one call — ask them together if the tool takes
  a list, otherwise one after another.

When `request_user_input` is not available, or returns no answer, ask
the question in plain text with numbered options and **end your turn**.
A gate marked `REQUIRED` must never be answered on the user's behalf.
Gates that the skill first routes through `mcp__cli__resolve_gate`
still follow its `effect`: `auto-advance` and `skip` need no question.

## Task lists — `TaskCreate`, `TaskUpdate`, `TaskList`, `TaskGet`, `TodoWrite`

Use `update_plan` when it is available: one plan step per task, with
`pending`, `in_progress` and `completed` statuses.

Without it, keep the plan as a written checklist in your replies,
restate it as items complete, and close with an explicit
**Verify AC** section (PR links, what changed, CI status, open review
comments).
Never declare the work complete on your own — the user confirms it.

## Running another skill — `Skill(...)`

`$Dev10x:<skill>` means: open that skill's `SKILL.md` — a sibling
folder of this skill, `../<skill>/SKILL.md` — and follow it.
`(args: …)` after the name are the arguments the skill expects.
`$Dev10x:py-test` stands in for the generic `test` skill.

## Subagents — `Agent(...)`, `subagent_type`, `run_in_background`, `SendMessage`

Use `spawn_agent` and collect the result with `wait_agent`.

- A named Dev10x agent — `subagent_type="Dev10x:code-reviewer"`, or
  a bare `code-reviewer`, `reviewer-*`, `architect-*`,
  `spec-reviewer`, `adr-reviewer` — is the Codex agent role of the
  same name with the `Dev10x:` prefix, once `codex/agents/` is
  installed (see the Dev10x-Codex `docs/codex.md`).
  If that role is not offered, spawn a default agent and give it the
  `developer_instructions` from `<plugin-root>/codex/agents/<name>.toml`.
- `general-purpose`, `Explore` and any other unnamed type mean the
  default Codex agent with the prompt as written.
- Model hints (`haiku`, `sonnet`, `opus`) do not apply: each Dev10x
  role already sets its own reasoning effort.
- `isolation="worktree"`, `mode` and `run_in_background` have no
  Codex flag; agents share your working directory, so give parallel
  agents disjoint files.
- The `SendMessage(to="main")` delivery protocol is not needed, even
  where a prompt template asks for it: the result arrives through
  `wait_agent`.

When spawning is not available, do the work yourself, in order.

## Reading the task list back

`update_plan` is write-only, and Codex has no hook that mirrors the
plan into Dev10x plan-sync (Dev10x-Codex#13).
Where a skill reads the task list (`TaskList`, `TaskGet`, a resumed
plan), use the checklist you keep in your own replies;
`mcp__cli__plan_sync_json_summary` will show no tasks.

## Waiting and polling — `Monitor`, `ScheduleWakeup`, `CronCreate`

There is no equivalent.
To wait for CI, call `mcp__cli__ci_check_status` with `wait=true`
(and `wait_for` for review bots).
Never write a `while … sleep` shell loop: the Dev10x guardrails block
it.

## Worktrees — `EnterWorktree`, `ExitWorktree`

Codex cannot switch a running session into another directory.
Create the worktree with `mcp__cli__create_worktree`, then ask the user
to start a new Codex session inside it.

## Files and search — `Read`, `Edit`, `Write`, `Grep`, `Glob`, `WebFetch`

Read files with the shell (`sed -n`, `cat`, `rg`) and change them with
`apply_patch`.
The Dev10x guardrails check `apply_patch` the same way they check
Claude Code edits.

- `Grep` → `rg <pattern>`; `Glob` → `rg --files -g '<glob>'`.
- `WebFetch` / `WebSearch` → the `web_search` tool when Codex runs
  with `--search`; otherwise ask the user for the page.
- `ToolSearch` is not needed: Codex lists every available tool.

## Shell commands

Run one simple command per shell call.
The Dev10x guardrails deny `for` and `while` loops, `$(…)`
substitution, heredocs, `&&` / `;` chains and environment-variable
prefixes, as they do in Claude Code.
Where a skill shows such a shape, run the commands one at a time and
write multi-line content with `apply_patch` instead.

Raw `gh` commands that Dev10x routes to its MCP tools:

| Command | Use |
|---------|-----|
| `gh pr view` | `mcp__cli__pr_get` |
| `gh pr edit` | `mcp__cli__update_pr` |
| `gh pr ready` | `mcp__cli__pr_ready` |
| `gh pr create` | `$Dev10x:gh-pr-create` |
| `gh pr merge` | `$Dev10x:gh-pr-merge` |
| `gh issue view` / `create` / `edit` / `close` | `mcp__cli__issue_get` / `issue_create` / `issue_edit` / `issue_close` |

`/tmp/Dev10x/bin/mktmp.sh <ns> <prefix> <ext>` is
`mcp__cli__mktmp(namespace, prefix, ext)`.

## Skill scripts and the `dev10x` command

Scripts under `<plugin-root>/skills/<skill>/scripts/` run in Codex,
but Codex asks for approval each time (Dev10x-Codex#32).
When `dev10x` is not on your `PATH`, run
`uv run --project <plugin-root> dev10x <command>`.

## Other MCP servers — Linear, Jira, Slack, Sentry

Dev10x renames only its own tools.
Names such as `mcp__claude_ai_Linear__save_issue`,
`mcp__plugin_linear_linear__…` or `mcp__sentry__…` are the user's
Claude Code servers: in Codex the same server appears as
`mcp__<server>__<tool>`, under whatever name the user gave it in
`~/.codex/config.toml`.
Find the matching tool in your tool list.
When no such server is configured, say which step you are skipping
and why, or ask the user to paste the content, then carry on.

## Paths written in skill text

Skills were written in the upstream layout, so a path in prose (not
a link) is relative to `<plugin-root>/skills/<skill>/`:
`../../references/X` means `<plugin-root>/references/X`.
Paths under `~/.claude/` (memory, `SKILLS.md`, `skills/`, `tools/`)
and repository `.claude/rules/` files belong to Claude Code and may
not exist.

## Slash commands and sessions

- `/Dev10x:<skill>` means `$Dev10x:<skill>`.
- `/clear` or `/compact` → start a new Codex session.
- `claude --resume <id>` → `codex resume` (or `codex resume --last`).

## Permissions — `allowed-tools`, allow rules, `settings.local.json`

Codex ignores a skill's `allowed-tools`.
Read-only Dev10x MCP tools run without a prompt; writes ask.
Shell commands follow `~/.codex/rules/dev10x.rules`
(see the Dev10x-Codex `docs/codex.md`).
Advice about Claude Code allow rules, `.claude/settings*.json` or
`/permissions` does not apply in Codex.

## Claude Code files and hooks

- `CLAUDE.md` → `AGENTS.md`.
- `.claude/` project settings → `~/.codex/config.toml`.
- Dev10x configuration under `~/.config/Dev10x/` is shared by both and
  works unchanged.
- Dev10x PreToolUse guardrails and the SessionStart briefing run in
  Codex.
  Stop, SessionEnd and PreCompact hooks do not yet (Dev10x-Codex#12),
  so a skill step that relies on them must be done by hand.
