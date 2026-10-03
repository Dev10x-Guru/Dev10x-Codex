from __future__ import annotations

import tomllib
from pathlib import Path, PurePosixPath

import pytest
from click.testing import CliRunner

import dev10x.skills.codex as codex_pkg
from dev10x.commands.skill import codex_agents
from dev10x.skills.codex.agents import (
    CODEX_AGENTS_RELPATH,
    DEFAULT_EFFORT,
    InvalidAgentFile,
    agent_tools,
    codex_role_description,
    codex_role_name,
    is_read_only,
    reasoning_effort,
    render_instructions,
    render_role,
    toml_multiline_string,
    toml_string,
    translate_agents,
)
from dev10x.skills.codex.catalog import DEFERRED_AGENTS
from dev10x.skills.codex.translate import InvalidPluginRoot
from dev10x.skills.codex.tree import read_tree, stale_paths, write_tree

REPO_ROOT = Path(codex_pkg.__file__).resolve().parents[4]
ROLE_KEYS = {"name", "description", "model_reasoning_effort", "developer_instructions"}


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def agent(name: str, *, tools: str = "Glob, Grep, Read", model: str = "sonnet") -> str:
    return (
        "---\n"
        f"name: {name}\n"
        "description: |\n"
        f"  Review {name} changes.\n"
        "\n"
        "  Triggers: files matching **/x.py\n"
        f"tools: {tools}\n"
        f"model: {model}\n"
        "color: blue\n"
        "---\n"
        "\n"
        f"# {name}\n"
        "\n"
        "Call `mcp__plugin_Dev10x_cli__pr_get` and use Skill(Dev10x:git-commit).\n"
    )


@pytest.fixture
def plugin(tmp_path: Path) -> Path:
    write(tmp_path / "agents" / "code-reviewer.md", agent("code-reviewer", model="opus"))
    write(
        tmp_path / "agents" / "pytest-test-writer.md",
        agent("pytest-test-writer", tools="Glob, Grep, Read, Edit, Write"),
    )
    write(tmp_path / "agents" / "permission-auditor.md", agent("permission-auditor"))
    return tmp_path


class TestCodexRoleName:
    def test_prefixes_the_agent_file_name(self) -> None:
        assert codex_role_name("reviewer-celery") == "Dev10x:reviewer-celery"

    @pytest.mark.parametrize("stem", ["Reviewer", "reviewer_celery", "-x", "a--b", ""])
    def test_rejects_names_outside_the_upstream_convention(self, stem: str) -> None:
        with pytest.raises(InvalidAgentFile, match="not a valid agent file name"):
            codex_role_name(stem)


class TestAgentTools:
    source = PurePosixPath("agents/x.md")

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("Glob, Grep, Read", {"Glob", "Grep", "Read"}),
            (["Read", " Edit "], {"Read", "Edit"}),
            (None, set()),
            ("", set()),
        ],
    )
    def test_accepts_comma_lists_and_yaml_lists(self, value: object, expected: set) -> None:
        assert agent_tools(value, source=self.source) == expected

    @pytest.mark.parametrize("value", [{"Glob": None}, [None], ["Read", 3], 7])
    def test_unreadable_tools_value_names_the_file(self, value: object) -> None:
        with pytest.raises(InvalidAgentFile, match="agents/x.md: tools must be"):
            agent_tools(value, source=self.source)

    def test_tool_names_compare_without_case(self) -> None:
        assert is_read_only(frozenset({"read", "edit"})) is False

    @pytest.mark.parametrize(
        ("tools", "read_only"),
        [
            ({"Glob", "Grep", "Read"}, True),
            ({"Read", "Bash"}, True),
            ({"Read", "Edit"}, False),
            ({"Read", "Write"}, False),
            (set(), False),
        ],
    )
    def test_read_only_means_tools_were_listed_and_none_edit(
        self, tools: set[str], read_only: bool
    ) -> None:
        assert is_read_only(frozenset(tools)) is read_only


class TestReasoningEffort:
    @pytest.mark.parametrize(
        ("model", "effort"),
        [
            ("opus", "high"),
            ("sonnet", "medium"),
            ("haiku", "low"),
            (" Opus ", "high"),
            ("claude-opus-4-5", "high"),
        ],
    )
    def test_maps_claude_model_tiers_to_codex_effort(self, model: str, effort: str) -> None:
        assert reasoning_effort(model) == effort

    @pytest.mark.parametrize("model", ["", "  ", None])
    def test_missing_model_gets_the_default(self, model: object) -> None:
        assert reasoning_effort(model) == DEFAULT_EFFORT

    @pytest.mark.parametrize("model", ["inherit", "gpt-5.5", ["opus"], 4])
    def test_unrecognised_model_is_reported_as_unknown(self, model: object) -> None:
        assert reasoning_effort(model) is None


