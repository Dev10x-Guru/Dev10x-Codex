from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath

import pytest
import yaml
from click.testing import CliRunner

import dev10x.skills.codex as codex_pkg
from dev10x.commands.skill import codex_skills
from dev10x.skills.codex.translate import (
    CODEX_SKILLS_RELPATH,
    DESCRIPTION_MAX_LENGTH,
    PLUGIN_ROOT_PLACEHOLDER,
    TOOL_EQUIVALENTS_RELPATH,
    VERIFIED_SKILLS,
    InvalidSkillFile,
    InvalidSkillName,
    codex_description,
    codex_skill_name,
    display_name,
    read_tree,
    rewrite_links,
    rewrite_text,
    split_front_matter,
    stale_paths,
    translate_skills,
    unknown_skill_mentions,
)

REPO_ROOT = Path(codex_pkg.__file__).resolve().parents[4]
CODEX_VALIDATOR_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}
CODEX_NAME_RE = re.compile(r"^[a-z0-9-]+$")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def plugin(tmp_path: Path) -> Path:
    write(
        tmp_path / "skills" / "git-commit" / "SKILL.md",
        "---\n"
        "name: Dev10x:git-commit\n"
        "description: >\n"
        "  Commit with <gitmoji>.\n"
        "  DO NOT TRIGGER when: fixups (use Dev10x:git-fixup).\n"
        "invocation-name: Dev10x:git-commit\n"
        "allowed-tools:\n"
        "  - mcp__plugin_Dev10x_cli__mktmp\n"
        "---\n"
        "\n"
        "# Commit\n"
        "\n"
        "Read [`instructions.md`](instructions.md) and the "
        "[guide](../../references/git-commits.md).\n"
        "Run [the script](scripts/run.sh) via "
        "`${CLAUDE_PLUGIN_ROOT}/skills/git-commit/scripts/run.sh`.\n"
        "Then `Skill(Dev10x:git-fixup)` and call `mcp__plugin_Dev10x_cli__push_safe`.\n",
    )
    write(
        tmp_path / "skills" / "git-commit" / "instructions.md",
        "See [fixup](../git-fixup/SKILL.md) and `Skill(test)`.\n",
    )
    write(
        tmp_path / "skills" / "git-commit" / "references" / "defaults.yaml",
        "tool: mcp__plugin_Dev10x_cli__mktmp\n",
    )
    write(tmp_path / "skills" / "git-commit" / "scripts" / "run.sh", "#!/bin/sh\n")
    write(tmp_path / "skills" / "git-commit" / "scripts" / "notes.md", "script notes\n")
    write(tmp_path / "skills" / "git-commit" / "evals" / "evals.json", "{}\n")
    write(
        tmp_path / "skills" / "git-fixup" / "SKILL.md",
        "---\nname: Dev10x:git-fixup\ndescription: Create a fixup.\n---\n\nBody.\n",
    )
    write(
        tmp_path / "skills" / "foreman" / "SKILL.md",
        "---\nname: Dev10x:foreman\ndescription: Night shift.\n---\n\n"
        "Uses Dev10x:retired-skill.\n",
    )
    (tmp_path / "skills" / "empty-leftover" / "__pycache__").mkdir(parents=True)
    write(tmp_path / "references" / "git-commits.md", "guide\n")
    (tmp_path / ".codex-plugin").mkdir()
    return tmp_path


class TestCodexSkillName:
    @pytest.mark.parametrize("name", ["git", "gh-pr-create", "k8s", "py-test"])
    def test_valid_directory_names_pass_through(self, name: str) -> None:
        assert codex_skill_name(name) == name

    @pytest.mark.parametrize(
        "name", ["Dev10x:git", "Git", "git--commit", "-git", "git_", "a" * 65]
    )
    def test_names_codex_rejects_raise(self, name: str) -> None:
        with pytest.raises(InvalidSkillName):
            codex_skill_name(name)


class TestDisplayName:
    @pytest.mark.parametrize(
        ("directory", "expected"),
        [
            ("gh-pr-create", "GH PR Create"),
            ("git-commit", "Git Commit"),
            ("jtbd", "JTBD"),
            ("verify-acc-dod", "Verify AC DoD"),
        ],
    )
    def test_acronyms_are_kept_upper_case(self, directory: str, expected: str) -> None:
        assert display_name(directory) == expected


