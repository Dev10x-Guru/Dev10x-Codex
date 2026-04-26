---
name: Dev10x-skill-audit
description: Audit a session's skill usage, compliance, and extract lessons learned. Reads the session transcript directly — run from a separate terminal.
---

# Skill Audit

Analyze a Claude Code session transcript for skill compliance, missed invocations,
user corrections, and process improvements worth persisting into skill definitions.

## Arguments

The skill accepts one optional argument, resolved in this order:

1. **JSONL path** — if arg ends in `.jsonl`, use it directly
2. **Worktree path** — if arg is a directory (e.g., `/work/myproject/my-repo`), encode it
   to a project directory and find the latest JSONL in it
3. **`latest`** (or no arg) — encode the current working directory, find latest JSONL

**Path encoding**: `/work/myproject/my-repo` → `-work-myproject-my-repo` (replace leading `/` then
all `/` with `-`).

**Project directory**: `$HOME/.codex/projects/<encoded-path>/`

## Proactive Triggers

**Auto-suggest this skill (DO NOT run it inline) when you detect:**

1. **Raw scripts instead of tools** — You wrote 3+ raw `gh api`, shell pipelines,
   or other manual commands when a dedicated tool exists. The audit captures which
   tools were missed so memory/skills can be updated.

2. **Repeated user corrections** — The user corrected your approach 3+ times
   in the same session (wrong triage verdict, wrong tone, wrong implementation
   choice). The audit extracts patterns from corrections and proposes skill updates.

3. **Skill deviation pattern** — You skipped documented steps in a skill 2+ times
   (e.g., forgot to resolve threads after replying, forgot one-fixup-per-comment rule).

4. **Permission friction** — The user had to approve 3+ safe, repetitive commands
   (e.g., `pytest`, `uv run`, `psql ... SELECT`) that should be pre-approved.
   The audit compares each prompted command against `settings.local.json` allow
   rules and proposes new patterns to eliminate the friction.

5. **Inline shell scripts** — A skill (SKILL.md) contains 3+ Bash lines written
   inline, OR a session used a multi-step shell pipeline/heredoc that would need
   repeated approval. Inline scripts can't be pre-approved with a single allow
   rule; extracting them to a `scripts/` file under a skill lets the user grant
   one `Bash($HOME/.codex/skills/<skill>/scripts/:*)` rule instead.

6. **Structural command friction** — You used `$()` subshells, `&&` chains,
   `git -C`, env var prefixes, or leading `#` comments that broke allow-rule
   prefix matching, AND the user had to reject/correct the approach. These
   are fundamentally unfixable with allow rules — they need skill updates
   and/or hookify rules to prevent recurrence. The audit's Step 4c detects
   these patterns and proposes both skill fixes and auto-reject hooks.

7. **Hook-blocked retries** — A PreToolUse hook rejected a command (e.g.,
   `cat <<` blocked by `validate-bash-security.py`) but you attempted the
   same pattern again in the same session. The audit detects these as
   HOOK_BLOCKED_RETRY and proposes skill updates to use the correct
   alternative.

8. **Redundant `uv run --script` prefixes** — A skill or shell script
   invokes a Python script with `uv run --script path/to/script.py` when
   the script already has `#!/usr/bin/env -S uv run --script` shebang and
   is executable. The prefix is redundant, breaks allow-rule matching
   (prefix becomes `uv` instead of the script path), and makes the command
   harder to pre-approve. The audit's Step 4g detects these and proposes
   dropping the prefix.

When a trigger is detected, find the current session's JSONL path and suggest:

> "I've noticed [trigger description]. Open a new terminal and run:
> ```
> claude 'Dev10x-skill-audit <jsonl-path>'
> ```
> to capture these as improvements."

To find the current session's JSONL path, use:
```bash
ls -t $HOME/.codex/projects/<encoded-cwd>/*.jsonl | head -1
```

## Workflow

### Step 1: Resolve session file

