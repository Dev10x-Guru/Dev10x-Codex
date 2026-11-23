---
name: diagram-bpmn
description: 'Use when someone asks to model a business process, workflow, approval chain, or hand-off between roles as BPMN — a file that opens in Camunda Modeler or bpmn.io, plus a rendered image for a doc or PR. TRIGGER when: drawing who does what, in which order, with decisions and loops, across roles or lanes. DO NOT TRIGGER when: drawing calls between services over time (use Dev10x:diagram-sequence) or system structure (use Dev10x:diagram-c4).'
metadata:
  upstream: plugins/scoping/skills/diagram-bpmn/SKILL.md
---

> **Running in Codex.** Generated from `plugins/scoping/skills/diagram-bpmn/` by `dev10x skill codex-skills` — edit the upstream skill, not this file.
> Where this skill names a Claude Code tool (`AskUserQuestion`, `TaskCreate`, `Agent`, `Monitor`, …), use the Codex equivalent in [../../references/claude-tool-equivalents.md](../../references/claude-tool-equivalents.md).
> `<plugin-root>` is the Dev10x plugin folder (the one holding `.codex-plugin/`); this skill's `scripts/` and `templates/` stay in `<plugin-root>/plugins/scoping/skills/diagram-bpmn/`.
> Reviewed for Codex but not yet run end to end in it: confirm before any step that writes to GitHub or rewrites history.

# Dev10x:diagram-bpmn

**Announce:** "Using Dev10x:diagram-bpmn to model <process name>."

## Orchestration

This skill follows `references/task-orchestration.md` patterns.

**REQUIRED: Create a task at invocation.** Execute at startup:

1. `TaskCreate(subject="Model BPMN process", activeForm="Modeling BPMN process")`

Mark completed when done: `TaskUpdate(taskId, status="completed")`

## Core rule: write the meaning, never the coordinates

You write the semantic BPMN — pool, lanes, tasks, gateways, flows.
`render.sh` writes every coordinate: shapes, edges, pool and lane
bands. Hand-placed `bpmndi:` coordinates are the failure this skill
exists to remove: they produce overlapping labels and crossing edges
nobody can fix without a modeler.

## Workflow

1. **List the roles and the steps.** Each role is a lane. For each
   step note who does it, whether a person or a system does it
   (`userTask` vs `serviceTask`), and every decision as a question.
   Ask only when the request names no roles and the process plainly
   has more than one actor.
2. **Write the `.bpmn`** beside the document it serves
   (`docs/processes/<name>.bpmn`), following
   [`references/bpmn-xml.md`](references/bpmn-xml.md):
   - one pool per file; every flow node in exactly one lane
   - `sequenceFlow`s only — no `incoming`/`outgoing` on nodes
   - typed tasks, gateways named as questions, branches as answers
   - a real `targetNamespace` and readable ids
3. **Lay out, validate, render:**

   ```bash
   <plugin-root>/plugins/scoping/skills/diagram-bpmn/scripts/render.sh <file.bpmn> [--format png|svg]
   ```

   The first run installs a pinned toolchain into the user cache. The
   script rejects unknown elements, dangling references, nodes outside
   every lane, and multi-pool files by name, then writes the layout
   into the `.bpmn` and renders the image. A file that already has a
   layout — say, tuned by hand in Camunda Modeler — keeps it unless
   you pass `--relayout`.
4. **Look at the image.** `Read` the PNG. Check that every node sits in
   its role's lane, each gateway's outgoing flows are labeled, and
   loops point back to the step that is actually repeated.
5. **Deliver** the `.bpmn` (the editable source) and the image. Say
   which roles or steps you inferred rather than read from the
   request.

Toolchain and troubleshooting:
[`references/diagrams/rendering.md`](../../../plugins/scoping/references/diagrams/rendering.md).

## Common Mistakes

| Mistake | Consequence |
|---------|-------------|
| Writing `bpmndi:` coordinates | Overlapping labels and crossing edges; the layout step keeps them unless `--relayout` |
| Plain `task` everywhere | Reader cannot tell what a person does from what a system does |
| Unnamed gateway branches | The diagram shows a fork but not the decision behind it |
| Two parties' pools in one file | Refused; model each party's process in its own file |
| A role's step left out of every lane | Refused by name — the picture would otherwise put it nowhere |
