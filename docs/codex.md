# Dev10x for Codex

Dev10x for Codex packages the Dev10x MCP tools and command-safety hooks
as a Codex plugin.
It tracks upstream Dev10x (Claude) and currently corresponds to v0.105.

## What is included

| Part | What you get |
|------|--------------|
| MCP servers `cli` and `db` | ~96 tools — safe push, PR create/get/merge, CI status, issues, milestones, rebase grooming, worktrees, read-only DB queries |
| PreToolUse guardrails | Every shell command runs through the DX001–DX017 validators; file edits (`apply_patch`) run through the sensitive-file and edit rules |
| SessionStart briefing | Git alias status, scratch directory setup, and a short guide to the Dev10x MCP tools and skills |
| Approval baseline | `codex/rules/dev10x.rules` — routine read-only commands pre-approved, privilege escalation forbidden |
| Dev10x skills | The branch-to-merge pipeline as Codex skills (`$Dev10x:git-commit`, `$Dev10x:gh-pr-create`, …) |

## Using the Dev10x skills

Fifteen skills cover a ticket from branch to merge and appear in
Codex's skill list:

| Step | Skill |
|------|-------|
| Branch or worktree for a ticket | `$Dev10x:ticket-branch`, `$Dev10x:git-worktree` |
| Commit, fixup, groom | `$Dev10x:git-commit`, `$Dev10x:git-fixup`, `$Dev10x:git-groom` |
| Push and rebase safely | `$Dev10x:git` |
| Job Story for the PR | `$Dev10x:jtbd` |
| Open the PR | `$Dev10x:gh-pr-create` |
| Watch CI and reviews | `$Dev10x:gh-pr-monitor` |
| Answer review comments | `$Dev10x:gh-pr-respond`, `$Dev10x:gh-pr-triage`, `$Dev10x:gh-pr-fixup` |
| Merge | `$Dev10x:gh-pr-merge` |
| Tests | `$Dev10x:py-test` |
| PR context | `$Dev10x:gh-context` |

Type the name (for example `$Dev10x:git-commit`) or describe the
outcome and let Codex pick the skill.

Every other Dev10x skill (`$Dev10x:work-on`, `$Dev10x:park`, …) is
installed too, but runs only when you invoke it by name and is not yet
verified in Codex
([#24](https://github.com/Dev10x-Guru/Dev10x-Codex/issues/24)).

The skills are written for Claude Code.
Each one opens with a short Codex note linking
`codex/references/claude-tool-equivalents.md`, which maps the Claude
Code tools a skill names — `AskUserQuestion`, `TaskCreate`, `Agent`,
`Monitor` — to their Codex equivalents.

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

## Updates and releases

A GitHub install tracks `main`.
Codex refreshes Git marketplaces in the background when a session
starts and reinstalls the plugin when `main` has moved, so updates
arrive on their own.
To update immediately:

```bash
codex plugin marketplace upgrade Dev10x-Codex
```

Releases are tagged `v<upstream version>+codex.<N>` — for example
`v0.105.0+codex.1` is the first Codex build on top of upstream
Dev10x 0.105.0; `N` restarts at 1 when a new upstream release is
merged.
The same version appears in `.codex-plugin/plugin.json`.
To stay on one release instead of following `main`, add the
marketplace with `--ref v0.105.0+codex.1`; move to a newer release by
removing the marketplace and adding it again with the new tag.

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

## Upgrading from the old Dev10x skills

Plugin builds up to `0.105.0+codex.1` listed every skill under a
doubled name, as `$Dev10x:Dev10x:git-commit`.
That name is gone: use `$Dev10x:git-commit`.

### From the hand-copied v0.55 skills

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

## Maintaining the Codex skills

`codex/skills/` is generated from upstream `skills/` — never edit it
by hand.
After `git merge upstream/main`, regenerate both Codex artefacts:

```bash
uv run dev10x skill codex-skills
uv run dev10x permission codex-rules
```

Add `--check` to either command to fail on a stale file without
writing; the test suite runs the same check.
The verified set lives in `src/dev10x/skills/codex/catalog.py`.

## Known limitations

- Only the fifteen pipeline skills are verified in Codex; the others
  are translated mechanically and may name Claude Code tools Codex does
  not have ([#24](https://github.com/Dev10x-Guru/Dev10x-Codex/issues/24)).
- Skills that rely on Claude Code's Stop, SessionEnd or PreCompact
  hooks lose that step in Codex
  ([#12](https://github.com/Dev10x-Guru/Dev10x-Codex/issues/12)).
- The first hook run after install can prefix a block message with a
  uv line such as `Installed 2 packages`.
- Stop and PreCompact hooks, plan-sync mirroring and session audits are
  tracked in the "Codex parity: deferred from core port" milestone.
- The `mcp__cli__*` tool names assume no other MCP server is named
  `cli`; Codex renames tools when server names collide.
