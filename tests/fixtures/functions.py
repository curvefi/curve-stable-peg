import pytest
from brownie import ZERO_ADDRESS, chain


@pytest.fixture(scope="module")
def base_amount():
    yield 1_000_000


@pytest.fixture(scope="module")
def initial_amounts(coins, base_amount):
    return [base_amount * 10 ** coin.decimals() for coin in coins]


@pytest.fixture(scope="module")
def add_initial_liquidity(swap, coins, initial_amounts, alice):
    for coin, amount in zip(coins, initial_amounts):
        coin._mint_for_testing(alice, amount)
        coin.approve(swap, amount, {"from": alice})

    swap.add_liquidity(initial_amounts, 0, {"from": alice})


def _mint(acct, coins, amounts):
    for coin, amount in zip(coins, amounts):
        coin._mint_for_testing(acct, amount, {"from": acct})


def _approve(acct, coins, pool, amounts):
    for coin, amount in zip(coins, amounts):
        coin.approve(pool, amount, {"from": acct})


@pytest.fixture(scope="module")
def mint_alice(alice, coins, initial_amounts):
    _mint(alice, coins, initial_amounts)


@pytest.fixture(scope="module")
def approve_alice(alice, coins, swap, initial_amounts):
    _approve(alice, coins, swap, initial_amounts)


@pytest.fixture(scope="module")
def mint_bob(bob, coins, initial_amounts):
    _mint(bob, coins, initial_amounts)


@pytest.fixture(scope="module")
def approve_bob(bob, coins, swap, initial_amounts):
    _approve(bob, coins, swap, initial_amounts)


# ---------------------------- Stable Swap functions ---------------------------


@pytest.fixture
def get_admin_balances(swap, n_coins):
    def _get_admin_balances():
        return [swap.admin_balances(i) for i in range(n_coins)]

    yield _get_admin_balances


@pytest.fixture(scope="module")
def set_fees(chain, swap, alice):
    def _set_fee_fixture_fn(fee, admin_fee):
        swap.commit_new_fee(fee, admin_fee, {"from": alice})
        chain.sleep(86400 * 3)
        swap.apply_new_fee({"from": alice})

    yield _set_fee_fixture_fn


# ---------------------------- Stable Peg functions ----------------------------


@pytest.fixture(scope="module")
def provide_token_to_peg_keeper(
    swap,
    peg,
    alice,
    peg_keeper_updater,
    peg_keeper,
    set_peg_keeper_func,
    initial_amounts,
):
    """Add 5x of peg, so Peg Keeper mints x, then remove 4x, so pool is balanced."""
    assert swap.balances(0) == swap.balances(1)
    amount = initial_amounts[1] * 5
    peg._mint_for_testing(alice, amount)
    peg.approve(swap, amount, {"from": alice})

    swap.add_liquidity(
        [0, amount],
        0,
        {"from": alice},
    )

    set_peg_keeper_func()
    peg_keeper.update({"from": peg_keeper_updater})
    set_peg_keeper_func(ZERO_ADDRESS)

    remove_amount = swap.balances(1) - swap.balances(0)
    swap.remove_liquidity_imbalance(
        [0, remove_amount],
        2 ** 256 - 1,
        {"from": alice},
    )

    assert swap.balances(0) == swap.balances(1)
    chain.sleep(15 * 60)


@pytest.fixture(scope="module")
def balance_change_after_provide(swap, coins):
    def _inner(diff: int):
        # diff should be positive
        assert swap.balances(0) + (diff - diff // 5) == swap.balances(1)
        assert coins[0].balanceOf(swap) + (diff - diff // 5) == coins[1].balanceOf(swap)

    return _inner


@pytest.fixture(scope="module")
def balance_change_after_withdraw(swap, coins):
    def _inner(diff: int):
        # diff should be positive
        assert swap.balances(0) - (diff - diff // 5) == swap.balances(1)
        assert coins[0].balanceOf(swap) - (diff - diff // 5) == coins[1].balanceOf(swap)

    return _inner


# TODO run only for MIM tests
@pytest.fixture(scope="module")
def provide_pegged_to_peg_keeper(peg_keeper, pegged, base_amount, alice):
    amount = base_amount * 50 * 10 ** pegged.decimals()

    pegged._mint_for_testing(alice, amount)
    pegged.transfer(peg_keeper, amount, {"from": alice})
