# Code Sharing Across Execution Contexts

Acceptable patterns for exposing code to multiple execution contexts:
MCP servers, standalone scripts, and shared libraries.

## Overview

Different parts of the codebase run in distinct execution environments:
- MCP servers execute with project sys.path pre-configured
- Standalone PEP 723 scripts run independently from anywhere
- Shared libraries must be designed for one or both contexts

Each context has different constraints. This guide documents patterns
that are architecturally sound, and helps reviewers distinguish intentional
code sharing from accidental duplication or dead code.

## Pattern 1: MCP Server Imports from lib/

**Execution context**: MCP servers (`servers/*.py`)

**Constraint**: Servers run under Claude Code with sys.path configured.
They can reliably import from the project's `lib/` directory.

**Pattern**:
```python
# lib/credentials.py
def lookup(service: str, key: str) -> str:
    """Shared credential retrieval for MCP servers."""
    ...

# servers/gh_server.py
from lib.credentials import lookup

@server.tool()
async def authenticate():
    token = lookup("github", "api_token")
    ...
```

**Reviewer guidance**:
- Functions in `lib/` used only by servers (not directly imported elsewhere)
are NOT "dead code."
- Grep from the main codebase won't find these imports; verify by reading
  the server files themselves.
- This pattern is correct and should not be flagged.

## Pattern 2: Standalone Script Inlining

**Execution context**: Standalone PEP 723 scripts (files with `# /// script`)

**Constraint**: Standalone scripts are self-contained executables.
They cannot reliably import from `lib/` without sys.path manipulation.

**Pattern**:
```python
# /// script
# dependencies = ["requests"]

def _get_credential(service: str, key: str) -> str:
    """Inlined credential retrieval for standalone execution."""
    import platform
    if platform.system() == "Darwin":
        # macOS: Keychain
        ...
    elif platform.system() == "Windows":
        # Windows: Credential Manager
        ...
    else:
        # Linux: secret-tool
        ...

result = _get_credential("github", "api_token")
```

**Reviewer guidance**:
- When PEP 723 scripts contain `_helper()` functions that duplicate
  logic from `lib/`, this is NOT code duplication — it's an architectural
  necessity.
- Standalone scripts must be self-contained to work from anywhere in the
  filesystem.
- Do NOT suggest refactoring inlined functions into `lib/` or shared imports.

## Pattern 3: Mixed Context – Shared Lib + Standalone Inlining

**Execution context**: Both MCP servers and standalone scripts need the
same cross-platform logic.

**Pattern**:
1. Implement shared logic in `lib/credentials.py` (for MCP servers)
2. Inline the same logic in standalone scripts (for self-containment)
3. Keep implementations identical to prevent divergence

```python
# lib/credentials.py (imported by servers)
def lookup(service: str, key: str) -> str:
    if platform.system() == "Darwin":
        # macOS implementation
        ...
    elif platform.system() == "Windows":
        # Windows implementation
        ...
    else:
        # Linux implementation
        ...

# scripts/install-ghcli.py (PEP 723 — inlined)
# /// script
def _lookup(service: str, key: str) -> str:  # Same logic, inline
    import platform
    if platform.system() == "Darwin":
        # macOS implementation (identical to lib/credentials.py)
        ...
    # ...rest identical
```

**Reviewer guidance**:
- Identical implementations across `lib/` and standalone scripts are
  intentional, not duplication.
- When reviewing changes to cross-platform logic, verify BOTH `lib/`
  and standalone versions are updated together.
- Use diff tools to confirm implementations remain synchronized.

## Anti-Pattern: Wrapper Scripts with Shared Backend

❌ **Do NOT use**:
```bash
# bin/get-cred.sh (wrapper)
source lib/credentials.sh  # Tries to source from lib/
_lookup "$@"
```

**Problems**:
1. Adds indirection without clear benefit
2. Breaks self-containment of standalone scripts
3. Confuses code ownership (where does the logic live?)
4. Fails when lib/ is not in the shell's search path

**Instead**: Choose inline (Pattern 2) or MCP import (Pattern 1) based
on execution context.

## Trade-Off Matrix

| Pattern | Works for MCP? | Self-contained? | Code reuse? | Maintenance |
|---------|---|---|---|---|
| lib/ import | ✅ Yes | ❌ No | ✅ High | ✅ Single source |
| Standalone inline | ❌ No | ✅ Yes | ❌ Low | ⚠️ Sync needed |
| Mixed (lib + inline) | ✅ Yes | ✅ Yes | ✅ Medium | ⚠️ Requires sync |
| Wrapper script | ⚠️ Maybe | ❌ No | ✅ Medium | ❌ Fragile |

## Decision Guide

**Choose Pattern 1 (lib/ import)** when:
- Code is only used by MCP servers
- Single implementation is acceptable
- Cross-platform logic doesn't need standalone execution

**Choose Pattern 2 (standalone inline)** when:
- Code is only used by self-contained scripts
- Scripts run from CI, command line, or user machines
- No MCP server needs the logic

**Choose Pattern 3 (mixed)** when:
- Both MCP servers and standalone scripts need the same logic
- Cross-platform support is critical
- You can commit to keeping implementations synchronized

**Never choose wrapper scripts** unless the delegation is the primary intent
(e.g., a wrapper that adds preprocessing or validation, not just forwarding).

## Verification for Reviewers

When code appears duplicated or unused:

1. **Identify execution contexts**: Does this code serve MCP servers,
   standalone scripts, or both?

2. **Check for intentional patterns**: Read the actual implementations
   (don't rely on grep). Are they identical? Do they follow one of the
   three valid patterns?

3. **Verify synchronization**: If Pattern 3 is used, confirm both
   implementations were updated together.

4. **Flag only genuine issues**:
   - Implementations diverging (Pattern 3 drift)
   - Unused code in wrong context (e.g., lib/ function only called from
     one script)
   - Anti-patterns (wrapper scripts)
   - Do NOT flag: code duplication in Patterns 1, 2, or 3 (intentional)
