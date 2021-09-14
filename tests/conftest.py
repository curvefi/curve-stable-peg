from pathlib import Path

import pytest
from brownie.project.main import get_loaded_projects

pytest_plugins = [
    "tests.fixtures.accounts",
    "tests.fixtures.coins",
    "tests.fixtures.functions",
]


def pytest_addoption(parser):
    parser.addoption(
        "--peg-keeper",
        action="store_true",
        default=False,
        help="only run tests for Peg Keeper",
    )
    parser.addoption(
        "--stable-swap",
        action="store_true",
        default=False,
        help="only run tests for Stable Swap",
    )
    parser.addoption(
        "--stable-peg",
        action="store_true",
        default=False,
        help="only run tests for TODO",
    )
    parser.addoption("--unitary", action="store_true", help="only run unit tests")
    parser.addoption(
        "--integration", action="store_true", help="only run integration tests"
    )


def pytest_configure(config):
    # add custom markers
    config.addinivalue_line(
        "markers",
        "itercoins: parametrize a test with one or more ranges, equal to the length "
        "of `coins` for the active pool",
    )


def _get_test_suits_flags(config) -> (bool, bool, bool):
    run_peg_keeper = config.getoption("peg_keeper")
    run_stable_swap = config.getoption("stable_swap")
    run_stable_peg = config.getoption("stable_peg")

    if not (run_peg_keeper or run_stable_swap or run_stable_peg):
        return True, True, True
    return run_peg_keeper, run_stable_swap, run_stable_peg


def pytest_ignore_collect(path, config):
    project = get_loaded_projects()[0]
    path = Path(path).relative_to(project._path)
    path_parts = path.parts[1:]

    if path.is_dir():
        return None

    if not path_parts:
        return None

    # always collect fixtures
    if path_parts[0] == "fixtures":
        return None

    # always allow forked tests
    if path_parts[-1] == "forked":
        return None

    run_peg_keeper, run_stable_swap, run_stable_peg = _get_test_suits_flags(config)
    if path_parts[0] == "peg_keeper" and not run_peg_keeper:
        return True

    if path_parts[0] == "stable_swap" and not run_stable_swap:
        return True

    if path_parts[0] == "stable_peg" and not run_stable_peg:
        return True

    # with the `--unitary` flag, skip any tests in an `integration` subdirectory
    if config.getoption("unitary") and "integration" in path_parts:
        return True

    # with the `--integration` flag, skip any tests NOT in an `integration` subdirectory
    if config.getoption("integration") and "integration" not in path_parts:
        return True


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


@pytest.fixture(scope="module")
def pool_token(ERC20LP, alice):
    yield ERC20LP.deploy("Curve Pool LP Token", "LP", {"from": alice})


@pytest.fixture(scope="module")
def swap(StablePegPool, coins, pool_token, alice):
    fee_denominator = 10 ** 10
    contract = StablePegPool.deploy(
        alice,  # owner
        coins,  # coins
        pool_token,  # pool token
        200 * 2,  # A
        0.0 * fee_denominator,  # fee
        0.5 * fee_denominator,  # admin_fee
        {"from": alice},
    )
    pool_token.set_minter(contract, {"from": alice})

    yield contract


@pytest.fixture(scope="module")
def peg_keeper(PegKeeper, swap, admin, pegged, alice):
    contract = PegKeeper.deploy(swap, 2, {"from": admin})
    pegged.add_minter(contract, {"from": alice})
    yield contract


@pytest.fixture(scope="module")
def set_peg_keeper(swap, peg_keeper, alice):
    swap.set_peg_keeper(peg_keeper, {"from": alice})