```python
import os, glob

arg = "$SKILL_ARG"  # from the invocation
claude_dir = os.path.expanduser("~/.claude")

if arg.endswith(".jsonl"):
    session_file = arg
elif arg and os.path.isdir(arg):
    encoded = arg.replace("/", "-")
    if encoded.startswith("-"):
        pass  # already correct
    project_dir = f"{claude_dir}/projects/{encoded}"
    jsonls = sorted(glob.glob(f"{project_dir}/*.jsonl"), key=os.path.getmtime, reverse=True)
    session_file = jsonls[0]  # latest
else:
    cwd = os.getcwd()
    encoded = cwd.replace("/", "-")
    project_dir = f"{claude_dir}/projects/{encoded}"
    jsonls = sorted(glob.glob(f"{project_dir}/*.jsonl"), key=os.path.getmtime, reverse=True)
    session_file = jsonls[0]  # latest
```

Implement this logic using Bash (ls -t + head) rather than running Python inline.
If resolution fails, ask the user to provide the JSONL path explicitly.

### Step 2: Extract transcript

Create a unique output file:
```bash
/tmp/claude/bin/mktmp.sh skill-audit audit-transcript .md
```
Store the returned path, then run the extraction script:
```bash
$HOME/.codex/skills/Dev10x-skill-audit/scripts/extract-session.sh \
  "<session_file>" <unique-path>
```

> **Note:** Do NOT prefix this with `mkdir -p ... &&` — the `mktmp.sh` script
> creates the directory automatically. Prefixing with `mkdir &&` shifts
> the command prefix to `mkdir`, breaking the `Bash($HOME/.codex/skills:*)` allow rule.

### Step 3: Read the transcript

Use the Read tool to read the transcript at the unique path returned in Step 2.
This is the session you are auditing.

### Step 4: Detect project context

From the transcript header, extract the **Project** path. Encode it to determine
the correct memory directory:
```
$HOME/.codex/projects/<encoded-project-path>/memory/
```

Also locate the skills directory: `$HOME/.codex/skills/`

### Step 5: Execute the 6-phase audit

Run all six phases directly (no subagent):

---

#### Phase 1: Action Inventory

Scan the transcript and catalog every significant action:

1. **Git operations**: commits, branch creation, rebases, pushes
2. **PR operations**: creation, review, comment responses, CI fixes
3. **Ticket operations**: creation, status changes, scoping
4. **Test operations**: running tests, fixing failures, coverage checks
5. **Code changes**: new files, refactoring, bug fixes
6. **Communication**: Slack messages, PR comments, Linear comments
7. **Process decisions**: user corrections, approach changes, manual overrides
8. **Configuration changes**: permissions, settings edits

For each action, note:
- What happened (brief description)
- Whether a skill was invoked (which one, or "none")
- Whether the user manually corrected the approach
- Look for `**[CORRECTION]**` markers in the transcript

Output a markdown table of actions.

---

#### Phase 2: Skill Coverage Analysis

For each action where NO skill was invoked:

1. Read SKILL.md files from `$HOME/.codex/skills/*/SKILL.md`
2. Check "When to Use" / trigger sections
3. Classify as:
   - **MISSED**: A skill exists and should have been used
   - **CORRECT_SKIP**: No applicable skill, or action was too simple
   - **GAP**: A skill SHOULD exist but doesn't

---

#### Phase 3: Compliance Check

For each action where a skill WAS invoked:

1. Read the corresponding SKILL.md
2. Compare actual steps against documented workflow
3. Identify deviations:
   - **SKIPPED_STEP**: A documented step was skipped
   - **WRONG_ORDER**: Steps executed out of order
   - **EXTRA_STEP**: An undocumented step was added
   - **DEVIATED**: A step was done differently
   - **COMPLIANT**: Skill was followed correctly

Assess each deviation: improvement, regression, or neutral?

---

#### Phase 4: Permission Friction Analysis

Identify tool calls that would have required user approval by comparing
them against the allow rules in `settings.local.json`. The JSONL format
does not explicitly tag permission prompts, so this phase uses pattern
matching: for every Bash, Read, Write, and Edit tool call in the
transcript, check whether it matches any existing allow rule.

**Step 4a: Inventory tool calls and match against allow rules**

Extract every Bash, Read, Write, and Edit tool call from the transcript.
For each, determine whether it matches any allow rule using the pattern
matching logic below.

**Allow rule format** (from `settings.local.json`):
```
"Bash(command-prefix:*)"   — matches if command starts with the prefix
"Read(/path/glob/**)"      — matches if file path matches the glob
"Write(/path/glob/**)"     — same for Write
"Edit(/path/glob/**)"      — same for Edit
```

**Matching algorithm**:
- `Bash(prefix:*)` matches if the command string starts with `prefix`
  (after stripping leading whitespace and env var assignments)
