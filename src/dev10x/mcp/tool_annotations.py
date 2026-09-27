from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from mcp.types import ToolAnnotations

log = logging.getLogger(__name__)

READ_LOCAL = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
READ_REMOTE = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
LOCAL_WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False)
LOCAL_DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=False)
REMOTE_WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True)
REMOTE_DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True)

_READ_LOCAL_TOOLS = (
    "audit_hook_log_path",
    "audit_hook_recent",
    "background_preamble",
    "detect_tracker",
    "human_review_status",
    "ide_status",
    "list_client_roots",
    "next_worktree_name",
    "permission_catalog_gap",
    "plan_sync_json_summary",
    "preset_pin_status",
    "resolve_plugin_origin",
    "rule_confidence_report",
    "slack_thread_is_forward",
    "supervisor_review_status",
    "task_index_get",
    "tracker_status",
    "usage_blocks",
)

_READ_REMOTE_TOOLS = (
    "author_reference_rules",
    "candidate_rules_report",
    "check_top_level_comments",
    "ci_check_status",
    "cluster_review_comments",
    "collect_prs",
    "detect_base_branch",
    "generate_commit_list",
    "issue_comments",
    "issue_get",
    "issue_list",
    "milestone_list",
    "pr_detect",
    "pr_get",
    "pr_list",
    "query",
    "triage_roster",
    "unresolved_threads",
    "validate_candidate_patterns",
    "verify_pr_state",
)

_LOCAL_WRITE_TOOLS = (
    "audit_analyze_actions",
    "audit_analyze_permissions",
    "audit_extract_session",
    "create_worktree",
    "generate_skill_index",
    "mktmp",
    "plan_sync_archive",
    "plan_sync_set_context",
    "pre_pr_checks",
    "resolve_gate",
    "run_node_tests",
    "run_tests",
    "task_index_append",
    "task_index_set",
)

_LOCAL_DESTRUCTIVE_TOOLS = (
    "mass_rewrite",
    "pin_gate_preset",
    "pin_ide",
    "pin_supervisor_review",
    "pin_tracker",
    "rebase_groom",
    "record_rule_feedback",
    "record_upgrade",
    "setup_aliases",
    "start_split_rebase",
    "update_paths",
)

_REMOTE_WRITE_TOOLS = (
    "create_pr",
    "issue_comment",
    "issue_create",
    "issue_reopen",
    "issues_bulk_create",
    "milestone_create",
    "milestone_reopen",
    "milestones_bulk_create",
    "minimize_comments",
    "post_summary_comment",
    "pr_comment_reply",
    "pr_issue_comment",
    "pr_notify",
    "pr_ready",
    "request_review",
    "request_sampling",
    "resolve_review_thread",
)

_REMOTE_DESTRUCTIVE_TOOLS = (
    "issue_close",
    "issue_comment_delete",
    "issue_comment_edit",
    "issue_edit",
    "issue_labels",
    "issues_bulk_edit",
    "merge_pr",
    "milestone_close",
    "milestone_edit",
    "pr_close",
    "pr_comments",
    "pr_labels",
    "pr_review_comment_edit",
    "pr_review_edit",
    "push_safe",
    "update_pr",
)


def _build_catalog() -> dict[str, ToolAnnotations]:
    catalog: dict[str, ToolAnnotations] = {}
    for names, profile in (
        (_READ_LOCAL_TOOLS, READ_LOCAL),
        (_READ_REMOTE_TOOLS, READ_REMOTE),
        (_LOCAL_WRITE_TOOLS, LOCAL_WRITE),
        (_LOCAL_DESTRUCTIVE_TOOLS, LOCAL_DESTRUCTIVE),
        (_REMOTE_WRITE_TOOLS, REMOTE_WRITE),
        (_REMOTE_DESTRUCTIVE_TOOLS, REMOTE_DESTRUCTIVE),
    ):
        for name in names:
            if name in catalog:
                raise ValueError(f"MCP tool {name!r} is classified twice")
            catalog[name] = profile
    return catalog


TOOL_ANNOTATIONS: Mapping[str, ToolAnnotations] = _build_catalog()


@dataclass
class AppliedAnnotations:
    annotated: list[str] = field(default_factory=list)
    unclassified: list[str] = field(default_factory=list)


def apply_tool_annotations(
    server: Any,
    *,
    annotations: Mapping[str, ToolAnnotations] = TOOL_ANNOTATIONS,
) -> AppliedAnnotations:
    applied = AppliedAnnotations()
    manager = getattr(server, "_tool_manager", None)
    if manager is None or not hasattr(manager, "list_tools"):
        log.error(
            "FastMCP server exposes no `_tool_manager.list_tools()`; serving every "
            "Dev10x tool unannotated, so harnesses will prompt for each call"
        )
        return applied

    for tool in manager.list_tools():
        classification = annotations.get(tool.name)
        if classification is None:
            applied.unclassified.append(tool.name)
            continue
        tool.annotations = classification
        applied.annotated.append(tool.name)

    if applied.unclassified:
        log.warning(
            "MCP tools registered without an approval classification (left "
            "unannotated, so harnesses prompt): %s",
            ", ".join(sorted(applied.unclassified)),
        )
    return applied
