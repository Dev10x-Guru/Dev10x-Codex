# Decision Gate: Restructuring Strategy

```
AskUserQuestion(questions=[{
    question: "Which restructuring strategy for N commits?",
    header: "Strategy",
    options: [
        {label: "Fixup (Recommended)",
         description: "Small targeted fixes to specific commits",
         preview: "git commit --fixup=<sha>\nGIT_SEQUENCE_EDITOR=true git rebase -i --autosquash"},
        {label: "Full restructure",
         description: "Reset all commits, rebuild from scratch",
         preview: "git reset --soft <base>\ngit reset HEAD\ngit add -p"},
        {label: "Mass rewrite",
         description: "Non-interactive message rewrite from JSON",
         preview: "mass-rewrite.py --config rewrite.json"},
        {label: "Interactive rebase",
         description: "Full manual control over commit order"}
    ],
    multiSelect: false
}])
```
