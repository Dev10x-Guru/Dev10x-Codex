---
name: Dev10x-git-commit
description: Create a properly formatted git commit following project conventions (gitmoji, ticket reference, 72 char limit). Extracts ticket ID from branch name, prompts for description and solution points, stages changes, and creates the commit.
---

# Create Commit

## Overview

This skill creates properly formatted git commits following project conventions:
- Gitmoji prefix based on change type
- Ticket reference extracted from branch name
- 72 character title limit
- Structured body with solution points
- Proper footer with ticket reference

## Guiding Principle: User-Facing Outcomes

**Shift the perspective from what changed in the code to what it enables for the user.** The same principle drives Job Stories — the "so I can" clause captures the outcome, not the mechanism. This applies to commit titles, PR titles, ticket titles, and branch grooming.
Use the project or ticket language for Job Stories and user-story prose;
when BDD or Gherkin-derived keywords appear, use Cucumber's official
language reference: https://cucumber.io/docs/gherkin/languages/

- Bad: `Add DEVICES_READ to Square OAuth scopes` (implementation)
- Good: `Enable automatic terminal discovery` (outcome)
- Bad: `Add Square location ID GraphQL query` (implementation)
- Good: `Enable multi-location payment routing` (outcome)
- Bad: `Add customer_id column to invoices table` (implementation)
- Good: `Link invoices to customer records` (outcome)

## Prerequisites Check

**IMPORTANT:** Verify git state before committing:

1. Check if we're in a git repository
2. Check if there are staged or unstaged changes
3. Check current branch (should not be develop/main/master)
4. Verify branch follows naming convention (username/TICKET-ID/[worktree/]description)

## When to Use This Skill

Use this skill when:
- Ready to commit changes with proper formatting
- Want to ensure commit follows project conventions
- Need help formatting commit message
- Want ticket reference auto-extracted from branch

## Workflow

### Step 1: Verify Git State

**Check repository status:**
```bash
# Verify in git repo
git rev-parse --git-dir

# Get current branch
BRANCH=$(git symbolic-ref --short HEAD)

# Check for changes
git status --porcelain
```

**Validations:**
- ❌ If not in git repo → Error: "Not in a git repository"
- ❌ If on develop/main/master → Error: "Cannot commit directly to develop/main/master"
- ❌ If no changes → Error: "No changes to commit"
- ✅ If staged changes exist → Continue
- ⚠️ If only unstaged changes → Ask: "Stage all changes? (y/n)"

### Step 2: Extract Ticket ID from Branch

**Branch naming convention:** `username/TICKET-ID/[worktree-name/]description`

**Examples:**
- `janusz/PAY-133/fix-motor-timeout` → `PAY-133`
- `janusz/ENG-42/add-retry-mechanism` → `ENG-42`
- `janusz/PAY-133/app-pos-7/fix-motor-timeout` → `PAY-133` (worktree)

**Extraction:**
```bash
# Extract ticket ID (second segment)
TICKET_ID=$(git branch --show-current | cut -d'/' -f2)

# Validate format (TEAM-NUMBER)
if [[ ! $TICKET_ID =~ ^[A-Z]+-[0-9]+$ ]]; then
  echo "⚠️  Warning: Could not extract ticket ID from branch name"
  echo "Branch: $(git branch --show-current)"
  echo "Expected format: username/TICKET-ID/[worktree/]description"
fi
```

**If extraction fails:**
- Ask user: "What is the ticket ID? (e.g., PAY-133)"
- Use provided ticket ID

**If no ticket (technical branch):**
- Commits without ticket reference are allowed
- Skip ticket prompts

### Step 2.5: Optional JTBD Title Derivation

This step activates when **any** of these conditions are met:
- **Explicit request:** User passes "use Dev10x:jtbd" (or similar) in `Dev10x-git-commit` args
- **First commit:** Ticket ID extracted, zero commits ahead of develop, and
  commit type is Feature (✨) or Bug (🐛)

**Flow:**
1. Invoke the `Dev10x:jtbd` base skill in **unattended** mode with `ticket_id`
2. Extract the "so I can" clause from the returned story
3. Transform it to an imperative title (e.g., "so I can track Zelle transactions" → "Enable Zelle transaction tracking")
4. Present as a suggestion:
   ```
   Suggested title: Enable Zelle transaction tracking
   Accept? (Enter = yes, or type your own)
   ```
5. If user accepts → use as the commit title description (Step 4 is pre-filled)
6. If user types their own → use that instead

**Skip entirely** when not explicitly requested AND it's a subsequent commit,
refactor, test, docs, or config change — keeping those fast. Also skip when a
Job Story was already sourced from the Linear ticket earlier in this session
(e.g., during `ticket:work-on`) — invoking the `jtbd` skill again is redundant.

