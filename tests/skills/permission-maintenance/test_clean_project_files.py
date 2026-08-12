"""Tests for the clean-project-files.py script."""

import importlib.util
import json
from pathlib import Path

import pytest

_repo_root = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT_PATH = (
    _repo_root / "skills" / "permission-maintenance" / "scripts" / "clean-project-files.py"
)
spec = importlib.util.spec_from_file_location("clean_project_files", SCRIPT_PATH)
clean_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clean_mod)


class TestIsCoveredByWildcard:
    @pytest.mark.parametrize(
        "rule,global_rules,expected_cover",
        [
            (
                "mcp__claude_ai_Linear__get_issue",
                {"mcp__claude_ai_Linear__*"},
                "mcp__claude_ai_Linear__*",
            ),
            (
                "Bash(/home/user/.codex/plugins/cache/Dev10x-Guru/dev10x-claude/0.30.0/scripts/foo.sh:*)",
                {"Bash(/home/user/.codex/plugins/cache/Dev10x-Guru/dev10x-claude/*:*)"},
                "Bash(/home/user/.codex/plugins/cache/Dev10x-Guru/dev10x-claude/*:*)",
            ),
            (
                "mcp__plugin_Dev10x_cli__detect_tracker",
                {"mcp__plugin_Dev10x_*"},
                "mcp__plugin_Dev10x_*",
            ),
        ],
    )
    def test_detects_wildcard_coverage(
        self,
        rule: str,
        global_rules: set[str],
        expected_cover: str,
    ) -> None:
        result = clean_mod.is_covered_by_wildcard(rule, global_rules)

        assert result == expected_cover

    @pytest.mark.parametrize(
        "rule,global_rules",
        [
            ("Bash(git log:*)", {"Bash(gh pr view:*)"}),
            ("mcp__claude_ai_Slack__send", {"mcp__claude_ai_Linear__*"}),
            ("Bash(git log:*)", {"Bash(git log:*)"}),
        ],
    )
    def test_returns_none_when_not_covered(
        self,
        rule: str,
        global_rules: set[str],
    ) -> None:
        result = clean_mod.is_covered_by_wildcard(rule, global_rules)

        assert result is None


class TestIsShellFragment:
    @pytest.mark.parametrize(
        "rule",
        [
            "Bash(do something)",
            "Bash(done)",
            "Bash(fi)",
            "Bash(for x in list)",
            "Bash(while true)",
            "Bash(break)",
            "Bash(then echo)",
            "Bash(else exit 1)",
            "Bash(if [ -f foo ])",
            "Bash(case $x in)",
            "Bash(esac)",
            "Bash(select item in list)",
            "Bash(until done)",
        ],
    )
    def test_detects_shell_fragments(self, rule: str) -> None:
        assert clean_mod.is_shell_fragment(rule) is True

    @pytest.mark.parametrize(
        "rule",
        [
            "Bash(git log:*)",
            "Bash(docker compose up)",
            "Bash(find . -name foo)",
        ],
    )
    def test_rejects_normal_commands(self, rule: str) -> None:
        assert clean_mod.is_shell_fragment(rule) is False


class TestIsOldVersion:
    def test_detects_old_version(self) -> None:
        rule = "Bash(/home/user/.codex/plugins/cache/Dev10x-Guru/dev10x-claude/0.16.0/scripts/foo.sh:*)"

        assert clean_mod.is_old_version(rule, "0.33.0") is True

    def test_current_version_is_not_old(self) -> None:
        rule = "Bash(/home/user/.codex/plugins/cache/Dev10x-Guru/dev10x-claude/0.33.0/scripts/foo.sh:*)"

        assert clean_mod.is_old_version(rule, "0.33.0") is False

    def test_returns_false_when_no_version_in_rule(self) -> None:
        assert clean_mod.is_old_version("Bash(git log:*)", "0.33.0") is False

    def test_returns_false_when_no_current_version(self) -> None:
        rule = "Bash(/home/user/.codex/plugins/cache/Dev10x-Guru/dev10x-claude/0.16.0/scripts/foo.sh:*)"

        assert clean_mod.is_old_version(rule, None) is False

    def test_detects_old_version_with_alternate_org(self) -> None:
        rule = (
            "Bash(/home/user/.codex/plugins/cache/WooYek/dev10x-claude/0.16.0/scripts/foo.sh:*)"
        )

        assert clean_mod.is_old_version(rule, "0.33.0") is True


