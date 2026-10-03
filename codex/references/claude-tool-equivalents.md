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

## Files — `Read`, `Edit`, `Write`

Read files with the shell (`sed -n`, `cat`, `rg`) and change them with
`apply_patch`.
The Dev10x guardrails check `apply_patch` the same way they check
Claude Code edits.

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
