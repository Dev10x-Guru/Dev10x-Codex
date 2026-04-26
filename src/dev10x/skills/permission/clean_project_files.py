#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""Clean redundant permission rules from project settings.local.json files.

Compares project-level allow rules against global ~/.claude/settings.json
and strips rules that are:
  - Exact duplicates of global rules
  - Covered by global wildcard patterns (MCP families, plugin path wildcards)
  - Old plugin version paths (any version older than current)
  - Env-prefixed session noise (GIT_SEQUENCE_EDITOR=*, DATABASE_URL=*, etc.)
  - Shell control flow fragments (do, done, fi, for, while, etc.)
  - Double-slash path typos (Read(//...), Write(//...))

Also flags rules containing leaked secrets (env vars with plaintext values).

Config lookup order:
  1. ~/.claude/skills/Dev10x:permission-maintenance/projects.yaml (userspace)
  2. ${CLAUDE_PLUGIN_ROOT}/skills/permission-maintenance/projects.yaml (plugin default)
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

USERSPACE_CONFIG = (
    Path.home() / ".claude" / "skills" / "Dev10x:permission-maintenance" / "projects.yaml"
)
PLUGIN_CONFIG = (
    Path(__file__).resolve().parents[4] / "skills" / "permission-maintenance" / "projects.yaml"
)
GLOBAL_SETTINGS = Path.home() / ".claude" / "settings.json"

PLUGIN_NAMES = r"(?:Dev10x|dev10x-claude)"
VERSION_PATTERN = re.compile(rf"plugins/cache/[^/]+/{PLUGIN_NAMES}/(\d+\.\d+\.\d+)")
PUBLISHER_PATTERN = re.compile(rf"plugins/cache/([^/]+)/{PLUGIN_NAMES}/")

ENV_PREFIX_PATTERN = re.compile(r"^Bash\([A-Z_]+=")

SHELL_FRAGMENTS = frozenset(
    {
        "do",
        "done",
        "fi",
        "for",
        "while",
        "break",
        "then",
        "else",
        "if",
        "case",
        "esac",
        "select",
        "until",
    }
)

DOUBLE_SLASH_PATTERN = re.compile(r"\(//")

HOOK_ENABLED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^Bash\(gh pr create"),
    re.compile(r"^Bash\(git push"),
    re.compile(r"^Bash\(git rebase -i"),
    re.compile(r"^Bash\(git commit -m"),
    re.compile(r"^Bash\(gh pr checks"),
]

SECRET_INDICATORS = [
    re.compile(r"LINEAR_KEY=lin_api_"),
    re.compile(r"DATABASE_URL=postgres"),
    re.compile(r"SECRET_KEY=\S"),
    re.compile(r"API_KEY=\S"),
    re.compile(r"TOKEN=\S{10,}"),
    re.compile(r"PASSWORD=\S"),
    re.compile(r"PRIVATE_KEY=\S"),
]


@dataclass
class RemovalResult:
    exact_duplicates: list[str] = field(default_factory=list)
    wildcard_covered: list[tuple[str, str]] = field(default_factory=list)
    old_versions: list[str] = field(default_factory=list)
    stale_publisher: list[str] = field(default_factory=list)
    env_noise: list[str] = field(default_factory=list)
    shell_fragments: list[str] = field(default_factory=list)
    double_slash: list[str] = field(default_factory=list)
    leaked_secrets: list[str] = field(default_factory=list)
    hook_enabled: list[str] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return (
            len(self.exact_duplicates)
            + len(self.wildcard_covered)
            + len(self.old_versions)
            + len(self.stale_publisher)
            + len(self.env_noise)
            + len(self.shell_fragments)
            + len(self.double_slash)
        )


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


def load_global_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def extract_allow_rules(data: dict) -> set[str]:
    return set(data.get("permissions", {}).get("allow", []))


def detect_current_version(cache_dir: Path) -> str | None:
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


def is_covered_by_wildcard(
    rule: str,
    global_rules: set[str],
) -> str | None:
    for global_rule in global_rules:
        if "*" not in global_rule:
            continue
        if rule == global_rule:
            continue
        pattern = re.escape(global_rule).replace(r"\*", ".*")
        if re.fullmatch(pattern, rule):
            return global_rule
    return None


def is_shell_fragment(rule: str) -> bool:
    match = re.match(r"^Bash\((\w+)\b", rule)
    if match:
        return match.group(1) in SHELL_FRAGMENTS
    return False


def is_stale_publisher(
    rule: str,
    *,
    cache_root: Path | None,
) -> bool:
    if cache_root is None:
        return False
    match = PUBLISHER_PATTERN.search(rule)
    if not match:
        return False
    publisher = match.group(1)
    return not (cache_root / publisher).is_dir()


def is_old_version(
    rule: str,
    current_version: str | None,
) -> bool:
    if current_version is None:
        return False
    match = VERSION_PATTERN.search(rule)
    if not match:
        return False
    rule_version = match.group(1)
    return _version_tuple(rule_version) < _version_tuple(current_version)


def is_hook_enabled(rule: str) -> bool:
    return any(p.search(rule) for p in HOOK_ENABLED_PATTERNS)


def has_leaked_secret(rule: str) -> bool:
    return any(p.search(rule) for p in SECRET_INDICATORS)


def classify_rules(
    project_rules: list[str],
    *,
    global_rules: set[str],
    current_version: str | None,
    base_permissions: set[str] | None = None,
    cache_root: Path | None = None,
) -> RemovalResult:
    result = RemovalResult()
    _base = base_permissions or set()

    for rule in project_rules:
        if has_leaked_secret(rule):
            result.leaked_secrets.append(rule)

        if rule in _base:
            result.kept.append(rule)
            continue

        if is_hook_enabled(rule):
            result.hook_enabled.append(rule)
            result.kept.append(rule)
            continue

        if rule in global_rules:
            result.exact_duplicates.append(rule)
            continue

        covering = is_covered_by_wildcard(rule, global_rules)
        if covering is not None:
            result.wildcard_covered.append((rule, covering))
            continue

        if is_stale_publisher(rule, cache_root=cache_root):
            result.stale_publisher.append(rule)
            continue

        if is_old_version(rule, current_version):
            result.old_versions.append(rule)
            continue

        if ENV_PREFIX_PATTERN.search(rule):
            result.env_noise.append(rule)
            continue

        if is_shell_fragment(rule):
            result.shell_fragments.append(rule)
            continue

        if DOUBLE_SLASH_PATTERN.search(rule):
            result.double_slash.append(rule)
            continue

        result.kept.append(rule)

    return result


def clean_file(
    path: Path,
    *,
    global_rules: set[str],
    current_version: str | None,
    base_permissions: set[str] | None = None,
    cache_root: Path | None = None,
    dry_run: bool = False,
) -> tuple[RemovalResult | None, list[str]]:
    content = path.read_text()
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return None, [f"  SKIP (invalid JSON): {e}"]

    allow_list: list[str] = data.get("permissions", {}).get("allow", [])
    if not allow_list:
        return RemovalResult(), []

    result = classify_rules(
        allow_list,
        global_rules=global_rules,
        current_version=current_version,
        base_permissions=base_permissions,
        cache_root=cache_root,
    )

    if result.total_removed == 0:
        return result, []

    if not dry_run:
        data["permissions"]["allow"] = result.kept
        path.write_text(json.dumps(data, indent=2) + "\n")

    messages = _format_messages(result)
    return result, messages


def _format_messages(result: RemovalResult) -> list[str]:
    messages: list[str] = []

    if result.leaked_secrets:
        messages.append(f"  ⚠ LEAKED SECRETS ({len(result.leaked_secrets)}):")
        for rule in result.leaked_secrets:
            messages.append(f"    ⚠ {rule}")

    if result.exact_duplicates:
        messages.append(f"  - {len(result.exact_duplicates)} exact duplicates of global rules")

    if result.wildcard_covered:
        messages.append(f"  - {len(result.wildcard_covered)} covered by global wildcards")

    if result.old_versions:
        messages.append(f"  - {len(result.old_versions)} old plugin versions")

    if result.stale_publisher:
        messages.append(f"  - {len(result.stale_publisher)} stale publisher paths")

    if result.env_noise:
        messages.append(f"  - {len(result.env_noise)} env-prefixed session noise")

    if result.shell_fragments:
        messages.append(f"  - {len(result.shell_fragments)} shell control flow fragments")

    if result.double_slash:
        messages.append(f"  - {len(result.double_slash)} double-slash paths")

    if result.hook_enabled:
        messages.append(f"  - {len(result.hook_enabled)} hook-enabled rules (kept)")

    messages.append(f"  Removed: {result.total_removed} | Kept: {len(result.kept)}")
    return messages


def find_settings_files(roots: list[str]) -> list[Path]:
    files: list[Path] = []

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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clean redundant permissions from project settings files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleaned without modifying files",
    )
    args = parser.parse_args()

    config_path = find_config()
    print(f"Config: {config_path}")
    config = load_config(config_path)

    global_data = load_global_settings(GLOBAL_SETTINGS)
    global_rules = extract_allow_rules(global_data)
    print(f"Global rules: {len(global_rules)}")

    cache_dir = Path(config.get("plugin_cache", "")).expanduser()
    cache_root = cache_dir.parent.parent if cache_dir.parts else None
    current_version = detect_current_version(cache_dir)
    if current_version:
        print(f"Current plugin version: {current_version}")

    base_permissions = set(config.get("base_permissions", []))

    settings_files = find_settings_files(roots=config.get("roots", []))

    if not settings_files:
        print("No project settings files found.")
        return 0

    print(f"Scanning {len(settings_files)} files")
    if args.dry_run:
        print("(dry run — no files will be modified)\n")
    else:
        print()

    total_removed = 0
    total_kept = 0
    files_changed = 0
    total_secrets = 0

    for path in sorted(settings_files):
        result, messages = clean_file(
            path,
            global_rules=global_rules,
            current_version=current_version,
            base_permissions=base_permissions,
            cache_root=cache_root,
            dry_run=args.dry_run,
        )
        if result is None:
            print(f"\n{path}")
            for msg in messages:
                print(msg)
            continue

        if result.total_removed > 0 or result.leaked_secrets:
            print(f"\n{path}")
            for msg in messages:
                print(msg)
            total_removed += result.total_removed
            total_kept += len(result.kept)
            total_secrets += len(result.leaked_secrets)
            if result.total_removed > 0:
                files_changed += 1
        else:
            total_kept += len(result.kept)

    print()
    if total_removed == 0:
        print("All project files are clean.")
    else:
        verb = "Would remove" if args.dry_run else "Removed"
        print(f"{verb} {total_removed} rules across {files_changed} files.")
        print(f"Kept {total_kept} rules total.")

    if total_secrets > 0:
        print(
            f"\n⚠ Found {total_secrets} rules containing leaked secrets."
            " Review and rotate affected credentials."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
