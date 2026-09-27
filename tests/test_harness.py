from __future__ import annotations

import pytest

from dev10x.harness import HARNESS_ENV_VAR, Harness, current_harness, is_codex


class TestCurrentHarness:
    def test_defaults_to_claude_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(HARNESS_ENV_VAR, raising=False)
        assert current_harness() is Harness.CLAUDE
        assert is_codex() is False

    @pytest.mark.parametrize("value", ["codex", "CODEX", " codex "])
    def test_recognises_codex_case_and_whitespace_insensitively(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        monkeypatch.setenv(HARNESS_ENV_VAR, value)
        assert current_harness() is Harness.CODEX
        assert is_codex() is True

    @pytest.mark.parametrize("value", ["", "claude", "gemini"])
    def test_falls_back_to_claude_for_anything_else(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        monkeypatch.setenv(HARNESS_ENV_VAR, value)
        assert current_harness() is Harness.CLAUDE
