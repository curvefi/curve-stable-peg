import brownie
import pytest
from brownie import ETH_ADDRESS

pytestmark = pytest.mark.usefixtures("add_initial_liquidity")


@pytest.mark.parametrize("idx", range(2))
@pytest.mark.parametrize("rate_mod", [0.9, 0.99, 1.01, 1.1])
def test_amount_received(chain, alice, swap, coins, decimals, idx, rate_mod):

    decimals = decimals[idx]
    wrapped = coins[idx]

    if hasattr(wrapped, "set_exchange_rate"):
        wrapped.set_exchange_rate(int(wrapped.get_rate() * rate_mod), {"from": alice})
        # time travel so rates take effect in pools that use rate caching
        chain.sleep(3600)
    else:
        rate_mod = 1.00001

    swap.remove_liquidity_one_coin(10 ** 18, idx, 0, {"from": alice})

    balance = wrapped.balanceOf(alice) if wrapped != ETH_ADDRESS else alice.balance()

    if rate_mod < 1:
        assert 10 ** decimals <= balance < 10 ** decimals / rate_mod
    else:
        assert 10 ** decimals // rate_mod <= balance <= 10 ** decimals


@pytest.mark.parametrize("idx", range(2))
@pytest.mark.parametrize("divisor", [1, 5, 42])
def test_lp_token_balance(alice, swap, pool_token, idx, divisor, n_coins, base_amount):
    amount = pool_token.balanceOf(alice) // divisor

    swap.remove_liquidity_one_coin(amount, idx, 0, {"from": alice})

    assert pool_token.balanceOf(alice) == n_coins * 10 ** 18 * base_amount - amount


@pytest.mark.parametrize("idx", range(2))
@pytest.mark.parametrize("rate_mod", [0.9, 1.1])
def test_expected_vs_actual(
    chain, alice, swap, coins, pool_token, n_coins, idx, rate_mod, base_amount
):
    amount = pool_token.balanceOf(alice) // 10
    wrapped = coins[idx]

    if hasattr(wrapped, "set_exchange_rate"):
        wrapped.set_exchange_rate(int(wrapped.get_rate() * rate_mod), {"from": alice})
        # time travel so rates take effect in pools that use rate caching
        chain.sleep(3600)
        chain.mine()

    expected = swap.calc_withdraw_one_coin(amount, idx)
    swap.remove_liquidity_one_coin(amount, idx, 0, {"from": alice})

    if coins[idx] == ETH_ADDRESS:
        assert alice.balance() == expected
    else:
        assert coins[idx].balanceOf(alice) == expected

    assert pool_token.balanceOf(alice) == n_coins * 10 ** 18 * base_amount - amount


@pytest.mark.parametrize("idx", range(2))
def test_below_min_amount(alice, swap, coins, pool_token, idx):
    amount = pool_token.balanceOf(alice)

    expected = swap.calc_withdraw_one_coin(amount, idx)
    with brownie.reverts():
        swap.remove_liquidity_one_coin(amount, idx, expected + 1, {"from": alice})


@pytest.mark.parametrize("idx", range(2))
def test_amount_exceeds_balance(bob, swap, coins, pool_token, idx):
    with brownie.reverts():
        swap.remove_liquidity_one_coin(1, idx, 0, {"from": bob})


def test_below_zero(alice, swap):
    with brownie.reverts():
        swap.remove_liquidity_one_coin(1, -1, 0, {"from": alice})


def test_above_n_coins(alice, swap, coins, n_coins):
    with brownie.reverts():
        swap.remove_liquidity_one_coin(1, n_coins, 0, {"from": alice})


@pytest.mark.parametrize("idx", range(2))
def test_event(alice, bob, swap, pool_token, idx, coins):
    pool_token.transfer(bob, 10 ** 18, {"from": alice})

    tx = swap.remove_liquidity_one_coin(10 ** 18, idx, 0, {"from": bob})

    event = tx.events["RemoveLiquidityOne"]
    assert event["provider"] == bob
    assert event["token_amount"] == 10 ** 18

    coin = coins[idx]
    if coin == ETH_ADDRESS:
        assert tx.internal_transfers[0]["value"] == event["coin_amount"]
    else:
        assert coin.balanceOf(bob) == event["coin_amount"]