class TestHasLeakedSecret:
    @pytest.mark.parametrize(
        "rule",
        [
            "Bash(LINEAR_KEY=lin_api_abc123 some-command)",
            "Bash(DATABASE_URL=postgres://user:pass@host/db command)",
            "Bash(API_KEY=sk_live_abcdef1234 curl)",
            "Bash(TOKEN=eyJhbGciOiJIUzI1NiJ9 command)",
        ],
    )
    def test_detects_leaked_secrets(self, rule: str) -> None:
        assert clean_mod.has_leaked_secret(rule) is True

    @pytest.mark.parametrize(
        "rule",
        [
            "Bash(git log:*)",
            "Bash(GIT_SEQUENCE_EDITOR=: git rebase)",
            "mcp__plugin_Dev10x_cli__detect_tracker",
        ],
    )
    def test_ignores_non_secrets(self, rule: str) -> None:
        assert clean_mod.has_leaked_secret(rule) is False


class TestIsHookEnabled:
    @pytest.mark.parametrize(
        "rule",
        [
            "Bash(gh pr create:*)",
            "Bash(git push:*)",
            "Bash(git push origin main)",
            "Bash(git rebase -i:*)",
            "Bash(git commit -m:*)",
            "Bash(gh pr checks:*)",
        ],
    )
    def test_detects_hook_enabled_rules(self, rule: str) -> None:
        assert clean_mod.is_hook_enabled(rule) is True

    @pytest.mark.parametrize(
        "rule",
        [
            "Bash(git log:*)",
            "Bash(gh pr view:*)",
            "Bash(docker compose up)",
            "mcp__plugin_Dev10x_cli__detect_tracker",
        ],
    )
    def test_rejects_non_hook_enabled_rules(self, rule: str) -> None:
        assert clean_mod.is_hook_enabled(rule) is False


