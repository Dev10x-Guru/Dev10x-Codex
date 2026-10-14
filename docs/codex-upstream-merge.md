# Merging upstream Dev10x into Dev10x for Codex

Dev10x for Codex follows upstream Dev10x (Claude) with ordinary merges:
upstream leads, this fork follows.
This runbook takes one upstream release from `git merge` to a tagged
Codex build.
Allow about an hour for a minor release; most of it is the test run.

## 1. Branch from `main`

```bash
git fetch origin
git fetch upstream --tags
git switch -c chore/GH-<issue>/merge-upstream-v<version> origin/main
```

Open a tracking issue first so the branch, commits and PR can name it.

## 2. Merge the release tag

```bash
git merge v<version>
```

Merge the release **tag**, not `upstream/develop`: a tag is what upstream
shipped and tested.

### Resolving conflicts

| Path | Resolution |
|------|------------|
| `codex/skills/**`, `codex/agents/**`, `codex/rules/dev10x.rules` | Take either side; step 3 regenerates them |
| Fork-only files (listed below) | Keep ours — upstream never touches them |
| Upstream files the fork patched (listed below) | Take upstream's change, then re-apply the fork's change on top |
| Everything else | Take upstream |

Fork-only files: `.codex-plugin/`, `.agents/plugins/`, `.gitattributes`,
`AGENTS.md`, `codex/references/`, `docs/codex*.md`,
`hooks/codex-hooks.json`, `hooks/scripts/session-guidance-codex.md`,
`src/dev10x/harness.py`, `src/dev10x/hooks/apply_patch_payload.py`,
`src/dev10x/hooks/session_codex.py`, `src/dev10x/mcp/tool_annotations.py`,
`src/dev10x/skills/codex/`, `src/dev10x/core/skills/permission/codex_rules.py`,
`src/dev10x/core/validators/codex_messages.py`, and their tests.

### Upstream module moves (ADR-0034)

Upstream moves modules into plugin namespaces (`dev10x.core`,
`dev10x.coding`, `dev10x.tasks`, …) and keeps the old dotted path as an
alias.
A fork-only module at an old path keeps working only when that old
package uses `alias_submodules` (it falls through to the old folder for a
name the new package lacks, as `dev10x.hooks` does).
A package switched to `alias_package` hides the old folder: move the
fork module next to its upstream siblings with `git mv` (as
`codex_rules.py` and `codex_messages.py` moved in `v0.108.0+codex.1`) —
old imports keep resolving through the alias.
A `ModuleNotFoundError` from a `dev10x skill codex-*` or
`dev10x permission codex-rules` run is the symptom.
Upstream's planned Stage B removes the aliases; every fork module at an
old path moves then.

### Upstream renames the plugin prefix

Upstream writes skills and MCP tools as `dev10x:<skill>` and
`mcp__plugin_dev10x_<server>__` since v0.106 (GH-1499); the Codex plugin
keeps the name `Dev10x`.
`to_codex_casing()` in `src/dev10x/skills/codex/catalog.py` maps both
spellings onto the Codex names before the generators and block messages
match them.
After regenerating, `rg 'Skill\(.?dev10x:|mcp__plugin_dev10x_' codex/`
must list only literal Claude permission patterns such as
`Skill(dev10x:*)`.

Upstream files the fork patched (as of `v0.108.0+codex.1`; refresh with
`git diff --name-only --diff-filter=M v<previous> HEAD`):

- `hooks/scripts/session-start.py`, `src/dev10x/core/hooks/session_place.py`,
  `src/dev10x/core/hooks/hook_transport.py`,
  `src/dev10x/core/hooks/edit_validator.py` — Codex payloads and the Codex
  SessionStart briefing
- `src/dev10x/mcp/server_cli.py`, `src/dev10x/db/mcp/server_db.py` — MCP
  tool annotations, applied once every namespace has registered
- `src/dev10x/core/validators/skill_redirect.py` — Codex block messages
- `src/dev10x/commands/skill.py`, `src/dev10x/commands/permission.py` — the
  `codex-skills`, `codex-agents` and `codex-rules` commands
