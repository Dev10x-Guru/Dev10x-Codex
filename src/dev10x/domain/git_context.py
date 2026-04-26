"""GitContext — lazy-cached git subprocess state.

Replaces duplicated get_toplevel(), get_branch(), _run_git()
calls scattered across session.py, task_plan_sync.py, and plan.py
with a single utility.
"""

from __future__ import annotations

import subprocess
from functools import cached_property


class GitContext:
    @cached_property
    def toplevel(self) -> str | None:
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    @cached_property
    def branch(self) -> str:
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "unknown"

    @staticmethod
    def run(*args: str) -> str:
        return subprocess.check_output(
            ["git", *args],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
