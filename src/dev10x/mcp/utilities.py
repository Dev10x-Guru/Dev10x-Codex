"""Utility MCP tool implementations.

Extracted from cli_server.py — general-purpose utility tools
(mktmp, etc.) that don't belong to GitHub or Git domains.
"""

from __future__ import annotations

from typing import Any

from dev10x.mcp.subprocess_utils import run_script


def mktmp(
    *,
    namespace: str,
    prefix: str,
    ext: str = "",
    directory: bool = False,
) -> dict[str, Any]:
    mk_args: list[str] = []
    if directory:
        mk_args.append("-d")
    mk_args.extend([namespace, prefix])
    if ext and not directory:
        mk_args.append(ext)

    result = run_script("bin/mktmp.sh", *mk_args)

    if result.returncode != 0:
        return {"error": result.stderr.strip()}

    return {"path": result.stdout.strip()}
