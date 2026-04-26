"""Session hook logic — reload prior state and compact context.

SessionReloader: reads persisted state file and plan file, produces
additionalContext for the agent on session start.

ContextCompactor: injects structured context summary before compaction
so the agent recovers gracefully after context window compression.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dev10x.domain.git_context import GitContext

_git = GitContext()


def _get_toplevel() -> str | None:
    return _git.toplevel


def _get_branch() -> str:
    return _git.branch


def _run_git(*args: str) -> str:
    try:
        return GitContext.run(*args)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, OSError):
        return {}


def _read_plan_summary(*, toplevel: str) -> dict[str, Any]:
    from dev10x.hooks.task_plan_sync import get_plan_path, read_plan

    plan_path = get_plan_path(toplevel=toplevel)
    return read_plan(plan_path=plan_path)


def _escape_for_json(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def session_reload() -> None:
    toplevel = _get_toplevel()
    if not toplevel:
        sys.exit(0)

    project_hash = hashlib.md5(toplevel.encode()).hexdigest()
    state_dir = Path.home() / ".claude" / "projects" / "_session_state"
    state_file = state_dir / f"{project_hash}.json"
    plan_file = Path(toplevel) / ".claude" / "session" / "plan.yaml"

    has_state = state_file.exists()
    has_plan = plan_file.exists()

    if not has_state and not has_plan:
        sys.exit(0)

    context = ""

    if has_state:
        state = _read_json(path=state_file)
        timestamp = state.get("timestamp", "")
        if not timestamp:
            state_file.unlink(missing_ok=True)
        else:
            try:
                file_dt = datetime.fromisoformat(timestamp)
                now_dt = datetime.now(UTC)
                age_hours = int((now_dt - file_dt).total_seconds() / 3600)
            except (ValueError, TypeError):
                age_hours = 0

            stale_flag = f" (STALE — {age_hours}h old, may be outdated)" if age_hours > 24 else ""

            branch = state.get("branch", "unknown")
            worktree = state.get("worktree", "")
            session_id = state.get("session_id", "")
            modified = state.get("modified_files", [])
            staged = state.get("staged_files", [])
            commits = state.get("recent_commits", [])

            modified_str = "\n".join(f"- {f}" for f in modified) if modified else "none"
            staged_str = "\n".join(f"- {f}" for f in staged) if staged else "none"
            commits_str = "\n".join(commits) if commits else "none"

            context = f"Prior session state detected{stale_flag}:\n- Branch: {branch}"
            if worktree:
                context += f"\n- Worktree: {worktree}"
            context += f"\n- Last active: {timestamp}"
            context += f"\n- Session ID: {session_id}"
            context += f"\n\nModified files:\n{modified_str}"
            context += f"\n\nStaged files:\n{staged_str}"
            context += f"\n\nRecent commits:\n{commits_str}"
            context += f"\n\nResume prior session with: claude --resume {session_id}"

    if has_plan:
        plan = _read_plan_summary(toplevel=toplevel)
        plan_meta = plan.get("plan", {})
        plan_status = plan_meta.get("status", "unknown")
        plan_branch = plan_meta.get("branch", "unknown")
        plan_synced = plan_meta.get("last_synced", "unknown")
        tasks = plan.get("tasks", [])
        task_count = len(tasks)
        completed_count = sum(1 for t in tasks if t.get("status") == "completed")
        pending_tasks = [
            f"  - [{t.get('status')}] #{t.get('id')} {t.get('subject')}"
            for t in tasks
            if t.get("status") not in ("completed", "deleted")
        ]

        if context:
            context += "\n\n"

        context += f"Persisted plan detected ({completed_count}/{task_count} tasks completed):"
        context += f"\n- Plan branch: {plan_branch}"
        context += f"\n- Plan status: {plan_status}"
        context += f"\n- Last synced: {plan_synced}"

        if pending_tasks:
            context += "\n- Remaining tasks:\n" + "\n".join(pending_tasks)

        plan_context = plan_meta.get("context", {})
        work_type = plan_context.get("work_type")
        if work_type:
            context += f"\n- Work type: {work_type}"

        tickets = plan_context.get("tickets", [])
        if tickets:
            context += (
                f"\n- Tickets: {', '.join(tickets) if isinstance(tickets, list) else tickets}"
            )

        routing = plan_context.get("routing_table", {})
        if routing and isinstance(routing, dict):
            routing_lines = [f"  {k} → {v}" for k, v in routing.items()]
            context += "\n- Skill routing:\n" + "\n".join(routing_lines)

        if plan_status == "completed":
            context += "\n- All tasks completed. Plan can be archived."

    if not context:
        sys.exit(0)

    escaped = _escape_for_json(s=context)
    output = (
        '{"hookSpecificOutput":{"hookEventName":"SessionStart",'
        f'"additionalContext":"{escaped}"}}}}'
    )
    print(output)

    if has_state:
        state_file.unlink(missing_ok=True)


def context_compact() -> None:
    toplevel = _get_toplevel()
    if not toplevel:
        sys.exit(0)

    branch = _get_branch()
    worktree_name = ""
    git_file = Path(toplevel) / ".git"
    if git_file.is_file():
        worktree_name = Path(toplevel).name

    modified = _run_git("diff", "--name-only").splitlines()[:20]
    staged = _run_git("diff", "--cached", "--name-only").splitlines()[:20]
    untracked = _run_git("ls-files", "--others", "--exclude-standard").splitlines()[:10]
    recent_commits = _run_git("log", "--oneline", "-5")

    plugin_root = Path(__file__).parents[3]
    essentials_file = plugin_root / ".claude" / "rules" / "essentials.md"
    essentials = ""
    if essentials_file.exists():
        essentials = essentials_file.read_text()

    summary = f"# Post-Compaction Context Recovery\n\n## Git State\n- **Branch:** {branch}"
    if worktree_name:
        summary += f"\n- **Worktree:** {worktree_name}"
    summary += f"\n- **Working directory:** {toplevel}"

    def format_files(files: list[str]) -> str:
        return "\n".join(f"- {f}" for f in files if f)

    if modified:
        summary += f"\n\n### Modified files (unstaged)\n{format_files(modified)}"
    if staged:
        summary += f"\n\n### Staged files\n{format_files(staged)}"
    if untracked:
        summary += f"\n\n### Untracked files\n{format_files(untracked)}"
    if recent_commits:
        summary += f"\n\n### Recent commits\n```\n{recent_commits}\n```"
    if essentials:
        summary += f"\n\n## Essential Conventions (from essentials.md)\n{essentials}"

    plan_file = Path(toplevel) / ".claude" / "session" / "plan.yaml"
    if plan_file.exists():
        plan = _read_plan_summary(toplevel=toplevel)
        plan_meta = plan.get("plan", {})
        plan_branch = plan_meta.get("branch", "unknown")
        plan_status = plan_meta.get("status", "unknown")
        plan_context = plan_meta.get("context", {})
        work_type = plan_context.get("work_type", "unknown")
        tasks = plan.get("tasks", [])

        task_lines = []
        for t in tasks:
            line = f"- [{t.get('status')}] #{t.get('id')} {t.get('subject')}"
            meta = t.get("metadata", {})
            if meta.get("type"):
                line += f" ({meta['type']})"
            if meta.get("skills"):
                line += f" → {', '.join(meta['skills'])}"
            task_lines.append(line)

        if task_lines:
            summary += "\n\n## Persisted Plan State"
            summary += f"\n- **Branch:** {plan_branch}"
            summary += f"\n- **Plan status:** {plan_status}"
            summary += f"\n- **Work type:** {work_type}"
            summary += "\n\n### Tasks\n" + "\n".join(task_lines)

        routing = plan_context.get("routing_table", {})
        if routing and isinstance(routing, dict):
            routing_lines = [f"{k} → {v}" for k, v in routing.items()]
            summary += "\n\n### Skill Routing Table (from plan context)\n" + "\n".join(
                routing_lines
            )
        else:
            recovery_file = plugin_root / "references" / "compaction-recovery.md"
            if recovery_file.exists():
                summary += f"\n\n{recovery_file.read_text()}"

        gathered = plan_context.get("gathered_summary")
        if gathered:
            summary += f"\n\n### Gathered Context (from Phase 2)\n{gathered}"

        summary += (
            "\n\n> Reconstructed from persisted plan file. Use TaskList to verify\n"
            "> current session state. If tasks are missing, recreate them from\n"
            "> this list. Use the routing table above for all shipping actions."
        )

    escaped = _escape_for_json(s=summary)
    print(f'{{"hookSpecificOutput":{{"systemMessage":"{escaped}"}}}}')


def session_tmpdir() -> None:
    """Create session scratch directory and install mktmp.sh (SessionStart hook)."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    session_id = data.get("session_id") or ""
    if not session_id:
        sys.exit(0)

    Path(f"/tmp/claude/{session_id}").mkdir(parents=True, exist_ok=True)

    plugin_root = Path(__file__).parents[3]
    mktmp_src = plugin_root / "bin" / "mktmp.sh"
    dest_bin = Path("/tmp/claude/bin")
    dest_bin.mkdir(parents=True, exist_ok=True)

    if mktmp_src.exists():
        dest = dest_bin / "mktmp.sh"
        shutil.copy2(src=mktmp_src, dst=dest)
        dest.chmod(0o755)


