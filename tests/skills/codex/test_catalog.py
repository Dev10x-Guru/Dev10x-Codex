from __future__ import annotations

import pytest

from dev10x.skills.codex.catalog import VERIFIED_SKILLS, codex_skill_for


class TestCodexSkillFor:
    @pytest.mark.parametrize("skill", ["Dev10x:git-commit", "git-commit"])
    def test_verified_skill_maps_to_its_codex_reference(self, skill: str) -> None:
        assert codex_skill_for(skill) == "$Dev10x:git-commit"

    def test_skill_outside_the_verified_set_has_no_reference(self) -> None:
        assert codex_skill_for("Dev10x:work-on") is None

    def test_verified_set_is_the_r2_pipeline(self) -> None:
        assert len(VERIFIED_SKILLS) == 15
        assert {"git-commit", "gh-pr-create", "gh-pr-merge"} <= VERIFIED_SKILLS
