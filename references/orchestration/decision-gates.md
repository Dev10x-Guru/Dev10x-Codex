# Pattern 3: AskUserQuestion for Decisions

Replace all plain-text y/n questions with `AskUserQuestion`.
This gives the user structured widgets instead of free-text
input.

## When to use AskUserQuestion

| Scenario | Use AskUserQuestion? |
|----------|---------------------|
| A/B choice (strategy, approach) | Yes — options with descriptions |
| Approval gate (plan, PR body) | Yes — Approve / Edit / Skip |
| Error recovery (retry, skip, abort) | Yes — with context in descriptions |
| Free-text input (commit message body) | No — plain text is better |
| Confirmation of auto-detected value | Yes — Confirm / Change |

## Widget patterns

**Binary choice with preview:**
```
AskUserQuestion(questions=[{
    question: "Which commit restructuring strategy?",
    header: "Strategy",
    options: [
        {label: "Fixup (Recommended)", description: "Small targeted fixes to specific commits", preview: "git commit --fixup=<sha>\ngit rebase -i --autosquash"},
        {label: "Full restructure", description: "Reset and rebuild commit history from scratch"},
        {label: "Mass rewrite", description: "Non-interactive message rewrite from JSON config"},
    ],
    multiSelect: false
}])
```

**Multi-select for batch operations:**
```
AskUserQuestion(questions=[{
    question: "Which review comments should I address?",
    header: "Comments",
    options: [
        {label: "r101 — Use SubFactory", description: "VALID: Change LazyFunction to SubFactory in fakers.py:21"},
        {label: "r102 — Randomize values", description: "VALID: Use Faker() for all fields"},
        {label: "r103 — TYPE_CHECKING", description: "INVALID: 38+ files use this pattern"},
    ],
    multiSelect: true
}])
```

**Error recovery:**
```
AskUserQuestion(questions=[{
    question: "Tests failed. How to proceed?",
    header: "Recovery",
    options: [
        {label: "Fix and retry (Recommended)", description: "Adjust the script and re-run"},
        {label: "Skip this test case", description: "Mark as skipped, continue with remaining"},
        {label: "Abort", description: "Stop QA execution entirely"},
    ],
    multiSelect: false
}])
```
