"""Benchmark: CLI startup time per command (GH-749).

Measures cold-start latency for key CLI entry points to catch
import-chain regressions. Primary gate: validate-bash median < 150 ms.

Run benchmarks:
    pytest tests/benchmarks/test_startup_time.py --benchmark-only

Run gate tests only:
    pytest tests/benchmarks/test_startup_time.py -k gate
"""

from __future__ import annotations

import json
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
BASELINE_FILE = FIXTURES_DIR / "startup_baseline.json"
MAX_MEDIAN_MS = 150
GATE_RUNS = 10
REGRESSION_FACTOR = 2.0


def _find_dev10x() -> str:
    path = shutil.which("dev10x")
    if not path:
        pytest.skip("dev10x entry point not on PATH")
    return path


def _run_cli(
    cmd: list[str],
    stdin_data: str = "{}",
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _measure_median_ms(
    cmd: list[str],
    runs: int = GATE_RUNS,
) -> float:
    times: list[float] = []
    for _ in range(runs):
        start = time.perf_counter()
        _run_cli(cmd=cmd)
        elapsed_ms = (time.perf_counter() - start) * 1000
        times.append(elapsed_ms)
    return statistics.median(times)


def _load_baseline() -> dict[str, float]:
    if not BASELINE_FILE.exists():
        return {}
    data = json.loads(BASELINE_FILE.read_text())
    return {k: v["median_ms"] for k, v in data.items()}


@pytest.fixture(scope="module")
def dev10x() -> str:
    return _find_dev10x()


@pytest.fixture(scope="module")
def baseline() -> dict[str, float]:
    return _load_baseline()


# ── Detailed benchmarks (run with --benchmark-only) ─────────────


@pytest.mark.benchmark(group="cli-startup")
class TestCLIStartupBenchmark:
    def test_hook_validate_bash(self, benchmark, dev10x: str) -> None:
        result = benchmark(_run_cli, cmd=[dev10x, "hook", "validate-bash"])
        assert result.returncode == 0

    def test_hook_session_tmpdir(self, benchmark, dev10x: str) -> None:
        result = benchmark(_run_cli, cmd=[dev10x, "hook", "session", "tmpdir"])
        assert result.returncode == 0

    def test_hook_skill_metrics(self, benchmark, dev10x: str) -> None:
        result = benchmark(_run_cli, cmd=[dev10x, "hook", "skill", "metrics"])
        assert result.returncode == 0

    def test_mcp_server_cold_import(self, benchmark) -> None:
        cmd = [sys.executable, "-c", "from dev10x.mcp.server_cli import server"]
        result = benchmark(_run_cli, cmd=cmd)
        assert result.returncode == 0


# ── Gate tests (always run) ─────────────────────────────────────


class TestStartupTimeGate:
    def test_validate_bash_under_threshold(self, dev10x: str) -> None:
        median = _measure_median_ms(cmd=[dev10x, "hook", "validate-bash"])
        assert median < MAX_MEDIAN_MS, (
            f"validate-bash median {median:.1f}ms exceeds {MAX_MEDIAN_MS}ms"
        )

    @pytest.mark.parametrize(
        "name",
        ["hook_validate_bash", "hook_session_tmpdir", "hook_skill_metrics", "mcp_server_import"],
    )
    def test_baseline_regression(
        self,
        name: str,
        dev10x: str,
        baseline: dict[str, float],
    ) -> None:
        if not baseline:
            pytest.skip("No baseline file at tests/fixtures/startup_baseline.json")
        if name not in baseline:
            pytest.skip(f"No baseline entry for {name}")

        cmd_map = {
            "hook_validate_bash": [dev10x, "hook", "validate-bash"],
            "hook_session_tmpdir": [dev10x, "hook", "session", "tmpdir"],
            "hook_skill_metrics": [dev10x, "hook", "skill", "metrics"],
            "mcp_server_import": [
                sys.executable,
                "-c",
                "from dev10x.mcp.server_cli import server",
            ],
        }
        median = _measure_median_ms(cmd=cmd_map[name])
        threshold = baseline[name] * REGRESSION_FACTOR
        assert median < threshold, (
            f"{name}: {median:.1f}ms exceeds "
            f"{REGRESSION_FACTOR}x baseline ({baseline[name]:.1f}ms)"
        )
