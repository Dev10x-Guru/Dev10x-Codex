#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""Maintain Dev10x plugin permission settings across all projects.

Modes:
  - (default) Update versioned plugin cache paths to the latest version
  - --ensure-base: Add missing base permissions from projects.yaml
  - --generalize: Replace session-specific args with wildcard patterns

Config lookup order:
  1. ~/.claude/skills/Dev10x:permission-maintenance/projects.yaml (userspace)
  2. ${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/projects.yaml (plugin default)
"""

import argparse
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
PLUGIN_NAMES = r"(?:Dev10x|dev10x-claude)"
VERSION_PATTERN = re.compile(rf"(plugins/cache/)([^/]+)(/{PLUGIN_NAMES}/)(\d+\.\d+\.\d+)")


def extract_cache_publisher(plugin_cache: str) -> str | None:
    path = Path(plugin_cache).expanduser()
    parts = list(path.parts)
    for i, part in enumerate(parts):
        if part == "cache" and i >= 2 and parts[i - 1] == "plugins":
            if i + 1 < len(parts):
                return parts[i + 1]
    return None


def find_config() -> Path:
    if USERSPACE_CONFIG.is_file():
        return USERSPACE_CONFIG
    if PLUGIN_CONFIG.is_file():
        return PLUGIN_CONFIG
    print(
        f"ERROR: No config found. Create {USERSPACE_CONFIG}\nor ensure {PLUGIN_CONFIG} exists.",
        file=sys.stderr,
    )
    sys.exit(1)


def load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def detect_latest_version(cache_dir: Path) -> str | None:
    if not cache_dir.is_dir():
        return None
    versions = sorted(
        cache_dir.iterdir(),
        key=lambda p: _version_tuple(p.name),
    )
    return versions[-1].name if versions else None


def _version_tuple(version: str) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in version.split("."))
    except ValueError:
        return (0,)


def find_settings_files(
    roots: list[str],
    *,
    include_user: bool,
) -> list[Path]:
    files: list[Path] = []
    if include_user:
        user_settings = Path.home() / ".claude" / "settings.local.json"
        if user_settings.exists():
            files.append(user_settings)

    project_settings_dir = Path.home() / ".claude" / "projects"
    if project_settings_dir.is_dir():
        for settings_file in project_settings_dir.rglob("settings.local.json"):
            files.append(settings_file)

    for root in roots:
        root_path = Path(root).expanduser()
        if not root_path.is_dir():
            continue
        for settings_file in root_path.rglob(".claude/settings.local.json"):
            files.append(settings_file)

    seen: set[Path] = set()
    unique: list[Path] = []
    for f in files:
        resolved = f.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def update_file(
    path: Path,
    target_version: str,
    *,
    target_publisher: str | None = None,
    dry_run: bool = False,
) -> tuple[int, list[str]]:
    content = path.read_text()
    old_versions: set[str] = set()
    old_publishers: set[str] = set()
    count = 0

    def replacer(match: re.Match) -> str:
        nonlocal count
        prefix = match.group(1)
        publisher = match.group(2)
        plugin_slug = match.group(3)
        old_ver = match.group(4)

        new_publisher = publisher
        new_ver = old_ver
        changed = False

        if target_publisher and publisher != target_publisher:
            old_publishers.add(publisher)
            new_publisher = target_publisher
            changed = True

        if old_ver != target_version:
            old_versions.add(old_ver)
            new_ver = target_version
            changed = True

        if changed:
            count += 1
            return prefix + new_publisher + plugin_slug + new_ver
        return match.group(0)

    new_content = VERSION_PATTERN.sub(replacer, content)

    if count > 0 and not dry_run:
        try:
            json.loads(new_content)
        except json.JSONDecodeError as e:
            return 0, [f"  SKIP (invalid JSON after replacement): {e}"]

        path.write_text(new_content)

    messages = []
    for old_pub in sorted(old_publishers):
        messages.append(f"  publisher: {old_pub} -> {target_publisher}")
    for old_ver in sorted(old_versions):
        messages.append(f"  {old_ver} -> {target_version} ({count} replacements)")
    return count, messages


def ensure_base_permissions(
    path: Path,
    base_permissions: list[str],
    *,
    dry_run: bool = False,
) -> tuple[int, list[str]]:
    content = path.read_text()
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return 0, [f"  SKIP (invalid JSON): {e}"]

    allow_list: list[str] = data.get("permissions", {}).get("allow", [])
    existing = set(allow_list)
    missing = [p for p in base_permissions if p not in existing]

    if not missing:
        return 0, []

    if not dry_run:
        if "permissions" not in data:
            data["permissions"] = {}
        if "allow" not in data["permissions"]:
            data["permissions"]["allow"] = []
        data["permissions"]["allow"].extend(missing)
        path.write_text(json.dumps(data, indent=2) + "\n")

    messages = [f"  + {p}" for p in missing]
    return len(missing), messages


GENERALIZE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(detect-tracker\.sh)\s+[^)]+"), r"\1:*"),
    (re.compile(r"(gh-issue-get\.sh)\s+[^)]+"), r"\1:*"),
    (re.compile(r"(gh-pr-detect\.sh)\s+[^)]+"), r"\1:*"),
    (re.compile(r"(generate-commit-list\.sh)\s+[^)]+"), r"\1:*"),
    (re.compile(r"(extract-session\.sh)\s+[^)]+"), r"\1:*"),
    (re.compile(r"(\.(?:sh|py))\s+[^):]+(?::\*)?"), r"\1:*"),
    (re.compile(r"(/tmp/claude/[^/]+/)[^/)]+\.[A-Za-z0-9]{6,}\.(txt|md|json)"), r"\1*"),
    (re.compile(r"(git reset --hard) origin/\S+"), r"\1"),
    (re.compile(r"(git reset --soft) [A-Fa-f0-9]{6,}"), r"\1"),
]


def generalize_permission(entry: str) -> str | None:
    original = entry
    for pattern, replacement in GENERALIZE_PATTERNS:
        entry = pattern.sub(replacement, entry)
    if entry != original:
        return entry
    return None


def generalize_permissions(
    path: Path,
    *,
    dry_run: bool = False,
) -> tuple[int, list[str]]:
    content = path.read_text()
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return 0, [f"  SKIP (invalid JSON): {e}"]

    allow_list: list[str] = data.get("permissions", {}).get("allow", [])
    if not allow_list:
        return 0, []

    existing = set(allow_list)
    replacements: list[tuple[str, str]] = []
    for entry in allow_list:
        generalized = generalize_permission(entry)
        if generalized and generalized != entry and generalized not in existing:
            replacements.append((entry, generalized))

    if not replacements:
        return 0, []

    if not dry_run:
        new_allow = list(allow_list)
        for old, new in replacements:
            idx = new_allow.index(old)
            new_allow[idx] = new
        data["permissions"]["allow"] = new_allow
        path.write_text(json.dumps(data, indent=2) + "\n")

    messages = [f"  {old} → {new}" for old, new in replacements]
    return len(replacements), messages


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Maintain Dev10x plugin permission settings",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )
    parser.add_argument(
        "--version",
        help="Target version (default: auto-detect latest installed)",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Create userspace config from plugin default",
    )
    parser.add_argument(
        "--ensure-base",
        action="store_true",
        help="Add missing base permissions from projects.yaml to all settings files",
    )
    parser.add_argument(
        "--generalize",
        action="store_true",
        help="Replace session-specific permission args with wildcard patterns",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-file details, emit only the summary line",
    )
    args = parser.parse_args()

    if args.init:
        return _init_userspace_config()

    config_path = find_config()
    if not args.quiet:
        print(f"Config: {config_path}")
    config = load_config(config_path)

    settings_files = find_settings_files(
        roots=config.get("roots", []),
        include_user=config.get("include_user_settings", True),
    )

    if not settings_files:
        print("No settings files found.")
        return 0

    if args.ensure_base:
        return _ensure_base(
            config=config,
            settings_files=settings_files,
            dry_run=args.dry_run,
            quiet=args.quiet,
        )

    if args.generalize:
        return _generalize(
            settings_files=settings_files,
            dry_run=args.dry_run,
            quiet=args.quiet,
        )

    cache_dir = Path(config["plugin_cache"]).expanduser()
    target = args.version or detect_latest_version(cache_dir)

    if not target:
        print(f"ERROR: No versions found in {cache_dir}", file=sys.stderr)
        return 1

    publisher = extract_cache_publisher(config["plugin_cache"])
    if not args.quiet:
        print(f"Target version: {target}")
        if publisher:
            print(f"Target publisher: {publisher}")
    if args.dry_run and not args.quiet:
        print("(dry run — no files will be modified)\n")

    total_changes = 0
    files_changed = 0

    for path in sorted(settings_files):
        count, messages = update_file(
            path,
            target,
            target_publisher=publisher,
            dry_run=args.dry_run,
        )
        if count > 0:
            if not args.quiet:
                print(f"\n{path}")
                for msg in messages:
                    print(msg)
            total_changes += count
            files_changed += 1

    if total_changes == 0:
        print("All files already up to date.")
    else:
        verb = "Would update" if args.dry_run else "Updated"
        print(f"{verb} {total_changes} paths in {files_changed} files.")

    return 0


def _load_global_allow_rules() -> set[str]:
    global_settings = Path.home() / ".claude" / "settings.json"
    if not global_settings.is_file():
        return set()
    try:
        data = json.loads(global_settings.read_text())
        return set(data.get("permissions", {}).get("allow", []))
    except (json.JSONDecodeError, OSError):
        return set()


def _ensure_base(
    *,
    config: dict,
    settings_files: list[Path],
    dry_run: bool,
    quiet: bool = False,
) -> int:
    base_permissions = config.get("base_permissions", [])
    if not base_permissions:
        print("No base_permissions defined in config.")
        return 0

    global_rules = _load_global_allow_rules()
    filtered = [p for p in base_permissions if p not in global_rules]
    skipped = len(base_permissions) - len(filtered)

    if not quiet:
        print(f"Base permissions: {len(base_permissions)} rules")
        if skipped > 0:
            print(f"  Skipping {skipped} already in global settings.json")
        if dry_run:
            print("(dry run — no files will be modified)\n")

    if not filtered:
        if not quiet:
            print("All base permissions already covered by global settings.")
        return 0

    total_added = 0
    files_changed = 0

    for path in sorted(settings_files):
        count, messages = ensure_base_permissions(
            path,
            filtered,
            dry_run=dry_run,
        )
        if count > 0:
            if not quiet:
                print(f"\n{path}")
                for msg in messages:
                    print(msg)
            total_added += count
            files_changed += 1

    if total_added == 0:
        print("All files already have base permissions.")
    else:
        verb = "Would add" if dry_run else "Added"
        print(f"{verb} {total_added} permissions across {files_changed} files.")

    return 0


def _generalize(
    *,
    settings_files: list[Path],
    dry_run: bool,
    quiet: bool = False,
) -> int:
    if dry_run and not quiet:
        print("(dry run — no files will be modified)\n")

    total_generalized = 0
    files_changed = 0

    for path in sorted(settings_files):
        count, messages = generalize_permissions(path, dry_run=dry_run)
        if count > 0:
            if not quiet:
                print(f"\n{path}")
                for msg in messages:
                    print(msg)
            total_generalized += count
            files_changed += 1

    if total_generalized == 0:
        print("No session-specific permissions found.")
    else:
        verb = "Would generalize" if dry_run else "Generalized"
        print(f"{verb} {total_generalized} permissions in {files_changed} files.")

    return 0


KNOWN_PLUGIN_DIRS = ("Dev10x", "dev10x-claude")


def _detect_plugin_cache() -> str:
    cache_root = Path.home() / ".claude" / "plugins" / "cache"
    if not cache_root.is_dir():
        return "~/.claude/plugins/cache/Dev10x-Guru/Dev10x"
    candidates: list[Path] = []
    for org_dir in cache_root.iterdir():
        if not org_dir.is_dir():
            continue
        for plugin_name in KNOWN_PLUGIN_DIRS:
            plugin_dir = org_dir / plugin_name
            if plugin_dir.is_dir():
                candidates.append(plugin_dir)
                break
    if len(candidates) == 1:
        return f"~/.claude/plugins/cache/{candidates[0].parent.name}/{candidates[0].name}"
    if len(candidates) > 1:
        names = ", ".join(f"{c.parent.name}/{c.name}" for c in candidates)
        print(f"Multiple plugin cache entries found: {names}")
        print(f"Using first match: {candidates[0].parent.name}/{candidates[0].name}")
        return f"~/.claude/plugins/cache/{candidates[0].parent.name}/{candidates[0].name}"
    return "~/.claude/plugins/cache/Dev10x-Guru/Dev10x"


def _init_userspace_config() -> int:
    if USERSPACE_CONFIG.is_file():
        print(f"Config already exists: {USERSPACE_CONFIG}")
        return 0
    if not PLUGIN_CONFIG.is_file():
        print(f"ERROR: Plugin default config not found: {PLUGIN_CONFIG}", file=sys.stderr)
        return 1
    USERSPACE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    content = PLUGIN_CONFIG.read_text()
    detected_cache = _detect_plugin_cache()
    content = content.replace(
        "~/.claude/plugins/cache/Dev10x-Guru/dev10x-claude",
        detected_cache,
    )
    USERSPACE_CONFIG.write_text(content)
    print(f"Created: {USERSPACE_CONFIG}")
    print(f"Plugin cache: {detected_cache}")
    print("Edit this file to add your project roots.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
