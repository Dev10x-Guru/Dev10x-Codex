# PR Creation Workflow

This document describes the PR creation workflow, based on the `gpr-develop` fish function.

## Overview

The workflow automatically:
1. Extracts the PR title from the commit message
2. Extracts the issue number from the branch name
3. Pushes the branch to origin
4. Creates a draft PR with proper title and body
5. Posts a checklist comment (if template exists)
6. Opens the PR in browser

## Fish Function Reference

Original fish function for reference:

```fish
function gpr-develop
    set MESSAGE (git cherry origin/develop -v | head -1 | cut -c 44-)
    set ISSUE (git branch --show | rev | cut -d"/" -f2 | rev)
    set BRANCH_NAME (git symbolic-ref --short HEAD)

    if string match --regex '^[TD|PAY].*' $ISSUE
        if string match --regex "(^$ISSUE .*)|(^. $ISSUE .*)" $MESSAGE
            set TITLE "$MESSAGE"
        else
            set TITLE "$ISSUE $MESSAGE"
        end
        set BODY "Related to https://linear.app/example/issue/$ISSUE"
        echo "Linear issue: $ISSUE"
    else
        set TITLE "$MESSAGE"
        set BODY ""
        echo "No Linear issue found in the branch name"
    end

    echo "Title: $TITLE"
    echo "For: $BRANCH_NAME -> develop"

    git push --set-upstream origin $BRANCH_NAME
    gh pr create --draft --title "$TITLE" --fill
    gh pr comment --body "$(sed -e "s/ISSUE-NO/$ISSUE/" .github/checklist.md)"
    gh pr view --web
end
```

## Bash Equivalent

For the commit-to-linear-ticket workflow, simplified version:

```bash
#!/bin/bash

# Extract information
TITLE=$(git log -1 --format=%s)
ISSUE=$(git branch --show-current | rev | cut -d"/" -f2 | rev)
BRANCH_NAME=$(git symbolic-ref --short HEAD)

# Display information
echo "Linear issue: $ISSUE"
echo "Title: $TITLE"
echo "For: $BRANCH_NAME -> develop"

# Push branch
git push --set-upstream origin "$BRANCH_NAME"

# Create draft PR
gh pr create --draft \
  --title "$TITLE" \
  --body "Fixes: https://linear.app/example/issue/$ISSUE"

# Post checklist comment if template exists
if [ -f .github/checklist.md ]; then
  gh pr comment --body "$(sed -e "s/ISSUE-NO/$ISSUE/" .github/checklist.md)"
fi

# Open PR in browser
gh pr view --web
```

## Key Differences

**Simplified version for commit-to-linear-ticket:**
- Assumes commit message already has the issue number (PAY-XXX)
- No need to check if message has issue number (we just amended it)
- Uses simpler body: "Fixes: <linear-url>" instead of "Related to"
- Works specifically with the commit-to-linear-ticket workflow

**Original fish function:**
- Extracts message from the first commit not in origin/develop
- Checks if message already has issue number
- Prepends issue number if missing
- More general-purpose for any branch

## Branch Name Format

Expected format: `janusz/PAY-XXX/<description>`

Where:
- `janusz` = author name
- `PAY-XXX` = issue number (extracted via `rev | cut -d"/" -f2 | rev`)
- `<description>` = short description

## Checklist Template

The workflow expects `.github/checklist.md` with `ISSUE-NO` placeholder:

```markdown
## Checklist for ISSUE-NO

- [ ] Tests pass
- [ ] Code review requested
- [ ] Documentation updated
- [ ] Issue linked: PAY-XXX
```

The placeholder is replaced with the actual issue number when posted.