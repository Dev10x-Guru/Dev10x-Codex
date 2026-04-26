---
name: Dev10x-db
description: Safe database query planning for Claude Code. When querying any database, ensures schema-first construction and read-only safety so queries are accurate and never modify production data.
---

# Database Query Planning

Schema-first query construction for safe, accurate database queries.

## Query Planning Workflow

Before writing any SQL:

1. **Load schema context** — search for schema memory files and
   project-specific db skills (see Context Discovery below)
2. **Verify table and column names** — never guess; cross-reference
   the schema files or run an `information_schema` query
3. **Write the query** — use verified names only
4. **Execute via engine-specific skill** — delegate to the appropriate
   execution layer (e.g., `Dev10x:db-psql` for PostgreSQL)

## Context Discovery Convention

Generic skills discover project-specific database context by searching
for these resources (in order):

1. **Schema memory files**: `memory/db-*-schema.md` in the active
   project's memory directory
2. **Project db skills**: any skill matching `*:db` pattern (e.g.,
   `tt:db`, `acme:db`) — these contain project-specific aliases,
   common queries, and DSN configuration
3. **CLAUDE.md database sections**: database connection info or
   references in project instructions

Always load available context before constructing queries.

## Safety Rules

1. **SELECT only** — never run INSERT, UPDATE, DELETE, DROP, ALTER,
   CREATE, TRUNCATE, or other write operations through automated tools
2. **Non-SELECT queries**: print the raw SQL and tell the user to run
   it manually. Never attempt workarounds or bypass safety checks
3. **Use timeouts** — all queries should have statement timeouts to
   prevent runaway execution
4. **Limit large result sets** — use LIMIT on exploratory queries;
   never `SELECT *` on production tables without a WHERE clause

## Anti-Patterns

| Anti-Pattern | What to Do Instead |
|---|---|
| Guess table/column names | Load schema files first, or query `information_schema.tables` / `information_schema.columns` |
| Retry with random name variations | Stop and look up the correct name in schema docs |
| `SELECT *` on large tables | Use specific columns and LIMIT |
| Inline DSN strings in prompts | Use the engine-specific skill's wrapper script |
| Skip schema check for "simple" queries | Always verify — even common tables have gotchas |

## Schema Memory File Format

Project-specific schema files should follow this template and be
placed at `memory/db-<name>-schema.md`:

```markdown
# <Project> Database Schema — <database-name>

## <Domain Group>

| Table | Key Columns | Notes |
|-------|-------------|-------|
| `table_name` | id, name, status, foreign_key_id | Brief purpose |

## Common Gotchas

- Table `actual_name` (NOT `guessed_name`)
- Money fields store JSON: `field::jsonb->>'amount'`

## Common Queries

### Find X by Y
\```sql
SELECT ... FROM ... WHERE ...
\```
```

## Integration

This skill provides query planning guidance. Actual query execution
is handled by engine-specific skills:

- **`Dev10x:db-psql`** — PostgreSQL via psql wrapper