def session_guidance() -> None:
    """Output session-guidance.md as additionalContext (SessionStart hook)."""
    plugin_root = Path(__file__).parents[3]
    guidance_file = plugin_root / "hooks" / "scripts" / "session-guidance.md"

    if not guidance_file.exists():
        sys.exit(0)

    content = guidance_file.read_text()
    escaped = _escape_for_json(s=content)
    print(
        '{"hookSpecificOutput":{"hookEventName":"SessionStart",'
        f'"additionalContext":"{escaped}"}}}}'
    )


def session_git_aliases() -> None:
    """Check git branch-comparison aliases and report status (SessionStart hook)."""
    aliases = [
        "develop-log",
        "develop-diff",
        "develop-rebase",
        "autosquash-develop",
        "development-log",
        "development-diff",
        "development-rebase",
        "autosquash-development",
        "trunk-log",
        "trunk-diff",
        "trunk-rebase",
        "autosquash-trunk",
        "main-log",
        "main-diff",
        "main-rebase",
        "autosquash-main",
        "master-log",
        "master-diff",
        "master-rebase",
        "autosquash-master",
    ]

    missing = []
    present = []
    for alias in aliases:
        if _run_git("config", "--get", f"alias.{alias}"):
            present.append(alias)
        else:
            missing.append(alias)

    if not missing:
        print(f"Git aliases available: {' '.join(present)}")
        print("Use `git {base}-log`, `git {base}-diff`, `git {base}-rebase`")
        print("instead of $(git merge-base ...) to avoid permission prompts.")
    else:
        print(f"Git aliases missing: {' '.join(missing)}")
        if present:
            print(f"Git aliases available: {' '.join(present)}")
        print("Run the git-alias-setup skill (/Dev10x:git-alias-setup) to configure them.")