class TestTomlStrings:
    TRICKY = [
        "plain",
        'say "hi"',
        'three """ quotes and four """"',
        "back\\slash \\n literal",
        "tab\there",
        "bell\x07 and delete\x7f",
        "unicode — ✓",
        'ends with a quote"',
    ]

    @pytest.mark.parametrize("text", TRICKY)
    def test_basic_string_round_trips(self, text: str) -> None:
        assert tomllib.loads(f"v = {toml_string(text)}")["v"] == text

    @pytest.mark.parametrize("text", [*TRICKY, "line one\nline two\n", "\n"])
    def test_multiline_string_round_trips_with_one_trailing_newline(self, text: str) -> None:
        expected = text if text.endswith("\n") else f"{text}\n"
        assert tomllib.loads(f"v = {toml_multiline_string(text)}")["v"] == expected

    def test_multiline_string_keeps_ordinary_quotes_readable(self) -> None:
        assert 'name="x"' in toml_multiline_string('name="x"')


class TestRenderRole:
    def test_role_file_holds_only_keys_codex_accepts(self) -> None:
        role = tomllib.loads(
            render_role(
                stem="code-reviewer",
                description="Review code.",
                effort="high",
                instructions="Do it.\n",
            )
        )
        assert set(role) == ROLE_KEYS
        assert role["name"] == "Dev10x:code-reviewer"
        assert role["model_reasoning_effort"] == "high"

    def test_role_file_opens_with_a_codegen_banner(self) -> None:
        text = render_role(stem="x", description="d", effort="low", instructions="i")
        assert text.startswith("# Generated from agents/x.md by `dev10x skill codex-agents`")


class TestRenderInstructions:
    def test_read_only_agents_are_told_codex_will_not_stop_them(self) -> None:
        text = render_instructions(stem="x", body="Body.", read_only=True)
        assert "Read-only" in text
        assert "Codex cannot restrict your tools" in text

    def test_editing_agents_get_no_read_only_rule(self) -> None:
        assert "Read-only" not in render_instructions(stem="x", body="Body.", read_only=False)

    def test_body_names_are_translated_for_codex(self) -> None:
        text = render_instructions(
            stem="x",
            body="Use mcp__plugin_Dev10x_cli__pr_get then Skill(Dev10x:git)",
            read_only=False,
        )
        assert "mcp__cli__pr_get" in text
        assert "$Dev10x:git" in text
        assert "codex/references/claude-tool-equivalents.md" in text


class TestCodexRoleDescription:
    def test_folds_the_description_onto_one_line(self) -> None:
        source = PurePosixPath("agents/x.md")
        assert codex_role_description("a\n\n  b  c\n", source=source) == "a b c"

    @pytest.mark.parametrize("description", [None, "", "   ", ["list"]])
    def test_missing_description_names_the_file(self, description: object) -> None:
        with pytest.raises(InvalidAgentFile, match="agents/x.md"):
            codex_role_description(description, source=PurePosixPath("agents/x.md"))


class TestTranslateAgents:
    def test_one_role_per_agent_except_deferred_ones(self, plugin: Path) -> None:
        tree = translate_agents(plugin)
        assert tree.output == CODEX_AGENTS_RELPATH
        assert sorted(path.name for path in tree.files) == [
            "code-reviewer.toml",
            "pytest-test-writer.toml",
        ]

    def test_effort_and_read_only_follow_the_upstream_front_matter(self, plugin: Path) -> None:
        files = translate_agents(plugin).files
        reviewer = tomllib.loads(files[CODEX_AGENTS_RELPATH / "code-reviewer.toml"])
        writer = tomllib.loads(files[CODEX_AGENTS_RELPATH / "pytest-test-writer.toml"])
        assert reviewer["model_reasoning_effort"] == "high"
        assert "Read-only" in reviewer["developer_instructions"]
        assert writer["model_reasoning_effort"] == "medium"
        assert "Read-only" not in writer["developer_instructions"]

    def test_mismatched_front_matter_name_is_a_warning(self, plugin: Path) -> None:
        write(plugin / "agents" / "reviewer-x.md", agent("reviewer-y"))
        assert translate_agents(plugin).warnings == [
            "agents/reviewer-x.md: name 'reviewer-y' differs from the file name 'reviewer-x'"
        ]

    def test_unknown_model_falls_back_with_a_warning(self, plugin: Path) -> None:
        write(plugin / "agents" / "reviewer-x.md", agent("reviewer-x", model="inherit"))
        tree = translate_agents(plugin)
        role = tomllib.loads(tree.files[CODEX_AGENTS_RELPATH / "reviewer-x.toml"])
        assert role["model_reasoning_effort"] == DEFAULT_EFFORT
        assert tree.warnings == [
            "agents/reviewer-x.md: model 'inherit' names no known tier; using medium effort"
        ]

    def test_agent_with_an_empty_body_is_refused(self, plugin: Path) -> None:
        write(plugin / "agents" / "empty.md", "---\nname: empty\ndescription: Nothing.\n---\n\n")
        with pytest.raises(InvalidAgentFile, match="agents/empty.md: agent body is empty"):
            translate_agents(plugin)

    def test_agent_without_description_is_refused(self, plugin: Path) -> None:
        write(plugin / "agents" / "broken.md", "# no front matter\n")
        with pytest.raises(InvalidAgentFile, match="agents/broken.md"):
            translate_agents(plugin)

    @pytest.mark.parametrize("make_agents_dir", [True, False])
    def test_plugin_without_agents_is_refused(self, tmp_path: Path, make_agents_dir: bool) -> None:
        if make_agents_dir:
            (tmp_path / "agents").mkdir()
        with pytest.raises(InvalidPluginRoot, match="holds no agent files"):
            translate_agents(tmp_path)


