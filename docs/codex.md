# Dev10x for Codex

Dev10x for Codex packages the Dev10x MCP tools and command-safety hooks
as a Codex plugin.
It tracks upstream Dev10x (Claude) and currently corresponds to v0.105.

## What is included (R1)

| Part | What you get |
|------|--------------|
| MCP servers `cli` and `db` | ~96 tools — safe push, PR create/get/merge, CI status, issues, milestones, rebase grooming, worktrees, read-only DB queries |
| PreToolUse guardrails | Every shell command runs through the DX001–DX017 validators; file edits (`apply_patch`) run through the sensitive-file and edit rules |
| SessionStart briefing | Git alias status, scratch directory setup, and a short guide to the Dev10x MCP tools |
| Approval baseline | `codex/rules/dev10x.rules` — routine read-only commands pre-approved, privilege escalation forbidden |

Dev10x skills (`git-commit`, `gh-pr-create`, …) arrive in R2.
Until then, ask Codex for the outcome and it will use the MCP tools.

## Prerequisites

- Codex CLI **0.157** or newer (`codex --version`)
- [`uv`](https://docs.astral.sh/uv/) on your `PATH` — the MCP servers and hooks are uv scripts
- `git` and an authenticated `gh`

## Install

From GitHub, fetching only the folders the plugin runs from:

```bash
codex plugin marketplace add Dev10x-Guru/Dev10x-Codex --sparse .agents --sparse .codex-plugin --sparse hooks --sparse servers --sparse src --sparse skills --sparse bin --sparse references --sparse codex
codex plugin add Dev10x@Dev10x-Codex
```

Add `--ref <branch>` to try an unreleased branch.
Every folder in that list is needed at runtime: the MCP tools launch
scripts from `skills/` and `bin/`, and read `references/`.
Dropping `--sparse` entirely also works; it just fetches the tests and
docs too.

From a local checkout (for development — Codex copies the whole
directory, including `.venv` and `.git`):

```bash
codex plugin marketplace add /path/to/Dev10x-Codex
codex plugin add Dev10x@Dev10x-Codex
```

Codex copies the plugin into `~/.codex/plugins/cache/`.
After changing a local checkout, reinstall it with
`codex plugin remove Dev10x@Dev10x-Codex` followed by `codex plugin add`.

Check the MCP servers are registered:

```bash
codex mcp list
```

`cli` and `db` should both show `enabled`.

## Trust the Dev10x hooks (one-time)

Codex does not run a plugin's hooks until you trust them.
Start an interactive `codex` session after installing and approve the
Dev10x hooks when Codex asks.
There is no CLI command for this step.

Until the hooks are trusted, the MCP tools work but the shell and edit
guardrails do not run.

## Command approvals

Read-only Dev10x MCP tools run without a prompt; tools that write to
GitHub, rewrite history or change your configuration still ask.
This comes from standard MCP tool annotations and needs no setup.

Shell commands use Codex's own rules files.
Codex cannot load rules from a plugin, so install the Dev10x baseline
yourself:

```bash
ln -s /path/to/Dev10x-Codex/codex/rules/dev10x.rules ~/.codex/rules/dev10x.rules
```

Use a symlink from a local checkout so updates apply automatically, or
copy the file from the plugin cache.
Check a command against it:

```bash
codex execpolicy check --rules ~/.codex/rules/dev10x.rules git status
```

The baseline never allows `rm`, `dd` or `sudo`.
The guardrail hooks still run on every allowed command.

## Upgrading from the old Dev10x Codex skills (v0.55)

The earlier fork installed hand-copied skills into
`~/.codex/skills/dev10x-*`.
They conflict with this plugin — Codex will read them and follow
outdated instructions.
Move them out of the way:

```bash
mkdir ~/.codex/skills-backup-v0.55
mv ~/.codex/skills/dev10x-* ~/.codex/skills-backup-v0.55/
```

Keep any `dev10x-*` folder you created yourself.

## Uninstall

```bash
codex plugin remove Dev10x@Dev10x-Codex
codex plugin marketplace remove Dev10x-Codex
rm ~/.codex/rules/dev10x.rules
```

## Known limitations

- Skills are not bundled yet (R2).
- The first hook run after install can prefix a block message with a
  uv line such as `Installed 2 packages`.
- Stop and PreCompact hooks, plan-sync mirroring and session audits are
  tracked in the "Codex parity: deferred from core port" milestone.
- The `mcp__cli__*` tool names assume no other MCP server is named
  `cli`; Codex renames tools when server names collide.
