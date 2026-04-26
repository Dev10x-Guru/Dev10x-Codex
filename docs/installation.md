# Installation

## Prerequisites

| Tool | Version | Used by |
|------|---------|---------|
| [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) | latest | Required — plugin host |
| [Git](https://git-scm.com/downloads) | 2.20+ | All skills (worktree support) |
| [GitHub CLI (`gh`)](https://github.com/cli/cli#installation) | latest | PR, ticket, release skills |
| [`jq`](https://jqlang.github.io/jq/download/) | 1.6+ | Tracker detection, worktree hooks, session hooks |
| [`uv`](https://docs.astral.sh/uv/getting-started/installation/) | latest | All Python scripts (PEP 723 shebang), worktree setup |
| [`yq` v4](https://github.com/mikefarah/yq#install) (mikefarah) | 4.x | `skill-index` (MOTD, skills menu) |

### Optional (skill-specific)

| Tool | Used by |
|------|---------|
| [PostgreSQL client (`psql`)](https://www.postgresql.org/download/) | `Dev10x:db-psql` — database queries |
| Linux: [`libsecret` (`secret-tool`)](https://gitlab.gnome.org/GNOME/libsecret); macOS: Keychain (built-in) | Keyring lookups for DB DSNs, Slack tokens, Linear API keys |
| [`ffmpeg`](https://ffmpeg.org/download.html) | `Dev10x:qa-self` — video evidence conversion |
| [ImageMagick](https://imagemagick.org/script/download.php) (`convert`) | `Dev10x:qa-self` — screenshot conversion |
| [Playwright](https://playwright.dev/python/docs/intro#installing-playwright) | `Dev10x:playwright` — browser QA (auto-installed via `uv`) |
| [`bump-my-version`](https://github.com/callowayproject/bump-my-version#installation) | `bin/release.sh` — plugin releases |

> **Python dependencies** are handled automatically. Scripts use
> [PEP 723](https://peps.python.org/pep-0723/) inline metadata so `uv`
> resolves packages like `slack_sdk`, `pyyaml`, and `requests` at
> runtime — no manual `pip install` needed.

## Option A: Marketplace install (recommended)

Add the marketplace source and install the plugin:

```
/plugin marketplace add Dev10x-Guru/dev10x-claude
/plugin install Dev10x@Dev10x-Guru
```

Update to the latest version:

```
/plugin update Dev10x@Dev10x-Guru
```

### Install the develop (pre-release) version

To test the latest develop branch before it's released:

```
/plugin marketplace remove Dev10x-Guru
/plugin marketplace add Dev10x-Guru/dev10x-claude#develop
/plugin install Dev10x@Dev10x-Guru
```

Switch back to stable releases:

```
/plugin marketplace remove Dev10x-Guru
/plugin marketplace add Dev10x-Guru/dev10x-claude
/plugin install Dev10x@Dev10x-Guru
```

## Option B: Manual clone

This is a private repository. You need GitHub access granted through
the [Dev10x community](https://www.skool.com/Dev10x-1892). Once you
have access:

```bash
git clone git@github.com:Dev10x-Guru/dev10x-claude.git \
  ~/.claude/plugins/Dev10x
```

> **Using HTTPS?** Replace the URL with
> `https://github.com/Dev10x-Guru/dev10x-claude.git` and
> authenticate when prompted.

Register the plugin so Claude Code loads it on every session:

```bash
claude plugin add --local ~/.claude/plugins/Dev10x
```

Update manually with:

```bash
cd ~/.claude/plugins/Dev10x && git pull
```

## Verify the installation

Start a new Claude Code session and check that skills are loaded:

```bash
claude
# Inside the session, type:
/Dev10x:skill-index
```

You should see a skills reference listing all available commands.

## Try without installing

Load the plugin for a single session:

```bash
claude --plugin-dir ~/.claude/plugins/Dev10x
```