class TestSplitFrontMatter:
    def test_returns_mapping_and_body(self) -> None:
        data, body = split_front_matter("---\nname: x\n---\n\n# Body\n")
        assert data == {"name": "x"}
        assert body == "\n# Body\n"

    def test_text_without_front_matter_is_all_body(self) -> None:
        assert split_front_matter("# Body\n") == ({}, "# Body\n")

    def test_non_mapping_front_matter_is_treated_as_body(self) -> None:
        text = "---\n- a\n---\nbody\n"
        assert split_front_matter(text) == ({}, text)


class TestRewriteText:
    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ("mcp__plugin_Dev10x_cli__push_safe", "mcp__cli__push_safe"),
            ("mcp__plugin_Dev10x_db__query", "mcp__db__query"),
            ("mcp__plugin_Dev10x_cli__*", "mcp__cli__*"),
            ("${CLAUDE_PLUGIN_ROOT}/bin/x.sh", f"{PLUGIN_ROOT_PLACEHOLDER}/bin/x.sh"),
            ("$CLAUDE_PLUGIN_ROOT/bin/x.sh", f"{PLUGIN_ROOT_PLACEHOLDER}/bin/x.sh"),
            ("Skill(Dev10x:git-commit)", "$Dev10x:git-commit"),
            (
                'Skill(skill="Dev10x:gh-pr-create", args="--unattended")',
                '$Dev10x:gh-pr-create (args: "--unattended")',
            ),
            ("Skill(Dev10x:py-test path/to/tests/)", "$Dev10x:py-test (args: path/to/tests/)"),
            ("Skill(test)", "$Dev10x:py-test"),
            ("run /Dev10x:git-groom now", "run $Dev10x:git-groom now"),
            ("(`/Dev10x:git`)", "(`$Dev10x:git`)"),
        ],
    )
    def test_maps_exact_claude_names_to_codex(self, source: str, expected: str) -> None:
        assert rewrite_text(source) == expected

    @pytest.mark.parametrize(
        "source",
        [
            "Skill(testing)",
            '"Skill(Dev10x:*)"',
            "cache/Dev10x:foo",
            "use Dev10x:git-commit",
            "AskUserQuestion",
        ],
    )
    def test_leaves_unmappable_or_already_valid_text_alone(self, source: str) -> None:
        assert rewrite_text(source) == source


class TestUnknownSkillMentions:
    def test_reports_names_without_a_skill(self) -> None:
        text = "use Dev10x:git and Dev10x:gone, not $Dev10x:git"
        assert unknown_skill_mentions(text, ["git"]) == ["gone"]

    def test_ignores_path_segments(self) -> None:
        assert unknown_skill_mentions("cache/Dev10x:gone", []) == []


