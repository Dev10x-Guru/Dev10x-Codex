# Skill Instruction Audit

**Date:** 2026-04-13
**Scope:** Line count breakdown for all 69 skills in `skills/`
**Budget:** SKILL.md ≤ 200 lines (per `.claude/rules/INDEX.md`)

---

## Summary

| Metric | Value |
|--------|-------|
| Total skills | 69 |
| Total SKILL.md lines | 20,271 |
| Total lines (all files) | 34,993 |
| Over SKILL.md budget | 41 / 69 (59%) |
| Within budget | 28 / 69 (41%) |

---

## Critical (>500 lines over budget)

These skills need immediate attention — split content into
`references/`, `tool-calls/`, or child skills.

| Skill | SKILL.md | Over by | Total | Refs | Scripts |
|-------|----------|---------|-------|------|---------|
| work-on | 1,336 | 1,136 | 2,159 | 49 | 0 |
| skill-audit | 1,109 | 909 | 1,301 | 0 | 65 |
| git-commit | 830 | 630 | 2,151 | 891 | 0 |
| gh-pr-respond | 789 | 589 | 1,708 | 569 | 0 |
| gh-pr-monitor | 755 | 555 | 1,001 | 171 | 75 |

**Note:** `work-on`, `skill-audit`, and `fanout` have documented
budget overrides in `INDEX.md` as orchestration hubs.

---

## High (200–500 lines over budget)

| Skill | SKILL.md | Over by | Total |
|-------|----------|---------|-------|
| fanout | 657 | 457 | 708 |
| git-groom | 626 | 426 | 875 |
| qa-self | 551 | 351 | 804 |
| git-commit-split | 520 | 320 | 1,036 |
| playbook | 445 | 245 | 1,186 |
| scope | 440 | 240 | 499 |
| ticket-scope | 442 | 242 | 1,168 |
| gh-pr-create | 404 | 204 | 1,016 |

---

## Moderate (50–200 lines over budget)

| Skill | SKILL.md | Over by |
|-------|----------|---------|
| ddd | 327 | 127 |
| project-scope | 324 | 124 |
| qa-scope | 364 | 164 |
| jtbd | 361 | 161 |
| git-fixup | 361 | 161 |
| gh-pr-merge | 354 | 154 |
| gh-pr-triage | 299 | 99 |
| ticket-branch | 347 | 147 |
| ticket-create | 293 | 93 |
| upgrade-cleanup | 299 | 99 |
| git-worktree | 282 | 82 |
| fanout-parallel | 284 | 84 |
| verify-acc-dod | 272 | 72 |
| playbook-maintenance | 265 | 65 |
| review | 258 | 58 |
| skill-create | 254 | 54 |

---

## Minor (<50 lines over budget)

| Skill | SKILL.md | Over by |
|-------|----------|---------|
| adr | 242 | 42 |
| ask | 224 | 24 |
| release-notes | 215 | 15 |
| gh-pr-review | 214 | 14 |
| ticket-jtbd | 208 | 8 |
| context-audit | 206 | 6 |
| project-audit | 206 | 6 |
| slack | 206 | 6 |
| park | 204 | 4 |
| gh-context | 203 | 3 |
| onboarding | 201 | 1 |

---

## Within Budget (≤200 lines)

| Skill | SKILL.md | Total |
|-------|----------|-------|
| py-test | 87 | 87 |
| skill-index | 45 | 858 |
| gh-pr-bookmark | 72 | 72 |
| session-tasks | 80 | 80 |
| git-alias-setup | 83 | 125 |
| plan-sync | 100 | 100 |
| park-remind | 102 | 102 |
| git-promote | 102 | 273 |
| park-todo | 110 | 110 |
| request-review | 109 | 109 |
| db | 128 | 128 |
| adr-evaluate | 137 | 137 |
| py-uv | 138 | 241 |
| linear | 142 | 142 |
| audit-report | 146 | 146 |
| gh-pr-request-review | 146 | 146 |
| memory-maintenance | 152 | 216 |
| review-fix | 153 | 153 |
| db-psql | 156 | 529 |
| slack-setup | 156 | 229 |
| slack-review-request | 177 | 194 |
| git | 168 | 338 |
| park-discover | 174 | 174 |
| investigate | 176 | 315 |
| session-wrap-up | 180 | 180 |
| skill-reinforcement | 190 | 265 |
| playwright | 199 | 310 |

---

## Content Distribution

Where instruction lines live across the plugin:

| Location | Lines | % of Total |
|----------|-------|-----------|
| SKILL.md files | 20,271 | 58% |
| References | 7,016 | 20% |
| Scripts | 3,496 | 10% |
| Tool-calls | 263 | 1% |
| Other (evals, config) | 3,947 | 11% |

---

## Recommendations

1. **Extract examples and schemas** from Critical-tier SKILL.md
   files into `references/` — the SKILL.md should focus on
   orchestration steps and decision gates only.

2. **Consolidate scope/ticket-scope/project-scope** — these
   three skills share significant overlap (scope: 440, ticket-scope:
   442, project-scope: 324 lines).

3. **Split git-commit** — at 830+891 lines (SKILL.md + refs),
   this is the largest skill by total content. Consider extracting
   the gitmoji reference and commit message examples.

4. **Track this metric in CI** — add the counting script to
   the test suite as a soft gate that warns when new skills
   exceed the 200-line budget.

---

## Audit Script

The counting script lives at `bin/skill-audit-counts.py` and
can be re-run anytime:

```bash
bin/skill-audit-counts.py skills
```