- `Read(/path/**)` matches if the file path starts with `/path/`
- Pipe chains: only the first command is matched against Bash rules

Record unmatched tool calls — these are the ones that would have
required a permission prompt.

Output a markdown table of all unmatched tool calls.

**Step 4b: Inline script detection**

Scan skills referenced during the session (`$HOME/.codex/skills/*/SKILL.md`) for
inline shell content that should live in a `scripts/` file:

- Any `bash` or `sh` code block with 4+ lines, OR
- Any `python` code block used as a CLI one-liner (not as an example snippet), OR
- Any block that mixes curl/jq/awk/sed into a multi-step pipeline

For each candidate, note:

| Skill | Inline block (type + line count) | Suggested script path |
|-------|----------------------------------|-----------------------|
| `Dev10x:some-skill` | 12-line bash loop | already extracted ✓ |
| `some:skill` | 8-line curl + jq pipeline | `scripts/fetch-data.sh` |

Also scan the session transcript for Bash tool calls that were multi-step
(heredoc, `&&`-chained, or 5+ commands in one call) — these are candidates
for extraction to a skill's `scripts/` directory even if no skill currently
owns them.

Classification:
- **EXTRACT_TO_SKILL_SCRIPT**: Inline script is complex enough to warrant a
  `scripts/` file; the parent skill should be updated + a `Bash(...scripts/:*)`
  allow rule added
- **EXTRACT_TO_NEW_SKILL**: The script logic is reusable but no skill owns it
  yet; suggest creating a skill with a `scripts/` directory
- **ACCEPTABLE_INLINE**: Short utility snippet (≤3 lines) — leave as-is

**Step 4c: Command Pattern Toxicity Analysis**

For each unmatched tool call from Step 4a, check whether the friction is
**structural** (no allow rule can ever fix it) vs **missing** (just needs
a new rule). Structural friction needs skill updates and/or hooks.

**Toxicity categories:**

| Category | Pattern | Why Allow Rules Fail | Fix |
|---|---|---|---|
| `PREFIX_POISONED_SUBSHELL` | `VAR=$(cmd) && script "$VAR"` | Prefix becomes `VAR=`, not `script` | Pass args directly to script |
| `PREFIX_POISONED_CHAIN` | `mkdir -p /tmp && script` | Prefix becomes `mkdir`, not `script` | Let script create dirs, or Write tool first |
| `PREFIX_POISONED_ENVVAR` | `ENV=val command` | Prefix becomes `ENV=`, not `command` | Script sets env internally |
| `PREFIX_POISONED_GIT_C` | `git -C /path log` | `git -C` doesn't match `Bash(git log:*)` | Use CWD, avoid `-C` |
| `PREFIX_POISONED_COMMENT` | `# comment\ncommand` | `#` breaks all prefix matching | Use Bash `description` param |
| `HOOK_BLOCKED_RETRY` | `cat <<'EOF'...` or `echo >` | Hook rejects it; Claude retries anyway | Update skill to use Write + `-F` |
| `NUISANCE_APPROVE` | Safe command prompted 3+ times | Allow rule exists but pattern doesn't match | Widen existing rule or add new one |
| `UNNECESSARY_CD_WORKTREE` | `cd /worktree/path && command` | `cd` shifts prefix; CWD is already the worktree | Drop the `cd` — session is already there |
| `WORKTREE_CWD_NOT_SWITCHED` | Commands run in main repo after worktree creation | Worktree creation should switch CWD | Investigate `Dev10x:git-worktree` — CWD switch may have failed |

**Detection algorithm:**

1. **Subshell poisoning**: Scan for `$(...) &&`, `$(...);`, or
   variable assignments like `VAR=$(...) && ...` where the second
   command is a pre-approved script path.

2. **Chain poisoning**: Scan for `cmd1 && cmd2` where `cmd2` matches
   a skill script path but `cmd1` does not. The `&&` shifts the
   effective prefix to `cmd1`.

3. **Env var poisoning**: Scan for `KEY=value command` where `command`
   would match an allow rule but `KEY=` prevents matching. Exception:
   env var prefixes that ARE in the allow list (e.g.,
   `Bash(GIT_SEQUENCE_EDITOR=:*)`) are not toxic.

4. **`git -C` poisoning**: Scan for `git -C <path> <subcommand>`.
   The allow rule `Bash(git log:*)` won't match `git -C /foo log`.

