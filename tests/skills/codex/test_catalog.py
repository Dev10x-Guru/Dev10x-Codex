from __future__ import annotations

import pytest

from dev10x.skills.codex.catalog import (
    DEFERRED_SKILLS,
    SKILL_CAVEATS,
    VERIFIED_SKILLS,
    codex_skill_for,
)


class TestCodexSkillFor:
    @pytest.mark.parametrize("skill", ["Dev10x:git-commit", "git-commit"])
    def test_verified_skill_maps_to_its_codex_reference(self, skill: str) -> None:
        assert codex_skill_for(skill) == "$Dev10x:git-commit"

    def test_skill_outside_the_verified_set_has_no_reference(self) -> None:
        assert codex_skill_for("Dev10x:work-on") is None

    def test_verified_set_is_the_r2_pipeline(self) -> None:
        assert len(VERIFIED_SKILLS) == 15
        assert {"git-commit", "gh-pr-create", "gh-pr-merge"} <= VERIFIED_SKILLS


class TestSkillStatus:
    def test_a_skill_is_never_both_verified_and_deferred(self) -> None:
        assert not VERIFIED_SKILLS & set(DEFERRED_SKILLS)

    def test_deferred_skills_carry_no_caveat(self) -> None:
        assert not set(SKILL_CAVEATS) & set(DEFERRED_SKILLS)

    def test_caveats_fit_on_one_line_without_markdown_breaks(self) -> None:
        for name, caveat in SKILL_CAVEATS.items():
            assert caveat.strip() == caveat and "\n" not in caveat, name
            assert len(caveat) <= 200, name