class TestRewriteLinks:
    source = PurePosixPath("skills/git-commit/SKILL.md")
    target = PurePosixPath("codex/skills/git-commit/SKILL.md")
    copied = frozenset(
        {
            PurePosixPath("skills/git-commit/instructions.md"),
            PurePosixPath("skills/git-fixup/SKILL.md"),
        }
    )

    existing = copied | {
        PurePosixPath("references/git-commits.md"),
        PurePosixPath("skills/git-commit/scripts/run.sh"),
    }

    def rewrite(self, text: str) -> str:
        return rewrite_links(
            text,
            source=self.source,
            target=self.target,
            copied=self.copied,
            exists=self.existing.__contains__,
        )

    @pytest.mark.parametrize(
        ("link", "expected"),
        [
            ("instructions.md", "instructions.md"),
            ("instructions.md#step-2", "instructions.md#step-2"),
            ("../git-fixup/SKILL.md", "../git-fixup/SKILL.md"),
            ("../../references/git-commits.md", "../../../references/git-commits.md"),
            ("scripts/run.sh", "../../../skills/git-commit/scripts/run.sh"),
        ],
    )
    def test_relative_links_point_at_the_same_file_from_the_new_location(
        self, link: str, expected: str
    ) -> None:
        assert self.rewrite(f"[x]({link})") == f"[x]({expected})"

    @pytest.mark.parametrize(
        "link",
        [
            "https://example.com/a",
            "#anchor",
            "/abs/path.md",
            "mailto:a@b.c",
            "${CLAUDE_PLUGIN_ROOT}/x.md",
            "../../../../outside.md",
        ],
    )
    def test_external_absolute_and_escaping_links_are_untouched(self, link: str) -> None:
        assert self.rewrite(f"[x]({link})") == f"[x]({link})"

    @pytest.mark.parametrize(
        "link", ["{permalink}", "REPO_URL/pull/NUMBER/commits/FULL_HASH", "url", "missing.md"]
    )
    def test_template_placeholders_and_missing_targets_are_untouched(self, link: str) -> None:
        assert self.rewrite(f"[x]({link})") == f"[x]({link})"

    def test_links_use_forward_slashes_whatever_the_os_separator(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import ntpath
        import os

        monkeypatch.setattr(os, "path", ntpath)
        assert self.rewrite("[x](scripts/run.sh)") == (
            "[x](../../../skills/git-commit/scripts/run.sh)"
        )

    def test_link_title_is_kept(self) -> None:
        assert self.rewrite('[x](scripts/run.sh "Run")') == (
            '[x](../../../skills/git-commit/scripts/run.sh "Run")'
        )


class TestCodexDescription:
    def test_folds_whitespace_and_replaces_angle_brackets(self) -> None:
        assert codex_description("Use\n  <thing>\n") == "Use ‹thing›"

    def test_long_description_is_cut_at_a_word(self) -> None:
        result = codex_description("word " * 400)
        assert len(result) <= DESCRIPTION_MAX_LENGTH
        assert result.endswith("word…")

    def test_missing_description_becomes_empty(self) -> None:
        assert codex_description(None) == ""


class TestTranslateSkills:
    def test_writes_one_codex_skill_per_upstream_skill(self, plugin: Path) -> None:
        tree = translate_skills(plugin)
        skills = {path.parts[2] for path in tree.files}
        assert skills == {"foreman", "git-commit", "git-fixup"}

    def test_scripts_evals_and_non_text_files_stay_upstream(self, plugin: Path) -> None:
        paths = {path.as_posix() for path in translate_skills(plugin).files}
        assert "codex/skills/git-commit/instructions.md" in paths
        assert "codex/skills/git-commit/references/defaults.yaml" in paths
        assert not any("/scripts/" in path or "/evals/" in path for path in paths)

    def test_skill_file_gets_codex_front_matter_and_preamble(self, plugin: Path) -> None:
        text = translate_skills(plugin).files[CODEX_SKILLS_RELPATH / "git-commit" / "SKILL.md"]
        front_matter, body = split_front_matter(text)
        assert front_matter == {
            "name": "git-commit",
            "description": (
                "Commit with ‹gitmoji›. DO NOT TRIGGER when: fixups (use Dev10x:git-fixup)."
            ),
            "metadata": {"upstream": "skills/git-commit/SKILL.md"},
        }
        assert "[../../references/claude-tool-equivalents.md]" in body
        assert "Not yet verified in Codex" not in body
        assert "$Dev10x:git-fixup" in body
        assert "`mcp__cli__push_safe`" in body
        assert f"`{PLUGIN_ROOT_PLACEHOLDER}/skills/git-commit/scripts/run.sh`" in body
        assert "[the script](../../../skills/git-commit/scripts/run.sh)" in body
        assert "[guide](../../../references/git-commits.md)" in body

    def test_sibling_markdown_and_yaml_are_rewritten(self, plugin: Path) -> None:
        files = translate_skills(plugin).files
        instructions = files[CODEX_SKILLS_RELPATH / "git-commit" / "instructions.md"]
        defaults = files[CODEX_SKILLS_RELPATH / "git-commit" / "references" / "defaults.yaml"]
        assert instructions == "See [fixup](../git-fixup/SKILL.md) and `$Dev10x:py-test`.\n"
        assert defaults == "tool: mcp__cli__mktmp\n"

    def test_unverified_skills_are_explicit_only_and_flagged(self, plugin: Path) -> None:
        files = translate_skills(plugin).files
        policy = yaml.safe_load(files[CODEX_SKILLS_RELPATH / "foreman" / "agents" / "openai.yaml"])
        assert policy == {
            "interface": {"display_name": "Foreman"},
            "policy": {"allow_implicit_invocation": False},
        }
        assert "Not yet verified in Codex" in files[CODEX_SKILLS_RELPATH / "foreman" / "SKILL.md"]

    def test_verified_skills_stay_in_the_catalog(self, plugin: Path) -> None:
        files = translate_skills(plugin).files
        policy = yaml.safe_load(
            files[CODEX_SKILLS_RELPATH / "git-commit" / "agents" / "openai.yaml"]
        )
        assert policy["policy"]["allow_implicit_invocation"] is True

    def test_mentions_of_missing_skills_become_warnings(self, plugin: Path) -> None:
        assert translate_skills(plugin).warnings == [
            "skills/foreman/SKILL.md: mentions Dev10x:retired-skill, which has no skill"
        ]

    def test_invalid_upstream_directory_name_fails_loudly(self, plugin: Path) -> None:
        write(plugin / "skills" / "Bad_Name" / "SKILL.md", "---\nname: x\n---\n")
        with pytest.raises(InvalidSkillName):
            translate_skills(plugin)

    @pytest.mark.parametrize(
        "text",
        [
            "# No front matter\n",
            "---\n- a list\n---\nbody\n",
            "---\nname: Dev10x:broken\n---\nbody\n",
            "---\nname: Dev10x:broken\ndescription: '   '\n---\nbody\n",
            "---\nname: Dev10x:broken\ndescription: [a, b]\n---\nbody\n",
        ],
    )
    def test_skill_without_a_usable_description_fails_naming_the_file(
        self, plugin: Path, text: str
    ) -> None:
        write(plugin / "skills" / "broken" / "SKILL.md", text)
        with pytest.raises(InvalidSkillFile, match="skills/broken/SKILL.md"):
            translate_skills(plugin)


class TestStalePaths:
    def test_missing_output_is_all_stale(self, plugin: Path) -> None:
        tree = translate_skills(plugin)
        assert stale_paths(plugin, tree) == sorted(tree.files)

    def test_written_output_is_fresh_until_an_extra_file_appears(self, plugin: Path) -> None:
        tree = translate_skills(plugin)
        for relative, content in tree.files.items():
            write(plugin / relative, content)
        assert stale_paths(plugin, tree) == []
        write(plugin / CODEX_SKILLS_RELPATH / "orphan" / "SKILL.md", "old\n")
        assert stale_paths(plugin, tree) == [CODEX_SKILLS_RELPATH / "orphan" / "SKILL.md"]

    def test_read_tree_of_absent_output_is_empty(self, tmp_path: Path) -> None:
        assert read_tree(tmp_path) == {}


class TestCodexSkillsCommand:
    def test_check_fails_on_stale_output_and_passes_after_writing(self, plugin: Path) -> None:
        runner = CliRunner()
        stale = runner.invoke(codex_skills, ["--root", str(plugin), "--check"])
        assert stale.exit_code == 1
        assert "STALE" in stale.output

        written = runner.invoke(codex_skills, ["--root", str(plugin)])
        assert written.exit_code == 0
        assert "for 3 skills" in written.output
        assert "Dev10x:retired-skill" in written.output

        fresh = runner.invoke(codex_skills, ["--root", str(plugin), "--check"])
        assert fresh.exit_code == 0

    def test_writing_removes_skills_that_no_longer_exist_upstream(self, plugin: Path) -> None:
        write(plugin / CODEX_SKILLS_RELPATH / "orphan" / "SKILL.md", "old\n")
        CliRunner().invoke(codex_skills, ["--root", str(plugin)])
        assert not (plugin / CODEX_SKILLS_RELPATH / "orphan").exists()

    def test_root_without_a_codex_plugin_manifest_is_refused(self, tmp_path: Path) -> None:
        write(tmp_path / "codex" / "skills" / "keep" / "SKILL.md", "keep\n")
        result = CliRunner().invoke(codex_skills, ["--root", str(tmp_path)])
        assert result.exit_code == 2
        assert "not a Dev10x plugin checkout" in result.output
        assert (tmp_path / "codex" / "skills" / "keep" / "SKILL.md").exists()

    def test_empty_upstream_skills_never_wipe_the_output(self, tmp_path: Path) -> None:
        (tmp_path / ".codex-plugin").mkdir()
        (tmp_path / "skills").mkdir()
        write(tmp_path / "codex" / "skills" / "keep" / "SKILL.md", "keep\n")
        result = CliRunner().invoke(codex_skills, ["--root", str(tmp_path)])
        assert result.exit_code == 1
        assert "refusing to empty" in result.output
        assert (tmp_path / "codex" / "skills" / "keep" / "SKILL.md").exists()

    def test_failed_write_keeps_the_previous_output_and_leaves_no_staging(
        self, plugin: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write(plugin / CODEX_SKILLS_RELPATH / "keep" / "SKILL.md", "keep\n")

        def fail_write(self: Path, *args: object, **kwargs: object) -> int:
            raise OSError("disk full")

        monkeypatch.setattr(Path, "write_text", fail_write)
        result = CliRunner().invoke(codex_skills, ["--root", str(plugin)])
        monkeypatch.undo()
        assert isinstance(result.exception, OSError)
        assert (plugin / CODEX_SKILLS_RELPATH / "keep" / "SKILL.md").read_text() == "keep\n"
        assert [p.name for p in (plugin / "codex").iterdir()] == ["skills"]

    def test_written_output_is_world_readable(self, plugin: Path) -> None:
        CliRunner().invoke(codex_skills, ["--root", str(plugin)])
        assert (plugin / CODEX_SKILLS_RELPATH).stat().st_mode & 0o777 == 0o755


class TestCommittedCodexSkills:
    @pytest.fixture(scope="class")
    def committed(self) -> dict[PurePosixPath, str]:
        return read_tree(REPO_ROOT)

    def test_committed_tree_matches_upstream_skills(self) -> None:
        stale = stale_paths(REPO_ROOT, translate_skills(REPO_ROOT))
        assert stale == [], "run `dev10x skill codex-skills` and commit codex/skills/"

    def test_every_verified_skill_is_generated(self, committed: dict[PurePosixPath, str]) -> None:
        generated = {path.parts[2] for path in committed}
        assert VERIFIED_SKILLS <= generated

    def test_skill_files_pass_codex_validator_rules(
        self, committed: dict[PurePosixPath, str]
    ) -> None:
        skill_files = {
            p: t for p, t in committed.items() if p.name == "SKILL.md" and len(p.parts) == 4
        }
        assert skill_files
        for path, text in skill_files.items():
            front_matter, _ = split_front_matter(text)
            assert set(front_matter) <= CODEX_VALIDATOR_KEYS, path
            assert front_matter["name"] == path.parts[2], path
            assert CODEX_NAME_RE.match(front_matter["name"]), path
            description = front_matter["description"]
            assert 0 < len(description) <= DESCRIPTION_MAX_LENGTH, path
            assert "<" not in description and ">" not in description, path

    def test_unresolved_links_are_upstream_placeholders_left_untouched(
        self, committed: dict[PurePosixPath, str]
    ) -> None:
        broken = []
        for path, text in committed.items():
            if path.suffix != ".md":
                continue
            upstream = REPO_ROOT / "skills" / path.relative_to(CODEX_SKILLS_RELPATH)
            upstream_links = set(MARKDOWN_LINK_RE.findall(upstream.read_text(encoding="utf-8")))
            for link in MARKDOWN_LINK_RE.findall(text):
                target = link.partition("#")[0]
                if not target or re.match(r"^(?:[a-z][a-z0-9+.-]*:|/|~|<|\$)", target, re.I):
                    continue
                if not (REPO_ROOT / path.parent / target).exists() and link not in upstream_links:
                    broken.append(f"{path}: {link}")
        assert broken == []

    def test_tool_equivalents_reference_exists(self) -> None:
        assert (REPO_ROOT / TOOL_EQUIVALENTS_RELPATH).is_file()

    def test_codex_manifest_loads_only_the_generated_skills(self) -> None:
        manifest = json.loads((REPO_ROOT / ".codex-plugin" / "plugin.json").read_text())
        assert manifest["skills"] == f"./{CODEX_SKILLS_RELPATH}/"
