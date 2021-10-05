import pytest


@pytest.fixture(scope="module")
def peg(ERC20Mock, alice):
    yield ERC20Mock.deploy("Peg Coin", "Peg", 18, {"from": alice})


@pytest.fixture(scope="module")
def pegged(ERC20Pegged, alice):
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