5. **Comment prefix**: Scan for commands starting with `#` — breaks
   all allow-rule prefix matching.

6. **Hook-blocked retries**: Cross-reference unmatched commands against
   known hook rejection patterns from `$HOME/.codex/settings.json`
   PreToolUse hooks and `$HOME/.codex/hooks/*.py`. If a command matches
   a hook block regex, Claude should never have attempted it.
   Read the hook scripts to extract their block patterns:
   - `validate-bash-security.py` blocks: `cat >`, `cat <<`, `echo >`,
     `printf >`, shell command substitution inside eval
   - Other hooks: extract reject conditions from their source

7. **Nuisance approvals**: Commands that are safe, not structurally
   broken, but prompted because no allow rule covers them. Detected
   when the same command pattern appears 3+ times with no structural
   issue.

8. **Unnecessary `cd` in worktree**: Scan for `cd /path && command`
   where `/path` matches the session's CWD (from transcript header).
   If the session is in a worktree (`.git` is a file), `cd` into
   the worktree root is always redundant. Classification:
   `UNNECESSARY_CD_WORKTREE`. Fix: drop the `cd` prefix.

9. **Worktree CWD not switched**: After a `Dev10x:git-worktree`
   invocation in the transcript, check whether subsequent Bash
   commands target the new worktree path or still operate in the
   original repo. If commands use `cd <worktree>` or `git -C
   <worktree>` after creation, the CWD switch may have failed.
   Classification: `WORKTREE_CWD_NOT_SWITCHED`. Fix: investigate
   `Dev10x:git-worktree` skill — the EnterWorktree tool should have
   switched the session directory automatically.

**Output format:**

| # | Command (truncated) | Toxicity | Root Cause | Recommended Fix |
|---|---|---|---|---|
| 1 | `BASE=$(git merge...) && script` | PREFIX_POISONED_SUBSHELL | `$()` shifts prefix | Skill: pass `develop` directly |
| 2 | `cat <<'EOF'\n...\nEOF` | HOOK_BLOCKED_RETRY | hook blocks `cat <<` | Skill: Write + `git commit -F` |
| 3 | `mkdir -p /tmp && script` | PREFIX_POISONED_CHAIN | `&&` shifts prefix to `mkdir` | Skill: script creates own dirs |
| 4 | `git -C /work/myproject log` | PREFIX_POISONED_GIT_C | `-C` breaks `Bash(git log:*)` | Skill: use CWD |
| 5 | `pytest src/` (3x) | NUISANCE_APPROVE | No matching rule | Allow: `Bash(pytest:*)` |
| 6 | `cd /work/.worktrees/proj && pytest` | UNNECESSARY_CD_WORKTREE | CWD is already the worktree | Drop the `cd` |
| 7 | `git -C /work/.worktrees/proj log` after worktree create | WORKTREE_CWD_NOT_SWITCHED | CWD switch failed | Fix `Dev10x:git-worktree` skill |

**10. Wrapper discovery**: For each PREFIX_POISONED or chained
command finding, check whether a wrapper already exists that
encapsulates the toxic pattern:

| Wrapper source | How to check | Example |
|---|---|---|
| Git aliases | `git config --list \| grep alias\.` | `git develop-log` wraps `$(git merge-base develop HEAD)` |
| Fish functions | `ls ~/.config/fish/functions/` | `fish_func.fish` wrapping a pipeline |
| Claude tools | `ls $HOME/.codex/tools/` | `$HOME/.codex/tools/helper.sh` |
| Skill scripts | `find $HOME/.codex/skills -name '*.sh'` | `scripts/fetch.sh` in a skill dir |

Classify each finding:

| Classification | Condition | Proposal |
|---|---|---|
| `USE_EXISTING_WRAPPER` | Wrapper found | MEMORY_UPDATE: document the wrapper invocation |
| `CREATE_WRAPPER_ALIAS` | No wrapper; git-related chain | Create git alias + MEMORY_UPDATE |
| `CREATE_WRAPPER_SCRIPT` | No wrapper; non-git chain | Create `$HOME/.codex/tools/<name>.sh` + allow rule + MEMORY_UPDATE |

Add a **Wrapper Status** column to the output table:

