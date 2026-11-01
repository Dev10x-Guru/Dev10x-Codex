from __future__ import annotations

import pytest

from dev10x.harness import HARNESS_ENV_VAR, Harness, current_harness, is_codex


class TestCurrentHarness:
    def test_defaults_to_codex_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(HARNESS_ENV_VAR, raising=False)
        assert current_harness() is Harness.CODEX
        assert is_codex() is True

    @pytest.mark.parametrize("value", ["", "codex", "gemini"])
    def test_falls_back_to_codex_for_anything_but_claude(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        monkeypatch.setenv(HARNESS_ENV_VAR, value)
        assert current_harness() is Harness.CODEX

    @pytest.mark.parametrize("value", ["claude", "CLAUDE", " claude "])
    def test_claude_opt_out_is_case_and_whitespace_insensitive(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        monkeypatch.setenv(HARNESS_ENV_VAR, value)
        assert current_harness() is Harness.CLAUDE
        assert is_codex() is False
