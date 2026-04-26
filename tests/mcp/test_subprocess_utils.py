"""Tests for dev10x.mcp.subprocess_utils."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from dev10x.mcp.subprocess_utils import (
    get_plugin_root,
    parse_json_output,
    parse_key_value_output,
    run_script,
)


class TestGetPluginRoot:
    def test_returns_path_two_levels_above_lib(self) -> None:
        result = get_plugin_root()

        assert isinstance(result, Path)
        assert result.name != "lib"
        assert (result / "servers").is_dir()


class TestRunScript:
    def test_raises_file_not_found_for_missing_script(self) -> None:
        with pytest.raises(FileNotFoundError, match="Script not found"):
            run_script("nonexistent/script.sh")

    @patch("dev10x.mcp.subprocess_utils.subprocess.run")
    def test_calls_subprocess_with_full_path(
        self,
        mock_run: patch,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="OK",
            stderr="",
        )
        plugin_root = get_plugin_root()
        script = "tests/mcp/conftest.py"

        run_script(script, "arg1", "arg2")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd[0] == str(plugin_root / script)
        assert cmd[1] == "arg1"
        assert cmd[2] == "arg2"

    @patch("dev10x.mcp.subprocess_utils.subprocess.run")
    def test_passes_env_vars(
        self,
        mock_run: patch,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="",
            stderr="",
        )
        script = "tests/mcp/conftest.py"

        run_script(script, env_vars={"MY_VAR": "my_value"})

        call_args = mock_run.call_args
        env = call_args[1]["env"]
        assert env["MY_VAR"] == "my_value"

    @patch("dev10x.mcp.subprocess_utils.subprocess.run")
    def test_captures_output_as_text(
        self,
        mock_run: patch,
    ) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="output",
            stderr="",
        )
        script = "tests/mcp/conftest.py"

        run_script(script)

        call_args = mock_run.call_args
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["text"] is True
        assert call_args[1]["check"] is False


class TestParseKeyValueOutput:
    def test_parses_single_pair(self) -> None:
        result = parse_key_value_output("KEY=value")

        assert result == {"KEY": "value"}

    def test_parses_multiple_pairs(self) -> None:
        text = "TRACKER=github\nTICKET_ID=GH-15\nFIXES_URL=http://example.com"

        result = parse_key_value_output(text)

        assert result == {
            "TRACKER": "github",
            "TICKET_ID": "GH-15",
            "FIXES_URL": "http://example.com",
        }

    def test_skips_empty_lines(self) -> None:
        text = "KEY1=val1\n\nKEY2=val2\n"

        result = parse_key_value_output(text)

        assert result == {"KEY1": "val1", "KEY2": "val2"}

    def test_skips_lines_without_equals(self) -> None:
        text = "KEY=value\nno-equals-here\nKEY2=val2"

        result = parse_key_value_output(text)

        assert result == {"KEY": "value", "KEY2": "val2"}

    def test_handles_equals_in_value(self) -> None:
        text = "URL=http://example.com?a=1&b=2"

        result = parse_key_value_output(text)

        assert result == {"URL": "http://example.com?a=1&b=2"}

    def test_returns_empty_dict_for_empty_input(self) -> None:
        result = parse_key_value_output("")

        assert result == {}


class TestParseJsonOutput:
    def test_parses_valid_json(self) -> None:
        data = {"key": "value", "count": 42}

        result = parse_json_output(json.dumps(data))

        assert result == data

    def test_raises_on_invalid_json(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            parse_json_output("not json")
