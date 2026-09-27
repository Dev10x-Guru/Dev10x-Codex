from __future__ import annotations

from pathlib import Path

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

import dev10x.skills.permission as permission_pkg
from dev10x.mcp.tool_annotations import (
    LOCAL_DESTRUCTIVE,
    LOCAL_WRITE,
    READ_LOCAL,
    READ_REMOTE,
    REMOTE_DESTRUCTIVE,
    REMOTE_WRITE,
    TOOL_ANNOTATIONS,
    apply_tool_annotations,
)
from dev10x.skills.permission.enumerate_mcp import (
    WRITE_TOOLS_NOT_SEEDED,
    discover_mcp_tools,
)

REPO_ROOT = Path(permission_pkg.__file__).resolve().parents[4]
CLI_PREFIX = "mcp__plugin_Dev10x_cli__"


def codex_requires_approval(annotations: ToolAnnotations | None) -> bool:
    destructive = annotations.destructiveHint if annotations else None
    if destructive is True:
        return True
    read_only = bool(annotations.readOnlyHint) if annotations else False
    if read_only:
        return False
    open_world = annotations.openWorldHint if annotations else None
    return (destructive if destructive is not None else True) or (
        open_world if open_world is not None else True
    )


def _short(tool: str) -> str:
    return tool.rsplit("__", 1)[-1]


def _discovered_short_names() -> list[str]:
    return [
        _short(tool) for tools in discover_mcp_tools(root=REPO_ROOT).values() for tool in tools
    ]


class TestClassificationCoverage:
    def test_every_discovered_tool_has_an_explicit_classification(self) -> None:
        unclassified = sorted(set(_discovered_short_names()) - set(TOOL_ANNOTATIONS))
        assert not unclassified, (
            "these MCP tools are registered without an approval classification — "
            "add each to TOOL_ANNOTATIONS in src/dev10x/mcp/tool_annotations.py "
            "after reading what the handler actually does:\n" + "\n".join(unclassified)
        )

    def test_classification_names_only_registered_tools(self) -> None:
        stale = sorted(set(TOOL_ANNOTATIONS) - set(_discovered_short_names()))
        assert not stale, "TOOL_ANNOTATIONS names unregistered tools:\n" + "\n".join(stale)

    def test_short_tool_names_are_unique_across_servers(self) -> None:
        names = _discovered_short_names()
        duplicates = sorted({name for name in names if names.count(name) > 1})
        assert not duplicates

    def test_every_classification_is_one_of_the_named_profiles(self) -> None:
        profiles = {
            id(profile)
            for profile in (
                READ_LOCAL,
                READ_REMOTE,
                LOCAL_WRITE,
                LOCAL_DESTRUCTIVE,
                REMOTE_WRITE,
                REMOTE_DESTRUCTIVE,
            )
        }
        stray = sorted(
            name for name, value in TOOL_ANNOTATIONS.items() if id(value) not in profiles
        )
        assert not stray


class TestWriteToolsNotSeededKeepPrompting:
    @pytest.mark.parametrize("tool", sorted(WRITE_TOOLS_NOT_SEEDED))
    def test_unseeded_write_is_not_read_only_and_codex_prompts(self, tool: str) -> None:
        annotations = TOOL_ANNOTATIONS[_short(tool)]
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is True or annotations.openWorldHint is True
        assert codex_requires_approval(annotations)


class TestCodexApprovalOutcome:
    @pytest.mark.parametrize(
        "tool",
        [
            "detect_base_branch",
            "pr_get",
            "issue_get",
            "ci_check_status",
            "task_index_get",
            "resolve_plugin_origin",
            "query",
        ],
    )
    def test_read_only_tool_runs_without_prompt(self, tool: str) -> None:
        assert TOOL_ANNOTATIONS[tool].readOnlyHint is True
        assert not codex_requires_approval(TOOL_ANNOTATIONS[tool])

    @pytest.mark.parametrize(
        "tool",
        ["merge_pr", "push_safe", "pr_close", "issue_close", "issue_comment_delete"],
    )
    def test_remote_destructive_tool_prompts(self, tool: str) -> None:
        assert TOOL_ANNOTATIONS[tool] is REMOTE_DESTRUCTIVE
        assert codex_requires_approval(TOOL_ANNOTATIONS[tool])

    @pytest.mark.parametrize("tool", ["issue_create", "pr_comment_reply", "create_pr"])
    def test_remote_additive_write_still_prompts(self, tool: str) -> None:
        assert TOOL_ANNOTATIONS[tool].openWorldHint is True
        assert codex_requires_approval(TOOL_ANNOTATIONS[tool])

    @pytest.mark.parametrize("tool", ["mktmp", "create_worktree", "task_index_append"])
    def test_closed_world_additive_write_runs_without_prompt(self, tool: str) -> None:
        assert TOOL_ANNOTATIONS[tool] is LOCAL_WRITE
        assert not codex_requires_approval(TOOL_ANNOTATIONS[tool])

    @pytest.mark.parametrize("tool", ["rebase_groom", "mass_rewrite", "pin_gate_preset"])
    def test_local_history_or_policy_rewrite_prompts(self, tool: str) -> None:
        assert TOOL_ANNOTATIONS[tool] is LOCAL_DESTRUCTIVE
        assert codex_requires_approval(TOOL_ANNOTATIONS[tool])

    def test_unannotated_tool_prompts(self) -> None:
        assert codex_requires_approval(None)


class TestApplyToolAnnotations:
    def test_known_tool_receives_its_classification(self) -> None:
        server = FastMCP(name="annotations-test")

        @server.tool()
        async def pr_get() -> dict:
            return {}

        applied = apply_tool_annotations(server, annotations={"pr_get": READ_REMOTE})

        assert applied.annotated == ["pr_get"]
        assert applied.unclassified == []
        assert server._tool_manager.get_tool("pr_get").annotations is READ_REMOTE

    def test_unclassified_tool_is_reported_and_left_unannotated(self) -> None:
        server = FastMCP(name="annotations-test")

        @server.tool()
        async def brand_new_tool() -> dict:
            return {}

        applied = apply_tool_annotations(server, annotations={})

        assert applied.unclassified == ["brand_new_tool"]
        assert server._tool_manager.get_tool("brand_new_tool").annotations is None

    def test_server_without_tool_manager_keeps_serving_unannotated_and_logs_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level("ERROR", logger="dev10x.mcp.tool_annotations"):
            applied = apply_tool_annotations(object(), annotations={"pr_get": READ_REMOTE})

        assert applied.annotated == []
        assert applied.unclassified == []
        assert "_tool_manager" in caplog.text


class TestAnnotationsReachTheWire:
    @pytest.mark.asyncio
    async def test_cli_server_list_tools_carries_annotations(self) -> None:
        from dev10x.mcp.server_cli import server

        listed = {tool.name: tool for tool in await server.list_tools()}

        assert listed["detect_base_branch"].annotations == READ_REMOTE
        assert listed["merge_pr"].annotations == REMOTE_DESTRUCTIVE
        assert listed["mktmp"].annotations == LOCAL_WRITE

    @pytest.mark.asyncio
    async def test_every_cli_tool_on_the_wire_is_annotated(self) -> None:
        from dev10x.mcp.server_cli import server

        bare = sorted(tool.name for tool in await server.list_tools() if tool.annotations is None)
        assert not bare

    @pytest.mark.asyncio
    async def test_db_server_query_is_read_only_on_the_wire(self) -> None:
        from dev10x.mcp.server_db import server

        listed = {tool.name: tool for tool in await server.list_tools()}

        assert listed["query"].annotations == READ_REMOTE