| # | Command | Toxicity | Wrapper Status | Recommended Fix |
|---|---|---|---|---|
| 1 | `BASE=$(git merge-base develop HEAD) && git log` | PREFIX_POISONED_SUBSHELL | EXISTS: `git develop-log` | MEMORY_UPDATE: use `git develop-log` |
| 2 | `mkdir -p /tmp/out && $HOME/.codex/tools/export.sh` | PREFIX_POISONED_CHAIN | MISSING | CREATE_WRAPPER_SCRIPT: let script create dirs |
| 3 | `ENV=val $HOME/.codex/skills/foo/scripts/run.sh` | PREFIX_POISONED_ENVVAR | MISSING | CREATE_WRAPPER_SCRIPT: script sets env internally |

When wrapper exists, the primary recommendation is MEMORY_UPDATE
(not a new script or alias). The memory note should document:
- The toxic pattern that triggers it
- The correct invocation using the wrapper
- Where the wrapper lives (for reference)

Example memory update proposal:
```
MEMORY_UPDATE: "Use `git develop-log` instead of
`git log $(git merge-base develop HEAD)..HEAD` —
the alias wraps the subshell, keeping the command prefix stable
for allow-rule matching."
```

When no wrapper exists, propose creating one AND a memory update
documenting it. For git aliases, reference `Dev10x:git-alias-setup`
as the canonical setup mechanism rather than proposing raw
`git config` commands.

**Recommendations per category:**

- **PREFIX_POISONED_***: First check wrapper discovery (step 8
  above). If a wrapper exists, propose MEMORY_UPDATE to use it
  and SKILL_UPDATE to teach the wrapper pattern. If no wrapper
  exists, propose creating one, then update the SKILL.md that
  teaches the broken pattern. Also propose a PreToolUse hook
  (via `/hookify`) to auto-reject the pattern with a helpful
  error message pointing to the wrapper.

- **HOOK_BLOCKED_RETRY**: Update the SKILL.md to use the correct
  pattern. No new hook needed (existing hook already blocks). Add a
  memory note so Claude stops attempting the blocked pattern.

- **NUISANCE_APPROVE**: Propose an allow rule (same as Step 4f).

**Hook proposal format** (for PREFIX_POISONED findings):

When proposing a new hookify rule, provide enough context for
`/hookify` to create it:

```
Proposed hook: prevent-subshell-in-script-calls
Trigger: PreToolUse (Bash)
Pattern: command contains $() && followed by a skill script path
Action: deny
Message: "Do not use $() before skill script calls — it breaks
  allow-rule prefix matching. Pass arguments directly to the script."
Source: TICKET-58 audit — 3 user corrections for this pattern
```

**Step 4d: Load existing permissions**

Read `$HOME/.codex/settings.local.json` and any project-level
`$HOME/.codex/projects/<encoded-path>/settings.local.json` to get the
current `permissions.allow` list.

**Step 4e: Match analysis**

For each permission prompt, determine why it wasn't pre-approved.
First check Step 4c toxicity results — toxic commands get a structural
classification. Non-toxic commands get a rule-based classification.

**Structural classifications** (from Step 4c — no allow rule can fix):

| Classification | Meaning | Example |
|---|---|---|
| **PREFIX_POISONED** | `$()`, `&&`, env vars, `git -C`, or `#` shifts the effective prefix | `BASE=$(...) && script` |
| **HOOK_BLOCKED** | An existing PreToolUse hook rejects this pattern | `cat <<'EOF'` blocked by validate-bash-security |
| **NUISANCE_PATTERN** | Safe command prompted 3+ times, structurally OK but tedious | Same `uv run` variant 4 times |

**Rule-based classifications** (fixable with allow rules):

| Classification | Meaning | Example |
|---|---|---|
| **MISSING_RULE** | No allow rule covers this command/path at all | `pytest` not in allow list |
| **PATTERN_TOO_NARROW** | A rule exists for similar commands but the glob pattern doesn't match this invocation | `Bash(git log:*)` exists but `git -C /other/path log` was used |
| **PREFIX_MISMATCH** | The command starts differently than the allow pattern expects | `uv run pytest` vs `pytest` |
| **PATH_NOT_COVERED** | A Read/Write/Edit rule exists but doesn't cover this path | `Read(/work/myproject/**)` missing |
| **CORRECTLY_PROMPTED** | The command is risky and SHOULD require approval | `git push --force`, `rm -rf` |

