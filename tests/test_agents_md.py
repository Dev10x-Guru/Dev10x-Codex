from __future__ import annotations

import re
from pathlib import Path

import pytest

import dev10x

REPO_ROOT = Path(dev10x.__file__).resolve().parents[2]
AGENTS_MD = REPO_ROOT / "AGENTS.md"
CODEX_PROJECT_DOC_MAX_BYTES = 32_768
REPO_PATH_RE = re.compile(r"`((?:\.?[\w-]+/)+(?:[\w.-]+\.(?:md|py|json|toml|rules|yaml))?)`")


def mentioned_paths() -> list[str]:
    return sorted(set(REPO_PATH_RE.findall(AGENTS_MD.read_text(encoding="utf-8"))))


class TestAgentsMd:
    def test_fits_the_codex_project_doc_budget(self) -> None:
        assert AGENTS_MD.stat().st_size <= CODEX_PROJECT_DOC_MAX_BYTES

    def test_names_repository_paths(self) -> None:
        assert len(mentioned_paths()) >= 10

    @pytest.mark.parametrize("path", mentioned_paths())
    def test_every_named_path_exists(self, path: str) -> None:
        assert (REPO_ROOT / path).exists(), f"AGENTS.md names {path}, which does not exist"
