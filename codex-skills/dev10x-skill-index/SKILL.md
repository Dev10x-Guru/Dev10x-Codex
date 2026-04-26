---
name: Dev10x-skill-index
description: Generate a family-grouped, adaptive-density skill index. Scans local skills and all installed plugins, groups by families.yaml, hides orchestration deps via hidden.yaml, and writes $HOME/.codex/SKILLS.md (≤45 lines, ≤300 chars/line).
---

## Instructions

Regenerate both skill index files by running the generator script:

```bash
$HOME/.codex/skills/Dev10x-skill-index/scripts/generate-all.sh --force
```

Then display the generated files to the user:

```bash
cat $HOME/.codex/SKILLS.md
cat $HOME/.codex/.skills-menu.txt
```