def _build_migration_replacements(
    *,
    plugin_root: Path,
    home: str,
) -> list[tuple[str, str]]:
    version_parent = plugin_root.parent
    current_abs = str(plugin_root) + "/"
    current_tilde = current_abs.replace(home, "~")

    replacements: list[tuple[str, str]] = []
    try:
        children = sorted(version_parent.iterdir())
    except OSError:
        return replacements

    for child in children:
        if not child.is_dir() or child == plugin_root:
            continue
        old_abs = str(child) + "/"
        old_tilde = old_abs.replace(home, "~")
        replacements.append((old_abs, current_abs))
        replacements.append((old_tilde, current_tilde))

    return replacements


def _migrate_rules(
    *,
    rules: list[str],
    replacements: list[tuple[str, str]],
) -> tuple[list[str], int]:
    migrated = 0
    result = []
    for rule in rules:
        new_rule = rule
        for old, new in replacements:
            if old in rule:
                new_rule = rule.replace(old, new)
                migrated += 1
                break
        result.append(new_rule)
    return result, migrated


def _deduplicate_rules(rules: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for rule in rules:
        if rule not in seen:
            seen.add(rule)
            deduped.append(rule)
    return deduped


def session_migrate_permissions() -> None:
    """Migrate stale plugin permission rules to current version (SessionStart hook).

    Only runs when installed via plugin cache (not --plugin-dir).
    """
    plugin_root = Path(__file__).parents[3]

    if "plugins/cache/" not in str(plugin_root):
        sys.exit(0)

    home_path = Path.home()
    home = str(home_path)
    replacements = _build_migration_replacements(plugin_root=plugin_root, home=home)
    if not replacements:
        sys.exit(0)

    settings_files = [
        f
        for f in [
            home_path / ".claude" / "settings.json",
            home_path / ".claude" / "settings.local.json",
        ]
        if f.exists()
    ]

    total_migrated = 0
    files_changed: list[str] = []

    for settings_file in settings_files:
        try:
            settings = json.loads(settings_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        permissions = settings.get("permissions", {})
        changed = False
        for key in ("allow", "deny"):
            raw = permissions.get(key, [])
            if not raw:
                continue
            new_rules, count = _migrate_rules(rules=raw, replacements=replacements)
            new_rules = _deduplicate_rules(rules=new_rules)
            total_migrated += count
            if count:
                permissions[key] = new_rules
                changed = True

        if changed:
            try:
                settings_file.write_text(json.dumps(settings, indent=2) + "\n")
            except OSError:
                continue
            files_changed.append(settings_file.name)

    if total_migrated > 0:
        files_str = ", ".join(files_changed)
        print(
            f"Migrated {total_migrated} stale permission rule(s) "
            f"to current plugin version in {files_str}"
        )


def session_persist() -> None:
    """Persist session state to disk for next-session reload (SessionStop hook)."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    session_id = data.get("session_id") or ""
    if not session_id:
        sys.exit(0)

    toplevel = _get_toplevel()
    if not toplevel:
        sys.exit(0)

    project_hash = hashlib.md5(toplevel.encode()).hexdigest()
    state_dir = Path.home() / ".claude" / "projects" / "_session_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_dir.chmod(0o700)
    state_file = state_dir / f"{project_hash}.json"

    branch = _run_git("rev-parse", "--abbrev-ref", "HEAD") or "unknown"

    worktree_name = ""
    git_file = Path(toplevel) / ".git"
    if git_file.is_file():
        worktree_name = Path(toplevel).name

    modified = _run_git("diff", "--name-only").splitlines()[:20]
    staged = _run_git("diff", "--cached", "--name-only").splitlines()[:20]
    recent_commits = _run_git("log", "--oneline", "-5").splitlines()

    has_plan = (Path(toplevel) / ".claude" / "session" / "plan.yaml").exists()

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    state: dict[str, Any] = {
        "session_id": session_id,
        "branch": branch,
        "worktree": worktree_name,
        "working_directory": toplevel,
        "timestamp": timestamp,
        "modified_files": modified,
        "staged_files": staged,
        "recent_commits": recent_commits,
        "has_plan": has_plan,
    }
    state_file.write_text(json.dumps(state, indent=2))


def session_goodbye() -> None:
    """Output goodbye message with community link and resume hint (SessionStop hook)."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}

    session_id = data.get("session_id") or ""

    url = "https://www.skool.com/Dev10x-1892"
    print()
    print("Thank you for using Dev10x. Join the community to get the most out of the plugin:")
    print(f"\033]8;;{url}\033\\{url}\033]8;;\033\\")

    if session_id:
        print()
        print("Resume this session with:")
        print(f"  claude --resume {session_id}")
