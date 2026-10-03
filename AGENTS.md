# Dev10x for Codex — contributor guide

This repository packages Dev10x — MCP tools, command-safety hooks,
skills and agents for the branch-to-merge workflow — as a Codex plugin.
It is a fork of upstream Dev10x for Claude Code
(`Dev10x-Guru/Dev10x-Claude`, remote `upstream`) and follows it by
ordinary merges.
User documentation: `docs/codex.md`.

Upstream's conventions live in `CLAUDE.md` and `.claude/rules/*.md`;
they apply here too.
They are long, so read the file for the area you are changing instead of
all of them up front.

## Where things live

| Path | What it is | Edit? |
|------|------------|-------|
| `.codex-plugin/plugin.json` | Codex plugin manifest | Fork-only |
| `hooks/codex-hooks.json`, `hooks/scripts/` | Hook registration and entry points | Fork-only / shared |
| `codex/skills/` | Codex skills generated from `skills/` | **Generated — never edit** |
| `codex/agents/` | Codex agent roles generated from `agents/` | **Generated — never edit** |
| `codex/rules/dev10x.rules` | Approval baseline generated from the command catalog | **Generated — never edit** |
| `codex/references/claude-tool-equivalents.md` | Claude Code tool → Codex mapping every skill links to | Fork-only |
| `src/dev10x/skills/codex/` | Skill and agent generators, skill status catalog | Fork-only |
| `src/dev10x/` (rest), `skills/`, `agents/`, `tests/` | Upstream code, skills, agents and tests | Shared |

A change to a skill or agent belongs upstream in `skills/` or `agents/`,
followed by regeneration — not in the generated copy.

## Commands

```bash
uv run --extra dev pytest                      # full suite with coverage
uv run --extra dev pre-commit run --all-files  # ruff, mypy, shellcheck, pins
uv run dev10x skill codex-skills               # regenerate codex/skills/
uv run dev10x skill codex-agents               # regenerate codex/agents/
uv run dev10x permission codex-rules           # regenerate dev10x.rules
```

Add `--check` to a generator to test for drift without writing.
The test suite fails when any generated tree is stale, so regenerate in
the same commit as the upstream change.
Never commit while the suite runs: `tests/conftest.py` resets `HEAD` if
it moves during a test run.

## Rules that bite

- **Fork changes stay in fork-owned paths.** Every edit to a shared file
  is a future merge conflict; prefer a new module the shared code calls
  into, and list any patched shared file in
  `docs/codex-upstream-merge.md`.
- **Skill status** (run end to end, deferred, Codex caveat) lives in
  `src/dev10x/skills/codex/catalog.py`; keep it free of heavy imports, it
  loads on the hook path.
- **New MCP tool:** register it, add it to the table in
  `.claude/rules/mcp-tools.md`, classify it in
  `src/dev10x/mcp/tool_annotations.py` (Codex approval prompts) and in
  `base_permissions`.
- **Subprocesses and CWD:** go through `dev10x.subprocess_utils` and a
  fresh `GitContext()` (`.claude/rules/cwd-discipline.md`).
- **Domain functions** return `Result[T]` and log; only a script's
  `main()` prints and exits (`.claude/rules/script-domain-boundaries.md`).
- **Dependencies** in `pyproject.toml` and uv-script headers need an
  upper bound.
- **Python style:** ruff, line length 99.
  Markdown: one sentence per line.

## Git and pull requests

- PRs target `main` (upstream works on `develop`; this fork does not).
- Branches: `<type>/GH-<issue>/<slug>`, for example
  `feat/GH-24/codex-core-complete`.
- Commits: `<gitmoji> GH-<issue> <outcome>`, at most 72 characters per
  line, a problem paragraph, a `Solution:` list and `Fixes: #<issue>`.
  Titles say what the change makes possible, not what was added.
- PR body: a Job Story first
  (`**When** … **<role> wants** … **so <beneficiary> can** …`), then the
  details, ending with `Fixes: <issue URL>`.
- Upstream CI runs on `develop` only, so a PR to `main` gets review bots
  but no test run: run the suite locally and say so in the PR.
- Use the Dev10x skills for this work: `$Dev10x:git-commit`,
  `$Dev10x:gh-pr-create`, `$Dev10x:gh-pr-monitor`, `$Dev10x:gh-pr-merge`.

## Merging upstream

Follow `docs/codex-upstream-merge.md`: merge the release tag, keep
fork-only files, re-apply fork patches, regenerate, triage new skills
and agents, run the tests, smoke-test in a throwaway `CODEX_HOME`, then
bump `.codex-plugin/plugin.json` to `<version>+codex.1`.
