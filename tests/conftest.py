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
    "template": "PegKeeperTemplate",
    "pluggable-optimized": "PegKeeperPluggableOptimized",
    "mim": "PegKeeperMim",
}
_types = {
    "template": "template",
    "pluggable-optimized": "pluggable-optimized",
    "mim": "mim",
}


def pytest_addoption(parser):
    parser.addoption(
        "--type",
        action="store",
        default="template,pluggable-optimized,mim",
        help="comma-separated list of peg keeper types to test against",
    )
    parser.addoption(
        "--contracts",
        action="store",
        default="",
        help="comma-separated list of peg keeper name to test against",
    )
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
        "template: template-specific tests",
    )
    config.addinivalue_line(
        "markers",
        "pluggable: pluggable-specific tests",
    )
    config.addinivalue_line(
        "markers",
        "mim: mim-specific tests",
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
    peg_types = config.getoption("type").split(",")

    for item in items.copy():
        path = Path(item.fspath).relative_to(project._path)
        path_parts = path.parts[1:-1]
        params = item.callspec.params
        peg_type = _types[params["peg_keeper_name"]]

        if peg_type not in peg_types:
            items.remove(item)
            continue

        # Temporarily skip template tests
        if peg_type == "template":
            items.remove(item)
            continue

        # Skip template-specific and stable_swap tests for non template
        if peg_type != "template":
            if item.get_closest_marker(name="template") or "stable_swap" in path_parts:
                items.remove(item)
                continue

        # Skip pluggable-specific tests for non pluggable
        if peg_type == "template":
            if item.get_closest_marker(name="pluggable"):
                items.remove(item)
                continue

        # Skip mim-specific tests for non mim
        if peg_type != "mim":
            if item.get_closest_marker(name="mim"):
                items.remove(item)
                continue

    # hacky magic to ensure the correct number of tests is shown in collection report
    config.pluginmanager.get_plugin("terminalreporter")._numcollected = len(items)


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


@pytest.fixture(scope="session")
def peg_keeper_name(request):
    return request.param


@pytest.fixture(scope="session")
def peg_keeper_type(peg_keeper_name):
    return _types[peg_keeper_name]


@pytest.fixture(scope="module")
def swap(StableSwap, peg_keeper_type, coins, alice, is_forked):
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
def peg_keeper(peg_keeper_name, swap, admin, receiver, pegged, alice, is_forked):
    project = get_loaded_projects()[0]
    peg_keeper = getattr(project, _contracts[peg_keeper_name])

    abi = next(i["inputs"] for i in peg_keeper.abi if i["type"] == "constructor")
    args = {
        "_pool": swap,
        "_receiver": receiver,
        "_min_asymmetry": 2,
    }

    contract = peg_keeper.deploy(*[args[i["name"]] for i in abi], {"from": admin})

    if not is_forked:
        pegged.add_minter(contract, {"from": alice})

    yield contract


@pytest.fixture(scope="module")
def set_peg_keeper_func(swap, peg_keeper, alice, peg_keeper_type):
    def inner(address=peg_keeper):
        if peg_keeper_type == "template":
            swap.set_peg_keeper(address, {"from": alice})

    return inner


@pytest.fixture(scope="module")
def set_peg_keeper(set_peg_keeper_func):
    set_peg_keeper_func()


@pytest.fixture(scope="module")
def peg_keeper_updater(peg_keeper_type, charlie, swap):
    if peg_keeper_type != "template":
        return charlie


@pytest.fixture(scope="session")
def is_forked():
    yield "fork" in CONFIG.active_network["id"]