class TestClassifyRules:
    GLOBAL_RULES = {
        "Bash(git log:*)",
        "Bash(gh pr view:*)",
        "mcp__claude_ai_Linear__*",
        "mcp__plugin_Dev10x_*",
    }

    def test_classifies_exact_duplicates(self) -> None:
        rules = ["Bash(git log:*)", "Bash(gh pr view:*)"]

        result = clean_mod.classify_rules(
            rules,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert result.exact_duplicates == rules
        assert result.kept == []

    def test_classifies_wildcard_covered(self) -> None:
        rules = ["mcp__claude_ai_Linear__get_issue", "mcp__plugin_Dev10x_cli__push"]

        result = clean_mod.classify_rules(
            rules,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert len(result.wildcard_covered) == 2
        assert result.kept == []

    def test_classifies_old_versions(self) -> None:
        rules = [
            "Bash(/home/u/.codex/plugins/cache/Dev10x-Guru/dev10x-claude/0.4.0/scripts/foo.sh:*)",
        ]

        result = clean_mod.classify_rules(
            rules,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert len(result.old_versions) == 1
        assert result.kept == []

    def test_classifies_env_noise(self) -> None:
        rules = [
            "Bash(GIT_SEQUENCE_EDITOR=: git rebase)",
            "Bash(DATABASE_URL=postgres://host/db command)",
        ]

        result = clean_mod.classify_rules(
            rules,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert len(result.env_noise) == 2

    def test_classifies_shell_fragments(self) -> None:
        rules = ["Bash(do something)", "Bash(done)", "Bash(fi)"]

        result = clean_mod.classify_rules(
            rules,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert len(result.shell_fragments) == 3

    def test_classifies_double_slash_paths(self) -> None:
        rules = ["Read(//work/example/app-pos/src/file.py)"]

        result = clean_mod.classify_rules(
            rules,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert len(result.double_slash) == 1

    def test_keeps_legitimate_rules(self) -> None:
        rules = [
            "Bash(docker compose up)",
            "Read(/work/my-project/src/file.py)",
        ]

        result = clean_mod.classify_rules(
            rules,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert result.kept == rules
        assert result.total_removed == 0

    def test_flags_leaked_secrets_alongside_classification(self) -> None:
        rules = ["Bash(LINEAR_KEY=lin_api_abc123 some-command)"]

        result = clean_mod.classify_rules(
            rules,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert len(result.leaked_secrets) == 1
        assert len(result.env_noise) == 1

    def test_keeps_hook_enabled_rules(self) -> None:
        rules = ["Bash(git push:*)", "Bash(gh pr create:*)"]

        result = clean_mod.classify_rules(
            rules,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert result.hook_enabled == rules
        assert result.kept == rules
        assert result.total_removed == 0

    def test_hook_enabled_takes_precedence_over_duplicate(self) -> None:
        global_rules = self.GLOBAL_RULES | {"Bash(git push:*)"}
        rules = ["Bash(git push:*)"]

        result = clean_mod.classify_rules(
            rules,
            global_rules=global_rules,
            current_version="0.33.0",
        )

        assert result.hook_enabled == ["Bash(git push:*)"]
        assert result.kept == ["Bash(git push:*)"]
        assert result.exact_duplicates == []

    def test_total_removed_counts_all_categories(self) -> None:
        rules = [
            "Bash(git log:*)",
            "mcp__claude_ai_Linear__get_issue",
            "Bash(/home/u/.codex/plugins/cache/Dev10x-Guru/dev10x-claude/0.4.0/x.sh:*)",
            "Bash(GIT_SEQUENCE_EDITOR=: git rebase)",
            "Bash(fi)",
            "Read(//work/example/file.py)",
        ]

        result = clean_mod.classify_rules(
            rules,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert result.total_removed == 6


class TestCleanFile:
    GLOBAL_RULES = {"Bash(git log:*)", "mcp__claude_ai_Linear__*"}

    @pytest.fixture()
    def settings_file(self, tmp_path: Path) -> Path:
        return tmp_path / "settings.local.json"

    def test_removes_redundant_rules(self, settings_file: Path) -> None:
        settings_file.write_text(
            json.dumps(
                {
                    "permissions": {
                        "allow": [
                            "Bash(git log:*)",
                            "mcp__claude_ai_Linear__get_issue",
                            "Bash(docker compose up)",
                        ]
                    }
                }
            )
            + "\n"
        )

        result, messages = clean_mod.clean_file(
            settings_file,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert result.total_removed == 2
        data = json.loads(settings_file.read_text())
        assert data["permissions"]["allow"] == ["Bash(docker compose up)"]

    def test_dry_run_does_not_write(self, settings_file: Path) -> None:
        settings_file.write_text(
            json.dumps({"permissions": {"allow": ["Bash(git log:*)"]}}) + "\n"
        )
        original = settings_file.read_text()

        result, messages = clean_mod.clean_file(
            settings_file,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
            dry_run=True,
        )

        assert result.total_removed == 1
        assert settings_file.read_text() == original

    def test_no_changes_when_all_clean(self, settings_file: Path) -> None:
        settings_file.write_text(
            json.dumps({"permissions": {"allow": ["Bash(docker compose up)"]}}) + "\n"
        )

        result, messages = clean_mod.clean_file(
            settings_file,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert result.total_removed == 0
        assert messages == []

    def test_skips_invalid_json(self, settings_file: Path) -> None:
        settings_file.write_text("{invalid json}")

        result, messages = clean_mod.clean_file(
            settings_file,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert result is None
        assert any("SKIP" in m for m in messages)

    def test_preserves_other_settings_keys(self, settings_file: Path) -> None:
        settings_file.write_text(
            json.dumps(
                {
                    "permissions": {
                        "allow": ["Bash(git log:*)"],
                        "deny": ["something"],
                    },
                    "hooks": {"PreToolUse": []},
                }
            )
            + "\n"
        )

        clean_mod.clean_file(
            settings_file,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        data = json.loads(settings_file.read_text())
        assert data["permissions"]["deny"] == ["something"]
        assert data["hooks"] == {"PreToolUse": []}

    def test_keeps_hook_enabled_rules(self, settings_file: Path) -> None:
        settings_file.write_text(
            json.dumps(
                {
                    "permissions": {
                        "allow": [
                            "Bash(git log:*)",
                            "Bash(git push:*)",
                            "Bash(docker compose up)",
                        ]
                    }
                }
            )
            + "\n"
        )

        result, messages = clean_mod.clean_file(
            settings_file,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert result.total_removed == 1
        data = json.loads(settings_file.read_text())
        assert "Bash(git push:*)" in data["permissions"]["allow"]
        assert "Bash(docker compose up)" in data["permissions"]["allow"]
        assert "Bash(git log:*)" not in data["permissions"]["allow"]

    def test_handles_empty_allow_list(self, settings_file: Path) -> None:
        settings_file.write_text(json.dumps({"permissions": {"allow": []}}) + "\n")

        result, messages = clean_mod.clean_file(
            settings_file,
            global_rules=self.GLOBAL_RULES,
            current_version="0.33.0",
        )

        assert result.total_removed == 0
        assert messages == []


class TestIsStalePublisher:
    def test_detects_stale_publisher(self, tmp_path: Path) -> None:
        cache_root = tmp_path / "cache"
        (cache_root / "Dev10x-Guru").mkdir(parents=True)
        rule = "Bash(~/.codex/plugins/cache/WooYek/Dev10x/0.48.0/skills/foo.sh:*)"

        assert clean_mod.is_stale_publisher(rule, cache_root=cache_root) is True

    def test_returns_false_for_existing_publisher(self, tmp_path: Path) -> None:
        cache_root = tmp_path / "cache"
        (cache_root / "Dev10x-Guru").mkdir(parents=True)
        rule = "Bash(~/.codex/plugins/cache/Dev10x-Guru/Dev10x/0.54.0/skills/foo.sh:*)"

        assert clean_mod.is_stale_publisher(rule, cache_root=cache_root) is False

    def test_returns_false_for_non_plugin_rule(self, tmp_path: Path) -> None:
        cache_root = tmp_path / "cache"
        (cache_root / "Dev10x-Guru").mkdir(parents=True)

        assert clean_mod.is_stale_publisher("Bash(git log:*)", cache_root=cache_root) is False

    def test_returns_false_when_cache_root_is_none(self) -> None:
        rule = "Bash(~/.codex/plugins/cache/WooYek/Dev10x/0.48.0/skills/foo.sh:*)"

        assert clean_mod.is_stale_publisher(rule, cache_root=None) is False

    def test_matches_dev10x_claude_plugin_name(self, tmp_path: Path) -> None:
        cache_root = tmp_path / "cache"
        (cache_root / "Dev10x-Guru").mkdir(parents=True)
        rule = "Bash(~/.codex/plugins/cache/WooYek/dev10x-claude/0.30.0/scripts/x.sh:*)"

        assert clean_mod.is_stale_publisher(rule, cache_root=cache_root) is True


class TestClassifyRulesStalePublisher:
    GLOBAL_RULES: set[str] = set()

    def test_classifies_stale_publisher_rules(self, tmp_path: Path) -> None:
        cache_root = tmp_path / "cache"
        (cache_root / "Dev10x-Guru").mkdir(parents=True)
        rules = [
            "Bash(~/.codex/plugins/cache/WooYek/Dev10x/0.48.0/skills/foo.sh:*)",
        ]

        result = clean_mod.classify_rules(
            rules,
            global_rules=self.GLOBAL_RULES,
            current_version="0.54.0",
            cache_root=cache_root,
        )

        assert len(result.stale_publisher) == 1
        assert result.total_removed == 1

    def test_stale_publisher_takes_precedence_over_old_version(
        self,
        tmp_path: Path,
    ) -> None:
        cache_root = tmp_path / "cache"
        (cache_root / "Dev10x-Guru").mkdir(parents=True)
        rules = [
            "Bash(~/.codex/plugins/cache/WooYek/Dev10x/0.30.0/skills/foo.sh:*)",
        ]

        result = clean_mod.classify_rules(
            rules,
            global_rules=self.GLOBAL_RULES,
            current_version="0.54.0",
            cache_root=cache_root,
        )

        assert len(result.stale_publisher) == 1
        assert len(result.old_versions) == 0