**Priority**: Structural classifications take precedence. If a command
is PREFIX_POISONED, do NOT also classify it as PATTERN_TOO_NARROW —
the root cause is the prefix, not the rule width.

**Step 4f: Generate recommendations**

Route each finding to the right fix type based on classification:

**1. NUISANCE_APPROVE / MISSING_RULE / PATTERN_TOO_NARROW / PREFIX_MISMATCH / PATH_NOT_COVERED → Allow rule**

Propose a specific allow rule:

```
Current: (none)
Proposed: Bash(pytest:*)
Reason: pytest is a safe read-only test runner, prompted 3 times
```

Group related proposals (e.g., all `uv run` variants) into a single
recommendation. Prefer broader patterns that cover foreseeable variants
over exact-match rules, but never propose patterns that would also
pre-approve destructive commands.

**Safety guardrails — never propose allow rules for:**
- `git push`, `git reset --hard`, `git clean`, `git checkout .`
- `rm -rf`, `rm -r` on non-temp paths
- Commands that write to production databases
- Commands that send messages (Slack, email) without review
- `--force`, `--no-verify`, `--hard` flags

**2. PREFIX_POISONED → Wrapper discovery + skill update + hook**

For each PREFIX_POISONED finding, run wrapper discovery (4c step 8)
first, then route based on result:

**2a. Wrapper exists (`USE_EXISTING_WRAPPER`):**
1. Propose MEMORY_UPDATE documenting the wrapper invocation
2. Propose SKILL_UPDATE replacing the toxic pattern with the wrapper
3. No new hook or script needed — the wrapper already solves it

```
Fix type: MEMORY_UPDATE + SKILL_UPDATE
Wrapper: git develop-log (git alias)
Skill: Dev10x:some-skill (line 38)
Before: git log $(git merge-base develop HEAD)..HEAD
After:  git develop-log
Memory: "Use `git develop-log` — wraps the subshell"
```

**2b. No wrapper exists (`CREATE_WRAPPER_ALIAS` / `CREATE_WRAPPER_SCRIPT`):**
1. Propose creating the wrapper (alias via `Dev10x:git-alias-setup`
   or script in `$HOME/.codex/tools/`)
2. Propose SKILL_UPDATE replacing the toxic pattern
3. Propose MEMORY_UPDATE documenting the new wrapper
4. If script: propose allow rule for the new path
5. Propose hookify rule to auto-reject the toxic pattern

```
Fix type: CREATE_WRAPPER + SKILL_UPDATE + HOOKIFY_RULE
Proposed: $HOME/.codex/tools/export-with-env.sh
Skill: Dev10x:some-skill (line 38)
Before: ENV=val $HOME/.codex/skills/foo/scripts/run.sh
After:  $HOME/.codex/tools/export-with-env.sh
Allow:  Bash($HOME/.codex/tools/export-with-env:*)
Hook: Reject ENV= prefix before skill scripts
Memory: "Use export-with-env.sh — sets env internally"
```

**3. HOOK_BLOCKED → Skill update + memory note**

For each HOOK_BLOCKED finding:
1. Identify the skill that teaches the blocked pattern
2. Propose a skill edit using the correct alternative
3. Propose a memory note so Claude stops attempting the pattern
4. No new hook needed — the existing hook already blocks it

```
Fix type: SKILL_UPDATE + MEMORY_NOTE
Skill: commit (Step 11)
Blocked by: validate-bash-security.py (cat << pattern)
Before: git commit -m "$(cat <<'EOF'...)"
After:  Write to /tmp/msg.txt, then git commit -F /tmp/msg.txt
Memory: "hookify blocks cat << — use Write + -F for commit messages"
```

**4. CORRECTLY_PROMPTED → No action**

Risky commands should require approval. No recommendation needed.

**5. REDUNDANT_UV_PREFIX → Skill update**

For each REDUNDANT_UV_PREFIX finding:
1. Identify the skill or shell script that uses the prefix
2. Propose removing the `uv run --script` prefix
3. If the underlying Python script lacks the proper shebang or
   permissions, propose fixing those first

```
Fix type: SKILL_UPDATE
Skill: Dev10x:some-skill (line 42)
Before: uv run --script $HOME/.codex/tools/gh-pr-comments.py get ...
After:  $HOME/.codex/tools/gh-pr-comments.py get ...
Prereq: script has #!/usr/bin/env -S uv run --script + chmod +x
```

