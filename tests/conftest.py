from pathlib import Path

import pytest
from brownie.project.main import get_loaded_projects

pytest_plugins = [
    "tests.fixtures.accounts",
    "tests.fixtures.coins",
    "tests.fixtures.functions",
]


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


@pytest.fixture(scope="module")
def swap(StablePegPool, coins, alice):
    fee_denominator = 10 ** 10
    contract = StablePegPool.deploy(
        "StablePegPool",
        "LP",
        coins,  # coins
        [10 ** 18, 10 ** 18],
        200 * 2,  # A
        0.0 * fee_denominator,  # fee
        {"from": alice},
    )

    yield contract


@pytest.fixture(scope="module")
def pool_token(swap):
    yield swap