class TestCodexAgentsCommand:
    def test_check_fails_on_stale_output_and_passes_after_writing(self, plugin: Path) -> None:
        runner = CliRunner()
        stale = runner.invoke(codex_agents, ["--root", str(plugin), "--check"])
        assert stale.exit_code == 1
        assert "STALE" in stale.output

        written = runner.invoke(codex_agents, ["--root", str(plugin)])
        assert written.exit_code == 0
        assert "Wrote 2 roles" in written.output

        fresh = runner.invoke(codex_agents, ["--root", str(plugin), "--check"])
        assert fresh.exit_code == 0
        assert "OK" in fresh.output

    def test_warnings_are_printed_after_writing(self, plugin: Path) -> None:
        write(plugin / "agents" / "reviewer-x.md", agent("reviewer-y"))
        result = CliRunner().invoke(codex_agents, ["--root", str(plugin)])
        assert result.exit_code == 0
        assert "differs from the file name" in result.output

    def test_root_without_agents_is_refused_and_output_kept(self, tmp_path: Path) -> None:
        write(tmp_path / "codex" / "agents" / "keep.toml", "keep\n")
        result = CliRunner().invoke(codex_agents, ["--root", str(tmp_path)])
        assert result.exit_code == 2
        assert "holds no agent files" in result.output
        assert (tmp_path / "codex" / "agents" / "keep.toml").exists()

    def test_invalid_agent_file_is_reported_by_path(self, plugin: Path) -> None:
        write(plugin / "agents" / "broken.md", "# no front matter\n")
        result = CliRunner().invoke(codex_agents, ["--root", str(plugin), "--check"])
        assert result.exit_code == 2
        assert "ERROR: agents/broken.md" in result.output

    def test_malformed_front_matter_is_reported_by_the_command(self, plugin: Path) -> None:
        write(plugin / "agents" / "bad.md", "---\ndescription: a: b: c\n---\n\nBody.\n")
        result = CliRunner().invoke(codex_agents, ["--root", str(plugin), "--check"])
        assert result.exit_code == 2
        assert "ERROR: agents/bad.md: front matter is not valid YAML" in result.output


class TestWriteAgentsTree:
    def test_written_roles_are_fresh_and_deferred_ones_removed(self, plugin: Path) -> None:
        write(plugin / "codex" / "agents" / "permission-auditor.toml", "old\n")
        tree = translate_agents(plugin)
        write_tree(plugin, tree)
        assert stale_paths(plugin, tree) == []
        assert not (plugin / "codex" / "agents" / "permission-auditor.toml").exists()


class TestCommittedCodexAgents:
    @pytest.fixture(scope="class")
    def committed(self) -> dict[PurePosixPath, str]:
        return read_tree(REPO_ROOT, CODEX_AGENTS_RELPATH)

    def test_committed_roles_match_upstream_agents(self) -> None:
        stale = stale_paths(REPO_ROOT, translate_agents(REPO_ROOT))
        assert stale == [], "run `dev10x skill codex-agents` and commit codex/agents/"

    def test_every_role_parses_with_only_codex_keys(
        self, committed: dict[PurePosixPath, str]
    ) -> None:
        assert committed
        for path, text in committed.items():
            role = tomllib.loads(text)
            assert set(role) == ROLE_KEYS, path
            assert role["name"] == f"Dev10x:{path.stem}", path
            assert role["description"].strip(), path
            assert role["developer_instructions"].strip(), path

    def test_deferred_agents_are_not_shipped(self, committed: dict[PurePosixPath, str]) -> None:
        assert not {path.stem for path in committed} & set(DEFERRED_AGENTS)

    def test_every_deferred_agent_still_exists_upstream(self) -> None:
        for name in DEFERRED_AGENTS:
            assert (REPO_ROOT / "agents" / f"{name}.md").is_file(), name
