---
name: Dev10x-git-worktree
description: Create external git worktrees for clean Codex workspace isolation.
---

# Git Worktree

**Announce:** "Using Dev10x:git-worktree skill to create an isolated workspace."

## Workflow

### Step 1: Determine Branch Name

The branch name is needed by both paths. Follow project naming conventions:

- username: check `git branch -a` for the pattern used (e.g. `janusz`)
- slug: lowercase ticket title, hyphens, stop-words removed, max 3–4 words
- regular repo: `username/TICKET-ID/slug`
- worktree: `username/TICKET-ID/worktree-name/slug`
  (worktree name = basename of the worktree directory, e.g. `app-pos-7`)

### Step 2: Determine Worktree Location

Default pattern: `../.worktrees/<project-basename>-NN`

Calculate the next available path:

```bash
$HOME/.codex/skills/dev10x-git-worktree/scripts/next-worktree-name.sh
```

Use the calculated path unless the user already provided a custom location.
Otherwise, ask one concise plain-text question that offers the calculated
path as the default and lets the user provide a custom location if they
want one.

Example:

```text
Create the worktree at ../.worktrees/<project-basename>-NN, or use a custom path?
```

### Step 3: Check post-checkout Hook

Read `.git/hooks/post-checkout` (or `.husky/post-checkout`) if it exists.
If it handles worktree setup adequately (uv sync, yarn install, env copy),
skip to Step 4.

If missing or incomplete, detect project type and propose the appropriate
template from the **Hook Templates** section below. Present to the user for
approval before writing. The hook must always ensure `.codex` exists.

### Step 4: Create the Worktree

```bash
$HOME/.codex/skills/dev10x-git-worktree/scripts/create-worktree.sh \
  <worktree-path> <branch-name> [repo-root]
```

- Omit `repo-root` when already inside the target repo.
- Pass `repo-root` when the CWD differs from the target repo.

The `post-checkout` hook fires automatically after this script runs.

### Step 5: Hand Off — STOP HERE

Codex sessions have a fixed workspace. Continuing in the original
workspace makes follow-up git commands and skills run against the wrong
repository path unless every command is manually overridden.

Print this message and **stop — do not continue with ticket workflow steps**:

```
Worktree ready
   Path:   <worktree-path>
   Branch: <branch-name>

Close this session and open a new one in the worktree:

  cd <worktree-path> && codex

Copy the command above, close this session, then paste it in your terminal.
The new session will have the correct CWD and all skills will work normally.
```

---

## Hook Templates

Templates for projects that lack a `post-checkout` hook.

### All hooks: use the all-zeros SHA guard

`git worktree add` passes `0000000000000000000000000000000000000000` as `$1`
(previous HEAD) when creating a new worktree. Guard on this value — do NOT
use `[ -f .git ]` which fires on every branch checkout inside any worktree:

```sh
if [ "$1" = "0000000000000000000000000000000000000000" ]; then
    # new worktree — run setup
fi
```

### Detect project type

| Check | Template |
|---|---|
| `uv.lock` or `pyproject.toml` exists | Template A (Python/uv) |
| `package.json` + `.husky/` directory | Template B (Node + Husky) |
| `package.json` without Husky | Template C (Node, no Husky) |

A project can match multiple templates (e.g. Django + SvelteKit). Apply all.

### Hook file location

| Condition | Write to |
|---|---|
| Husky present (`prepare` script or `.husky/` dir) | `.husky/post-checkout` (tracked) |
| No Husky | `.git/hooks/post-checkout` (untracked, local only) |

Husky overwrites `.git/hooks/` on every `yarn/npm install`. Writing to
`.git/hooks/post-checkout` in a Husky project means changes are silently lost.

### Template A: Python/uv

Source: [`templates/post-checkout-python-uv.sh`](./templates/post-checkout-python-uv.sh)

Copies `.env`, `development.secrets.env`, `.codex/`, `.idea/`,
and runs `uv sync`.

### Template B: Node.js + Husky (write to `.husky/post-checkout`)

Source: [`templates/post-checkout-node-husky.sh`](./templates/post-checkout-node-husky.sh)

Copies `.env`, `.codex/`, and runs `yarn install --frozen-lockfile`.

For monorepos (yarn workspaces), run `yarn install --frozen-lockfile` from
the repo root — this installs all workspace packages in one pass.

### Template C: Node.js without Husky (write to `.git/hooks/post-checkout`)

Source: [`templates/post-checkout-node.sh`](./templates/post-checkout-node.sh)

Copies `.env`, `.codex/`, and runs `yarn install` or `npm ci`.

Make executable: `chmod +x .git/hooks/post-checkout`

**Never symlink `node_modules`** — a symlink means `yarn add/remove` in any
worktree mutates the shared directory. Always run `yarn install --frozen-lockfile`
(fast via Yarn's hardlink cache).

---

## Cleanup

Manual removal:

```bash
git worktree remove <path>
git worktree remove --force <path>  # if dirty
git worktree list                   # list all worktrees
```