**Step 4g: Script Shebang and Invocation Audit**

Scan all Python scripts in `$HOME/.codex/skills/` and `$HOME/.codex/tools/`
for shebang and invocation hygiene. Also scan SKILL.md files and shell
scripts for redundant `uv run --script` prefixes.

**Convention**: Every Python script under `$HOME/.codex/skills/` and
`$HOME/.codex/tools/` MUST use the self-executing shebang pattern:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["requests"]  # or [] for stdlib-only
# ///
```

This makes scripts executable directly (`./script.py`) without
needing a `uv run --script` prefix. The PEP 723 metadata block
is required even for stdlib-only scripts (use `dependencies = []`)
for consistency.

**Detection algorithm:**

1. **Missing uv shebang**: Find Python scripts (`.py`) under
   `$HOME/.codex/skills/` and `$HOME/.codex/tools/` whose shebang is
   `#!/usr/bin/env python3` or `#!/usr/bin/python3` instead of
   `#!/usr/bin/env -S uv run --script`. Classification:
   `WRONG_SHEBANG`.

2. **Missing PEP 723 metadata**: Find scripts with the correct
   uv shebang but no `# /// script` block. Classification:
   `MISSING_PEP723`.

3. **Missing execute permission**: Find scripts that are not
   executable (`! -x`). Classification: `NOT_EXECUTABLE`.

4. **Redundant `uv run --script` prefix in SKILL.md**: Grep
   SKILL.md files for `uv run --script` invocations of scripts
   that already have the self-executing shebang. Classification:
   `REDUNDANT_UV_PREFIX`.

5. **Redundant `uv run --script` prefix in shell scripts**: Grep
   `scripts/*.sh` files for `uv run --script` invocations.
   Classification: `REDUNDANT_UV_PREFIX_SHELL`.

**Output format:**

| # | Script / Caller | Issue | Classification | Fix |
|---|---|---|---|---|
| 1 | `tools/gh-pr-comments.py` | `#!/usr/bin/env python3` | WRONG_SHEBANG | Change to uv shebang + PEP 723 |
| 2 | `tools/upload-screenshots.py` | Has deps but python3 shebang | WRONG_SHEBANG | Change shebang (deps already in PEP 723) |
| 3 | `scripts/fernet-decrypt.py` | mode 644 | NOT_EXECUTABLE | `chmod +x` |
| 4 | `Dev10x:some-skill/SKILL.md` | `uv run --script $HOME/.codex/tools/...` | REDUNDANT_UV_PREFIX | Drop prefix |
| 5 | `Dev10x:some-skill/scripts/notify.sh` | `uv run --script ...slack-notify.py` | REDUNDANT_UV_PREFIX_SHELL | Drop prefix |

**Recommendations:**

- **WRONG_SHEBANG**: Fix the shebang to
  `#!/usr/bin/env -S uv run --script` and add PEP 723 block.
  If the script has external deps, they go in `dependencies = [...]`.
  If stdlib-only, use `dependencies = []`.
- **MISSING_PEP723**: Add the `# /// script` block after the shebang.
- **NOT_EXECUTABLE**: Run `chmod +x <script>`.
- **REDUNDANT_UV_PREFIX**: Update the SKILL.md or shell script to
  call the Python script directly without the `uv run --script`
  prefix. This simplifies allow-rule matching — the command prefix
  becomes the script path, not `uv`.
- **REDUNDANT_UV_PREFIX_SHELL**: Same as above but in `.sh` files.

**Why direct invocation matters for allow rules:**

```
# With prefix — allow rule must match "uv run":
Bash(uv run --script $HOME/.codex/tools/gh-pr-comments.py:*)

# Without prefix — allow rule matches the script path directly:
Bash($HOME/.codex/tools/gh-pr-comments.py:*)
```

The second form is simpler, more specific, and follows the same
pattern as skill scripts under `Bash($HOME/.codex/skills/<name>/scripts/:*)`.

**Summary table format:**

