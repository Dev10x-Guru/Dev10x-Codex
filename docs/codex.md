# Codex Skills (Published Pack)

This repository includes a Codex-native pack in `codex-skills/`.
Each skill is installable into `~/.codex/skills/<skill-name>`.

## What was ported

- All 67 Dev10x skills were ported to Codex format under `codex-skills/`
- `SKILL.md` frontmatter normalized to Codex-compatible fields:
  - `name`
  - `description`
- Claude-specific frontmatter fields were removed from the Codex pack

## Install all Codex skills (local clone)

```bash
bin/install-codex-skills.sh
```

## Validate Codex pack before publishing

```bash
bin/validate-codex-skills.sh
```

## Install from GitHub with Codex skill installer

Install one or more skills directly from this repository:

```bash
scripts/install-skill-from-github.py \
  --repo Dev10x-Guru/dev10x-claude \
  --path codex-skills/Dev10x-git-commit \
  --path codex-skills/Dev10x-gh-pr-create
```

To install all skills from GitHub, pass every path under `codex-skills/`.
You can list them with:

```bash
find codex-skills -mindepth 1 -maxdepth 1 -type d | sort
```
