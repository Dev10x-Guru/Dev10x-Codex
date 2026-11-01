from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from dev10x.harness import HARNESS_ENV_VAR, Harness

REPO_ROOT = Path(__file__).resolve().parent

UPSTREAM_TESTS_ASSERTING_CLAUDE_OUTPUT = frozenset(
    {
        "tests/hooks/test_hook_transport.py",
        "tests/hooks/test_permission_denied.py",
        "tests/hooks/test_validate_edit_write.py",
        "tests/validators/test_dispatcher.py",
        "tests/validators/test_skill_redirect.py",
    }
)

PLAN_SYNC_IS_OFF = "plan-sync writes are off in Dev10x-Codex (#13, #36)"
SKILLS_INDEX_IS_OFF = "Codex SessionStart leaves out the Claude skills index"

UPSTREAM_TESTS_OF_CLAUDE_ONLY_FEATURES: dict[str, str] = {
    "tests/hooks/test_orchestrators.py::TestSkillsIndexWiring::"
    "test_orchestrator_includes_index_in_envelope": SKILLS_INDEX_IS_OFF,
    "tests/mcp/test_cli_server.py::TestPlanSyncArchive::": PLAN_SYNC_IS_OFF,
    "tests/mcp/test_cli_server.py::TestPlanSyncSetContext::": PLAN_SYNC_IS_OFF,
    "tests/mcp/test_plan_tools.py::TestPlanSyncArchiveErrorContract::": PLAN_SYNC_IS_OFF,
    "tests/mcp/test_plan_tools.py::TestPlanSyncSetContextErrorContract::": PLAN_SYNC_IS_OFF,
    "tests/mcp/test_plan_tools.py::TestPlanToolsCwdActivation::"
    "test_archive_activates_cwd": PLAN_SYNC_IS_OFF,
    "tests/mcp/test_plan_tools.py::TestPlanToolsCwdActivation::"
    "test_set_context_activates_cwd": PLAN_SYNC_IS_OFF,
}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        for prefix, reason in UPSTREAM_TESTS_OF_CLAUDE_ONLY_FEATURES.items():
            if item.nodeid.startswith(prefix):
                item.add_marker(pytest.mark.skip(reason=reason))
                break


@pytest.fixture(autouse=True)
def _run_upstream_claude_output_tests_as_claude(
    request: pytest.FixtureRequest,
) -> Generator[None, None, None]:
    test_file = Path(request.node.path).resolve()
    with pytest.MonkeyPatch.context() as harness_env:
        if test_file.is_relative_to(REPO_ROOT):
            relative = test_file.relative_to(REPO_ROOT).as_posix()
            if relative in UPSTREAM_TESTS_ASSERTING_CLAUDE_OUTPUT:
                harness_env.setenv(HARNESS_ENV_VAR, Harness.CLAUDE.value)
        yield
