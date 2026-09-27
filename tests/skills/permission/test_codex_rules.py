from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

import dev10x.skills.permission as permission_pkg
from dev10x.skills.permission.codex_rules import (
    ALLOW,
    FORBIDDEN,
    NEVER_ALLOWED_PROGRAMS,
    PROMPT,
    CodexRule,
    SkippedRule,
    render_rules,
    translate_catalog,
    translate_rule,
)
from dev10x.skills.permission.config import parse_config

REPO_ROOT = Path(permission_pkg.__file__).resolve().parents[4]
PROJECTS_YAML = REPO_ROOT / "skills" / "upgrade-cleanup" / "projects.yaml"
COMMITTED_RULES = REPO_ROOT / "codex" / "rules" / "dev10x.rules"


class TestTranslateRule:
    def test_command_prefix_becomes_token_pattern(self) -> None:
        assert translate_rule("Bash(git status:*)", ALLOW) == CodexRule(
            pattern=("git", "status"), decision=ALLOW, source="Bash(git status:*)"
        )

    def test_deny_becomes_forbidden(self) -> None:
        rule = translate_rule("Bash(sudo:*)", FORBIDDEN)
        assert isinstance(rule, CodexRule)
        assert rule.pattern == ("sudo",)
        assert rule.decision == FORBIDDEN

    def test_ask_becomes_prompt(self) -> None:
        rule = translate_rule("Bash(gh api -X POST:*)", PROMPT)
        assert isinstance(rule, CodexRule)
        assert rule.pattern == ("gh", "api", "-X", "POST")

    @pytest.mark.parametrize(
        "source",
        [
            "Bash(pwd)",
            "Bash(sudo *)",
            "Bash(git -C * status:*)",
            "Bash(find ~/.claude/plugins/cache/Dev10x-Guru/Dev10x:*)",
            "Bash(uv run --project $CLAUDE_PLUGIN_ROOT dev10x foreman probe:*)",
            "Bash(/tmp/Dev10x/*.py:*)",
            "Bash(cp /tmp:*)",
        ],
    )
    def test_shapes_without_a_clean_token_prefix_are_skipped(self, source: str) -> None:
        skipped = translate_rule(source, ALLOW)
        assert isinstance(skipped, SkippedRule)
        assert skipped.reason

    def test_absolute_program_path_is_kept(self) -> None:
        rule = translate_rule("Bash(/tmp/Dev10x/bin/mktmp.sh:*)", ALLOW)
        assert isinstance(rule, CodexRule)
        assert rule.pattern == ("/tmp/Dev10x/bin/mktmp.sh",)

    @pytest.mark.parametrize("program", sorted(NEVER_ALLOWED_PROGRAMS))
    def test_destructive_program_is_never_allowed(self, program: str) -> None:
        assert isinstance(translate_rule(f"Bash({program}:*)", ALLOW), SkippedRule)

    @pytest.mark.parametrize(
        "source", ["Bash(gh api:*)", "Bash(gh api graphql:*)", "Bash(gh api repos:*)"]
    )
    def test_gh_api_is_never_allowed_because_later_flags_can_make_it_a_write(
        self, source: str
    ) -> None:
        assert isinstance(translate_rule(source, ALLOW), SkippedRule)

    def test_gh_api_write_methods_still_prompt(self) -> None:
        rule = translate_rule("Bash(gh api --method DELETE:*)", PROMPT)
        assert isinstance(rule, CodexRule)
        assert rule.decision == PROMPT

    def test_rm_may_still_be_forbidden(self) -> None:
        rule = translate_rule("Bash(rm -rf:*)", FORBIDDEN)
        assert isinstance(rule, CodexRule)
        assert rule.decision == FORBIDDEN

    def test_non_shell_rule_is_not_translated(self) -> None:
        assert translate_rule("mcp__plugin_Dev10x_cli__pr_get", ALLOW) is None