- `src/dev10x/core/skills/permission/baseline-permissions.yaml`,
  `skills/upgrade-cleanup/projects.yaml` — catalog entries for those commands
- `src/dev10x/core/namespaces.yaml` — the `dev10x.harness: core` entry
- `tests/fixtures/skill_reference_inventory.json` — upstream's counts plus
  the `$Dev10x:<skill>` references in `docs/codex*.md`; take upstream's file,
  run `tests/core/test_skill_references.py`, and paste the counts its failure
  prints
- `tests/hooks/test_hook_transport.py`

## 3. Regenerate the Codex artifacts

```bash
uv run dev10x skill codex-skills
uv run dev10x skill codex-agents
uv run dev10x permission codex-rules
```

Read the warnings each command prints:

- **A new upstream skill** joins the Codex catalog automatically.
  Read its `SKILL.md` against `codex/references/claude-tool-equivalents.md`.
  If it depends on something Codex lacks, add it to `DEFERRED_SKILLS` in
  `src/dev10x/skills/codex/catalog.py` with the issue that owns the gap; if
  it works with one thing the user must know, add a `SKILL_CAVEATS` line.
  Regenerate after either change.
- **A new Claude Code tool** named in skills (a new `Agent` flag, a new
  built-in) needs a line in the equivalents reference.
- **A new upstream agent** becomes a Codex role on its own; add it to
  `DEFERRED_AGENTS` in `src/dev10x/skills/codex/catalog.py` only when it
  belongs to deferred work.

## 4. Extend the approval baseline

`codex-rules` translates upstream's command catalog
(`src/dev10x/core/skills/permission/baseline-permissions.yaml`).
Check its "skipped" list for a new read-only command that Codex users will
run often.
A rule that cannot be expressed as a Codex prefix rule stays skipped —
never widen it to fit.

## 5. Run the tests

```bash
uv run --extra dev pytest
uv run --extra dev pre-commit run --all-files
```

Upstream's CI runs on `develop` only, so this fork's PRs to `main` get no
test CI (#33): the local run is the evidence.
The suite fails when a generated tree is stale, when a new MCP tool has no
Codex annotation (`tests/mcp/test_tool_annotations.py`), or when a
cataloged skill or role is missing.

### Which tests apply to Codex

Keep every upstream test.
Tests for Claude-only hooks (Stop, PreCompact, the task-plan mirror,
permission prompts) and for `.claude/settings*.json` seeding still cover
code this fork ships unchanged, and deleting upstream test files would
turn every later upstream edit to them into a merge conflict.
Codex behavior is covered by the fork's own tests: `tests/skills/codex/`,
`tests/skills/permission/test_codex_rules.py`,
`tests/hooks/test_session_start_codex.py`,
`tests/hooks/test_edit_validator_apply_patch.py`,
`tests/hooks/test_apply_patch_payload.py`,
`tests/validators/test_codex_messages.py`, `tests/test_harness.py` and
`tests/mcp/test_tool_annotations.py`.
On macOS the daemon tests fail with `AF_UNIX path too long`; they fail
identically upstream.

## 6. Smoke-test in Codex

Install the branch into a throwaway `CODEX_HOME` and confirm the catalog:

```bash
export CODEX_HOME="$(mktemp -d)"
codex plugin marketplace add /path/to/Dev10x-Codex
codex plugin add Dev10x@Dev10x-Codex
codex debug prompt-input
```

The skill list must show every non-deferred skill once, as `Dev10x:<name>`
(never `Dev10x:Dev10x:<name>`).
For the agents, link `codex/agents` into `$CODEX_HOME/agents/dev10x`, copy
or link your `~/.codex/auth.json`, and ask `codex exec` which agent roles
it can spawn.

## 7. Version, PR and release

1. Set `version` in `.codex-plugin/plugin.json` to `<version>+codex.1`
   (the counter restarts at 1 for each upstream release).
2. Open the PR into `main` with `$Dev10x:gh-pr-create`; the body lists the
   upstream release notes link, the conflicts resolved, and any skill or
   agent that changed status.
3. After merging, tag `v<version>+codex.1` on `main`.
