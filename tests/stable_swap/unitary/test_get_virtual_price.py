import pytest
from brownie import ETH_ADDRESS

MAX_FEE = 5 * 10 ** 9


@pytest.fixture(scope="module", autouse=True, params=[1.1, 0.9])
def setup(
    chain, alice, coins, add_initial_liquidity, approve_bob, mint_bob, set_fees, request
):
    set_fees(MAX_FEE, MAX_FEE)

    for i, coin in enumerate(coins, start=1):
        if hasattr(coin, "set_exchange_rate"):
            rate_mod = request.param
            if rate_mod > 1:
                rate_mod += i / 20
            else:
                rate_mod -= i / 20
            rate = int(coin.get_rate() * rate_mod)
            coin.set_exchange_rate(rate, {"from": alice})

    # time travel so rates take effect in pools that use rate caching
    chain.sleep(3600)


def test_number_go_up(bob, swap, initial_amounts, coins, n_coins):
    virtual_price = swap.get_virtual_price()

    for i, amount in enumerate(initial_amounts):
        amounts = [0] * n_coins
        amounts[i] = amount
        value = amount if coins[i] == ETH_ADDRESS else 0
        swap.add_liquidity(amounts, 0, {"from": bob, "value": value})

        new_virtual_price = swap.get_virtual_price()
        assert new_virtual_price > virtual_price
        virtual_price = new_virtual_price


@pytest.mark.parametrize("idx", range(2))
# @pytest.mark.skip_pool("busd", "compound", "pax", "ren", "sbtc", "susd", "usdt", "y")
def test_remove_one_coin(alice, swap, pool_token, idx):
    amount = pool_token.balanceOf(alice) // 10

    virtual_price = swap.get_virtual_price()
    swap.remove_liquidity_one_coin(amount, idx, 0, {"from": alice})

    assert swap.get_virtual_price() > virtual_price


@pytest.mark.parametrize("idx", range(2))
def test_remove_imbalance(
    alice, swap, coins, pool_token, idx, initial_amounts, base_amount, n_coins
):
    amounts = [i // 2 for i in initial_amounts]
    amounts[idx] = 0

    virtual_price = swap.get_virtual_price()
    swap.remove_liquidity_imbalance(
        amounts, n_coins * 10 ** 18 * base_amount, {"from": alice}
    )

    assert swap.get_virtual_price() > virtual_price


def test_remove(alice, swap, coins, pool_token, initial_amounts, n_coins):
    withdraw_amount = sum(initial_amounts) // 2

    virtual_price = swap.get_virtual_price()
    swap.remove_liquidity(withdraw_amount, [0] * n_coins, {"from": alice})

    assert swap.get_virtual_price() >= virtual_price


@pytest.mark.parametrize("sending,receiving", [(0, 1), (1, 0)])
def test_exchange(bob, swap, sending, receiving, coins, decimals):
    virtual_price = swap.get_virtual_price()

    amount = 10 ** decimals[sending]
    value = amount if coins[sending] == ETH_ADDRESS else 0
    swap.exchange(sending, receiving, amount, 0, {"from": bob, "value": value})

    assert swap.get_virtual_price() > virtual_price
