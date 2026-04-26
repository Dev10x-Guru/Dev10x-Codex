#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""Thin shim — delegates to dev10x.skills.permission.clean_project_files."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from dev10x.skills.permission.clean_project_files import *  # noqa: F401, F403
from dev10x.skills.permission.clean_project_files import main

if __name__ == "__main__":
    sys.exit(main())