### Step 3: Determine Commit Type

**Orchestrated mode:** When this skill is invoked by an orchestrating skill
(e.g., `test:fix-flaky`, `Dev10x:git-promote`) and the commit type is
unambiguous from context, auto-select the type and description without
interactive prompts. Present the result in the preview (Step 9) for review.

**Ask user to select commit type:**
```
What type of change is this?

1. ✅ Test - Adding/updating/fixing tests
2. 🐛 Bug - Bug fixes
3. ♻️ Refactor - Code refactoring
4. ✨ Feature - New features
5. 📝 Docs - Documentation
6. 🔒 Security - Security fixes
7. ⚡ Performance - Performance improvements
8. 💄 UI - UI/styling updates
9. 🔧 Config - Configuration changes
10. Other (specify gitmoji)

Select number (1-10):
```

**Gitmoji mapping:**
- 1 → ✅ (`:white_check_mark:`)
- 2 → 🐛 (`:bug:`)
- 3 → ♻️ (`:recycle:`)
- 4 → ✨ (`:sparkles:`)
- 5 → 📝 (`:memo:`)
- 6 → 🔒 (`:lock:`)
- 7 → ⚡ (`:zap:`)
- 8 → 💄 (`:lipstick:`)
- 9 → 🔧 (`:wrench:`)
- 10 → Ask: "Enter gitmoji (e.g., 🎨)"

### Step 4: Get Commit Description

**Ask user:**
```
Short description (will be title line):
[User types description]
```

**Validate:**
- Calculate total length: `gitmoji + space + TICKET-ID + space + description`
- If > 72 chars → Ask: "Title is {X} characters (max 72). Please shorten the description."
- Iterate until ≤ 72 chars

**JTBD self-check (mandatory):** Before accepting the description, verify it
describes the **user-facing outcome**, not the implementation action. A
PreToolUse hook will block implementation-focused verbs at commit time, but
catch them earlier here to avoid the round-trip.

| Blocked verb | Example bad title | JTBD rewrite |
|---|---|---|
| Add | "Add retry logic" | "Enable automatic retry on failure" |
| Update | "Update OAuth scopes" | "Enable terminal discovery" |
| Remove | "Remove dead code" | "Simplify payment flow" |
| Refactor | "Refactor repository" | "Simplify repository hierarchy" |
| Move/Rename | "Move factory to utils" | "Enable shared factory access" |
| Synchronize | "Sync skill with source" | "Enable dual-mode workflow" |

If the description starts with an implementation verb, rewrite it before
proceeding. Use outcome verbs: **Enable, Allow, Support, Prevent, Ensure,
Simplify, Improve, Resolve, Streamline, Protect, Stabilize, Automate**.

**Example titles:**
- `✅ PAY-310 Stabilize tax amount tests` (38 chars)
- `🐛 PAY-133 Resolve motor timeout in payments` (46 chars)
- `♻️ PAY-200 Simplify payment repository hierarchy` (50 chars)

### Step 5: Get Problem Explanation

**If the problem and solution are already known from prior context** in the
session (e.g., from a preceding scope, code review, or ticket investigation),
auto-generate Steps 5-6 rather than asking redundant questions. Present the
pre-filled content in the preview (Step 9) for user review.

**Important:** Auto-generation applies only to Steps 5 and 6. Step 9
(preview + confirm) is **always** shown to the user, even when the
commit message was fully auto-generated from session context.

**Otherwise, ask user:**
```
Detailed explanation of the problem being solved:
(What was wrong? Why did it need fixing? Context?)

[User provides explanation - can be multiple lines]
```

**Guidance:**
- Explain WHAT was wrong
- Explain WHY it needed fixing
- Provide context
- 2-4 sentences typically sufficient

**Example:**
```
Tests in TestAddTireServiceIndividual and TestAddTireServiceMultiple
were marked as flaky because they randomly failed when tax amounts
or percentages were generated as zero by Faker.
```

### Step 6: Get Solution Points

**Ask user:**
```
Solution points (what did you change?):
Enter each point on a new line. Type 'done' when finished.

1: [User enters first point]
2: [User enters second point]
3: [User enters third point]
done
```

**Format each point:**
- Start with `-` (bullet point)
- Be specific about what changed
- Include file names if relevant

**Example:**
```
- Added non_zero trait to MoneyFaker with min_value=Decimal('0.01')
- Updated test fixtures to ensure tax amounts and percentages >= 0.01
- Removed @pytest.mark.flaky decorators
```

