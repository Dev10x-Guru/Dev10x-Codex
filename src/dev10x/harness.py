from __future__ import annotations

import os
from enum import StrEnum

HARNESS_ENV_VAR = "DEV10X_HARNESS"


class Harness(StrEnum):
    CLAUDE = "claude"
    CODEX = "codex"


def current_harness() -> Harness:
    value = os.environ.get(HARNESS_ENV_VAR, "").strip().lower()
    return Harness.CLAUDE if value == Harness.CLAUDE else Harness.CODEX


def is_codex() -> bool:
    return current_harness() is Harness.CODEX
