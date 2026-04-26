import pytest

from tests.fakers import (
    BashHookInputFaker,
    CompensationFaker,
    ConfigFaker,
    EditHookInputFaker,
    HookInputFaker,
    RuleFaker,
)


@pytest.fixture()
def hook_input_faker() -> type[HookInputFaker]:
    return HookInputFaker


@pytest.fixture()
def bash_hook_input_faker() -> type[BashHookInputFaker]:
    return BashHookInputFaker


@pytest.fixture()
def edit_hook_input_faker() -> type[EditHookInputFaker]:
    return EditHookInputFaker


@pytest.fixture()
def rule_faker() -> type[RuleFaker]:
    return RuleFaker


@pytest.fixture()
def compensation_faker() -> type[CompensationFaker]:
    return CompensationFaker


@pytest.fixture()
def config_faker() -> type[ConfigFaker]:
    return ConfigFaker
