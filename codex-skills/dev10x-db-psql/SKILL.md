---
name: Dev10x-db-psql
description: Safe read-only psql wrapper for Claude Code. Provides db.sh with SQL validation hook so database queries are safe and auditable. Configure databases in databases.yaml with env var or keyring backends.
---

# PostgreSQL Query Execution

Safe read-only psql wrapper with two layers of protection:

1. **PreToolUse hook** (`hooks/scripts/validate-sql.py`) — blocks
   non-SELECT queries before they reach psql
2. **Connection-level safety** — `SET default_transaction_read_only = on`
   and read-only DB users / read-replica endpoints

## How to Use

```bash
$HOME/.codex/skills/Dev10x-db-psql/scripts/db.sh <database> "<SQL>"
$HOME/.codex/skills/Dev10x-db-psql/scripts/db.sh <database> -f <file>
$HOME/.codex/skills/Dev10x-db-psql/scripts/db.sh --list
```

## Common Mistakes (DO NOT do these)

```bash
# WRONG — -c flag is not supported, triggers safety hook block
db.sh pp -c "SELECT ..."

# WRONG — stdin piping is not supported
echo "SELECT ..." | db.sh pp

# CORRECT — SQL as second positional argument in quotes
db.sh pp "SELECT ..."
```

## Setup

### 0. Prerequisites

- `psql` (PostgreSQL client)
- `uv` -- Python package manager used by `parse-databases.py`
  (`pip install uv` or `brew install uv`)
- `secret-tool` (libsecret-tools) -- only needed for `keyring` backend

### 1. Configure databases

Create `databases.yaml` in one of the discovered locations. The
db.sh script searches for config files in this order:

1. `$DB_CONFIG` environment variable (explicit path)
2. Own skill directory (`skills/db-psql/databases.yaml`)
3. `$HOME/.codex/memory/databases.yaml` (global, user-level)
4. Sibling plugin skill directories (`skills/*/databases.yaml`)
5. User skill directories (`$HOME/.codex/skills/*/databases.yaml`)

Example YAML with both backends:

```yaml
databases:
  my-prod:
    label: "My App production (read-only)"
    aliases: [mp]
    backend: env
    env_var: DB_MY_PRODUCTION_RO

  my-staging:
    label: "My App staging (read-only)"
    aliases: [ms]
    backend: keyring
    keyring_service: claude-db
    keyring_account: my-staging
```

### 2. Set DSN

Configure the connection string using the backend specified in
`databases.yaml`:

**env backend** — set the environment variable in your shell profile:

```bash
export DB_MY_PRODUCTION_RO="postgres://user:pass@host:5432/db"
```

**keyring backend** — store the DSN in the system keyring:

```bash
secret-tool store --label "claude-db my-staging" \
  service claude-db account my-staging
```

### 3. Safety hook (auto-registered)

The SQL validation hook (`validate-sql.py`) is automatically
registered via `hooks/hooks.json` when this plugin is installed.
No manual configuration needed.

## Safety Rules

1. **SELECT only** — the hook rejects INSERT, UPDATE, DELETE, DROP,
   ALTER, CREATE, TRUNCATE, and other write operations
2. **Read-only connections** — DSNs should use read-only DB users or
   read-replica endpoints
3. **30-second timeout** — prevents runaway queries
4. **Non-SELECT queries**: print the raw SQL and tell the user to run
   it manually. Never attempt workarounds.

## When a Query Is Blocked

If the PreToolUse hook blocks a non-SELECT query, tell the user:

> This query modifies data and cannot be run through the read-only
> tool. Here's the SQL to run manually:
>
> ```sql
> <the blocked query>
> ```

Never attempt to bypass the safety checks.

## Integration

- Uses **`Dev10x:db`** for query planning and schema discovery
- Project-specific skills (e.g., `tt:db`) provide `databases.yaml`
  with aliases and schema references
