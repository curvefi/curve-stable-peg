from pathlib import Path

import pytest
from brownie import ZERO_ADDRESS, Contract
from brownie._config import CONFIG
from brownie.project.main import get_loaded_projects

pytest_plugins = [
    "tests.fixtures.accounts",
    "tests.fixtures.coins",
    "tests.fixtures.functions",
]


# Metadata of each peg keeper
_contracts = {
    "pluggable-optimized": "PegKeeperPluggableOptimized",
    "mim": "PegKeeperMim",
}


def pytest_addoption(parser):
    parser.addoption(
        "--contracts",
        action="store",
        default="",
        help="comma-separated list of peg keeper name to test against",
    )
    parser.addoption("--unitary", action="store_true", help="only run unit tests")
    parser.addoption(
        "--integration", action="store_true", help="only run integration tests"
    )
    parser.addoption(
        "--forked-tests",
        action="store_true",
        default=False,
        help="only run forked tests",
    )


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

    # Run forked tests only when forked
    if config.getoption("forked_tests") and "forked" in path_parts:
        return None

    # Skip other tests when forked or forked tests when not
    if config.getoption("forked_tests") or "forked" in path_parts:
        return True

    # with the `--unitary` flag, skip any tests in an `integration` subdirectory
    if config.getoption("unitary") and "integration" in path_parts:
        return True

    # with the `--integration` flag, skip any tests NOT in an `integration` subdirectory
    if config.getoption("integration") and "integration" not in path_parts:
        return True


def pytest_generate_tests(metafunc):
    cli_options = metafunc.config.getoption("contracts").split(",")
    if cli_options[0] == "":
        cli_options = _contracts.keys()
    metafunc.parametrize(
        "peg_keeper_name",
        cli_options,
        indirect=True,
        ids=[f"(PegKeeper={i})" for i in cli_options],
        scope="session",
    )


def pytest_collection_modifyitems(config, items):
    project = get_loaded_projects()[0]

    for item in items.copy():
        path = Path(item.fspath).relative_to(project._path)
        path_parts = path.parts[1:]
        params = item.callspec.params
        peg_keeper_name = params["peg_keeper_name"]

        if peg_keeper_name != "mim":
            if "test_mim.py" in path_parts:
                items.remove(item)
                continue

    # hacky magic to ensure the correct number of tests is shown in collection report
    config.pluginmanager.get_plugin("terminalreporter")._numcollected = len(items)


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


@pytest.fixture(scope="session")
def is_forked():
    yield "fork" in CONFIG.active_network["id"]


@pytest.fixture(scope="session")
def peg_keeper_name(request):
    return request.param


@pytest.fixture(scope="module")
def swap(StableSwap, coins, alice, is_forked):
    if is_forked:
        yield Contract(
            "0x5a6A4D54456819380173272A5E8E9B9904BdF41B"
        )  # MIM Pool Swap Address
    else:
        yield StableSwap.deploy(
            "Test",  # name
            "TEST",  # symbol
            coins + [ZERO_ADDRESS] * 2,  # coins[4]
            [10 ** 18] * 4,  # rate_multipliers[4]
            200 * 2,  # A
            0,  # fee
            {"from": alice},
        )


@pytest.fixture(scope="module")
def peg_keeper(
    peg_keeper_name, swap, admin, receiver, pegged, alice, initial_amounts, is_forked
):
    project = get_loaded_projects()[0]
    peg_keeper = getattr(project, _contracts[peg_keeper_name])

    abi = next(i["inputs"] for i in peg_keeper.abi if i["type"] == "constructor")
    args = {
        "_pool": swap,
        "_receiver": receiver,
        "_min_asymmetry": 2,
        "_caller_share": 2 * 10 ** 4,
    }

    contract = peg_keeper.deploy(*[args[i["name"]] for i in abi], {"from": admin})

    if not is_forked:
        pegged.add_minter(contract, {"from": alice})

    if peg_keeper_name == "mim":
        pegged._mint_for_testing(contract, 10 * initial_amounts[0], {"from": alice})

    yield contract


@pytest.fixture(scope="module")
def peg_keeper_updater(charlie, swap):
    return charlie
