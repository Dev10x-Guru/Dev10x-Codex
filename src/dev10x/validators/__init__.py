"""Bash command validators for Claude Code PreToolUse hooks.

Single-dispatcher architecture: one Python process validates all Bash
commands by iterating a registry of Validator implementations. Each
validator has a fast `should_run` predicate and a `validate` method.

Ordering matters: allow-validators run before deny-validators so safe
patterns get auto-approved before a deny-validator would block them.

Validators are lazily imported — only loaded when the registry is
first accessed via get_validators(). This avoids paying the import
cost of all 8 modules at module-level on every hook invocation.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dev10x.validators.base import Validator

_VALIDATOR_SPECS: list[tuple[str, str]] = [
    ("dev10x.validators.safe_subshell", "SafeSubshellValidator"),
    ("dev10x.validators.command_substitution", "CommandSubstitutionValidator"),
    ("dev10x.validators.prefix_friction", "PrefixFrictionValidator"),
    ("dev10x.validators.execution_safety", "ExecutionSafetyValidator"),
    ("dev10x.validators.skill_redirect", "SkillRedirectValidator"),
    ("dev10x.validators.commit_jtbd", "CommitJtbdValidator"),
    ("dev10x.validators.sql_safety", "SqlSafetyValidator"),
    ("dev10x.validators.pr_base", "PrBaseValidator"),
]

_validators: list[Validator] | None = None


def get_validators() -> list[Validator]:
    global _validators
    if _validators is None:
        from dev10x.validators.base import Validator as V

        _validators = []
        for module_path, class_name in _VALIDATOR_SPECS:
            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
            instance = cls()
            assert isinstance(instance, V), f"{class_name} does not implement Validator"
            _validators.append(instance)
    return _validators


__all__ = ["get_validators"]