### Step 7: Generate Complete Commit Message

**Assemble message:**
```
<gitmoji> <TICKET-ID> <description>

<problem explanation>

Solution:
<solution points>

Fixes: <TICKET-ID>
```

**Example:**
```
✅ PAY-310 Fix flaky tests with non-zero tax amounts

Tests in TestAddTireServiceIndividual and TestAddTireServiceMultiple
were marked as flaky because they randomly failed when tax amounts
or percentages were generated as zero by Faker.

Solution:
- Added non_zero trait to MoneyFaker with min_value=Decimal('0.01')
- Updated test fixtures to ensure tax amounts and percentages >= 0.01
- Removed @pytest.mark.flaky decorators

Fixes: PAY-310
```

### Step 8: Validate Line Lengths (72 char limit)

**IMPORTANT:** Before showing preview, validate ALL lines are ≤ 72 characters.

**Validation command:**
```bash
# Check each line of the commit message
echo "$COMMIT_MESSAGE" | awk '
  length > 72 {
    print "❌ Line " NR " too long (" length " chars): " $0
    fail = 1
  }
  END { exit fail }
'
```

**If any line exceeds 72 characters:**
1. Show which line(s) are too long with character count
2. Ask user to shorten the offending line(s)
3. Re-validate until all lines pass

**Quick length check for a single line:**
```bash
echo "your line here" | awk '{print length " chars"}'
```

**Common fixes for long lines:**
- Split into multiple bullet points
- Use shorter synonyms
- Move details to next line
- Abbreviate file paths (just filename, not full path)

**Example validation output:**
```
❌ Line 7 too long (77 chars): - Rename stages: base-os → system-base, base-python → python-dependencies

Suggestion: Split into two lines or shorten:
- Rename stages for clarity (system-base, python-dependencies)
```

### Step 9: Show Preview and Confirm

**This step is mandatory — never skip it, even when Steps 5-6 were
auto-generated from session context.**

**Display formatted message:**
```
Preview of commit message:
─────────────────────────────────
<formatted message>
─────────────────────────────────

Create this commit? (y/n/edit)
- y: Create commit
- n: Cancel
- edit: Modify the message
```

**If edit:**
- Ask which part to edit (title/explanation/solution)
- Re-prompt for that section
- Show new preview

### Step 10: Stage Files (if needed)

**If unstaged changes exist:**
```bash
# Show what will be staged
git status --short

# Ask user
echo "Stage all changes? (y/n/select)"
- y: git add .
- n: Only commit already staged files
- select: Ask which files to stage
```

**If select:**
```bash
# List unstaged files
git diff --name-only

# User selects files (space-separated)
# Stage selected files
git add file1 file2 file3
```

### Step 11: Create the Commit

**Use Write tool + `-F` to preserve formatting (hookify blocks heredocs):**

1. Create a unique temp file to avoid cross-session collisions:
   ```bash
   /tmp/claude/bin/mktmp.sh git commit-msg .txt
   ```
   Store the returned path (e.g., `/tmp/claude/git/commit-msg.7f3a9b2c1d4e.txt`).

2. Write the commit message to that file using the Write tool:
   ```
   Write <unique-path>:
   <gitmoji> <TICKET-ID> <description>

   <problem explanation>

   Solution:
   <solution point 1>
   <solution point 2>
   <solution point 3>

   Fixes: <TICKET-ID>
   ```

3. Create the commit from the file:
   ```bash
   git commit -F <unique-path>
   ```

**Verify success:**
```bash
if [ $? -eq 0 ]; then
  echo "✅ Commit created successfully"
  git log -1 --oneline
else
  echo "❌ Commit failed"
  # Show error
fi
```

### Step 12: Next Steps

**Ask user:**
```
Commit created successfully!

Next steps:
1. Continue working
2. Create another commit
3. Create PR (Dev10x-gh-pr-create)

What would you like to do? (1/2/3/done)
```

**If 3 (Create PR):**
- Use `Dev10x:gh-pr-create` skill
- PR title will use this commit message

## Important Notes

- **No Co-Authoring:** Never add "Co-Authored-By: Claude" footer (per CLAUDE.md)
- **72 char limit:** ALL lines strictly enforced (title AND body)
- **Always validate:** Run `echo "line" | awk '{print length}'` before committing
- **Ticket extraction:** Automatic from branch name
- **Gitmoji format:** Use emoji character, not :code:
- **Footer:** Always include `Fixes: TICKET-ID`
- **Spacing:** One space after gitmoji, one space after ticket ID
- **Never `git -C <path>`**: Always use plain `git` from the session
  CWD. `git -C` breaks allow-rule matching in `settings.local.json`
  and forces permission prompts after every fresh session start.