class TestTranslateCatalog:
    def test_buckets_map_to_codex_decisions(self) -> None:
        translation = translate_catalog(
            {
                "base_permissions": ["Bash(git status:*)", "Read(//tmp/Dev10x/**)"],
                "base_asks": ["Bash(gh api -X DELETE:*)"],
                "base_denies": ["Bash(sudo:*)"],
            }
        )
        assert [(rule.pattern, rule.decision) for rule in translation.rules] == [
            (("git", "status"), ALLOW),
            (("gh", "api", "-X", "DELETE"), PROMPT),
            (("sudo",), FORBIDDEN),
        ]
        assert translation.skipped == []

    def test_duplicate_patterns_are_emitted_once(self) -> None:
        translation = translate_catalog(
            {"base_permissions": ["Bash(git status:*)", "Bash(git status:*)"]}
        )
        assert len(translation.rules) == 1

    def test_shipped_catalog_never_allows_a_destructive_program(self) -> None:
        translation = translate_catalog(parse_config(PROJECTS_YAML))
        allowed_programs = {
            Path(rule.pattern[0]).name for rule in translation.rules if rule.decision == ALLOW
        }
        assert not allowed_programs & NEVER_ALLOWED_PROGRAMS

    def test_shipped_catalog_never_allows_a_gh_api_prefix(self) -> None:
        translation = translate_catalog(parse_config(PROJECTS_YAML))
        allowed_gh_api = [
            rule.pattern
            for rule in translation.rules
            if rule.decision == ALLOW and rule.pattern[:2] == ("gh", "api")
        ]
        assert allowed_gh_api == []

    def test_shipped_catalog_forbids_privilege_escalation(self) -> None:
        translation = translate_catalog(parse_config(PROJECTS_YAML))
        forbidden = {rule.pattern for rule in translation.rules if rule.decision == FORBIDDEN}
        assert ("sudo",) in forbidden


class TestRenderRules:
    def test_rule_renders_as_starlark_prefix_rule(self) -> None:
        text = render_rules(
            [CodexRule(pattern=("git", "status"), decision=ALLOW, source="Bash(git status:*)")]
        )
        assert 'pattern = ["git", "status"],' in text
        assert 'decision = "allow",' in text
        assert text.startswith("# Generated by")

    def test_committed_rules_file_matches_regeneration(self) -> None:
        expected = render_rules(translate_catalog(parse_config(PROJECTS_YAML)).rules)
        assert COMMITTED_RULES.read_text() == expected, (
            "codex/rules/dev10x.rules is stale — regenerate it with "
            "`dev10x permission codex-rules`"
        )


class TestCodexRulesCommand:
    def test_writes_rules_file(self, tmp_path: Path) -> None:
        from dev10x.commands.permission import permission

        output = tmp_path / "dev10x.rules"
        result = CliRunner().invoke(
            permission,
            ["codex-rules", "--catalog", str(PROJECTS_YAML), "--output", str(output)],
        )

        assert result.exit_code == 0, result.output
        assert output.read_text() == COMMITTED_RULES.read_text()
        assert "skipped" in result.output

    def test_check_fails_on_drift(self, tmp_path: Path) -> None:
        from dev10x.commands.permission import permission

        output = tmp_path / "dev10x.rules"
        output.write_text("stale\n")
        result = CliRunner().invoke(
            permission,
            ["codex-rules", "--catalog", str(PROJECTS_YAML), "--output", str(output), "--check"],
        )

        assert result.exit_code == 1
        assert output.read_text() == "stale\n"

    def test_check_passes_when_current(self) -> None:
        from dev10x.commands.permission import permission

        result = CliRunner().invoke(
            permission,
            [
                "codex-rules",
                "--catalog",
                str(PROJECTS_YAML),
                "--output",
                str(COMMITTED_RULES),
                "--check",
            ],
        )

        assert result.exit_code == 0, result.output
