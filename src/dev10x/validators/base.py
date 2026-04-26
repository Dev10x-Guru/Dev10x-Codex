"""Validator protocol for Bash command validation.

Two hook integration points:

  PreToolUse  → should_run() + validate()  — block before execution
  PermissionDenied → should_run() + correct() — guide after auto-mode denial

The correct() method is optional. Validators that implement it can
provide retry-with-guidance responses for the PermissionDenied hook.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from dev10x.domain import HookAllow, HookInput, HookResult, HookRetry


@runtime_checkable
class Validator(Protocol):
    name: str

    def should_run(self, inp: HookInput) -> bool:
        """Fast predicate — return False to skip this validator entirely."""
        ...

    def validate(self, inp: HookInput) -> HookResult | HookAllow | None:
        """Return HookResult to block, HookAllow to auto-approve, None for no opinion."""
        ...


@runtime_checkable
class Corrector(Protocol):
    """Optional extension for validators that support PermissionDenied corrections."""

    def correct(self, inp: HookInput) -> HookRetry | None:
        """Return HookRetry to suggest retry with corrective guidance, None otherwise."""
        ...