- **Never chain `git add && git commit`**: Use two separate Bash tool
  calls — one to stage, one to commit. Same rule applies to
  `git add && git rebase --continue`. Each call must stand alone.

## Integration with Other Skills

```
Dev10x:git-commit
├── Used during development workflow
├── Output: Properly formatted commit
└── Can be followed by: Dev10x:gh-pr-create
```

## Example Usage

### Example 1: Create commit with auto-extracted ticket

**User request:**
```
Dev10x-git-commit
```

**Current branch:** `janusz/PAY-310/fix-flaky-tests`

**Workflow execution:**
1. Check git status → Unstaged changes found
2. Ask: "Stage all changes?" → User: Yes
3. Stage files: `git add .`
4. Extract ticket ID → `PAY-310`
5. Ask commit type → User selects: 1 (Test)
6. Ask description → User: "Fix flaky tests with non-zero tax amounts"
7. Validate length → 51 chars ✓
8. Ask problem explanation → User provides
9. Ask solution points → User provides 3 points
10. Generate message
11. Show preview → User approves
12. Create commit with heredoc
13. Verify success → "✅ Commit created"
14. Show: `git log -1 --oneline`

**Result:**
```
✅ PAY-310 Fix flaky tests with non-zero tax amounts
```

### Example 2: Bug fix commit

**User request:**
```
Dev10x-git-commit
```

**Current branch:** `janusz/PAY-133/fix-motor-timeout`

**Workflow execution:**
1. Check status → Staged changes ready
2. Extract ticket → `PAY-133`
3. Ask type → User: 2 (Bug)
4. Ask description → "Fix motor timeout in payment processing"
5. Length check → 53 chars ✓
6. Problem explanation → "MotorTimeoutException occurs when Square API is slow..."
7. Solution points:
   - Increase timeout from 5s to 15s
   - Add retry with exponential backoff
   - Improve error logging
8. Preview → User approves
9. Create commit
10. Success!

**Result:**
```
🐛 PAY-133 Fix motor timeout in payment processing
```

### Example 3: Commit with manual ticket ID

**User request:**
```
Dev10x-git-commit
```

**Current branch:** `feature/improve-search` (no ticket ID)

**Workflow execution:**
1. Check status → OK
2. Try extract ticket → Failed (no standard format)
3. Warn: "Could not extract ticket ID"
4. Ask: "Ticket ID?" → User: `PAY-200`
5. Ask type → User: 3 (Refactor)
6. Ask description → "Refactor search to use Elasticsearch"
7. Continue normally...

**Result:**
```
♻️ PAY-200 Refactor search to use Elasticsearch
```

### Example 4: Technical commit without ticket

**User request:**
```
Dev10x-git-commit
```

**Current branch:** `fix-typo-in-readme`

**Workflow execution:**
1. Check status → OK
2. Try extract ticket → Failed
3. Ask: "Ticket ID?" → User: (press Enter for none)
4. Ask type → User: 5 (Docs)
5. Ask description → "Fix typo in README"
6. Length check → 25 chars ✓
7. Problem: "README had typo in installation section"
8. Solution: "Fixed typo: 'instal' → 'install'"
9. Generate WITHOUT ticket reference:
   ```
   📝 Fix typo in README

   README had typo in installation section

   Solution:
   - Fixed typo: 'instal' → 'install'
   ```
10. Create commit

**Result:**
```
📝 Fix typo in README
```

## Error Handling

### Common Scenarios

**"Not in a git repository":**
- Error and stop
- Suggest: Initialize git repo first

**"No changes to commit":**
- Show: `git status`
- Suggest: Make changes first

**"Cannot commit to develop/main/master":**
- Error and stop
- Suggest: Create feature branch first

**"Title too long":**
- Show character count
- Ask for shorter description
- Iterate until ≤ 72

**"Pre-commit hook failed":**
- Show hook error
- Ask: "Fix issues and retry? (y/n)"
- If yes: Return to Step 9 (stage files)

**"Commit failed":**
- Show git error
- Suggest common fixes (conflicts, permissions, etc.)

## Resources

### references/gitmoji-guide.md

Complete gitmoji reference with usage guidelines.

### references/commit-examples.md

Real commit message examples from the project.

## Success Criteria

A successful commit should:
- ✅ Follow gitmoji convention
- ✅ Include ticket reference (if applicable)
- ✅ Have title ≤ 72 characters
- ✅ Include problem explanation
- ✅ List solution points
- ✅ Include `Fixes:` footer (if ticket)
- ✅ No co-authoring attribution
- ✅ Be properly formatted for git log viewing
