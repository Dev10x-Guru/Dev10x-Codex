"""Tests for CommitJtbdValidator."""

from __future__ import annotations

import pytest

from dev10x.validators.commit_jtbd import CommitJtbdValidator
from tests.fakers import BashHookInputFaker


def _make_input(*, command: str) -> BashHookInputFaker:
    return BashHookInputFaker.build(
        command=command,
    )


class TestShouldRun:
    @pytest.fixture()
    def validator(self) -> CommitJtbdValidator:
        return CommitJtbdValidator()

    def test_true_for_git_commit(self, validator: CommitJtbdValidator) -> None:
        inp = _make_input(command='git commit -m "Enable feature"')
        assert validator.should_run(inp=inp) is True

    def test_false_for_non_commit(self, validator: CommitJtbdValidator) -> None:
        inp = _make_input(command="git status")
        assert validator.should_run(inp=inp) is False


class TestValidate:
    @pytest.fixture()
    def validator(self) -> CommitJtbdValidator:
        return CommitJtbdValidator()

    @pytest.mark.parametrize(
        "verb",
        ["Add", "Update", "Remove", "Refactor", "Implement", "Configure"],
    )
    def test_blocks_implementation_verbs(self, validator: CommitJtbdValidator, verb: str) -> None:
        inp = _make_input(command=f'git commit -m "{verb} something"')
        result = validator.validate(inp=inp)
        assert result is not None
        assert "JTBD violation" in result.message

    @pytest.mark.parametrize(
        "verb",
        ["Enable", "Allow", "Support", "Prevent", "Ensure", "Simplify"],
    )
    def test_allows_jtbd_verbs(self, validator: CommitJtbdValidator, verb: str) -> None:
        inp = _make_input(command=f'git commit -m "{verb} something"')
        result = validator.validate(inp=inp)
        assert result is None

    def test_allows_fixup_commits(self, validator: CommitJtbdValidator) -> None:
        inp = _make_input(command='git commit -m "fixup! Add something"')
        result = validator.validate(inp=inp)
        assert result is None

    def test_allows_squash_commits(self, validator: CommitJtbdValidator) -> None:
        inp = _make_input(command='git commit -m "squash! Add something"')
        result = validator.validate(inp=inp)
        assert result is None

    def test_allows_amend(self, validator: CommitJtbdValidator) -> None:
        inp = _make_input(command='git commit --amend -m "Add something"')
        result = validator.validate(inp=inp)
        assert result is None

    def test_strips_gitmoji_and_ticket(self, validator: CommitJtbdValidator) -> None:
        inp = _make_input(command='git commit -m "\u2728 PAY-32 Enable multi-location routing"')
        result = validator.validate(inp=inp)
        assert result is None

    def test_blocks_gitmoji_with_impl_verb(self, validator: CommitJtbdValidator) -> None:
        inp = _make_input(command='git commit -m "\u2728 PAY-32 Add multi-location routing"')
        result = validator.validate(inp=inp)
        assert result is not None
