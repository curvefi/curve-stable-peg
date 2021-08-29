import pytest

from brownie import Contract, chain


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


@pytest.fixture(scope="session")
def owner(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def admin(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[3]


@pytest.fixture(scope="session")
def receiver(accounts):
    yield accounts[4]


@pytest.fixture(scope="module")
def peg(ERC20Mock, owner, alice):
    contract = ERC20Mock.deploy("Peg Coin", "Peg", 18, {"from": owner})
    contract._mint_for_testing(alice, 11 * 10 ** contract.decimals(), {"from": owner})
    yield contract


@pytest.fixture(scope="module")
def pegged(ERC20Pegged, owner, alice):
    contract = ERC20Pegged.deploy("Pegged Coin", "Pegged", 18, {"from": owner})
    contract.add_minter(owner, {"from": owner})
    contract.mint(alice, 11 * 10 ** contract.decimals(), {"from": owner})
    yield contract


@pytest.fixture(scope="module")
def pool_token(ERC20LP, owner):
    yield ERC20LP.deploy("Curve Pool LP Token", "LP", {"from": owner})


@pytest.fixture(scope="module")
def pool(CurvePool, peg, pegged, pool_token, owner, alice):
    fee_denominator = 10 ** 10
    contract = CurvePool.deploy(
        owner,  # owner
        [peg, pegged],  # coins
        pool_token,  # pool token
        200 * 2,  # A
        0. * fee_denominator,  # fee 0.0004
        0.5 * fee_denominator,  # admin_fee
        {"from": owner}
    )
    pool_token.set_minter(contract, {"from": owner})

    # Provide initial liquidity
    amounts = [10 ** peg.decimals(), 10 ** pegged.decimals()]
    peg.approve(contract, amounts[0], {"from": alice})
    pegged.approve(contract, amounts[1], {"from": alice})
    contract.add_liquidity(amounts, 0, {"from": alice})
    yield contract


@pytest.fixture(scope="module")
def peg_keeper(PegKeeper, pool, receiver, admin, pegged, owner):
    contract = PegKeeper.deploy(pool, 0, receiver, {"from": admin})
    pegged.add_minter(contract, {"from": owner})
    yield contract
