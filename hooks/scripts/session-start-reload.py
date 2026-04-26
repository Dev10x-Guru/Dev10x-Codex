#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""SessionStart hook: thin shim delegating to dev10x.hooks.session.

All logic lives in src/dev10x/hooks/session.py.
"""

import sys

try:
    from dev10x.hooks.session import session_reload
except ImportError:
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))
    from dev10x.hooks.session import session_reload

if __name__ == "__main__":
    session_reload()
