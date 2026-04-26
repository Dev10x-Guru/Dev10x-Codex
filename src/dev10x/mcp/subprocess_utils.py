"""Shared utilities for calling external scripts via subprocess."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


def get_plugin_root() -> Path:
    return Path(__file__).parents[3]


def run_script(
    script_path: str,
    *args: str,
    env_vars: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    plugin_root = get_plugin_root()
    full_path = plugin_root / script_path

    if not full_path.exists():
        raise FileNotFoundError(f"Script not found: {full_path}")

    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    return subprocess.run(
        [str(full_path), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def parse_key_value_output(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.strip().split("\n"):
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def parse_json_output(text: str) -> dict[str, Any]:
    return json.loads(text)
