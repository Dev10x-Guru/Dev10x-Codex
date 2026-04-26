#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""Merge permissions from worktree settings back into the main project.

Worktrees accumulate session-specific allow rules that the main project
never sees. This script collects stable, reusable permissions from all
worktrees of a project and merges them into the main project's
settings.local.json.

Session-specific entries (temp file hashes, specific ticket numbers,
one-off inline commands) are filtered out automatically.
"""

import json
import re
import sys
from pathlib import Path

import yaml

USERSPACE_CONFIG = (
    Path.home() / ".claude" / "skills" / "Dev10x:permission-maintenance" / "projects.yaml"
)
PLUGIN_CONFIG = (
    Path(__file__).resolve().parents[4] / "skills" / "permission-maintenance" / "projects.yaml"
)

NOISE_PATTERNS = [
    re.compile(r"\.[A-Za-z0-9]{8,}\.(txt|md|json)"),
    re.compile(r"/tmp/claude/[^/]+/[^/]+\.[A-Za-z0-9]{6,}"),
    re.compile(r"Bash\(if \["),
    re.compile(r"Bash\(then "),
    re.compile(r"Bash\(else "),
    re.compile(r"Bash\(fi\b"),
    re.compile(r"GROOM_SEQ_FILE="),
    re.compile(r'"[A-Z]+-\d+"'),
    re.compile(r"detect-tracker\.sh\s+\S"),
    re.compile(r"gh-issue-get\.sh\s+\d"),
    re.compile(r"gh-pr-detect\.sh\s+\d"),
    re.compile(r"generate-commit-list\.sh\s+\d"),
    re.compile(r"generate-commit-list\.sh\s+PLACEHOLDER"),
    re.compile(r"extract-session\.sh\s+"),
    re.compile(r"Bash\(bash -[nc] "),
    re.compile(r"Bash\(bash -c '"),
    re.compile(r"\.local/.*\.py\s+/tmp/"),
    re.compile(r"\s+2>&1"),
    re.compile(r'\.sh\)"?\s*$'),
    re.compile(r"git-push-safe\.sh\s+-u\s+origin\s+\S+/"),
    re.compile(r"Bash\(find "),
]

GENERALIZE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(detect-tracker\.sh)\s+[^:)]+"), r"\1"),
    (re.compile(r"(gh-issue-get\.sh)\s+[^:)]+"), r"\1"),
    (re.compile(r"(gh-pr-detect\.sh)\s+[^:)]+"), r"\1"),
    (re.compile(r"(generate-commit-list\.sh)\s+[^:)]+"), r"\1"),
    (re.compile(r"(extract-session\.sh)\s+[^:)]+"), r"\1"),
    (re.compile(r"(/tmp/claude/[^/]+/)[^/]+\.[A-Za-z0-9]{6,}\.(txt|md|json)"), r"\1**"),
    (re.compile(r"(\.[A-Za-z0-9]{8,})\.(txt|md|json)"), r"**"),
    (re.compile(r"(git reset --hard) origin/\S+"), r"\1"),
    (re.compile(r"(git reset --soft) [A-Fa-f0-9]{6,}"), r"\1"),
]


def generalize_permission(entry: str) -> str:
    for pattern, replacement in GENERALIZE_PATTERNS:
        entry = pattern.sub(replacement, entry)
    return entry


def find_config() -> Path:
    if USERSPACE_CONFIG.is_file():
        return USERSPACE_CONFIG
    if PLUGIN_CONFIG.is_file():
        return PLUGIN_CONFIG
    print("ERROR: No config found.", file=sys.stderr)
    sys.exit(1)


def load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def is_noise(entry: str) -> bool:
    return any(p.search(entry) for p in NOISE_PATTERNS)


def resolve_main_project(worktree_dir: Path) -> Path | None:
    git_file = worktree_dir / ".git"
    if not git_file.is_file():
        return None
    content = git_file.read_text().strip()
    if not content.startswith("gitdir:"):
        return None
    gitdir = content.split(":", 1)[1].strip()
    gitdir_path = Path(gitdir)
    if "/worktrees/" not in str(gitdir_path):
        return None
    main_git_dir = gitdir_path.parent.parent
    return main_git_dir.parent


def find_worktree_groups(roots: list[str]) -> dict[Path, list[Path]]:
    groups: dict[Path, list[Path]] = {}
    for root in roots:
        root_path = Path(root).expanduser()
        worktrees_dir = root_path / ".worktrees"
        if not worktrees_dir.is_dir():
            continue
        for wt_dir in sorted(worktrees_dir.iterdir()):
            if not wt_dir.is_dir():
                continue
            settings = wt_dir / ".claude" / "settings.local.json"
            if not settings.exists():
                continue
            main_project = resolve_main_project(wt_dir)
            if main_project is None:
                continue
            groups.setdefault(main_project, []).append(wt_dir)
    return groups


def load_permissions(settings_path: Path) -> dict:
    if not settings_path.exists():
        return {}
    with open(settings_path) as f:
        return json.load(f)


def extract_allow_set(data: dict) -> set[str]:
    return set(data.get("permissions", {}).get("allow", []))


def merge_permissions(
    *,
    main_project: Path,
    worktree_dirs: list[Path],
    dry_run: bool = False,
) -> tuple[int, list[str]]:
    main_settings = main_project / ".claude" / "settings.local.json"
    main_data = load_permissions(main_settings)
    main_allow = extract_allow_set(main_data)

    new_entries: set[str] = set()
    for wt_dir in worktree_dirs:
        wt_settings = wt_dir / ".claude" / "settings.local.json"
        wt_data = load_permissions(wt_settings)
        wt_allow = extract_allow_set(wt_data)
        new_entries |= wt_allow - main_allow

    generalized = {generalize_permission(e) for e in new_entries}
    generalized -= main_allow
    stable_entries = sorted(e for e in generalized if not is_noise(e))

    if not stable_entries:
        return 0, []

    messages = [f"  +{len(stable_entries)} permissions from {len(worktree_dirs)} worktrees"]
    for entry in stable_entries:
        messages.append(f"    + {entry}")

    if not dry_run:
        if "permissions" not in main_data:
            main_data["permissions"] = {}
        if "allow" not in main_data["permissions"]:
            main_data["permissions"]["allow"] = []

        allow_list = main_data["permissions"]["allow"]
        allow_list.extend(stable_entries)

        main_settings.parent.mkdir(parents=True, exist_ok=True)
        main_settings.write_text(json.dumps(main_data, indent=2) + "\n")

    return len(stable_entries), messages


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Merge worktree permissions back into main project settings",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be merged without modifying files",
    )
    args = parser.parse_args()

    config_path = find_config()
    print(f"Config: {config_path}")
    config = load_config(config_path)

    roots = config.get("roots", [])
    if not roots:
        print("No roots configured. Run update-paths.py --init first.")
        return 0

    groups = find_worktree_groups(roots)
    if not groups:
        print("No worktree groups found.")
        return 0

    if args.dry_run:
        print("(dry run — no files will be modified)\n")

    total_merged = 0
    projects_changed = 0

    for main_project, worktree_dirs in sorted(groups.items()):
        count, messages = merge_permissions(
            main_project=main_project,
            worktree_dirs=worktree_dirs,
            dry_run=args.dry_run,
        )
        if count > 0:
            print(f"\n{main_project}")
            for msg in messages:
                print(msg)
            total_merged += count
            projects_changed += 1
        else:
            print(f"\n{main_project} — up to date ({len(worktree_dirs)} worktrees)")

    if total_merged == 0:
        print("\nAll projects up to date.")
    else:
        verb = "Would merge" if args.dry_run else "Merged"
        print(f"\n{verb} {total_merged} permissions into {projects_changed} projects.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
