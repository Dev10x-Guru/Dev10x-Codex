"""Cross-platform credential lookup from system keyring.

Linux:  secret-tool lookup service <svc> key <key>
macOS:  security find-generic-password -s <svc> -a <key> -w
"""

from __future__ import annotations

import subprocess
import sys


def _is_macos() -> bool:
    return sys.platform == "darwin"


def lookup(*, service: str, key: str) -> str:
    if _is_macos():
        cmd = ["security", "find-generic-password", "-s", service, "-a", key, "-w"]
    else:
        cmd = ["secret-tool", "lookup", "service", service, "key", key]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()
