from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

import click

_DEBUG = os.environ.get("HOOK_DEBUG", "") != ""


@click.group()
def hook() -> None:
    """Hook entry points (validate-bash, validate-edit, plan-sync, session)."""


@hook.command(name="validate-bash")
def validate_bash() -> None:
    """Validate Bash commands via the unified validator registry.

    Reads JSON from stdin, dispatches to registered validators.
    Exit codes: 0=allow, 2=block.
    """
    from dev10x.domain import HookInput
    from dev10x.validators import get_validators

    inp = HookInput.from_stdin()
    if inp.tool_name != "Bash":
        sys.exit(0)
    if not inp.command:
        sys.exit(0)

    for validator in get_validators():
        try:
            if validator.should_run(inp=inp):
                result = validator.validate(inp=inp)
                if result is not None:
                    result.emit()
        except Exception:
            if _DEBUG:
                print(
                    f"[HOOK_DEBUG] {validator.name} raised:",
                    file=sys.stderr,
                )
                traceback.print_exc(file=sys.stderr)
            continue

    sys.exit(0)


@hook.group(name="plan")
def plan() -> None:
    """Plan synchronization commands."""


@plan.command(name="sync")
def plan_sync() -> None:
    """Sync task state from stdin (PostToolUse hook mode)."""
    from dev10x.hooks.task_plan_sync import cmd_hook

    cmd_hook()


@plan.command(name="summary")
def plan_summary() -> None:
    """Read plan YAML, output JSON summary."""
    from dev10x.hooks.task_plan_sync import cmd_json_summary

    cmd_json_summary()


@plan.command(name="set-context")
@click.argument("pairs", nargs=-1, required=True)
def plan_set_context(pairs: tuple[str, ...]) -> None:
    """Store plan-level context metadata (K=V pairs, dot-paths supported)."""
    from dev10x.hooks.task_plan_sync import cmd_set_context

    cmd_set_context(args=list(pairs))


@plan.command(name="archive")
def plan_archive() -> None:
    """Archive completed plan to .claude/session/archive/."""
    from dev10x.hooks.task_plan_sync import cmd_archive

    cmd_archive()


@hook.command(name="permission-denied")
def permission_denied() -> None:
    """Handle PermissionDenied events via the validator registry.

    Reads JSON from stdin, dispatches to validators that implement
    correct(). Returns retry=true with corrective guidance when a
    validator recognizes the denied command.
    Exit codes: 0 always (retry decision is in JSON output).
    """
    from dev10x.domain import HookInput
    from dev10x.validators import get_validators
    from dev10x.validators.base import Corrector

    inp = HookInput.from_stdin()
    if not inp.command:
        sys.exit(0)

    for validator in get_validators():
        try:
            if not validator.should_run(inp=inp):
                continue
            if not isinstance(validator, Corrector):
                continue
            result = validator.correct(inp=inp)
            if result is not None:
                result.emit()
        except Exception:
            if _DEBUG:
                print(
                    f"[HOOK_DEBUG] {validator.name} correct() raised:",
                    file=sys.stderr,
                )
                traceback.print_exc(file=sys.stderr)
            continue

    sys.exit(0)


@hook.command(name="validate-edit")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
)
@click.option("--debug", is_flag=True)
def validate_edit(config_path: Path | None, debug: bool) -> None:
    """Validate Edit/Write tool calls against sensitive file rules.

    Reads JSON from stdin, checks file paths against rules.
    Exit codes: 0=allow, 2=block.
    """
    import json

    from dev10x.hooks.edit_validator import validate_edit_write

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    validate_edit_write(
        data=data,
        yaml_path=config_path,
        debug=debug,
    )


@hook.group(name="session")
def session() -> None:
    """Session lifecycle commands."""


@session.command(name="reload")
def session_reload_cmd() -> None:
    """Reload prior session state (SessionStart hook)."""
    from dev10x.hooks.session import session_reload

    session_reload()


@session.command(name="compact")
def session_compact_cmd() -> None:
    """Inject context summary before compaction (PreCompact hook)."""
    from dev10x.hooks.session import context_compact

    context_compact()


@session.command(name="tmpdir")
def session_tmpdir_cmd() -> None:
    """Create session scratch directory and install mktmp.sh (SessionStart hook)."""
    from dev10x.hooks.session import session_tmpdir

    session_tmpdir()


@session.command(name="guidance")
def session_guidance_cmd() -> None:
    """Output session-guidance.md as additionalContext (SessionStart hook)."""
    from dev10x.hooks.session import session_guidance

    session_guidance()


@session.command(name="git-aliases")
def session_git_aliases_cmd() -> None:
    """Check git branch-comparison aliases and report status (SessionStart hook)."""
    from dev10x.hooks.session import session_git_aliases

    session_git_aliases()


@session.command(name="migrate-permissions")
def session_migrate_permissions_cmd() -> None:
    """Migrate stale plugin permission rules to current version (SessionStart hook)."""
    from dev10x.hooks.session import session_migrate_permissions

    session_migrate_permissions()


@session.command(name="persist")
def session_persist_cmd() -> None:
    """Persist session state to disk for next-session reload (SessionStop hook)."""
    from dev10x.hooks.session import session_persist

    session_persist()


@session.command(name="goodbye")
def session_goodbye_cmd() -> None:
    """Output goodbye message with community link and resume hint (SessionStop hook)."""
    from dev10x.hooks.session import session_goodbye

    session_goodbye()


@hook.group(name="skill")
def skill() -> None:
    """Skill lifecycle commands."""


@skill.command(name="tmpdir")
def skill_tmpdir_cmd() -> None:
    """Create scratch directory for skill (PreToolUse hook)."""
    from dev10x.hooks.skill import skill_tmpdir

    skill_tmpdir()


@skill.command(name="metrics")
def skill_metrics_cmd() -> None:
    """Append skill invocation metric to JSONL file (PostToolUse hook)."""
    from dev10x.hooks.skill import skill_metrics

    skill_metrics()


@hook.command(name="ruff-format")
def ruff_format_cmd() -> None:
    """Auto-format Python files with ruff after Edit/Write (PostToolUse hook)."""
    from dev10x.hooks.skill import ruff_format

    ruff_format()
