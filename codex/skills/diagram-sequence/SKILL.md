---
name: diagram-sequence
description: 'Use when someone asks for a sequence diagram, a call flow, a request/response timeline, or "who calls whom" between services, agents, or APIs — for a PR description, issue, ADR, or design doc. TRIGGER when: drawing interactions between participants over time. DO NOT TRIGGER when: drawing system structure (use Dev10x:diagram-c4) or a business process with lanes and gateways (use Dev10x:diagram-bpmn).'
metadata:
  upstream: plugins/scoping/skills/diagram-sequence/SKILL.md
---

> **Running in Codex.** Generated from `plugins/scoping/skills/diagram-sequence/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/plugins/scoping/skills/diagram-sequence/`.
> Reviewed for Codex but not yet run end to end in it: confirm before any step that writes to GitHub or rewrites history.

# Dev10x:diagram-sequence

**Announce:** "Using Dev10x:diagram-sequence to draw <flow name>."

## Orchestration

This skill follows `references/task-orchestration.md` patterns.

**REQUIRED: Create a task at invocation.** Execute at startup:

1. `TaskCreate(subject="Draw sequence diagram", activeForm="Drawing sequence diagram")`

Mark completed when done: `TaskUpdate(taskId, status="completed")`

## Pick the notation from where the diagram lands

| Destination | Notation | Why |
|-------------|----------|-----|
| PR body, issue, comment, any GitHub-rendered `.md` | **Mermaid** (default) | GitHub renders a ` ```mermaid ` block inline — no image to host or keep in sync |
| ADR, design doc, slide, anything needing a PNG/SVG file | **PlantUML** | Finer layout control (`box`, activation bars, `autonumber` formats); matches `Dev10x:adr` |
| Both ("for the PR, and a PNG for the doc") | Mermaid source + rendered PNG from the same `.mmd` | One source of truth; never maintain two notations of one flow |

Mermaid is the default. Choose PlantUML only when the destination
needs a file Mermaid cannot produce well, or the repo already keeps
`.puml` sources next to the document.

## Workflow

1. **Name the participants first.** List every actor/service the flow
   touches, in left-to-right order of first appearance. Use the names
   the codebase uses (`MCP server`, not `Backend`). Add a participant
   the request did not name only when a step cannot be drawn without
   it, and say so in your reply.
2. **Write the source** next to the document it serves
   (`docs/<area>/<flow>.mmd` or `docs/adr/diagrams/NNNN/<flow>.puml`).
   Syntax: [`references/mermaid.md`](references/mermaid.md) or
   [`references/plantuml.md`](references/plantuml.md).
   - Branches → `alt`/`else`; optional step → `opt`; retry → `loop`.
   - Return arrows are dashed (`-->>` Mermaid, `-->` PlantUML).
   - Payload labels use the real field names from the code.
3. **Render and validate** — always, even for inline Mermaid:

   ```bash
   <plugin-root>/plugins/scoping/skills/diagram-sequence/scripts/render.sh <source> [--format png|svg]
   ```

   It exits non-zero with the offending line on any error: PlantUML is
   syntax-checked before rendering, and Mermaid parse errors come from
   mermaid-cli with a line and caret. Fix the source and re-run; never
   hand back a diagram whose last render failed. PlantUML runs
   sandboxed — see the security profile in the rendering reference
   below.
4. **Look at the image.** `Read` the PNG the script printed. Check
   that every message has a sender and receiver, `alt` frames enclose
   the steps you meant, and no label is clipped. A clean exit is not
   proof — PlantUML silently closes an unterminated `alt` and drops
   the frame.
5. **Deliver.** For GitHub destinations paste the ` ```mermaid ` block;
   for files link the rendered image and commit the source beside it.

Toolchain details and troubleshooting (jar lookup, Chrome for
puppeteer, offline use): [`references/diagrams/rendering.md`](../../../plugins/scoping/references/diagrams/rendering.md).

## Common Mistakes

| Mistake | Consequence |
|---------|-------------|
| PlantUML for a PR description | Reader sees a raw code block or a stale pasted image instead of a rendered diagram |
| Hand-back without rendering | A typo ships as a broken block GitHub shows as an error box |
| Trusting a clean exit | Missing `end`/`alt` frames render silently wrong — only reading the image catches it |
| Invented participant names | Diagram disagrees with the code it documents and misleads reviewers |
| Two notations for one flow | They drift; one of them is wrong within a release |