| # | Classification | Fix Type | Target | Action |
|---|---|---|---|---|
| 1 | PREFIX_POISONED (wrapper exists) | Memory + Skill | `Dev10x:some-skill` | USE_EXISTING_WRAPPER: `git develop-log` |
| 2 | PREFIX_POISONED (no wrapper) | Wrapper + Skill + Hook | `$HOME/.codex/tools/` | CREATE_WRAPPER_SCRIPT + hookify |
| 3 | HOOK_BLOCKED | Skill + Memory | `commit` | Replace heredoc with Write + -F |
| 4 | MISSING_RULE | Allow rule | `settings.local.json` | Add `Bash(pytest:*)` |
| 5 | CORRECTLY_PROMPTED | None | — | `git push` should require approval |
| 6 | REDUNDANT_UV_PREFIX | Skill update | `Dev10x:some-skill` | Drop `uv run --script` prefix |
| 7 | WRONG_SHEBANG | Script fix | `tools/script.py` | Add uv shebang + PEP 723 |

---

#### Phase 5: Lessons Learned Extraction

Review user corrections and `[CORRECTION]` markers:

1. For each correction, determine:
   - What did Claude do wrong?
   - What did the user want instead?
   - One-off preference or repeatable pattern?
   - Which skill should encode this lesson?

2. Check memory directory for existing notes on the topic.

3. Classify each lesson:
   - **SKILL_UPDATE**: Add to an existing SKILL.md
   - **NEW_SKILL**: Warrants a new skill
   - **MEMORY_UPDATE**: Add to memory (not skill-specific)
   - **CLAUDE_MD_UPDATE**: Add to CLAUDE.md (global rule)
   - **NO_ACTION**: One-off, not worth persisting

---

#### Phase 6: Propose Changes (REQUIRES USER CONFIRMATION)

**CRITICAL: Do NOT modify any files without user confirmation.**

1. Present each proposed change clearly:
   - Which file to modify
   - What to add/change/remove
   - Why (reference the specific transcript turn)

2. Use AskUserQuestion to confirm each change (or batch related changes).

3. If approved, edit the files. For new skills, suggest using `Dev10x-skill-create`.

4. Generate a summary report:
   - Total actions reviewed
   - Skills invoked vs missed vs gaps
   - Compliance score (% of steps followed correctly)
   - Permission prompts: total, avoidable, proposed rules
   - Changes applied (skill updates + permission rules)
   - Recommendations for future sessions

---

## Important Rules

- **Read-only by default**: Only modify files after explicit user approval
- **Be specific**: Reference exact transcript turns and skill file lines
- **Prioritize impact**: Focus on deviations that caused real problems, not nitpicks
- **Respect intent**: If the user's correction was clearly better, update the skill.
  If it was situational, note it but don't change the default.
- **No duplicate memory**: Check existing memory/CLAUDE.md before proposing additions
- **Inline script extraction**: Phase 4b detects inline shell/python blocks in
  skill SKILL.md files and session Bash calls. For each `EXTRACT_TO_SKILL_SCRIPT`
  finding, propose: (1) moving the block to `$HOME/.codex/skills/<skill>/scripts/`,
  (2) updating SKILL.md to call the script, (3) adding a
  `Bash($HOME/.codex/skills/<skill>/scripts/:*)` allow rule so future runs need zero
  approval prompts. Reference `Dev10x:some-skill/scripts/triage.py` as the canonical
  example of a skill that already does this correctly.
- **Structural before rule-based**: When analyzing permission friction, always
  check Step 4c toxicity first. A PREFIX_POISONED command should never get a
  "widen the allow rule" recommendation — the fix is the skill pattern, not
  the rule. Proposing allow rules for structurally broken commands is a false
  fix that will fail on the next invocation.
- **Hook proposals are skill-coupled**: Every hookify rule proposal must come
  with a corresponding skill update that teaches the correct pattern. A hook
  that blocks a bad pattern without showing the alternative just shifts the
  friction from "approve?" to "what now?".
- **Script shebang hygiene**: Phase 4g scans Python scripts for proper
  self-executing setup. All scripts under `$HOME/.codex/skills/` and
  `$HOME/.codex/tools/` must use `#!/usr/bin/env -S uv run --script` shebang
  + PEP 723 metadata + executable permission. SKILL.md files and shell
  scripts must NOT prefix these scripts with `uv run --script` — the
  prefix is redundant and breaks allow-rule prefix matching.
- **Prefer jq/yq over Python scripts**: When a hook or skill script
  only does JSON/YAML parsing, prefer `jq` or `yq` over inline
  `python3 -c "import json..."`. Flag Python one-liners that could be
  replaced with a single `jq`/`yq` invocation as `PREFER_JQ_YQ`.
