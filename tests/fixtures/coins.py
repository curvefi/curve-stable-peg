import pytest
from brownie import Contract


@pytest.fixture(scope="module")
def peg(ERC20Mock, alice, is_forked):
    if is_forked:
        yield Contract("0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490")  # 3CRV
    else:
        yield ERC20Mock.deploy("Peg Coin", "Peg", 18, {"from": alice})


@pytest.fixture(scope="module")
def pegged(ERC20Pegged, alice, is_forked):
    if is_forked:
        yield Contract("0x99d8a9c45b2eca8864373a26d1459e3dff1e17f3")  # MIM
    else:
        yield ERC20Pegged.deploy("Pegged Coin", "Pegged", 18, {"from": alice})


@pytest.fixture(scope="module")
def coins(peg, pegged):
    yield [pegged, peg]


@pytest.fixture(scope="module")
def decimals(coins):
    yield [coin.decimals() for coin in coins]


@pytest.fixture(scope="module")
def n_coins(coins):
    yield len(coins)
